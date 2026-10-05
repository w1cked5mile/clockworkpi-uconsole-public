"""tar1090/readsb status via the aircraft.json tar1090 already serves at :80.

readsb crash-loops whenever the SDR rail is off (`aiov2_ctl SDR off`, the default at boot — see
software/aiov2_ctl.md) since there's then no RTL-SDR for it to open. Confirmed 2026-09-21 via
`journalctl -u readsb`: `FATAL: rtlsdr: no supported devices found`. That is this build's normal
resting state, not an error — report it as "stopped", not surface a traceback.
"""
import time

import httpx

AIRCRAFT_URL = "http://127.0.0.1/tar1090/data/aircraft.json"

# Previous (monotonic time, readsb "messages" counter) for the rate. The counter is cumulative
# since readsb started, so a drop means readsb restarted — the rate is unknown for that interval.
_LAST: dict = {"t": None, "messages": None}


def _rate(messages) -> float | None:
    now = time.monotonic()
    prev_t, prev_m = _LAST["t"], _LAST["messages"]
    _LAST["t"], _LAST["messages"] = now, messages
    if not isinstance(messages, (int, float)) or prev_m is None or prev_t is None:
        return None
    if messages < prev_m or now <= prev_t:
        return None
    return round((messages - prev_m) / (now - prev_t), 1)


async def collect() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(AIRCRAFT_URL)
    except httpx.ConnectError:
        return {"state": "stopped"}
    except httpx.HTTPError as exc:
        return {"state": "unavailable", "error": str(exc)}

    if r.status_code == 404:
        _LAST["t"] = _LAST["messages"] = None
        # lighttpd is up but readsb hasn't written /run/readsb/aircraft.json yet —
        # crash-looping (SDR rail off) or still starting.
        return {"state": "stopped"}
    if r.status_code != 200:
        return {"state": "unavailable", "http_status": r.status_code}

    try:
        data = r.json()
    except ValueError:
        return {"state": "unavailable", "error": "non-JSON response"}
    aircraft = data.get("aircraft", [])
    return {
        "state": "running",
        "aircraft_count": len(aircraft),
        "with_position": sum(1 for a in aircraft if "lat" in a and "lon" in a),
        "messages_per_s": _rate(data.get("messages")),
    }
