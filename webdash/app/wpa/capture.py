"""webdash -> wpa-audit-bridge client (127.0.0.1:8766) for authorized WPA capture.

The app checks the allowlist here too (defense in depth), but the bridge and the root capture script
are the real enforcement points — they re-check it where the privileged commands actually run.
"""
import httpx

from . import allowlist

BRIDGE = "http://127.0.0.1:8766"


async def start(bssid: str, channel: int | None = None) -> dict:
    if not allowlist.is_authorized(bssid):
        return {"ok": False, "error": f"{bssid} is not on the authorized allowlist"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{BRIDGE}/capture", json={"bssid": bssid, "channel": channel})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": f"capture bridge unreachable: {exc}"}


async def status() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{BRIDGE}/capture/status")
            return r.json()
    except (httpx.HTTPError, ValueError):
        return {"stage": "unavailable", "message": "capture bridge unreachable", "running": False}


async def cancel() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{BRIDGE}/capture/cancel", json={})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}
