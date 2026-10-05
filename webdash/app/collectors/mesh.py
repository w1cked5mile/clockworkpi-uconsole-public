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
    info = iface.getMyNodeInfo() or {}
    user = info.get("user", {})
    metrics = info.get("deviceMetrics", {})
    nodes = getattr(iface, "nodes", {}) or {}
    with _MSG_LOCK:
        rx = {k: v for k, v in _RX.items() if k != "from"}
        rx_nodes = len(_RX["from"])
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
    }


def _fetch_sync() -> dict:
    global _IFACE
    if _IFACE is None:
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
        _CACHE["at"], _CACHE["data"] = now, data
        return data


def messages() -> dict:
    with _MSG_LOCK:
        msgs = list(_MESSAGES)
    channels = []
    if _IFACE is not None:
        try:
            channels = _channel_list(_IFACE)
        except Exception:
            pass
    return {"messages": msgs, "channels": channels, "connected": _IFACE is not None}


def _send_sync(text: str, channel: int) -> None:
    global _IFACE
    if _IFACE is None:
        _IFACE = _connect_sync()
    _IFACE.sendText(text, channelIndex=channel)


async def send_text(text: str, channel: int = 0) -> dict:
    """Broadcast `text` on channel index `channel`. Shares _LOCK with collect() so a send never
    races a reconnect swapping _IFACE out from under it."""
    if len(text.encode("utf-8")) > MAX_TEXT_BYTES:
        return {"ok": False, "error": f"message is over {MAX_TEXT_BYTES} bytes"}
    async with _LOCK:
        try:
            await asyncio.wait_for(asyncio.to_thread(_send_sync, text, channel), timeout=8.0)
        except Exception as exc:  # noqa: BLE001
            return {"ok": False, "error": str(exc) or type(exc).__name__}
    # The library doesn't publish our own sends on the receive topic — echo them so the
    # conversation reads both ways.
    _append(
        {"ts": time.time(), "from_id": None, "from_name": "me", "channel": channel,
         "direct": False, "text": text, "snr": None, "rssi": None, "mine": True}
    )
    return {"ok": True}
