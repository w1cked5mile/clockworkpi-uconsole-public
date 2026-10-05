"""gpsd status via its raw JSON protocol (127.0.0.1:2947) — same approach used for the manual
`gpspipe -w` checks in docs/logs/build-log.md's 2026-09-21 entry, just automated.

No `gps3`/`gpsd-py3` dependency: gpsd's wire protocol is newline-delimited JSON over a plain TCP
socket, small enough to speak directly and one fewer package to track.
"""
import asyncio
import json
import time
from datetime import datetime

HOST, PORT = "127.0.0.1", 2947
WATCH_CMD = b'?WATCH={"enable":true,"json":true};\n'


async def collect() -> dict:
    try:
        reader, writer = await asyncio.wait_for(asyncio.open_connection(HOST, PORT), timeout=2.0)
    except (OSError, asyncio.TimeoutError):
        return {"state": "stopped"}

    # gpsd 3.25 sends several SKY reports a second; only some carry the `satellites` list, the
    # rest carry just DOPs and uSat/nSat. Keep the full one for counts, DOPs from any.
    tpv, sky, dops = None, None, {}
    try:
        writer.write(WATCH_CMD)
        await writer.drain()
        deadline = asyncio.get_event_loop().time() + 2.0
        while asyncio.get_event_loop().time() < deadline and (tpv is None or sky is None):
            try:
                line = await asyncio.wait_for(reader.readline(), timeout=1.0)
            except asyncio.TimeoutError:
                break
            if not line:
                break
            try:
                msg = json.loads(line)
            except ValueError:
                continue
            if msg.get("class") == "TPV":
                tpv = msg
            elif msg.get("class") == "SKY":
                dops.update({k: msg[k] for k in ("hdop", "pdop", "uSat", "nSat") if k in msg})
                if "satellites" in msg:
                    sky = msg
    finally:
        writer.close()

    mode = tpv.get("mode") if tpv else None
    satellites = sky.get("satellites") if sky else None
    has_fix = bool(tpv) and mode in (2, 3)
    lat = tpv.get("lat") if has_fix else None
    lon = tpv.get("lon") if has_fix else None
    return {
        "state": "running",
        "fix": {0: "unknown", 1: "none", 2: "2D", 3: "3D"}.get(mode, "unknown"),
        "lat": lat,
        "lon": lon,
        # Grid square computed here too, so labs, evidence and notes can use location without
        # ever handling lat/lon (the repo records location as a grid square only).
        "grid": maidenhead(lat, lon) if lat is not None and lon is not None else None,
        "satellites_visible": len(satellites) if satellites else dops.get("nSat", 0),
        "satellites_used": sum(1 for s in satellites or [] if s.get("used")) if satellites else dops.get("uSat", 0),
        "hdop": dops.get("hdop"),
        "pdop": dops.get("pdop"),
        "eph_m": tpv.get("eph") if has_fix else None,  # gpsd's horizontal error estimate
        "tpv_age_s": _age_s(tpv.get("time")) if tpv else None,
    }


def _age_s(iso: str | None) -> float | None:
    """Seconds since gpsd's TPV timestamp. Needs a correct system clock — which, with no RTC
    cell fitted, isn't guaranteed after an offline cold boot."""
    if not iso:
        return None
    try:
        t = datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
    return round(time.time() - t, 1)


def maidenhead(lat: float, lon: float) -> str:
    """6-character Maidenhead locator; same algorithm as maidenhead() in static/js/ui.js."""
    lon += 180.0
    lat += 90.0
    a = ord("A")
    field = chr(a + int(lon // 20)) + chr(a + int(lat // 10))
    square = str(int((lon % 20) // 2)) + str(int(lat % 10))
    sub = chr(ord("a") + int((lon % 2) * 12)) + chr(ord("a") + int((lat % 1) * 24))
    return field + square + sub
