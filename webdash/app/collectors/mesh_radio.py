"""Pure helpers for the mesh transmit control: operating frequency, position precision, power
wording, send readiness, and the copy the UI shows. Stdlib only, no I/O, so it is unit-tested on
the host and in the container (tests/test_mesh_radio.py).

The wording here was reviewed by the senior-rf-engineer agent (2026-10-11). Rules it enforces:
never claim compliance ("legal under"), never say a message was sent without evidence, and never
show the configured 30 dBm, which the SX1262 clamps to 22 dBm.
"""

# Region band plans: start MHz, end MHz, channel spacing MHz (firmware RadioInterface.cpp RDEF).
# Regions not listed give an unknown frequency rather than a guess.
BAND = {"US": (902.0, 928.0, 0.0)}

# Modem preset -> bandwidth in kHz. Presets not listed give an unknown frequency.
PRESET_BW_KHZ = {
    "LONG_FAST": 250, "MEDIUM_SLOW": 250, "MEDIUM_FAST": 250, "SHORT_FAST": 250,
    "SHORT_SLOW": 250, "SHORT_TURBO": 500, "LONG_TURBO": 500, "LONG_MODERATE": 125,
    "LONG_SLOW": 125, "VERY_LONG_SLOW": 62.5,
}
CUSTOM_BW = {31: 31.25, 62: 62.5}  # lora.bandwidth codes for fractional bandwidths

# Display names whose spelling matches what the firmware hashes for an unnamed primary channel.
# Others (VERY_LONG_SLOW, LONG_MODERATE, newer presets) are unverified, so they give None.
TRUSTED_PRESET_NAMES = {"LONG_FAST", "LONG_SLOW", "MEDIUM_SLOW", "MEDIUM_FAST", "SHORT_FAST",
                        "SHORT_SLOW", "SHORT_TURBO", "LONG_TURBO"}

SX1262_MAX_DBM = 22
BYTE_LIMIT = 200

LEGAL = ("Transmits in the US 902–928 MHz ISM band (unlicensed, FCC Part 15 rules). "
         "You're responsible for operating within them.")
PUBLIC = ("Public channel: the key is published. Anyone with a Meshtastic radio can read it, it "
          "can be relayed beyond range, and others' gateways may post it online. Don't include "
          "your location or personal details.")
QUEUED = "Queued in meshtasticd for {mhz} MHz."
# Shown beside a send, since every send asks for a relay check (wantAck). Firmware ReliableRouter:
# NUM_RELIABLE_RETX = 3 transmissions in all; retry interval ≈7.7 s on a quiet LONG_FAST channel.
RETRIES = ("If no nearby node is heard repeating it, the radio re-sends it up to 2 more times, "
           "about 8 s apart.")
NO_RETRIES = ("Sends once, with no relay check: delivery shows only as queued, plus the "
              "transmit counter.")
# The transmit counter also counts beacons, relays and this send's own retries: a correlation.
COUNTER = ("Handed to the radio: its transmit counter rose after this message. The counter also "
           "counts the node's own beacons and relays.")
RELAYED = "Relayed: a nearby node repeated it over the air."
RELAYED_SUB = "Shows that one node received it and passed it on, not that anyone read it."
MQTT_ECHO = "Echoed by the MQTT server, which doesn't prove a radio heard it."
NO_RELAY = ("No relay heard after 3 sends. Nearby nodes may still have received it; the radio just "
            "didn't hear one repeat it.")
NO_ANSWER = ("No answer from the radio within 60 s, so delivery is unknown. Check its transmit "
             "counter.")
NOT_SENT = {
    "DUTY_CYCLE_LIMIT": "Not sent: the radio's airtime limit was reached.",
    "TOO_LARGE": "Not sent: the message is too large for one packet.",
    "NO_CHANNEL": "Not sent: the radio has no such channel.",
    "NO_INTERFACE": "Not sent: the radio has no interface to send on.",
    "BAD_REQUEST": "Not sent: the radio rejected the request.",
}
MQTT_LINE = ("This node's MQTT uplink is on for this channel: it may post the message online too, "
             "and an echo from the server can look like a relay.")
# A NAK for "no relay" arrives ≈23 s after the send on a quiet channel and up to ≈44 s on a busy
# one, so the UI waits this long before calling delivery unknown.
RESPONSE_TIMEOUT_S = 60


def classify_response(packet: dict) -> tuple[str, str]:
    """A Routing response to our wantAck broadcast -> (tier, copy). protobuf omits errorReason when
    it is NONE, so a missing reason means an ACK. The ACK comes from our own radio (an implicit
    ACK on hearing a rebroadcast), so the relayer is never named."""
    routing = (packet.get("decoded") or {}).get("routing") or {}
    reason = routing.get("errorReason", "NONE")
    if reason == "NONE":
        if packet.get("transportMechanism") == "TRANSPORT_MQTT":
            return "mqtt_echo", MQTT_ECHO
        return "relayed", RELAYED
    if reason == "MAX_RETRANSMIT":
        return "no_relay", NO_RELAY
    return "not_sent", NOT_SENT.get(reason, f"Not sent: the radio refused it ({reason}).")


def djb2(s: str) -> int:
    h = 5381
    for c in s.encode("utf-8"):
        h = (h * 33 + c) & 0xFFFFFFFF
    return h


def preset_display_name(preset: str | None) -> str | None:
    """LONG_FAST -> "LongFast", only for presets whose firmware name is known to match."""
    if preset not in TRUSTED_PRESET_NAMES:
        return None
    return "".join(part.capitalize() for part in preset.split("_"))


def lora_frequency(region, preset, use_preset, bandwidth, channel_num, name,
                   override_mhz=0.0, offset_mhz=0.0) -> dict | None:
    """The firmware's frequency rule (RadioInterface::applyModemConfig). Only the primary
    channel's name counts: secondaries transmit on the primary's frequency."""
    if override_mhz:
        return {"mhz": round(override_mhz + offset_mhz, 4), "source": "override",
                "slot": None, "slots": None}
    band = BAND.get(region)
    bw = PRESET_BW_KHZ.get(preset) if use_preset else CUSTOM_BW.get(bandwidth, bandwidth or None)
    if not band or not bw or not name:
        return None
    start, end, spacing = band
    # Integer kHz arithmetic, so a float floor can't drop a channel.
    n = round((end - start) * 1000) // round(spacing * 1000 + bw)
    slot = (channel_num - 1 if channel_num else djb2(name)) % n
    return {"mhz": round(start + bw / 2000 + slot * bw / 1000 + offset_mhz, 4),
            "source": "config", "slot": slot, "slots": n}


def precision_km(bits) -> float | str | None:
    """Meshtastic position precision: the top `bits` bits of each 1e-7-degree coordinate are kept.
    Half the resulting cell, in km at the equator. 0 = not shared, 32 = full precision."""
    if not bits:
        return None
    if bits >= 32:
        return "precise"
    return round(2 ** (32 - bits) * 1e-7 * 111.32 / 2, 1)


def _mw(dbm: float) -> str:
    mw = 10 ** (dbm / 10)
    return f"{float(f'{mw:.2g}'):g}"


def power_dbm(tx_power_set, journal_dbm=None) -> tuple[int, str]:
    """Power at the chip: the radio's own log line if we have it, else the clamp. A config value of
    0 means "region maximum", which the SX1262 clamps to 22 dBm."""
    if journal_dbm is not None:
        return int(journal_dbm), "journal"
    return min(tx_power_set or 30, SX1262_MAX_DBM), "clamped"


def power_line(tx_power_set, journal_dbm=None) -> str:
    dbm, _ = power_dbm(tx_power_set, journal_dbm)
    return f"Set to {dbm} dBm (≈{_mw(dbm)} mW) at the radio chip; not measured."


def _block(code, reason, fix=None):
    return {"can_send": False, "code": code, "reason": reason, "fix": fix}


def daemon_readiness(mesh: dict, services: dict, what: str = "nothing can be sent") -> dict | None:
    """The meshtasticd checks shared by every mesh control: None when the daemon is reachable."""
    mesh = mesh or {}
    svc = ((services or {}).get("meshtasticd") or {}) if (services or {}).get("state") == "ok" else {}
    if svc.get("crash_looping"):
        return _block("daemon_crash", f"meshtasticd is restarting in a loop, so {what}.",
                      "journalctl -u meshtasticd -n 50")
    if svc and svc.get("active") != "active":
        return _block("daemon_down", f"meshtasticd isn't running, so {what}.",
                      "sudo systemctl start meshtasticd")
    if mesh.get("state") != "running" or mesh.get("connected") is False:
        return _block("daemon_unreachable",
                      "meshtasticd is running but not answering on port 4403.",
                      "journalctl -u meshtasticd -n 50")
    return None


def readiness(mesh: dict, aiov2: dict, services: dict) -> dict:
    """Whether a send can go out, and if not, why and what clears it. Checked in this order, so the
    reason shown is the most fundamental one."""
    block = _block
    mesh = mesh or {}
    radio = mesh.get("radio") or {}
    daemon = daemon_readiness(mesh, services)
    if daemon:
        return daemon
    a = aiov2 or {}
    lora = (a.get("rails") or {}).get("LORA") if a.get("state") == "ok" else None
    if lora is None:
        return block("rail_unknown",
                     "LORA rail state unknown: the aiov2 bridge isn't answering, so this can't "
                     "tell if the radio is powered.", "systemctl status uconsole-aiov2-bridge")
    if not lora.get("on"):
        return block("rail_off",
                     "LORA rail off: the SX1262 is unpowered, so nothing would be transmitted.",
                     "Turn on the LORA rail switch below.")
    region = radio.get("region")
    if region == "UNSET":
        return block("region_unset", "No LoRa region is set, so the radio won't transmit.",
                     "meshtastic --host localhost --set lora.region US")
    if region and region not in BAND:
        return block("region_other",
                     f"Region is {region}; this dashboard only knows the US 902–928 MHz band plan.",
                     "see software/meshtastic.md")
    if radio.get("tx_enabled") is False:
        return block("tx_disabled",
                     "Transmit is turned off in the radio's config (lora.tx_enabled is false).",
                     "meshtastic --host localhost --set lora.tx_enabled true")
    if radio.get("is_licensed"):
        return block("licensed", "Ham mode set — out of this platform's scope.",
                     "see software/meshtastic.md")
    if not mesh.get("channel_detail"):
        return block("no_channels", "meshtasticd hasn't sent its channel list yet.")
    return {"can_send": True, "code": "ready", "reason": "", "fix": None}


def channel_captions(radio: dict, channels: list[dict]) -> list[dict]:
    """Per-channel copy for the transmit control. Every channel goes out on the primary's
    frequency, so a secondary gets a note saying its own community won't hear it."""
    radio = radio or {}
    freq = radio.get("freq_mhz")
    known = freq is not None and radio.get("freq_check") != "disagrees"
    primary = radio.get("primary")
    out = []
    for ch in channels or []:
        if not known:
            where = "Transmits in 902–928 MHz · frequency unknown"
            if radio.get("freq_check") == "disagrees":
                where += " (config and radio log disagree)"
        elif radio.get("freq_source") == "override":
            where = f"Transmits on {freq:g} MHz [override]"
        elif radio.get("freq_source") == "radio log":
            where = f"Transmits on {freq:g} MHz (from radio log)"
        else:
            where = f"Transmits on {freq:g} MHz (from config)"
        kind = "public channel" if ch.get("public") else "encrypted channel"
        caption = f"{where} · LoRa SX1262 · {kind} {ch.get('name')}"
        note = None
        own = ch.get("own_freq_mhz")
        if ch.get("role") != "PRIMARY" and known and own is not None and abs(own - freq) > 0.001:
            note = (f"Sent on {freq:g} MHz (set by primary {primary}). {ch.get('name')} nodes on "
                    f"{own:g} MHz won't hear it.")
        km = ch.get("position_km")
        if km is None or not radio.get("position_on"):
            position = "Position broadcast: off"
        elif km == "precise":
            position = f"This node also broadcasts its precise position on {ch.get('name')}"
        else:
            position = f"This node also broadcasts its position to ~{km:g} km on {ch.get('name')}"
        mqtt = MQTT_LINE if radio.get("mqtt_enabled") and ch.get("uplink") else None
        out.append({"index": ch.get("index"), "caption": caption, "note": note,
                    "public": bool(ch.get("public")), "position_line": position,
                    "mqtt_line": mqtt})
    return out


# --- MQTT uplink switch ---------------------------------------------------------------------------

DEFAULT_MQTT_BROKER = "mqtt.meshtastic.org"  # firmware Default.h, used when the address is blank
MQTT_RESTART = ("Applying it restarts meshtasticd (about 7 s, plus reconnecting). When it comes "
                "back, the node announces itself on the mesh, as on any restart.")
MQTT_OTHERS = ("Other nodes' gateways can still post your public-channel messages online, "
               "whatever this switch says.")
MQTT_SCOPE = "Only switches MQTT on or off: channel uplink settings and broker login are unchanged."


def mqtt_model(mesh: dict, services: dict) -> dict:
    """Readiness and copy for the MQTT on/off control. It doesn't transmit by itself, but toggling
    restarts meshtasticd, and the node announces itself on the mesh when it comes back."""
    mesh = mesh or {}
    radio = mesh.get("radio") or {}
    enabled = radio.get("mqtt_enabled")
    broker = radio.get("mqtt_address") or f"Meshtastic's default public broker ({DEFAULT_MQTT_BROKER})"
    uplink = [c.get("name") for c in mesh.get("channel_detail") or [] if c.get("uplink")]
    if enabled is None:
        caption, verb = "MQTT state unknown.", "Turn MQTT on/off"
    elif enabled:
        if uplink:
            caption = f"MQTT on: this node posts {', '.join(uplink)} traffic to {broker}."
        else:
            caption = f"MQTT on ({broker}), but no channel has uplink enabled, so nothing is posted."
        verb = "Turn MQTT off"
    else:
        caption = "MQTT off: this node posts nothing online."
        verb = f"Turn MQTT on (to {radio.get('mqtt_address') or DEFAULT_MQTT_BROKER})"
    note = None
    if enabled and radio.get("mqtt_map_reporting"):
        km = radio.get("mqtt_map_precision_km")
        mins = round((radio.get("mqtt_map_interval_s") or 0) / 60)
        where = "its precise position" if km == "precise" else (
            f"its position (~{km:g} km)" if isinstance(km, (int, float)) else "its position")
        every = f" every {mins} min" if mins else ""
        note = f"Map reporting on: publishes {where} to the public map{every}."
    blocked = daemon_readiness(mesh, services, what="MQTT can't be changed")
    if not blocked and enabled is None:
        blocked = _block("mqtt_unknown", "The radio hasn't reported its MQTT setting yet.")
    return {"enabled": enabled, "caption": caption, "note": note, "verb": verb,
            "restart": MQTT_RESTART, "detail": [MQTT_OTHERS, MQTT_SCOPE],
            "ready": blocked or {"can_send": True, "code": "ready", "reason": "", "fix": None}}
