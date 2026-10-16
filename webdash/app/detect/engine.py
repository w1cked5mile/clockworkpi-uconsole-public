"""The Detect watch: while it's on, poll what Kismet has heard and fold rule matches into the log.

Receive-only. It reads Kismet's REST API (the same authenticated API collectors/kismet.py and
survey/snapshot.py use) and nothing else; it never asks Kismet to do anything. Two inputs:

  * Kismet's device table, only devices updated since the last poll
    (POST /devices/last-time/<ts>/devices.json with the survey's field simplification), matched
    against the owner's rules (rules.py).
  * Kismet's own alerts since the last poll (GET /alerts/last-time/<ts>/alerts.json). These are
    Kismet's built-in detections, logged as they are; the frame addresses in them are what the
    frames claim, not proof of the sender.

*Unverified on this build:* both last-time endpoints and the kismet.alert.* field names are taken
from Kismet's REST documentation and haven't yet been exercised against the running Kismet
2025.09. Parsing is defensive, so a schema difference reads as "nothing new" and is reported in
the watch state's last_error rather than raising. Settle with the curl lines in
software/webdash.md, "Detect".

The BLE half (a passive listener on hci1) is not built yet; the state says so.
"""
import asyncio
import json
import time

import httpx

from ..collectors.kismet import _credentials
from ..survey import snapshot
from . import rules as rules_mod
from . import store
from .observe import fold

KISMET = "http://127.0.0.1:2501"
POLL_S = 10.0
# Coverage intervals join across polls up to this gap; a longer gap is a break in listening.
COVERAGE_GAP_S = POLL_S * 3
# On switching the watch on, look back this far so a device heard just before isn't missed.
LOOKBACK_S = 60

_runtime = {"since": None, "last_poll": None, "last_error": None, "rules": [], "rule_errors": [],
            "rules_loaded": 0.0}


def _rules() -> tuple[list[dict], list[str]]:
    # Re-read at most every 10 s, so an edit to the rules file is picked up without a restart.
    if time.time() - _runtime["rules_loaded"] >= POLL_S:
        _runtime["rules"], _runtime["rule_errors"] = rules_mod.load()
        _runtime["rules_loaded"] = time.time()
    return _runtime["rules"], _runtime["rule_errors"]


async def _fetch(client: httpx.AsyncClient, since: float) -> tuple[list[dict], list[dict]]:
    auth = _credentials()
    ts = int(since)
    r = await client.post(f"{KISMET}/devices/last-time/{ts}/devices.json", auth=auth,
                          data={"json": json.dumps({"fields": snapshot.FIELDS})})
    r.raise_for_status()
    rows = r.json()
    devices = [snapshot._reduce(d) for d in rows if isinstance(d, dict)] if isinstance(rows, list) else []
    r = await client.get(f"{KISMET}/alerts/last-time/{ts}/alerts.json", auth=auth)
    r.raise_for_status()
    body = r.json()
    alerts = body.get("kismet.alert.list", []) if isinstance(body, dict) else body
    return devices, [a for a in alerts if isinstance(a, dict)] if isinstance(alerts, list) else []


async def poll_once(status: dict | None) -> None:
    st = store.state()
    if not st["armed"]:
        _runtime["since"] = None
        return
    rules, _ = _rules()
    k = (status or {}).get("kismet") or {}
    if k.get("state") != "running":
        return
    now = time.time()
    # First poll after the watch starts (or after an app restart with it on): look back a minute
    # before it was switched on, but never more than five minutes into the past.
    since = _runtime["since"] or max(st["armed_since"] or now, now - 300) - LOOKBACK_S
    grid = ((status or {}).get("gps") or {}).get("grid")
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            devices, alerts = await _fetch(client, since)
    except (httpx.HTTPError, ValueError) as exc:
        _runtime["last_error"] = f"Kismet read failed: {exc}"
        return
    fold(devices, alerts, rules, grid)
    store.mark_listening("wifi", now, COVERAGE_GAP_S)
    # Kismet's last-time is inclusive and second-resolution; overlap by a poll so nothing falls
    # between two reads. upsert() ignores re-reads of the same sighting.
    _runtime["since"] = now - POLL_S
    _runtime["last_poll"] = now
    _runtime["last_error"] = None


async def run(get_status) -> None:
    """Background loop, started with the app. One bad poll never stops it."""
    while True:
        try:
            await poll_once(get_status())
        except Exception as exc:  # noqa: BLE001
            _runtime["last_error"] = f"watch poll failed: {exc!r}"
            print(f"detect: {_runtime['last_error']}", flush=True)
        await asyncio.sleep(POLL_S)


def wifi_state(status: dict | None, armed: bool) -> dict:
    """The Wi-Fi source's state for the watch line: (level, code, words)."""
    a = (status or {}).get("aiov2") or {}
    rails = a.get("rails") or {}
    usb = rails.get("USB", {}).get("on") if a.get("state") == "ok" and "USB" in rails else None
    k = ((status or {}).get("kismet") or {}).get("state")
    if usb is False:
        return {"level": "off", "code": "rail_off", "words": "USB rail off"}
    if k == "stopped":
        return {"level": "off", "code": "kismet_stopped", "words": "Kismet stopped"}
    if k == "locked":
        return {"level": "action", "code": "kismet_locked", "words": "Kismet login needed"}
    if k != "running":
        return {"level": "err", "code": "kismet_error", "words": "Kismet unreachable"}
    if not armed:
        return {"level": "off", "code": "watch_off", "words": "watch off"}
    if _runtime["last_error"]:
        return {"level": "err", "code": "read_error", "words": _runtime["last_error"]}
    return {"level": "ok", "code": "listening", "words": "listening"}


def status_summary(status: dict | None) -> dict:
    """The small block the 3 s status snapshot carries as data["detect"]."""
    st = store.state()
    rules, errors = _rules()
    return {
        "armed": st["armed"],
        "armed_since": st["armed_since"],
        "wifi": wifi_state(status, st["armed"]),
        "ble": {"level": "off", "code": "not_built", "words": "BLE listener not installed"},
        "rules": {"count": len(rules), "wifi": sum(r["radio"] == "wifi" for r in rules),
                  "ble": sum(r["radio"] == "ble" for r in rules), "errors": errors[:10]},
        "last_poll": _runtime["last_poll"],
        **store.summary(),
    }
