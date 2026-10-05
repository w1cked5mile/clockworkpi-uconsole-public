"""aiov2_ctl rail/power status, via the host-side bridge (127.0.0.1:8765).

See docs/reference/webdash-architecture.md — aiov2_ctl shells out to `pinctrl`, which needs GPIO
device access; a tiny host-side systemd service exposes its --status output as JSON instead of
bind-mounting the binary + device nodes into this container.
"""
import httpx

BRIDGE_BASE = "http://127.0.0.1:8765"
VALID_FEATURES = {"GPS", "LORA", "SDR", "USB"}


async def collect() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{BRIDGE_BASE}/status")
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"state": "unavailable", "error": str(exc)}
    return {"state": "ok" if data.get("ok") else "error", **data,
            "power_num": power_numbers(data.get("power") or {})}


def num(v) -> float | None:
    """'4.2 V' / '0.83 W' / '100%' from aiov2_ctl -> float; None if absent or unparseable."""
    try:
        return float(str(v).split()[0].rstrip("%"))
    except (ValueError, IndexError):
        return None


def power_numbers(p: dict) -> dict:
    """The bridge passes aiov2_ctl's strings through unchanged (kept for display). Labs and
    history need numbers, so parse them once here rather than in every consumer."""
    return {
        "voltage_v": num(p.get("voltage")),
        "current_a": num(p.get("current")),
        "power_w": num(p.get("power")),
        "capacity_pct": num(p.get("capacity")),
        "on_battery": None if p.get("source") is None else p.get("source") != "AC",
    }


async def set_rail(feature: str, state: str) -> dict:
    """Actually changes hardware state — the bridge shells out to `aiov2_ctl <feature> on|off`.
    Caller (main.py) is responsible for the auth gate; this module trusts its input is already
    validated by the route, and validates again anyway since it's a POST to real hardware."""
    feature = feature.upper()
    state = state.lower()
    if feature not in VALID_FEATURES or state not in ("on", "off"):
        return {"ok": False, "error": "invalid feature or state"}
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            r = await client.post(f"{BRIDGE_BASE}/rail", json={"feature": feature, "state": state})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}
