"""Meshtastic mesh status via meshtasticd's own TCP API (127.0.0.1:4403).

Uses the `meshtastic` Python library's TCPInterface — meshtasticd already owns the SX1262
directly (see software/meshtastic.md), so this app never touches /dev/serial0 or any serial
port. Confirmed working against this build's meshtasticd 2026-09-21.

Keeps ONE persistent interface for the app's lifetime rather than reconnecting per poll.
Originally this opened and closed a fresh TCPInterface every ~15s (a TTL cache, see build-log);
that hit a real race in the library's own teardown — closing right after the initial handshake
races its background reader thread, which reacts to the just-received "config complete" message
by firing an immediate heartbeat send on a now-closed socket (BrokenPipeError, logged repeatedly
by the library itself, not raised to our caller — it never broke `collect()`'s return value, just
spammed `docker logs`). A single long-lived connection sidesteps the race entirely: it's never
closed mid-session, and if the socket does drop, the next `collect()` call detects the dead
interface and reconnects once, from a clean process-lifetime lock rather than a tight loop.

Text messaging (added 2026-09-23) follows CyberDeck's MeshClient shape: a pubsub subscriber on
the library's receive topic fills a rolling in-memory buffer that the UI polls, and sends go out
through the same interface via sendText(). The buffer lives only in this process — a container
restart empties it, and anything received while no interface is connected is simply not seen.
main.py keeps the interface up with a background refresh so reception doesn't depend on someone
having the dashboard open.
"""
import asyncio
import threading
import time
from collections import deque

from .. import places
from . import mesh_radio

_IFACE = None
_LOCK = asyncio.Lock()
_CACHE: dict = {"at": 0.0, "data": {"state": "unavailable"}}
_TTL_S = 15.0

MAX_MESSAGES = 200
# Meshtastic's text payload limit is ~228 bytes after protobuf framing; 200 matches CyberDeck.
MAX_TEXT_BYTES = 200
_MESSAGES: deque = deque(maxlen=MAX_MESSAGES)
_MSG_LOCK = threading.Lock()  # appended from the library's reader thread, read from the event loop
_SUBSCRIBED = False
_NEXT_ID = 0  # monotonic per process; the UI keys on it, since the deque's length stops changing once full

# Every packet received from another node (any portnum, not only text) since this process started.
# The learning platform's "first packet heard" check needs this: text messages alone miss the
# NodeInfo/telemetry/position traffic that makes up most of a quiet mesh. Counts and link quality
# only — no payloads are kept.
_RX: dict = {"packets": 0, "last_ts": None, "last_snr": None, "last_rssi": None, "from": set()}

# This node's own transmit counters (LocalStats telemetry, which the library stores on our node
# entry). changed_at is stamped here when a value moves, so a send can later be upgraded from
# "queued" to "sent by the radio" only on evidence that came after it.
_STATS: dict = {"num_packets_tx": None, "air_util_tx": None, "changed_at": None}

# The radio's own log of the frequency and power it set (host bridge GET /mesh-radio, from the
# journal, which the container can't read). Cached separately: it only changes on a retune.
# Sends awaiting a Routing response (wantAck): packet id -> {msg_id, deadline}. The library never
# expires its own response handlers, so messages() does, after mesh_radio.RESPONSE_TIMEOUT_S.
_PENDING: dict = {}

_RADIO_LOG: dict = {"at": -1e9, "data": None}
_RADIO_LOG_TTL_S = 60.0


def _append(msg: dict) -> None:
    global _NEXT_ID
    with _MSG_LOCK:
        _NEXT_ID += 1
        msg["id"] = _NEXT_ID
        _MESSAGES.append(msg)


def _node_label(iface, node_id: str | None) -> str | None:
    try:
        user = (iface.nodes or {}).get(node_id, {}).get("user", {})
        return user.get("shortName") or user.get("longName")
    except Exception:
        return None


# A message's sender-place label is retried this long after receipt: a node's position often
# arrives after its first text. Past this, a later position would describe where they went next,
# not where they were when they sent it.
PLACE_RETRY_S = 3600
POSITION_STALE_S = 86400  # older than this, the header says how old


def _fmt_age(seconds: float) -> str:
    h = seconds / 3600
    return f"{h:.0f}h" if h < 48 else f"{h / 24:.0f}d"


def _sender_place(iface, node_id: str | None) -> str | None:
    """Rough location of `node_id` from its last NodeDB position, as a nearby place name. Never
    returns coordinates — only the label leaves this function (see app/places.py)."""
    if not node_id:
        return None
    try:
        pos = (iface.nodes or {}).get(node_id, {}).get("position") or {}
        lat, lon = pos.get("latitude"), pos.get("longitude")
        if lat is None and pos.get("latitudeI") is not None:
            lat, lon = pos["latitudeI"] * 1e-7, pos.get("longitudeI", 0) * 1e-7
        if lat is None or lon is None or (lat == 0 and lon == 0):  # 0,0 = no fix, not the Gulf of Guinea
            return None
        label = places.describe(lat, lon)
        if label and pos.get("time"):
            age = time.time() - pos["time"]
            if age > POSITION_STALE_S:
                label += f" (pos {_fmt_age(age)} old)"
        return label
    except Exception:
        return None


def _fill_places(iface) -> None:
    """Retry the place label for recent received messages that didn't have one yet. Runs from
    _read_sync (a worker thread). Never waits on the place list: until its background load is
    done this just starts it and returns; the next collect (15 s later) fills the labels."""
    if not places.loaded():
        places.preload()
        return
    if not places.available():
        return
    now = time.time()
    with _MSG_LOCK:
        pending = [m for m in _MESSAGES
                   if not m["mine"] and m.get("place") is None and now - m["ts"] < PLACE_RETRY_S]
    for m in pending:
        label = _sender_place(iface, m["from_id"])
        if label:
            with _MSG_LOCK:
                m["place"] = label


def _on_text(packet, interface):
    # Only the live interface: a stale one being torn down must not double-log.
    if interface is not _IFACE:
        return
    try:
        decoded = packet.get("decoded", {}) or {}
        from_id = packet.get("fromId")
        to_id = packet.get("toId")
        msg = {
            "ts": time.time(),
            "from_id": from_id,
            "from_name": _node_label(interface, from_id),
            "channel": packet.get("channel", 0),
            "direct": to_id not in (None, "^all"),
            "text": decoded.get("text", ""),
            "snr": packet.get("rxSnr"),
            "rssi": packet.get("rxRssi"),
            "mine": False,
            # Only once places.tsv is loaded — this is the library's reader thread and must not
            # wait on the load. Until then _fill_places labels it on a later collect.
            "place": _sender_place(interface, from_id) if places.loaded() else None,
        }
        _append(msg)
    except Exception:
        pass  # never let a malformed packet raise inside the library's reader thread


def _on_receive(packet, interface):
    if interface is not _IFACE:
        return
    try:
        frm = packet.get("from")
        my_num = getattr(getattr(interface, "myInfo", None), "my_node_num", None)
        if frm is None or frm == my_num:
            return
        # fromId is None for a node not yet in the NodeDB — its first packets must still count.
        from_id = packet.get("fromId") or f"!{frm:08x}"
        with _MSG_LOCK:
            _RX["packets"] += 1
            _RX["last_ts"] = time.time()
            _RX["last_snr"] = packet.get("rxSnr")
            _RX["last_rssi"] = packet.get("rxRssi")
            _RX["from"].add(from_id)
    except Exception:
        pass


def _connect_sync():
    global _SUBSCRIBED
    import meshtastic.tcp_interface  # imported lazily — protobuf/pypubsub init is not free
    from pubsub import pub

    if not _SUBSCRIBED:
        # Subscribed once per process; _on_text filters to whichever interface is current.
        pub.subscribe(_on_text, "meshtastic.receive.text")
        # Parent topic: pypubsub also delivers every meshtastic.receive.* subtopic here.
        pub.subscribe(_on_receive, "meshtastic.receive")
        _SUBSCRIBED = True
    return meshtastic.tcp_interface.TCPInterface(hostname="127.0.0.1")


def _preset_name(iface) -> str | None:
    """LONG_FAST -> "LongFast": what Meshtastic apps show for an unnamed primary channel."""
    try:
        from meshtastic.protobuf import config_pb2

        preset = iface.localNode.localConfig.lora.modem_preset
        enum = config_pb2.Config.LoRaConfig.ModemPreset.Name(preset)
        return "".join(part.capitalize() for part in enum.split("_"))
    except Exception:
        return None


def _alive(iface) -> bool:
    """Whether the interface is really connected. getMyNodeInfo() reads the library's cache and
    never touches the socket, so a dead meshtasticd can't be detected by reading status; the
    library clears isConnected and its reader thread exits when the stream drops."""
    if iface is None:
        return False
    try:
        if not iface.isConnected.is_set():
            return False
    except AttributeError:
        return False
    rx = getattr(iface, "_rxThread", None)  # private; guarded so a library change degrades safely
    if rx is not None and not rx.is_alive():
        return False
    return getattr(iface, "socket", 1) is not None


def _enum_name(enum, value) -> str | None:
    try:
        return enum.Name(value)
    except Exception:
        return None


def _radio_sync(iface) -> tuple[dict, list[dict]]:
    """Radio settings the transmit control states, and per-channel detail. Key bytes never leave
    this function: only whether a channel uses the published default key."""
    from meshtastic.protobuf import channel_pb2, config_pb2

    role = channel_pb2.Channel.Role
    lc = iface.localNode.localConfig
    lora = lc.lora
    region = _enum_name(config_pb2.Config.LoRaConfig.RegionCode, lora.region)
    preset = _enum_name(config_pb2.Config.LoRaConfig.ModemPreset, lora.modem_preset)
    chans = [(i, c) for i, c in enumerate(getattr(iface.localNode, "channels", []) or [])
             if c.role != role.DISABLED]

    def name_of(c):
        return c.settings.name or mesh_radio.preset_display_name(preset)

    prim = next((c for _, c in chans if c.role == role.PRIMARY), None)
    primary = name_of(prim) if prim is not None else None
    f = mesh_radio.lora_frequency(region, preset, lora.use_preset, lora.bandwidth, lora.channel_num,
                                  primary, lora.override_frequency, lora.frequency_offset)
    dbm, dbm_src = mesh_radio.power_dbm(lora.tx_power)
    user = iface.getMyUser() or {}
    pos = lc.position
    radio = {
        "region": region,
        "preset": preset,
        "use_preset": bool(lora.use_preset),
        "channel_num": lora.channel_num,
        "tx_enabled": bool(lora.tx_enabled),
        "tx_power_dbm": dbm,
        "tx_power_source": dbm_src,
        "primary": primary,
        "freq_mhz": f["mhz"] if f else None,
        "freq_slot": f["slot"] if f else None,
        "freq_slots": f["slots"] if f else None,
        "freq_source": f["source"] if f else None,
        "freq_check": "unchecked",
        "is_licensed": bool(user.get("isLicensed", False)),
        "mqtt_enabled": bool(iface.localNode.moduleConfig.mqtt.enabled),
        # The broker hostname (public, no credentials) and what map reporting shares.
        "mqtt_address": iface.localNode.moduleConfig.mqtt.address or None,
        "mqtt_map_reporting": bool(iface.localNode.moduleConfig.mqtt.map_reporting_enabled),
        "mqtt_map_precision_km": mesh_radio.precision_km(
            iface.localNode.moduleConfig.mqtt.map_report_settings.position_precision),
        "mqtt_map_interval_s": iface.localNode.moduleConfig.mqtt.map_report_settings.publish_interval_secs,
        # Whether the node has a position to broadcast; firmware semantics are unverified.
        "position_on": (bool(pos.fixed_position)
                        or pos.gps_mode == config_pb2.Config.PositionConfig.ENABLED),
    }
    detail = []
    for i, c in chans:
        own = mesh_radio.lora_frequency(region, preset, lora.use_preset, lora.bandwidth, 0,
                                        name_of(c), 0.0, lora.frequency_offset)
        detail.append({
            "index": i,
            "name": name_of(c) or f"channel-{i}",
            "role": _enum_name(role, c.role),
            "public": len(c.settings.psk) <= 1,  # empty = none, 1 byte = the published default key
            "uplink": bool(c.settings.uplink_enabled),
            "position_km": mesh_radio.precision_km(c.settings.module_settings.position_precision),
            "own_freq_mhz": own["mhz"] if own else None,
        })
    return radio, detail


def _local_stats(iface) -> dict:
    try:
        num = iface.myInfo.my_node_num
        ls = (iface.nodesByNum or {}).get(num, {}).get("localStats", {}) or {}
    except Exception:
        ls = {}
    tx, air = ls.get("numPacketsTx"), ls.get("airUtilTx")
    with _MSG_LOCK:
        if tx is not None and (tx, air) != (_STATS["num_packets_tx"], _STATS["air_util_tx"]):
            _STATS.update(num_packets_tx=tx, air_util_tx=air, changed_at=time.time())
        return dict(_STATS)


def _channel_list(iface) -> list[dict]:
    out = []
    for i, ch in enumerate(getattr(iface.localNode, "channels", []) or []):
        if getattr(ch, "role", 0) == 0:  # DISABLED
            continue
        name = ch.settings.name or (i == 0 and _preset_name(iface)) or f"channel-{i}"
        out.append({"index": i, "name": name})
    return out


def _web_ui_up() -> bool:
    """Whether meshtasticd's own web UI port answers; the dashboard links to it only when it does.
    meshtasticd listens on 9444 locally; `tailscale serve` publishes it on the tailnet as :9443
    (it can't share 9443 — tailscaled's tailnet-IP listener blocks meshtasticd's 0.0.0.0 bind)."""
    import socket

    try:
        with socket.create_connection(("127.0.0.1", 9444), timeout=0.5):
            return True
    except OSError:
        return False


def _read_sync(iface) -> dict:
    _fill_places(iface)
    info = iface.getMyNodeInfo() or {}
    user = info.get("user", {})
    metrics = info.get("deviceMetrics", {})
    nodes = getattr(iface, "nodes", {}) or {}
    with _MSG_LOCK:
        rx = {k: v for k, v in _RX.items() if k != "from"}
        rx_nodes = len(_RX["from"])
    try:
        radio, detail = _radio_sync(iface)
    except Exception:  # noqa: BLE001 — never let a config read break the status tile
        radio, detail = {}, []  # readiness then blocks sending ("no channels")
    return {
        "state": "running",
        "node_id": user.get("id"),
        "long_name": user.get("longName"),
        "battery_percent": metrics.get("batteryLevel"),
        "nodes_seen": len(nodes),  # NodeDB size, including this node and stale entries
        "rx_packets": rx["packets"],  # from other nodes, since webdash started
        "rx_nodes": rx_nodes,  # distinct other nodes heard since webdash started
        "last_rx_ts": rx["last_ts"],
        "last_rx_snr": rx["last_snr"],
        "last_rx_rssi": rx["last_rssi"],
        "channels": sorted({c["name"] for c in _channel_list(iface)}),
        "web_ui": _web_ui_up(),
        "radio": radio,
        "channel_detail": detail,
        "local_stats": _local_stats(iface),
    }


def _fetch_sync() -> dict:
    global _IFACE
    if not _alive(_IFACE):
        # A dropped stream leaves the old interface object behind; replace it, so messages() and
        # the send gate see "not connected" instead of stale channels.
        old, _IFACE = _IFACE, None
        if old is not None:
            try:
                old.close()
            except Exception:
                pass
        _IFACE = _connect_sync()
    try:
        return _read_sync(_IFACE)
    except Exception:
        # Stale/dead connection (meshtasticd restarted, socket dropped, etc.) — drop it and
        # reconnect once. If the reconnect also fails, let the exception propagate to collect(),
        # which reports "unreachable"; don't loop retrying within a single call.
        try:
            _IFACE.close()
        except Exception:
            pass
        _IFACE = _connect_sync()
        return _read_sync(_IFACE)


async def _radio_log() -> dict | None:
    now = time.monotonic()
    if now - _RADIO_LOG["at"] < _RADIO_LOG_TTL_S:
        return _RADIO_LOG["data"]
    import httpx  # lazily, like meshtastic: keeps this module importable by the host-side tests

    from .aiov2 import BRIDGE_BASE

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{BRIDGE_BASE}/mesh-radio")
            r.raise_for_status()
            data = r.json()
        data = data if data.get("ok") else None
    except (httpx.HTTPError, ValueError):
        data = None
    _RADIO_LOG["at"], _RADIO_LOG["data"] = now, data
    return data


def apply_radio_log(data: dict, log: dict | None) -> None:
    """Cross-check the computed frequency against the radio's log line. On disagreement the UI
    shows "unknown" rather than either number (senior-rf-engineer, 2026-10-11)."""
    radio = data.get("radio")
    if not radio or not log:
        return
    if log.get("tx_dbm") is not None:
        radio["tx_power_dbm"], radio["tx_power_source"] = int(log["tx_dbm"]), "journal"
    jf = log.get("freq_mhz")
    if jf is None:
        return
    if radio.get("freq_mhz") is None:
        radio.update(freq_mhz=jf, freq_source="radio log", freq_slot=None, freq_slots=None)
    else:
        radio["freq_check"] = "agrees" if abs(jf - radio["freq_mhz"]) <= 0.001 else "disagrees"


async def collect() -> dict:
    now = time.monotonic()
    if now - _CACHE["at"] < _TTL_S:
        return _CACHE["data"]
    async with _LOCK:
        if now - _CACHE["at"] < _TTL_S:  # re-check: another task may have refreshed while waiting
            return _CACHE["data"]
        try:
            data = await asyncio.wait_for(asyncio.to_thread(_fetch_sync), timeout=8.0)
        except Exception as exc:  # noqa: BLE001 — meshtasticd unreachable, bad handshake, etc.
            data = {"state": "unreachable", "error": str(exc)}
        if data.get("state") == "running":
            apply_radio_log(data, await _radio_log())
        _CACHE["at"], _CACHE["data"] = now, data
        return data


def _row(msg_id: int) -> dict | None:
    """The message row with this id. Caller holds _MSG_LOCK."""
    for m in reversed(_MESSAGES):
        if m["id"] == msg_id:
            return m
    return None


def _sweep_sends() -> None:
    """Expire unanswered sends, and mark a send's transmit counter rising after it."""
    now = time.time()
    iface = _IFACE
    with _MSG_LOCK:
        for pid, p in list(_PENDING.items()):
            if now < p["deadline"]:
                continue
            _PENDING.pop(pid, None)
            row = _row(p["msg_id"])
            if row is not None and row.get("tier") in ("queued", "mqtt_echo"):
                row["tier"], row["tier_text"] = "no_answer", mesh_radio.NO_ANSWER
            try:  # internal library dict; guarded so a library change degrades safely
                iface.responseHandlers.pop(pid, None)
            except Exception:
                pass
        tx, changed = _STATS["num_packets_tx"], _STATS["changed_at"]
        for m in _MESSAGES:
            if (m.get("mine") and not m.get("counter_rose") and m.get("tx_base") is not None
                    and tx is not None and tx > m["tx_base"] and changed and changed > m["ts"]
                    and m.get("tier") != "not_sent"):
                m["counter_rose"], m["counter_text"] = True, mesh_radio.COUNTER


def messages() -> dict:
    _sweep_sends()
    with _MSG_LOCK:
        msgs = [dict(m) for m in _MESSAGES]
    alive = _alive(_IFACE)
    channels = []
    if alive:
        try:
            channels = _channel_list(_IFACE)
        except Exception:
            pass
    return {"messages": msgs, "channels": channels, "connected": alive}


def with_tx(m: dict, aiov2: dict, services: dict) -> dict:
    """Add the transmit control's readiness and copy to a mesh status dict. Cheap and pure, so it
    runs on every status tick: a rail flip reaches the button within one tick even though the
    mesh read itself is cached for _TTL_S."""
    m = dict(m or {})
    if m.get("state") == "running":
        m["connected"] = _alive(_IFACE)
    m["tx"] = mesh_radio.readiness(m, aiov2, services)
    m["mqtt"] = mesh_radio.mqtt_model(m, services)
    radio = m.get("radio") or {}
    m["tx_copy"] = {
        "captions": mesh_radio.channel_captions(radio, m.get("channel_detail")),
        "legal": mesh_radio.LEGAL,
        "public": mesh_radio.PUBLIC,
        "power": mesh_radio.power_line(None, radio.get("tx_power_dbm")) if radio else None,
        "retries": mesh_radio.RETRIES,
        "no_retries": mesh_radio.NO_RETRIES,
        "byte_limit": mesh_radio.BYTE_LIMIT,
    }
    return m


def _on_routing(msg_id: int, holder: dict):
    """Response callback for one send. Runs on the library's reader thread: it only touches the
    message buffer under _MSG_LOCK, never the asyncio lock."""
    def on_response(packet):
        tier, text = mesh_radio.classify_response(packet)
        with _MSG_LOCK:
            row = _row(msg_id)
            if row is None:
                _PENDING.pop(holder.get("id"), None)
                return
            if tier == "mqtt_echo":
                # The firmware keeps retrying after an MQTT echo, so keep waiting for an RF result.
                row["tier"], row["tier_text"] = tier, text
                try:
                    holder["iface"]._addResponseHandler(holder["id"], on_response, ackPermitted=True)
                except Exception:
                    pass
                return
            _PENDING.pop(holder.get("id"), None)
            row["tier"], row["tier_text"] = tier, text
            if tier == "relayed":
                row["tier_sub"] = mesh_radio.RELAYED_SUB
            if tier == "not_sent":
                row["counter_rose"] = False  # a refused send never went out
                row.pop("counter_text", None)
    return on_response


def _send_sync(text: str, channel: int, msg_id: int, want_ack: bool = True) -> int:
    """Send, by default with wantAck so the radio reports whether a neighbour relayed it (and
    re-sends up to twice if none is heard). want_ack=False sends once with no relay check.
    Refuses when the interface is dead rather than connecting inside a send (the 8 s handshake)."""
    if not _alive(_IFACE):
        raise RuntimeError("meshtasticd not connected")
    from meshtastic.protobuf import portnums_pb2

    iface = _IFACE
    base = _local_stats(iface)["num_packets_tx"]
    port = portnums_pb2.PortNum.TEXT_MESSAGE_APP
    if not want_ack:
        pkt = iface.sendData(text.encode("utf-8"), portNum=port, wantAck=False,
                             channelIndex=channel)
        with _MSG_LOCK:
            row = _row(msg_id)
            if row is not None:
                row["packet_id"], row["tx_base"], row["relay_check"] = pkt.id, base, False
        return pkt.id
    holder = {"iface": iface}
    # sendData, not sendText: only sendData can mark the handler ackPermitted. Without it the
    # library drops ACKs and only NAKs would arrive (senior-rf-engineer review, 2026-10-11).
    pkt = iface.sendData(text.encode("utf-8"), portNum=port, wantAck=True,
                         onResponse=_on_routing(msg_id, holder), onResponseAckPermitted=True,
                         channelIndex=channel)
    holder["id"] = pkt.id
    with _MSG_LOCK:
        _PENDING[pkt.id] = {"msg_id": msg_id,
                            "deadline": time.time() + mesh_radio.RESPONSE_TIMEOUT_S}
        row = _row(msg_id)
        if row is not None:
            row["packet_id"], row["tx_base"], row["relay_check"] = pkt.id, base, True
    return pkt.id


def _set_mqtt_sync(enabled: bool) -> None:
    if not _alive(_IFACE):
        raise RuntimeError("meshtasticd not connected")
    node = _IFACE.localNode
    node.moduleConfig.mqtt.enabled = enabled
    # Sends the whole MQTT block back as the radio reported it, with only `enabled` changed. The
    # firmware saves it and restarts meshtasticd (AdminModule::saveChanges, shouldReboot).
    node.writeConfig("mqtt")


async def set_mqtt(enabled: bool) -> dict:
    """Turn the MQTT module on or off. Readiness is checked by the caller (main.py)."""
    async with _LOCK:
        try:
            await asyncio.wait_for(asyncio.to_thread(_set_mqtt_sync, enabled), timeout=8.0)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc) or type(exc).__name__}
        _CACHE["at"] = 0.0  # re-read the config as soon as the daemon is back
    word = "on" if enabled else "off"
    return {"ok": True, "enabled": enabled,
            "message": f"MQTT turned {word}. meshtasticd is restarting to apply it; this panel "
                       "reconnects on its own in about 15–30 s."}


def _discard(msg_id: int) -> None:
    with _MSG_LOCK:
        row = _row(msg_id)
        if row is not None:
            _MESSAGES.remove(row)


async def send_text(text: str, channel: int = 0, want_ack: bool = True) -> dict:
    """Broadcast `text` on channel index `channel`, asking for a relay check unless want_ack is
    False. Shares _LOCK with
    collect() so a send never races a reconnect swapping _IFACE out from under it. Readiness and
    channel validity are checked by the caller (main.py) against current status."""
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        return {"ok": False, "error": f"message is over {MAX_TEXT_BYTES} bytes"}
    # The library doesn't publish our own sends on the receive topic, so echo them. The row goes in
    # first so a fast Routing response always finds it; it is removed again if the send fails.
    _append(
        {"ts": time.time(), "from_id": None, "from_name": "me", "channel": channel,
         "direct": False, "text": text, "snr": None, "rssi": None, "mine": True,
         "place": None, "tier": "queued", "tier_text": None, "counter_rose": False}
    )
    with _MSG_LOCK:
        msg_id = _MESSAGES[-1]["id"]
    async with _LOCK:
        try:
            await asyncio.wait_for(asyncio.to_thread(_send_sync, text, channel, msg_id, want_ack),
                                   timeout=8.0)
        except Exception as exc:  # noqa: BLE001
            _discard(msg_id)
            return {"ok": False, "error": str(exc) or type(exc).__name__}
    radio = (_CACHE["data"] or {}).get("radio") or {}
    freq = radio.get("freq_mhz") if radio.get("freq_check") != "disagrees" else None
    queued = mesh_radio.QUEUED.format(mhz=f"{freq:g}") if freq else "Queued in meshtasticd."
    with _MSG_LOCK:
        row = _row(msg_id)
        if row is not None and row.get("tier") == "queued":
            row["tier_text"] = queued
    return {"ok": True, "tier": "queued", "message": queued, "freq_mhz": freq,
            "relay_check": want_ack}
