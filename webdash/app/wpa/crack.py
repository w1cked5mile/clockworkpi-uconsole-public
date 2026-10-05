"""webdash -> wpa-audit-bridge crack client. Offloads a captured handshake to the GPU host
(gpu-host) and reports progress/result. Authorized-audit use only — the cap must be one this
webdash captured, which the bridge re-validates. The recovered PSK is returned to the authenticated
UI only; it is never persisted by the app.
"""
import httpx

from .capture import BRIDGE  # same host bridge (127.0.0.1:8766)


async def start(cap: str) -> dict:
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{BRIDGE}/crack", json={"cap": cap})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": f"crack bridge unreachable: {exc}"}


async def status() -> dict:
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{BRIDGE}/crack/status")
            return r.json()
    except (httpx.HTTPError, ValueError):
        return {"stage": "unavailable", "message": "crack bridge unreachable", "running": False}
