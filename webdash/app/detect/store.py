"""The Detect contact log, persisted as JSON in the read-write data dir (outside git).

One record per contact — a (source, class, identifier) triple — not per sighting: later sightings
update its last-seen time, RSSI and count. Location is the 6-character Maidenhead grid only, never
lat/lon (repo convention), plus an optional operator place label.

Also kept here: whether the watch is on, the "seen" marker (one server-side timestamp, so the
uConsole and a phone agree on what is new), and per-source coverage intervals — when each radio
was actually listening — so an empty log can say what was listened to rather than claim nothing
was there.

Writes are atomic (temp file then rename), like survey/store.py. Coverage changes every poll, so it
is flushed at most once a minute; contacts are flushed when they change.
"""
import hashlib
import json
import os
import threading
import time
from pathlib import Path

from .rules import CONF_RANK

DATA_DIR = Path(os.environ.get("WEBDASH_DATA_DIR", "/data"))
DETECT_DIR = DATA_DIR / "detect"
LOG_PATH = DETECT_DIR / "contacts.json"
STATE_PATH = DETECT_DIR / "state.json"

MAX_RECORDS = 5000
MAX_SSIDS = 20
MAX_INTERVALS = 500
MAX_PLACE = 80
COVERAGE_FLUSH_S = 60

_lock = threading.RLock()
_records: dict[str, dict] | None = None
_state: dict | None = None
_last_state_flush = 0.0


def _write_atomic(path: Path, obj) -> None:
    DETECT_DIR.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    tmp.replace(path)


def _read(path: Path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def _load() -> None:
    global _records, _state
    if _records is None:
        recs = _read(LOG_PATH, {}).get("records", {})
        _records = recs if isinstance(recs, dict) else {}
    if _state is None:
        st = _read(STATE_PATH, {})
        st = st if isinstance(st, dict) else {}
        st.setdefault("armed", False)
        st.setdefault("armed_since", None)
        st.setdefault("seen_marker", 0.0)
        st.setdefault("coverage", {})
        _state = st


def reset_cache() -> None:
    """Forget the in-memory copy (tests, or after the files were changed by hand)."""
    global _records, _state
    with _lock:
        _records = _state = None


def _flush_records() -> None:
    _write_atomic(LOG_PATH, {"records": _records})


def _flush_state(force: bool = True) -> None:
    global _last_state_flush
    now = time.time()
    if force or now - _last_state_flush >= COVERAGE_FLUSH_S:
        _write_atomic(STATE_PATH, _state)
        _last_state_flush = now


def record_id(key: str) -> str:
    return hashlib.sha1(key.encode()).hexdigest()[:12]


# --- watch state -----------------------------------------------------------------------------

def state() -> dict:
    with _lock:
        _load()
        return {k: _state[k] for k in ("armed", "armed_since", "seen_marker")}


def set_armed(on: bool) -> dict:
    with _lock:
        _load()
        if on and not _state["armed"]:
            _state["armed_since"] = time.time()
        if not on:
            _state["armed_since"] = None
        _state["armed"] = bool(on)
        _flush_state()
        return state()


def mark_seen(ts: float | None = None) -> float:
    with _lock:
        _load()
        _state["seen_marker"] = ts if ts is not None else time.time()
        _flush_state()
        return _state["seen_marker"]


def mark_listening(source: str, now: float, gap_s: float) -> None:
    """Extend `source`'s current coverage interval to `now`, or open a new one if the last one
    ended more than `gap_s` ago."""
    with _lock:
        _load()
        iv = _state["coverage"].setdefault(source, [])
        if iv and now - iv[-1][1] <= gap_s:
            iv[-1][1] = now
        else:
            iv.append([now, now])
            del iv[:-MAX_INTERVALS]
        _flush_state(force=False)


def coverage(since: float) -> dict:
    """Seconds each source listened since `since`, and its intervals clipped to that window."""
    with _lock:
        _load()
        out = {}
        for src, ivs in _state["coverage"].items():
            clipped = [[max(a, since), b] for a, b in ivs if b >= since]
            out[src] = {"seconds": round(sum(b - a for a, b in clipped)), "intervals": clipped}
        return out


# --- contacts --------------------------------------------------------------------------------

def upsert(obs: dict, flush: bool = True) -> tuple[dict, bool]:
    """Fold one observation into the log → (record, is_new).

    `obs` keys: key, cls, source, radio, name, ident, addr_type, ssid, channel, rssi, grid, ts,
    rule_id, rule_text, confidence, manuf, detail. A sighting is counted only when the observation
    is newer than the record's last sighting, so re-reading the same Kismet state doesn't inflate it.
    A poll that folds in many observations passes flush=False and calls flush() once at the end.
    """
    with _lock:
        _load()
        rid = record_id(obs["key"])
        ts = float(obs.get("ts") or time.time())
        rec = _records.get(rid)
        new = rec is None
        if new:
            rec = {
                "id": rid, "cls": obs["cls"], "source": obs["source"], "radio": obs["radio"],
                "ident": obs.get("ident"), "addr_type": obs.get("addr_type"), "name": None,
                "ssids": [], "channel": None, "manuf": obs.get("manuf"),
                "rssi_first": obs.get("rssi"), "rssi_peak": obs.get("rssi"), "rssi_last": obs.get("rssi"),
                "first_seen": ts, "last_seen": ts, "sightings": 1,
                "grid_first": obs.get("grid"), "grid_last": obs.get("grid"), "place": "",
                "rule_id": obs.get("rule_id"), "rule_text": obs.get("rule_text"),
                "confidence": obs.get("confidence"), "detail": obs.get("detail"),
            }
            _records[rid] = rec
        elif ts > rec["last_seen"]:
            rec["last_seen"] = ts
            rec["sightings"] += 1
            if obs.get("grid"):
                rec["grid_last"] = obs["grid"]
                rec["grid_first"] = rec["grid_first"] or obs["grid"]
            rssi = obs.get("rssi")
            if isinstance(rssi, (int, float)):
                rec["rssi_last"] = rssi
                if rec["rssi_first"] is None:
                    rec["rssi_first"] = rssi
                if rec["rssi_peak"] is None or rssi > rec["rssi_peak"]:
                    rec["rssi_peak"] = rssi
            # A stronger rule matching later wins; a weaker one never downgrades the record.
            conf = obs.get("confidence")
            if conf and CONF_RANK.get(conf, 0) > CONF_RANK.get(rec["confidence"], 0):
                rec.update(rule_id=obs.get("rule_id"), rule_text=obs.get("rule_text"), confidence=conf)
            if obs.get("detail"):
                rec["detail"] = obs["detail"]
        if obs.get("name"):
            rec["name"] = obs["name"]
        if obs.get("channel"):
            rec["channel"] = obs["channel"]
        ssid = obs.get("ssid")
        if ssid and ssid not in rec["ssids"] and len(rec["ssids"]) < MAX_SSIDS:
            rec["ssids"].append(ssid)
        if len(_records) > MAX_RECORDS:
            for old in sorted(_records.values(), key=lambda r: r["last_seen"])[:len(_records) - MAX_RECORDS]:
                del _records[old["id"]]
        if flush:
            _flush_records()
        return dict(rec), new


def flush() -> None:
    with _lock:
        _load()
        _flush_records()


def records() -> list[dict]:
    """Every contact, newest last-seen first."""
    with _lock:
        _load()
        return sorted((dict(r) for r in _records.values()), key=lambda r: r["last_seen"], reverse=True)


def filtered(cls: str = "", min_conf: str = "", since: float = 0.0) -> list[dict]:
    rank = CONF_RANK.get(min_conf, 0)
    return [r for r in records()
            if (not cls or r["cls"] == cls)
            and CONF_RANK.get(r.get("confidence"), 0) >= rank
            and r["last_seen"] >= since]


def set_place(rid: str, place: str) -> dict:
    with _lock:
        _load()
        rec = _records.get(rid)
        if not rec:
            return {"ok": False, "error": "no such contact"}
        rec["place"] = place.strip()[:MAX_PLACE]
        _flush_records()
        return {"ok": True, "record": dict(rec)}


def delete(rid: str) -> dict:
    with _lock:
        _load()
        if _records.pop(rid, None) is None:
            return {"ok": False, "error": "no such contact"}
        _flush_records()
        return {"ok": True}


def clear() -> dict:
    with _lock:
        _load()
        n = len(_records)
        _records.clear()
        _flush_records()
        return {"ok": True, "deleted": n}


def summary(now: float | None = None, window_s: float = 300) -> dict:
    """What the 3 s status snapshot carries: counts only, plus the newest contact's class, time,
    confidence and RSSI. No names, SSIDs or addresses — those stay behind the tab's own fetch."""
    now = now or time.time()
    with _lock:
        _load()
        recs = list(_records.values())
        marker = _state["seen_marker"]
    recent = [r for r in recs if now - r["last_seen"] <= window_s]
    by_class: dict[str, int] = {}
    for r in recent:
        by_class[r["cls"]] = by_class.get(r["cls"], 0) + 1
    newest = max(recs, key=lambda r: r["first_seen"], default=None)
    unseen_high = [r for r in recs if r["confidence"] == "high" and r["first_seen"] > marker]
    return {
        "total": len(recs),
        "now_count": len(recent),
        "now_by_class": by_class,
        "window_s": window_s,
        "unseen_high": len(unseen_high),
        "unseen_high_classes": sorted({r["cls"] for r in unseen_high}),
        "newest": {k: newest[k] for k in ("id", "cls", "first_seen", "last_seen", "confidence",
                                            "rssi_last", "radio")} if newest else None,
    }
