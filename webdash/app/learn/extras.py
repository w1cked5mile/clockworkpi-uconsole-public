"""Review queue, notes and endorsements (build step S8).

Review is Leitner-lite (plan §3.1): five boxes at 1/2/4/8/16 days, no streaks, no daily targets.
Cards are glossary terms, enrolled when a lesson that uses them is finished. A term with a `live`
path becomes a live-read card: its prompt quotes the current value, or a stored example marked
"example, not live" when the reading isn't available — never skipped silently.

Notes can pin a reading: a snapshot of a fixed, location-safe set of status fields. Position is
only ever the grid square.

Endorsements are awarded once, from lab and check passes the server recorded.
"""
import time

from . import bundle, db
from .schema import get_path

DAY = 86400


class NoCard(LookupError):
    pass
BOX_DAYS = {1: 1, 2: 2, 3: 4, 4: 8, 5: 16}

# What "Pin reading" captures. gps.grid, never lat/lon.
PIN_PATHS = (
    "gps.fix", "gps.grid", "gps.satellites_used", "gps.satellites_visible", "gps.hdop",
    "aiov2.power.source", "aiov2.power_num.voltage_v", "aiov2.power_num.power_w",
    "aiov2.rails.GPS.on", "aiov2.rails.LORA.on", "aiov2.rails.SDR.on", "aiov2.rails.USB.on",
    "adsb.state", "adsb.aircraft_count", "adsb.with_position", "adsb.messages_per_s",
    "mesh.state", "mesh.nodes_seen", "mesh.rx_packets", "mesh.last_rx_snr", "mesh.last_rx_rssi",
    "system.temp_c", "system.cpu_percent",
)


def _get(st, path):
    try:
        return get_path(st or {}, path)
    except KeyError:
        return None


# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------


def enroll_lesson(lesson_id: str):
    b = bundle.get() or {}
    le = (b.get("lessons") or {}).get(lesson_id) or {}
    now = time.time()
    for g in le.get("glossary") or []:
        if g in (b.get("glossary") or {}):
            db.x("INSERT OR IGNORE INTO review_card (user_id, card_id, box, due_at) VALUES (?,?,1,?)",
                 (db.OWNER, f"g:{g}", now))


def _card(row, b, st) -> dict | None:
    gid = row["card_id"].split(":", 1)[1]
    g = (b.get("glossary") or {}).get(gid)
    if g is None:
        return None
    card = {"card_id": row["card_id"], "box": row["box"], "due_at": row["due_at"], "term": g["term"],
            "kind": "term", "prompt": f"What is {g['term']}?",
            "answer": g.get("tooltip"), "detail": g.get("good_bad"), "learn_more": g.get("learn_more")}
    if g.get("live"):
        v = _get(st, g["live"])
        live = v is not None
        card.update(kind="live", live_path=g["live"], live=live,
                    prompt=g["live_prompt"].replace("{value}", str(v if live else g["example"])))
    return card


def due(st: dict | None) -> dict:
    b = bundle.get() or {}
    now = time.time()
    rows = db.q("SELECT * FROM review_card WHERE user_id=? AND suspended=0 ORDER BY due_at", (db.OWNER,))
    cards = [c for c in (_card(r, b, st) for r in rows if r["due_at"] <= now) if c]
    upcoming = [r["due_at"] for r in rows if r["due_at"] > now]
    boxes = {}
    for r in rows:
        boxes[r["box"]] = boxes.get(r["box"], 0) + 1
    return {"due": cards, "count_due": len(cards), "total": len(rows),
            "next_due_at": min(upcoming) if upcoming else None, "boxes": boxes}


def grade(card_id: str, g: str):
    rows = db.q("SELECT box FROM review_card WHERE user_id=? AND card_id=?", (db.OWNER, card_id))
    if not rows:
        raise NoCard(card_id)
    box = rows[0]["box"]
    box = 1 if g == "again" else box if g == "hard" else min(5, box + 1)
    days = 1 if g == "again" else BOX_DAYS[box]
    db.x("UPDATE review_card SET box=?, due_at=?, last_seen=? WHERE user_id=? AND card_id=?",
         (box, time.time() + days * DAY, time.time(), db.OWNER, card_id))
    db.add_event("review", card_id, {"grade": g, "box": box})
    return {"card_id": card_id, "box": box, "due_in_days": days}


def suspend(card_id: str):
    db.x("UPDATE review_card SET suspended=1 WHERE user_id=? AND card_id=?", (db.OWNER, card_id))


# ---------------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------------


def pin(st: dict | None) -> dict:
    snap = {p: _get(st, p) for p in PIN_PATHS}
    snap["_at"] = time.time()
    return snap


def notes(anchor: str | None = None) -> list[dict]:
    sql, args = "SELECT * FROM note WHERE user_id=?", [db.OWNER]
    if anchor:
        sql += " AND anchor=?"
        args.append(anchor)
    rows = db.q(sql + " ORDER BY created_at DESC", args)
    import json
    return [{"id": r["id"], "anchor": r["anchor"], "body": r["body"], "created_at": r["created_at"],
             "updated_at": r["updated_at"], "pinned": json.loads(r["pinned_reading"]) if r["pinned_reading"] else None}
            for r in rows]


def add_note(anchor: str, body: str, pinned: dict | None) -> int:
    now = time.time()
    return db.x("INSERT INTO note (user_id, anchor, body, pinned_reading, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                (db.OWNER, anchor, body, db.dumps(pinned) if pinned else None, now, now))


def delete_note(note_id: int):
    db.x("DELETE FROM note WHERE user_id=? AND id=?", (db.OWNER, note_id))


# ---------------------------------------------------------------------------
# Endorsements
# ---------------------------------------------------------------------------


def _passed_labs() -> dict:
    rows = db.q("SELECT lab_id, MAX(ended) AS at, evidence FROM lab_run WHERE user_id=? AND outcome='pass' "
                "GROUP BY lab_id", (db.OWNER,))
    return {r["lab_id"]: r for r in rows}


def _passed_assessments() -> dict:
    rows = db.q("SELECT assessment_id, MAX(submitted) AS at FROM attempt WHERE user_id=? AND passed=1 "
                "GROUP BY assessment_id", (db.OWNER,))
    return {r["assessment_id"]: r for r in rows}


def award_due() -> list[str]:
    """Award every endorsement whose rule is now met and that hasn't been awarded. Cheap; called
    after lab and check passes."""
    import json
    b = bundle.get() or {}
    have = {r["endorsement_id"] for r in db.q("SELECT endorsement_id FROM endorsement WHERE user_id=?", (db.OWNER,))}
    labs, quizzes = _passed_labs(), _passed_assessments()
    new = []
    for e in b.get("endorsements") or []:
        if e["id"] in have:
            continue
        rule = e.get("rule") or {}
        if all(l in labs for l in rule.get("lab_pass", [])) and all(a in quizzes for a in rule.get("assessment_pass", [])):
            ev = {}
            for l in rule.get("lab_pass", []):
                ev.update({k: v for k, v in json.loads(labs[l]["evidence"] or "{}").items() if v is not None})
            db.x("INSERT OR IGNORE INTO endorsement (user_id, endorsement_id, awarded_at, evidence) VALUES (?,?,?,?)",
                 (db.OWNER, e["id"], time.time(), db.dumps(ev)))
            db.add_event("endorsement", e["id"], None)
            new.append(e["id"])
    return new


def endorsements() -> list[dict]:
    import json
    b = bundle.get() or {}
    got = {r["endorsement_id"]: r for r in db.q("SELECT * FROM endorsement WHERE user_id=?", (db.OWNER,))}
    return [{**e, "awarded_at": got[e["id"]]["awarded_at"] if e["id"] in got else None,
             "evidence": json.loads(got[e["id"]]["evidence"]) if e["id"] in got else None}
            for e in b.get("endorsements") or []]


def log(limit: int = 12) -> list[dict]:
    """Ship's log: milestones only — lab passes, checks passed, endorsements."""
    rows = db.q("SELECT ts, kind, item_id FROM event WHERE user_id=? AND kind IN "
                "('lab_pass','assessment_pass','endorsement') ORDER BY ts DESC LIMIT ?", (db.OWNER, limit))
    return [dict(r) for r in rows]
