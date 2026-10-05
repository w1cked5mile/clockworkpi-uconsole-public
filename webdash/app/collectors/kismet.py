"""Kismet status via its own REST API (127.0.0.1:2501).

Kismet is off by default on this build (see software/kismet.md) and its web API requires an
admin login before most endpoints work (first-run sets it via the Kismet web UI itself). This
app does not store its own Kismet credentials: it reads Kismet's *own* auth file read-only
(WEBDASH_KISMET_AUTH_FILE, Kismet's ~/.kismet/kismet_httpd.conf bind-mounted in), so there is a
single source of truth and a password rotation on the host is picked up with no redeploy.

Both "not running" and "running but locked" (auth file missing/unreadable, or creds rejected)
are normal, expected states here, not failures to alarm on.
"""
import os

import httpx

from .aiov2 import BRIDGE_BASE

STATUS_URL = "http://127.0.0.1:2501/system/status.json"
AUTH_FILE = os.environ.get("WEBDASH_KISMET_AUTH_FILE", "/secrets/kismet_httpd.conf")
VALID_ACTIONS = ("start", "stop")


def _credentials() -> tuple[str, str] | None:
    """(username, password) from Kismet's httpd auth file, or None if unavailable.

    Read on each call: the file is tiny, and this lets a host-side password rotation take
    effect without restarting the container."""
    user = password = None
    try:
        with open(AUTH_FILE) as f:
            for line in f:
                key, _, val = line.partition("=")
                key = key.strip()
                if key == "httpd_username":
                    user = val.strip()
                elif key == "httpd_password":
                    password = val.strip()
    except OSError:
        return None
    return (user, password) if user and password else None


async def collect() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(STATUS_URL, auth=_credentials())
    except httpx.ConnectError:
        return {"state": "stopped"}
    except httpx.HTTPError as exc:
        return {"state": "unavailable", "error": str(exc)}

    if r.status_code in (401, 403):
        return {"state": "locked", "detail": "Kismet is running but needs its admin login set"}
    if r.status_code != 200:
        return {"state": "unavailable", "http_status": r.status_code}

    try:
        data = r.json()
    except ValueError:
        return {"state": "unavailable", "error": "non-JSON response"}
    return {
        "state": "running",
        "devices": data.get("kismet.system.devices.count"),
        "memory_rss_mb": data.get("kismet.system.memory.rss", 0) // (1024 * 1024)
        if data.get("kismet.system.memory.rss")
        else None,
    }


async def control(action: str) -> dict:
    """Start or stop Kismet via the host bridge, which drives a user systemd service
    (host-helpers/kismet-user.service) — see docs/reference/webdash-architecture.md. Kismet runs
    passive/receive-only, within the repo's legal posture. The route is responsible for the auth
    gate; this validates again since it reaches a real control path."""
    if action not in VALID_ACTIONS:
        return {"ok": False, "error": "action must be 'start' or 'stop'"}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            r = await client.post(f"{BRIDGE_BASE}/kismet", json={"action": action})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}
