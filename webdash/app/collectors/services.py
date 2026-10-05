"""systemd state of the services webdash reads, via the host bridge's GET /services.

The container can't ask systemd itself (no D-Bus socket, and it shouldn't get one). The bridge
already runs on the host, so it answers with a fixed, argument-free `systemctl show`. This is how
the dashboard and the lab engine tell "stopped" from "crash-looping" — e.g. readsb restarting in a
loop is the normal state while the SDR rail is off (see adsb.py).
"""
import httpx

from .aiov2 import BRIDGE_BASE


async def collect() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{BRIDGE_BASE}/services")
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"state": "unavailable", "error": str(exc)}
    if not data.get("ok"):
        # An older bridge without /services answers 404 -> raise_for_status above; this is the
        # bridge reporting that systemctl itself failed.
        return {"state": "error", "error": data.get("error")}
    return {"state": "ok", **data.get("services", {})}
