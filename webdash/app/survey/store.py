"""Survey session persistence — JSON files in the read-write data dir, one per survey.

A survey is a named session with an ordered list of waypoints. Each waypoint bundles a Kismet
device snapshot (from snapshot.py) with the location it was taken at (a Maidenhead grid square and
an operator label — never raw lat/lon, per the repo's location convention) and the GPS fix state
at that moment. Exactly one survey is "active" at a time; dropping a waypoint appends to it.

Storage mirrors the WPA allowlist: atomic temp-file-then-rename writes, so a half-written survey
can never be read back, and everything lives under WEBDASH_DATA_DIR — outside the repo and git,
because a survey's SSID/BSSID list is the same kind of sensitive on-device data as the captures.
"""
import json
import os
import time
import uuid
from pathlib import Path

DATA_DIR = Path(os.environ.get("WEBDASH_DATA_DIR", "/data"))
SURVEY_DIR = DATA_DIR / "surveys"
STATE_PATH = DATA_DIR / "survey-state.json"  # {"active": "<id>"} or {}

MAX_NAME = 80
MAX_LABEL = 80
MAX_NOTE = 400


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _write_atomic(path: Path, obj: dict) -> None:
    SURVEY_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2))
    tmp.replace(path)


def _survey_path(survey_id: str) -> Path:
    # survey_id is a uuid4 hex we generate; never a client-supplied path. Guard anyway so a bad id
    # can only ever miss, not escape the survey dir.
    if not survey_id or "/" in survey_id or "." in survey_id or ".." == survey_id:
        return SURVEY_DIR / "__invalid__"
    return SURVEY_DIR / f"{survey_id}.json"


def _load_state() -> dict:
    try:
        return json.loads(STATE_PATH.read_text())
    except (OSError, ValueError):
        return {}


def _save_state(state: dict) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = STATE_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(state, indent=2))
    tmp.replace(STATE_PATH)


def _read(survey_id: str) -> dict | None:
    try:
        return json.loads(_survey_path(survey_id).read_text())
    except (OSError, ValueError):
        return None


def active_id() -> str | None:
    aid = _load_state().get("active")
    # A stale pointer (file deleted out from under us) reads as no active survey.
    return aid if aid and _survey_path(aid).exists() else None


def get_active() -> dict | None:
    aid = active_id()
    return _read(aid) if aid else None


def start(name: str) -> dict:
    """Begin a new survey and make it the active one. Only one may be active; starting another
    while one is open is refused so waypoints can't be split across two sessions by accident."""
    if active_id():
        return {"ok": False, "error": "a survey is already active — stop it before starting another"}
    name = (name or "").strip()[:MAX_NAME] or f"Survey {_now()}"
    survey = {
        "version": 1,
        "id": uuid.uuid4().hex,
        "name": name,
        "status": "active",
        "created": _now(),
        "stopped": None,
        "waypoints": [],
    }
    _write_atomic(_survey_path(survey["id"]), survey)
    _save_state({"active": survey["id"]})
    return {"ok": True, "survey": survey}


def add_waypoint(label: str, location: dict, snapshot: dict, note: str = "") -> dict:
    """Append a waypoint to the active survey.

    `location` is the GPS collector's reduced output (grid, fix, satellite counts — no lat/lon is
    stored here). `snapshot` is snapshot.capture()'s result; if it failed, the waypoint is still
    recorded with the error so the walk and the position aren't lost."""
    survey = get_active()
    if not survey:
        return {"ok": False, "error": "no active survey — start one first"}

    ok = bool(snapshot.get("ok"))
    wp = {
        "seq": len(survey["waypoints"]) + 1,
        "label": (label or "").strip()[:MAX_LABEL] or f"WP{len(survey['waypoints']) + 1}",
        "time": _now(),
        "grid": location.get("grid"),
        "fix": location.get("fix"),
        "satellites_used": location.get("satellites_used"),
        "hdop": location.get("hdop"),
        # Precise coordinates for the site map / roaming analysis. Survey data lives in the data
        # dir, outside git — the dashboard is allowed to hold a precise fix (operator tool behind
        # auth); it is grid-square-only that the repo's committed docs are held to. null with no fix.
        "lat": location.get("lat"),
        "lon": location.get("lon"),
        "note": (note or "").strip()[:MAX_NOTE],
        "device_count": snapshot.get("device_count") if ok else None,
        "devices": snapshot.get("devices", []) if ok else [],
        "snapshot_error": None if ok else snapshot.get("error", "snapshot unavailable"),
    }
    survey["waypoints"].append(wp)
    _write_atomic(_survey_path(survey["id"]), survey)
    return {"ok": True, "waypoint": wp, "waypoint_count": len(survey["waypoints"])}


def delete_last_waypoint() -> dict:
    """Drop the most recent waypoint from the active survey (an undo for a mis-dropped point)."""
    survey = get_active()
    if not survey:
        return {"ok": False, "error": "no active survey"}
    if not survey["waypoints"]:
        return {"ok": False, "error": "no waypoints to remove"}
    removed = survey["waypoints"].pop()
    _write_atomic(_survey_path(survey["id"]), survey)
    return {"ok": True, "removed": removed["label"], "waypoint_count": len(survey["waypoints"])}


def stop() -> dict:
    """Close the active survey. It stays on disk (readable, reportable) but is no longer active."""
    survey = get_active()
    if not survey:
        return {"ok": False, "error": "no active survey"}
    survey["status"] = "completed"
    survey["stopped"] = _now()
    _write_atomic(_survey_path(survey["id"]), survey)
    _save_state({})
    return {"ok": True, "survey_id": survey["id"], "waypoint_count": len(survey["waypoints"])}


def get(survey_id: str) -> dict | None:
    return _read(survey_id)


def delete(survey_id: str) -> dict:
    path = _survey_path(survey_id)
    if not path.exists():
        return {"ok": False, "error": "no such survey"}
    try:
        path.unlink()
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    if active_id() == survey_id:
        _save_state({})
    return {"ok": True}


def list_surveys() -> list[dict]:
    """Every survey on disk, newest first, as lightweight summaries (no device lists)."""
    out = []
    try:
        paths = sorted(SURVEY_DIR.glob("*.json"))
    except OSError:
        return out
    aid = active_id()
    for p in paths:
        try:
            s = json.loads(p.read_text())
        except (OSError, ValueError):
            continue
        out.append({
            "id": s.get("id"),
            "name": s.get("name"),
            "status": "active" if s.get("id") == aid else s.get("status", "completed"),
            "created": s.get("created"),
            "stopped": s.get("stopped"),
            "waypoint_count": len(s.get("waypoints", [])),
        })
    out.sort(key=lambda s: s.get("created") or "", reverse=True)
    return out
