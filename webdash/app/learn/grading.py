"""Server-side assessment grading (plan §2.4). Answers stay in the bundle on the server; the
browser only ever sees prompts and choices (bundle.public_assessment) and, after submitting, which
items were right plus each item's explanation.

Pass = score ≥ pass_threshold AND every `required` item right. The legal and safety items are
required, so a transmit lab gated on them can't be reached by guessing the rest.
"""
import time

from . import bundle, db, extras

HOTSPOT_MIN_ATTEMPTS = 3


class NoAssessment(LookupError):
    pass
HOTSPOT_WRONG_RATE = 0.5


def _correct(item: dict, given) -> bool:
    t, ans = item.get("type"), item.get("answer")
    isint = lambda x: type(x) is int  # noqa: E731 — 1.7 must not count as choice 1
    try:
        if t == "single":
            return isint(given) and given == ans
        if t == "multi":
            return isinstance(given, list) and all(map(isint, given)) and sorted(given) == sorted(ans)
        if t == "numeric":
            return isinstance(given, (int, float)) and abs(float(given) - float(ans)) <= float(item["tolerance"])
        if t == "order":
            return isinstance(given, list) and all(map(isint, given)) and given == ans
    except (TypeError, ValueError, KeyError):
        return False
    return False


def grade(aid: str, answers: dict) -> dict:
    a = ((bundle.get() or {}).get("assessments") or {}).get(aid)
    if a is None:
        raise NoAssessment(aid)
    items = a.get("items") or []
    results = []
    for it in items:
        ok = _correct(it, answers.get(it["id"]))
        answered = it["id"] in answers
        # Explanations only for questions actually answered, so a blank submit can't harvest them.
        results.append({"id": it["id"], "correct": ok, "required": bool(it.get("required")),
                        "answered": answered, "explanation": it.get("explanation") if answered else None})
    right = sum(r["correct"] for r in results)
    score = right / len(items) if items else 0.0
    passed = score >= float(a.get("pass_threshold", 1.0)) and all(r["correct"] for r in results if r["required"])
    db.x("INSERT INTO attempt (user_id, assessment_id, content_hash, submitted, score, passed, item_results) "
         "VALUES (?,?,?,?,?,?,?)",
         (db.OWNER, aid, a.get("content_hash"), time.time(), score, int(passed),
          db.dumps([{k: r[k] for k in ("id", "correct")} for r in results])))
    if passed:
        db.set_progress("assessment", aid, "done", a.get("content_hash"))
    db.add_event("assessment_pass" if passed else "assessment_fail", aid, {"score": round(score, 3)})
    _hotspots(aid, a)
    endorsed = extras.award_due() if passed else []
    return {"endorsed": endorsed, "assessment": aid, "passed": passed, "score": round(score, 3), "right": right,
            "total": len(items), "results": results,
            "required_missed": [r["id"] for r in results if r["required"] and not r["correct"]]}


def _hotspots(aid: str, a: dict):
    """An item most learners get wrong is usually a content problem: open a review item for the
    owner (plan §3.7) once it has ≥3 attempts and ≥50% wrong. One open item per question."""
    import json

    rows = db.q("SELECT item_results FROM attempt WHERE assessment_id=?", (aid,))
    stats: dict[str, list[int]] = {}
    for r in rows:
        for it in json.loads(r["item_results"]):
            s = stats.setdefault(it["id"], [0, 0])
            s[0] += 1
            s[1] += 0 if it["correct"] else 1
    for item_id, (n, wrong) in stats.items():
        if n >= HOTSPOT_MIN_ATTEMPTS and wrong / n >= HOTSPOT_WRONG_RATE:
            key = f"assessment hotspot: {aid} item {item_id}"
            # Exact prefix match up to the separator: item "a1" must not match an open "a10".
            if not db.q("SELECT 1 FROM review_item WHERE state='open' AND substr(reason, 1, ?) = ?",
                        (len(key) + 2, key + " —")):
                db.x("INSERT INTO review_item (module_id, reason, created_at) VALUES (?,?,?)",
                     (a.get("module"), f"{key} — wrong in {wrong} of {n} attempts", time.time()))


def passed(aid: str) -> bool:
    return bool(db.q("SELECT 1 FROM attempt WHERE user_id=? AND assessment_id=? AND passed=1 LIMIT 1",
                     (db.OWNER, aid)))


def last_attempt(aid: str) -> dict | None:
    rows = db.q("SELECT submitted, score, passed FROM attempt WHERE user_id=? AND assessment_id=? "
                "ORDER BY id DESC LIMIT 1", (db.OWNER, aid))
    return dict(rows[0]) if rows else None
