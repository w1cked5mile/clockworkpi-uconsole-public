"""Turn what Kismet heard into contact-log observations, and fold a poll's worth into the store.

Pure stdlib (no httpx), so the unit tests run on the host: engine.py does the network reads and
hands the decoded device and alert lists here.
"""
import time

from . import rules as rules_mod
from . import store

# Kismet's own alerts that name a deauthentication/disassociation flood. Everything else Kismet
# raises is logged under "other" with Kismet's header as its name.
DEAUTH_ALERTS = {"DEAUTHFLOOD", "BCASTDISCON"}


def _mac_type(mac: str | None) -> str | None:
    """'local' when the 802 locally administered bit is set (a randomized or assigned address),
    else 'global' (IEEE-assigned, so its OUI means something)."""
    try:
        return "local" if int(mac.split(":")[0], 16) & 0x02 else "global"
    except (AttributeError, ValueError, IndexError):
        return None


def device_observation(dev: dict, rule: dict, grid: str | None) -> dict:
    """One reduced Kismet device (snapshot._reduce) that matched `rule` → a store observation."""
    mac = dev.get("mac")
    return {
        "key": f"kismet-device:{rule['class']}:{(mac or '').upper()}",
        "cls": rule["class"], "source": "kismet-device", "radio": "wifi",
        "name": dev.get("name") or dev.get("ssid"), "ident": mac, "addr_type": _mac_type(mac),
        "ssid": dev.get("ssid"), "channel": dev.get("channel"), "rssi": dev.get("signal_dbm"),
        "manuf": dev.get("manuf"), "grid": grid, "ts": dev.get("last_time") or time.time(),
        "rule_id": rule["id"], "rule_text": rules_mod.describe(rule),
        "confidence": rule["confidence"], "detail": rule.get("note") or None,
    }


def _g(a: dict, key: str):
    v = a.get(f"kismet.alert.{key}")
    return v if v not in ("", None, 0, "00:00:00:00:00:00") else None


def alert_observation(alert: dict, grid: str | None) -> dict | None:
    """One Kismet alert → a store observation, or None if it has no header."""
    header = _g(alert, "header")
    if not isinstance(header, str):
        return None
    mac = _g(alert, "transmitter_mac") or _g(alert, "source_mac")
    deauth = header.upper() in DEAUTH_ALERTS
    text = _g(alert, "text")
    return {
        "key": f"kismet-alert:{header}:{(mac or '').upper()}",
        "cls": "deauth_flood" if deauth else "other", "source": "kismet-alert", "radio": "wifi",
        "name": header, "ident": mac, "addr_type": _mac_type(mac), "ssid": None,
        "channel": str(_g(alert, "channel")) if _g(alert, "channel") is not None else None,
        "rssi": None, "manuf": None, "grid": grid, "ts": _g(alert, "timestamp") or time.time(),
        "rule_id": f"kismet:{header}", "rule_text": f"Kismet's built-in alert {header}",
        "confidence": "medium" if deauth else "low",
        "detail": text[:400] if isinstance(text, str) else None,
    }


def fold(devices: list[dict], alerts: list[dict], rules: list[dict], grid: str | None) -> list[dict]:
    """Match a poll's worth of devices and alerts and write them to the store → the new records."""
    new = []
    for dev in devices:
        rule = rules_mod.match(dev, rules, "wifi")
        if rule:
            rec, is_new = store.upsert(device_observation(dev, rule, grid), flush=False)
            if is_new:
                new.append(rec)
    for a in alerts:
        obs = alert_observation(a, grid)
        if obs:
            rec, is_new = store.upsert(obs, flush=False)
            if is_new:
                new.append(rec)
    if devices or alerts:
        store.flush()
    return new


