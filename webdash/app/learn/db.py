"""Learner state in SQLite (/data/learn.db, host ~/.local/share/uconsole-webdash/data/).

stdlib sqlite3 in WAL mode: atomic, one file to back up, survives a battery pull (the last few
commits may be lost). Calls are tiny and infrequent, so a single connection behind a lock is
enough; FastAPI handlers call these from the event loop and they return in well under a
millisecond on NVMe.

The MVP has one learner — the existing webdash account — so every row carries user_id "owner".
The column is there so guests can be added later without a data migration (plan §3.2, S11).
"""
import json
import os
import sqlite3
import threading
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("WEBDASH_DATA_DIR", "/data"))
DB_PATH = DATA_DIR / "learn.db"
OWNER = "owner"

_LOCK = threading.RLock()  # re-entrant: write helpers hold it while conn() may initialise
_CONN: sqlite3.Connection | None = None

# Each entry runs once, in order; PRAGMA user_version records how many have run.
MIGRATIONS = [
    """
    CREATE TABLE progress (
        user_id TEXT NOT NULL, item_type TEXT NOT NULL, item_id TEXT NOT NULL,
        state TEXT NOT NULL CHECK (state IN ('not_started','in_progress','done')),
        content_hash_at_done TEXT, started_at REAL, done_at REAL, active_s REAL NOT NULL DEFAULT 0,
        PRIMARY KEY (user_id, item_type, item_id)
    );
    CREATE TABLE event (
        id INTEGER PRIMARY KEY, ts REAL NOT NULL, clock_ok INTEGER, user_id TEXT NOT NULL,
        kind TEXT NOT NULL, item_id TEXT, content_hash TEXT, data TEXT
    );
    CREATE INDEX event_kind_ts ON event (kind, ts);
    CREATE TABLE lab_run (
        id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, lab_id TEXT NOT NULL, content_hash TEXT,
        started REAL NOT NULL, ended REAL,
        outcome TEXT CHECK (outcome IN ('pass','abandoned','safety_stop','env_error','platform_error')),
        step_results TEXT NOT NULL DEFAULT '{}', evidence TEXT NOT NULL DEFAULT '{}',
        baseline TEXT NOT NULL DEFAULT '{}', saved TEXT NOT NULL DEFAULT '{}'
    );
    CREATE INDEX lab_run_open ON lab_run (user_id, ended);
    CREATE TABLE attempt (
        id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, assessment_id TEXT NOT NULL,
        content_hash TEXT, submitted REAL NOT NULL, score REAL NOT NULL, passed INTEGER NOT NULL,
        item_results TEXT NOT NULL
    );
    CREATE TABLE review_card (
        user_id TEXT NOT NULL, card_id TEXT NOT NULL, box INTEGER NOT NULL DEFAULT 1,
        due_at REAL NOT NULL, suspended INTEGER NOT NULL DEFAULT 0, last_seen REAL,
        PRIMARY KEY (user_id, card_id)
    );
    CREATE TABLE note (
        id INTEGER PRIMARY KEY, user_id TEXT NOT NULL, anchor TEXT NOT NULL, body TEXT NOT NULL,
        pinned_reading TEXT, created_at REAL NOT NULL, updated_at REAL NOT NULL
    );
    CREATE TABLE endorsement (
        user_id TEXT NOT NULL, endorsement_id TEXT NOT NULL, awarded_at REAL NOT NULL,
        evidence TEXT NOT NULL DEFAULT '{}', PRIMARY KEY (user_id, endorsement_id)
    );
    CREATE TABLE audit (
        id INTEGER PRIMARY KEY, ts REAL NOT NULL, user_id TEXT, action TEXT NOT NULL,
        target TEXT, result TEXT, detail TEXT
    );
    CREATE TABLE content_version (
        bundle_sha TEXT PRIMARY KEY, commit_sha TEXT, seen_at REAL NOT NULL
    );
    CREATE TABLE review_item (
        id INTEGER PRIMARY KEY, module_id TEXT NOT NULL, commit_from TEXT, commit_to TEXT,
        changed_paths TEXT NOT NULL DEFAULT '[]', reason TEXT NOT NULL,
        state TEXT NOT NULL DEFAULT 'open' CHECK (state IN ('open','accepted','edited')),
        created_at REAL NOT NULL, resolved_at REAL
    );
    """,
]


def conn() -> sqlite3.Connection:
    global _CONN
    if _CONN is None:
        with _LOCK:
            if _CONN is None:
                DATA_DIR.mkdir(parents=True, exist_ok=True)
                c = sqlite3.connect(DB_PATH, check_same_thread=False, isolation_level=None)
                c.row_factory = sqlite3.Row
                c.execute("PRAGMA journal_mode=WAL")
                c.execute("PRAGMA synchronous=NORMAL")
                c.execute("PRAGMA foreign_keys=ON")
                # Wait briefly instead of failing if the owner has the DB open in sqlite3.
                c.execute("PRAGMA busy_timeout=250")
                version = c.execute("PRAGMA user_version").fetchone()[0]
                for n, sql in enumerate(MIGRATIONS[version:], start=version + 1):
                    try:
                        c.executescript("BEGIN;" + sql + f"; PRAGMA user_version={n}; COMMIT;")
                    except sqlite3.Error:
                        c.rollback()
                        c.close()
                        raise
                os.chmod(DB_PATH, 0o600)
                _CONN = c
    return _CONN


def q(sql: str, args=()) -> list[sqlite3.Row]:
    with _LOCK:
        return conn().execute(sql, args).fetchall()


def x(sql: str, args=()) -> int:
    """Execute a write; returns lastrowid."""
    with _LOCK:
        cur = conn().execute(sql, args)
        return cur.lastrowid


def dumps(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), sort_keys=True)


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------

ITEM_TYPES = ("module", "lesson", "lab", "assessment")


def progress(user=OWNER) -> dict:
    rows = q("SELECT * FROM progress WHERE user_id=?", (user,))
    return {r["item_id"]: {k: r[k] for k in ("item_type", "state", "content_hash_at_done",
                                             "started_at", "done_at", "active_s")} for r in rows}


def set_progress(item_type: str, item_id: str, state: str, content_hash: str | None, user=OWNER):
    """Monotonic: done never goes back to in_progress (re-opening a finished lesson doesn't undo
    it). Re-finishing an item updates its content hash, so "done (earlier version)" clears."""
    now = time.time()
    with _LOCK:
        c = conn()
        row = c.execute("SELECT state FROM progress WHERE user_id=? AND item_type=? AND item_id=?",
                        (user, item_type, item_id)).fetchone()
        if row is None:
            c.execute("INSERT INTO progress (user_id,item_type,item_id,state,started_at,done_at,"
                      "content_hash_at_done) VALUES (?,?,?,?,?,?,?)",
                      (user, item_type, item_id, state, now, now if state == "done" else None,
                       content_hash if state == "done" else None))
        elif state == "done":
            c.execute("UPDATE progress SET state='done', done_at=?, content_hash_at_done=? "
                      "WHERE user_id=? AND item_type=? AND item_id=?",
                      (now, content_hash, user, item_type, item_id))


def add_active(item_type: str, item_id: str, seconds: float, user=OWNER):
    """Upsert: time spent on a lab or check that has no progress row yet still counts."""
    with _LOCK:
        conn().execute("INSERT INTO progress (user_id,item_type,item_id,state,started_at,active_s) "
                       "VALUES (?,?,?,'in_progress',?,?) ON CONFLICT(user_id,item_type,item_id) "
                       "DO UPDATE SET active_s = active_s + excluded.active_s",
                       (user, item_type, item_id, time.time(), seconds))


def add_event(kind: str, item_id: str | None, data: dict | None, ts: float | None = None,
              content_hash: str | None = None, clock_ok: bool | None = None, user=OWNER):
    x("INSERT INTO event (ts,clock_ok,user_id,kind,item_id,content_hash,data) VALUES (?,?,?,?,?,?,?)",
      (ts or time.time(), None if clock_ok is None else int(clock_ok), user, kind, item_id,
       content_hash, dumps(data) if data else None))
