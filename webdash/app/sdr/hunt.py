"""webdash -> sdr-bridge client (127.0.0.1:8767) for the broadcast/airband hunt.

Receive-only. The bridge runs the rtl_power sweep on the host (the container has no /dev access) and
brackets readsb (the shared tuner). See docs/reference/webdash-architecture.md and software/sdr-stack.md.
"""
import httpx

BRIDGE = "http://127.0.0.1:8767"
BANDS = ("fm", "airband")


async def start(band: str) -> dict:
    if band not in BANDS:
        return {"ok": False, "error": f"band must be one of {list(BANDS)}"}
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{BRIDGE}/hunt", json={"band": band})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": f"SDR bridge unreachable: {exc}"}


async def status() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{BRIDGE}/hunt/status")
            return r.json()
    except (httpx.HTTPError, ValueError):
        return {"stage": "unavailable", "message": "SDR bridge unreachable", "stations": [], "running": False}


async def scan_status() -> dict:
    """Live airband-scanner state from the bridge: which frequency it's parked on (active), or
    None while sweeping between channels."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{BRIDGE}/scan/status")
            return r.json()
    except (httpx.HTTPError, ValueError):
        return {"stage": "unavailable", "active": None, "channels": []}


async def set_adsb(action: str) -> dict:
    """Start/stop ADS-B (readsb) as the chosen SDR application via the host bridge. readsb is
    systemctl-disabled on this build, so the rail coming on no longer starts it — this does."""
    if action not in ("start", "stop"):
        return {"ok": False, "error": "action must be start or stop"}
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            r = await client.post(f"{BRIDGE}/adsb", json={"action": action})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": f"SDR bridge unreachable: {exc}"}
