"""Learning-platform API. Everything is behind the dashboard login (auth.require_session)."""
import time
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .. import auth
from . import bundle, db, extras, grading, labs, sync

router = APIRouter(prefix="/api/learn", dependencies=[Depends(auth.require_session)])

# main.py hands over its cached status snapshot getter at startup, so learning code reads the same
# 3 s snapshot as the stations instead of polling anything itself.
_status_getter = None


def set_status_source(fn):
    global _status_getter
    _status_getter = fn


def latest_status() -> dict | None:
    return _status_getter() if _status_getter else None


def clock_ok() -> bool | None:
    """No RTC cell is fitted, so after an offline cold boot the system clock can be wrong. Trust it
    when gpsd's latest fix timestamp agrees with it; None when there's no fix to compare."""
    age = ((latest_status() or {}).get("gps") or {}).get("tpv_age_s")
    return None if age is None else abs(age) < 5


def _bundle() -> dict:
    b = bundle.get()
    if b is None:
        raise HTTPException(503, detail=bundle.error() or "no curriculum bundle compiled yet")
    return b


@router.get("/catalog")
async def catalog():
    b = bundle.get()
    if b is None:
        return {"state": "no-bundle", "error": bundle.error()}
    cat = bundle.catalog(b)
    # Modules whose sources changed since the lesson was last reviewed carry a banner.
    for mid, reasons in sync.open_by_module().items():
        if mid in cat["modules"]:
            cat["modules"][mid]["open_review"] = sorted(set(reasons))
    return {"state": "ok", **cat}


@router.get("/module/{mid}")
async def module(mid: str):
    m = _bundle()["modules"].get(mid)
    if m is None:
        raise HTTPException(404, detail="no such module")
    return m


@router.get("/lesson/{lid}")
async def lesson(lid: str):
    b = _bundle()
    le = b["lessons"].get(lid)
    if le is None:
        raise HTTPException(404, detail="no such lesson")
    return {**le, "glossary_entries": {g: b["glossary"][g] for g in le.get("glossary", []) if g in b["glossary"]}}


@router.get("/lab/{lab_id}")
async def lab(lab_id: str):
    x = _bundle()["labs"].get(lab_id)
    if x is None:
        raise HTTPException(404, detail="no such lab")
    return x


@router.get("/assessment/{aid}")
async def assessment(aid: str):
    a = _bundle()["assessments"].get(aid)
    if a is None:
        raise HTTPException(404, detail="no such assessment")
    return {**bundle.public_assessment(a), "passed": grading.passed(aid), "last": grading.last_attempt(aid)}


class AnswersIn(BaseModel):
    answers: dict[str, int | float | list[int] | None] = Field(max_length=100)


@router.post("/assessment/{aid}/submit")
async def assessment_submit(aid: str, body: AnswersIn):
    try:
        return grading.grade(aid, {k: v for k, v in body.answers.items() if v is not None})
    except grading.NoAssessment:
        raise HTTPException(404, detail="no such assessment")


@router.get("/glossary")
async def glossary():
    return _bundle()["glossary"]


# ---------------------------------------------------------------------------
# Progress and events (S5)
# ---------------------------------------------------------------------------


def _hash_of(item_type: str, item_id: str) -> str | None:
    b = bundle.get() or {}
    table = {"module": "modules", "lesson": "lessons", "lab": "labs", "assessment": "assessments"}[item_type]
    return ((b.get(table) or {}).get(item_id) or {}).get("content_hash")


@router.get("/progress")
async def get_progress():
    items = db.progress()
    for item_id, p in items.items():
        current = _hash_of(p["item_type"], item_id)
        # Finished against content that has since changed: shown as "done (earlier version)".
        p["earlier_version"] = bool(p["state"] == "done" and current and p["content_hash_at_done"]
                                    and p["content_hash_at_done"] != current)
    return {"items": items}


class ProgressIn(BaseModel):
    # Only lessons are marked by the browser. Labs and assessments are marked by the server when
    # their checks pass, so a client can't claim them.
    item_type: Literal["lesson"]
    item_id: str = Field(max_length=64)
    state: Literal["in_progress", "done"]


@router.put("/progress")
async def put_progress(body: ProgressIn):
    b = bundle.get() or {}
    if body.item_id not in (b.get("lessons") or {}):
        raise HTTPException(404, detail="no such lesson")
    db.set_progress(body.item_type, body.item_id, body.state, _hash_of("lesson", body.item_id))
    if body.state == "done":
        extras.enroll_lesson(body.item_id)
    db.add_event(f"lesson_{body.state}", body.item_id, None, content_hash=_hash_of("lesson", body.item_id),
                 clock_ok=clock_ok())
    return {"ok": True}


class EventIn(BaseModel):
    kind: Literal["heartbeat", "view", "ui"]
    item_id: str | None = Field(default=None, max_length=64)
    item_type: Literal["module", "lesson", "lab", "assessment"] | None = None
    seconds: float | None = Field(default=None, ge=0, le=30)
    data: dict | None = None
    ts: float | None = None


class EventsIn(BaseModel):
    events: list[EventIn] = Field(max_length=50)


@router.post("/events")
async def post_events(body: EventsIn):
    ok = clock_ok()
    now = time.time()
    for e in body.events:
        data = e.data if e.data and len(str(e.data)) <= 512 else None
        # Browser clocks can be wrong too; accept their timestamp only if it's close to ours.
        ts = e.ts if e.ts and abs(e.ts - now) < 3600 else now
        if e.kind == "heartbeat":
            if e.item_type and e.item_id and e.seconds:
                db.add_active(e.item_type, e.item_id, e.seconds)
            continue  # heartbeats go straight into progress.active_s, not the event table
        db.add_event(e.kind, e.item_id, data, ts=ts, clock_ok=ok)
    return {"ok": True, "accepted": len(body.events)}


# ---------------------------------------------------------------------------
# Labs (S6)
# ---------------------------------------------------------------------------


@router.post("/labs/{lab_id}/start")
async def lab_start(lab_id: str):
    lab = (_bundle()["labs"]).get(lab_id)
    if lab is None:
        raise HTTPException(404, detail="no such lab")
    # Hard gate (plan D3): a lab may require passed checks — every transmit lab requires the legal
    # items. Everything else about prerequisites is advice.
    missing = [a for a in (lab.get("requires") or {}).get("assessments", []) if not grading.passed(a)]
    if missing:
        raise HTTPException(403, detail=f"Locked until you pass {', '.join(missing)}.")
    return labs.start(lab_id, latest_status())


@router.get("/labs/{lab_id}/run")
async def lab_run(lab_id: str):
    return {"run": labs.latest(lab_id)}


class SubmitIn(BaseModel):
    step_id: str = Field(max_length=64)
    text: str | None = Field(default=None, max_length=labs.MAX_PASTE)


@router.post("/labs/run/{run_id}/submit")
async def lab_submit(run_id: int, body: SubmitIn):
    try:
        return labs.submit(run_id, body.step_id, body.text, latest_status())
    except labs.NoRun:
        raise HTTPException(404, detail="no open run with that id")


@router.post("/labs/run/{run_id}/stop")
async def lab_stop(run_id: int):
    try:
        return labs.stop(run_id, latest_status())
    except labs.NoRun:
        raise HTTPException(404, detail="no open run with that id")


# ---------------------------------------------------------------------------
# Review, notes, endorsements, ship's log (S8)
# ---------------------------------------------------------------------------


@router.get("/summary")
async def summary():
    """Small, polled by the status strip's Learn chip."""
    return {"review_due": extras.due(latest_status())["count_due"]}


@router.get("/review")
async def review():
    return extras.due(latest_status())


class GradeIn(BaseModel):
    grade: Literal["again", "hard", "good"]


@router.post("/review/{card_id}")
async def review_grade(card_id: str, body: GradeIn):
    try:
        return extras.grade(card_id, body.grade)
    except extras.NoCard:
        raise HTTPException(404, detail="no such card")


@router.post("/review/{card_id}/suspend")
async def review_suspend(card_id: str):
    extras.suspend(card_id)
    return {"ok": True}


@router.get("/notes")
async def notes_list(anchor: str | None = None):
    return {"notes": extras.notes(anchor)}


class NoteIn(BaseModel):
    anchor: str = Field(min_length=1, max_length=64)
    body: str = Field(min_length=1, max_length=4000)
    pin: bool = False


@router.post("/notes")
async def notes_add(body: NoteIn):
    nid = extras.add_note(body.anchor, body.body, extras.pin(latest_status()) if body.pin else None)
    return {"ok": True, "id": nid}


@router.delete("/notes/{note_id}")
async def notes_delete(note_id: int):
    extras.delete_note(note_id)
    return {"ok": True}


@router.get("/endorsements")
async def endorsements():
    return {"endorsements": extras.endorsements()}


@router.get("/log")
async def ship_log():
    return {"log": extras.log()}


# ---------------------------------------------------------------------------
# Owner view: content review queue and health (S9)
# ---------------------------------------------------------------------------


@router.get("/owner")
async def owner():
    sync.ingest(force=True)
    b = bundle.get() or {}
    return {"meta": b.get("meta"), "review_items": sync.review_items(),
            "health": sync.health(latest_status()), "bundle_error": bundle.error()}


class ResolveIn(BaseModel):
    state: Literal["accepted", "edited"]


@router.post("/owner/review/{item_id}")
async def owner_resolve(item_id: int, body: ResolveIn):
    sync.resolve(item_id, body.state)
    return {"ok": True}
