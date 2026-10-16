"""One passive snapshot of Kismet's device table, reduced to the fields a survey needs.

Kismet (2025.09 on this build) exposes its device list over the same authenticated REST API the
kismet.py collector already reads. This asks for a narrow set of fields via Kismet's field-
simplification mechanism (a `json={"fields": [...]}` POST variable), so the device objects come
back small rather than as Kismet's full multi-kilobyte-per-device records.

It is receive-only: it reads what Kismet has already heard. No MACs leave this process except
into the survey store, which lives in the read-write data dir outside git (same boundary as the
WPA allowlist and captures).

Not yet exercised against live Kismet on this hardware — the field paths below are from Kismet's
documented schema and must be confirmed with a running Kismet before the numbers are trusted
(see docs/reference/webdash-architecture.md, "Wi-Fi survey"). The parsing is defensive: any field
Kismet omits simply reads as None rather than raising, so an API or schema drift degrades the
snapshot instead of breaking the waypoint.
"""
import httpx

from ..collectors.kismet import _credentials
from . import rf

DEVICES_URL = "http://127.0.0.1:2501/devices/views/all/devices.json"

# [kismet field path, stable alias] — Kismet returns each device as {alias: value}. The signal
# paths dereference into the base signal object; a device Kismet has only ever heard once may not
# have every signal sub-field, hence the defensive .get() in _reduce().
FIELDS = [
    ["kismet.device.base.macaddr", "mac"],
    ["kismet.device.base.phyname", "phy"],
    ["kismet.device.base.type", "type"],
    ["kismet.device.base.commonname", "name"],
    ["kismet.device.base.channel", "channel"],
    ["kismet.device.base.frequency", "freq_khz"],
    ["kismet.device.base.manuf", "manuf"],
    ["kismet.device.base.crypt", "crypt"],
    ["kismet.device.base.last_time", "last_time"],
    ["kismet.device.base.signal/kismet.common.signal.last_signal", "signal_dbm"],
    ["kismet.device.base.signal/kismet.common.signal.max_signal", "max_signal_dbm"],
    ["kismet.device.base.signal/kismet.common.signal.min_signal", "min_signal_dbm"],
    # Noise: on the mt76 path this comes back 0 (a placeholder, not a real floor), so SNR is not
    # computed. Kept so the "no SNR" state is observed, not assumed (confirmed 2026-10-08).
    ["kismet.device.base.signal/kismet.common.signal.last_noise", "noise_dbm"],
    ["kismet.device.base.packets.total", "packets_total"],
    ["kismet.device.base.datasize", "datasize"],
    ["dot11.device/dot11.device.num_associated_clients", "num_clients"],
    # The SSID string lives in the last-beacon record (Kismet 2025.09). The flat
    # dot11.device.last_beaconed_ssid field is deprecated and returns integer 0 when empty, so it
    # is NOT used. This nested path dereferences to the advertised SSID string ("" for a hidden
    # network); field simplification returns 0/null when the record is absent (e.g. a client).
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ssid", "ssid"],
    # Channel geometry (for width/overlap) and contention, all read from the last beacon record.
    # Confirmed populated on this build 2026-10-08: ht_mode="HT80", ht_center_1 in MHz,
    # dot11e_channel_utilization_perc is a ready-made percent (not a raw 0-255).
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.channel", "adv_channel"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ht_mode", "ht_mode"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.ht_center_1", "ht_center1"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.dot11e_qbss", "qbss_present"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.dot11e_channel_utilization_perc", "qbss_util_pct"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.dot11e_qbss_stations", "qbss_stations"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.maxrate", "maxrate"],
    ["dot11.device/dot11.device.last_beaconed_ssid_record/dot11.advertisedssid.dot11r_mobility_domain_id", "mobility_domain"],
]


async def capture() -> dict:
    """Pull and reduce Kismet's current device table.

    Returns {"ok": True, "devices": [...], "device_count": n} on success, or
    {"ok": False, "error": ...} if Kismet is down, locked (no admin login set), or unreachable.
    A failed snapshot does not raise — the caller records the waypoint with the error noted, so a
    survey can still be walked past a point where Kismet happened to be restarting.
    """
    creds = _credentials()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.post(DEVICES_URL, auth=creds,
                                  data={"json": _fields_json()})
    except httpx.ConnectError:
        return {"ok": False, "error": "Kismet is not running"}
    except httpx.HTTPError as exc:
        return {"ok": False, "error": f"Kismet request failed: {exc}"}

    if r.status_code in (401, 403):
        return {"ok": False, "error": "Kismet is running but its admin login is not set"}
    if r.status_code != 200:
        return {"ok": False, "error": f"Kismet returned HTTP {r.status_code}"}
    try:
        rows = r.json()
    except ValueError:
        return {"ok": False, "error": "Kismet returned a non-JSON device list"}
    if not isinstance(rows, list):
        return {"ok": False, "error": "unexpected Kismet device-list shape"}

    devices = [_reduce(row) for row in rows if isinstance(row, dict)]
    return {"ok": True, "devices": devices, "device_count": len(devices)}


def _fields_json() -> str:
    import json
    return json.dumps({"fields": FIELDS})


def _reduce(row: dict) -> dict:
    """One Kismet device → the flat record the survey keeps. Missing fields read as None.

    `channel` is normalized to a string (Kismet gives e.g. "6", "36", "149", or "" for a device
    with no settled channel). Frequency is kept in kHz as Kismet reports it; the band is derived
    in analysis, not here."""
    def g(key):
        v = row.get(key)
        return v if v not in ("", None) else None

    sig = g("signal_dbm")
    # SSID: only a non-empty string is a real SSID. Kismet returns integer 0 for an absent record
    # and "" for a hidden network — both read as None (hidden/unknown), never as a value.
    ssid = g("ssid")
    ssid = ssid if isinstance(ssid, str) and ssid else None
    # commonname is the SSID for a named AP but falls back to the MAC for a hidden one, so drop it
    # when it just echoes the MAC — otherwise a hidden AP would appear "named" after its address.
    name = g("name")
    if isinstance(name, str) and name.upper() == (g("mac") or "").upper():
        name = None

    # Primary channel: the beacon's advertised channel is more reliable than the base channel for a
    # hopping capture; fall back to the base channel.
    primary = g("adv_channel") if g("adv_channel") is not None else g("channel")
    primary = str(primary) if primary is not None else None
    freq_khz = g("freq_khz")

    # Channel geometry (width/center/span) for overlap math — see rf.py.
    ht_mode = g("ht_mode")
    width = rf.width_mhz(ht_mode)
    p_center = rf.channel_center_mhz(primary, freq_khz)
    lo, hi, center, width_mhz, width_source = rf.occupied_span_mhz(
        p_center, width, g("ht_center1"), ht_mode)

    # Noise 0 is a placeholder (no real floor on this radio) → None, so no bogus SNR downstream.
    noise = g("noise_dbm")
    noise = noise if isinstance(noise, (int, float)) and noise < 0 else None

    return {
        "mac": g("mac"),
        "phy": g("phy"),
        "type": g("type"),
        "name": name,
        "ssid": ssid,
        "channel": primary,
        "freq_khz": freq_khz,
        "manuf": g("manuf"),
        "crypt": g("crypt"),
        "signal_dbm": sig,
        "max_signal_dbm": g("max_signal_dbm"),
        "min_signal_dbm": g("min_signal_dbm"),
        "noise_dbm": noise,
        "last_time": g("last_time"),
        # Channel geometry
        "ht_mode": ht_mode,
        "width_mhz": width_mhz,
        "center_mhz": round(center, 1) if center is not None else None,
        "span_lo_mhz": round(lo, 1) if lo is not None else None,
        "span_hi_mhz": round(hi, 1) if hi is not None else None,
        "width_source": width_source,
        # Contention / load
        "num_clients": g("num_clients"),
        "qbss_present": bool(g("qbss_present")),
        "qbss_util_pct": round(g("qbss_util_pct"), 1) if isinstance(g("qbss_util_pct"), (int, float)) else None,
        "qbss_stations": g("qbss_stations"),
        "maxrate": g("maxrate"),
        "mobility_domain": g("mobility_domain"),
        "packets_total": g("packets_total"),
        "datasize": g("datasize"),
    }
