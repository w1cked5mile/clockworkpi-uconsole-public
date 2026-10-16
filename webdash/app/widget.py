"""Compact status for the phone widget (GET /api/widget) and its bearer token.

A home-screen widget can't do the dashboard's password + TOTP login, so this route takes a
separate token instead: read-only, this one route only, revocable by rotating. Only its SHA-256
is stored, in the same /auth volume as the login store (outside the repo, outside git). See
software/webdash.md#phone-widget.

The summary never carries lat/lon — the grid square is cut to 4 characters (~1° x 2°), the same
precision the repo records location at. No fastapi import here, so the tests run on the host.

Rotate (prints the new token once):
  sg docker -c 'docker exec uconsole-webdash python -m app.widget --rotate'
"""
import hashlib
import os
import secrets
import sys
from pathlib import Path

TOKEN_PATH = Path(os.environ.get("WEBDASH_AUTH_DIR", "/auth")) / "widget_token.sha256"
HOST = "fancy"
HISTORY_POINTS = 24  # 2 h of history at one point per 5 min

# Pack voltage on battery, from docs/reference/power-budget.md: plug in by 3.60 V; the supply has
# cut out with no warning at ≈3.5 V under load. "low" gives about an hour's notice at 3.8 W.
LOW_V = 3.70
PLUG_IN_V = 3.60


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def rotate_token(path: Path = TOKEN_PATH) -> str:
    """New 256-bit token; overwrites the stored hash, so the previous token stops working."""
    token = secrets.token_urlsafe(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(_hash(token) + "\n")
    tmp.chmod(0o600)
    tmp.replace(path)
    return token


def token_ok(token: str | None, path: Path = TOKEN_PATH) -> bool:
    if not token:
        return False
    try:
        stored = path.read_text().strip()
    except OSError:
        return False
    return bool(stored) and secrets.compare_digest(_hash(token), stored)


def bearer(header: str | None) -> str | None:
    """Token from an `Authorization: Bearer <token>` header, else None."""
    if not header:
        return None
    scheme, _, value = header.strip().partition(" ")
    if scheme.lower() != "bearer" or not value.strip():
        return None
    return value.strip()


def _level(v: float | None, on_battery: bool | None) -> str:
    if on_battery is False:
        return "charging"
    if v is None:
        return "unknown"
    if v < PLUG_IN_V:
        return "plug_in"
    if v < LOW_V:
        return "low"
    return "ok"


def _voltage_history(history: list[dict]) -> list[float]:
    """Newest-last, at most HISTORY_POINTS values, the newest sample always kept."""
    volts = [float(s["voltage_v"]) for s in history if s.get("voltage_v") is not None]
    if len(volts) <= HISTORY_POINTS:
        return volts
    step = len(volts) / HISTORY_POINTS
    return [volts[len(volts) - 1 - round(i * step)] for i in range(HISTORY_POINTS)][::-1]


def _state(d: dict | None) -> str:
    return (d or {}).get("state") or "unavailable"


def summary(status: dict, history: list[dict]) -> dict:
    sysd = status.get("system") or {}
    ai = status.get("aiov2") or {}
    p = ai.get("power_num") or {}
    g = status.get("gps") or {}
    k = status.get("kismet") or {}
    m = status.get("mesh") or {}
    a = status.get("adsb") or {}
    fix = g.get("fix") if g.get("state") == "running" else None
    grid = g.get("grid")
    return {
        "host": HOST,
        "generated_at": status.get("generated_at"),
        "power": {
            "voltage_v": p.get("voltage_v"),
            "power_w": p.get("power_w"),
            "on_battery": p.get("on_battery"),
            "level": _level(p.get("voltage_v"), p.get("on_battery")),
            "history_v": _voltage_history(history),
        },
        "gps": {
            "fix": fix if fix in ("2D", "3D") else "none",
            "sats": g.get("satellites_used"),
            "hdop": g.get("hdop"),
            "grid": grid[:4] if grid else None,
        },
        "system": {
            "temp_c": sysd.get("temp_c"),
            "cpu_percent": sysd.get("cpu_percent"),
            "disk_percent": (sysd.get("disk") or {}).get("percent"),
            "uptime_s": sysd.get("uptime_s"),
            "undervoltage": sysd.get("undervoltage"),
        },
        "rails": {name: bool((r or {}).get("on")) for name, r in (ai.get("rails") or {}).items()},
        "kismet": {"state": _state(k), "devices": k.get("devices")},
        "mesh": {"state": _state(m), "nodes": m.get("nodes_seen")},
        "adsb": {"state": _state(a), "aircraft": a.get("aircraft_count")},
    }


if __name__ == "__main__":
    if sys.argv[1:] != ["--rotate"]:
        sys.exit("usage: python -m app.widget --rotate")
    print(rotate_token())
