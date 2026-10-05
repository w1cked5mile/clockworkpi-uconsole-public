"""Turn host-side sync records (/learn/changes/<commit>.json, written by
host-helpers/learn-sync.py) into review items for the owner, and report content health.

Ingestion is idempotent: a record is skipped if review items for its target commit already exist
or its file was seen before in this process. Called from the lab tick about every 30 s.
"""
import json
import time
from pathlib import Path

from . import bundle, db
from .schema import get_path

_seen: set[str] = set()
_last = 0.0


def ingest(force: bool = False) -> int:
    global _last
    if not force and time.time() - _last < 30:
        return 0
    _last = time.time()
    changes = Path(bundle.LEARN_DIR) / "changes"
    added = 0
    try:
        files = sorted(changes.glob("*.json")) if changes.is_dir() else []  # names: stable order
    except OSError:
        files = []
    for f in files:
        if f.name in _seen:
            continue
        _seen.add(f.name)
        try:
            rec = json.loads(f.read_text())
            to = rec.get("to")
            if not to or db.q("SELECT 1 FROM content_version WHERE commit_sha=?", (to,)):
                continue
            items = [it for it in rec.get("items") or [] if isinstance(it, dict)
                     and it.get("module") and it.get("reason")]
            with db._LOCK:  # one transaction per record: all of it or none
                c = db.conn()
                c.execute("BEGIN")
                try:
                    c.execute("INSERT OR IGNORE INTO content_version (bundle_sha, commit_sha, seen_at) VALUES (?,?,?)",
                              (f"{rec.get('bundle_sha')}@{to}", to, time.time()))
                    for it in items:
                        c.execute("INSERT INTO review_item (module_id, commit_from, commit_to, changed_paths, "
                                  "reason, created_at) VALUES (?,?,?,?,?,?)",
                                  (it["module"], rec.get("from"), to, db.dumps(it.get("paths", [])),
                                   it["reason"], time.time()))
                    c.execute("COMMIT")
                except Exception:
                    c.execute("ROLLBACK")
                    raise
            added += len(items)
            db.add_event("content_sync", to, {"items": len(items)})
        except (OSError, ValueError, TypeError) as exc:
            print(f"learn: skipped sync record {f.name}: {exc!r}", flush=True)
    return added


def open_by_module() -> dict:
    out = {}
    for r in db.q("SELECT module_id, reason FROM review_item WHERE state='open'"):
        out.setdefault(r["module_id"], []).append(r["reason"])
    return out


def review_items(limit=50) -> list[dict]:
    rows = db.q("SELECT * FROM review_item ORDER BY state='open' DESC, created_at DESC LIMIT ?", (limit,))
    return [{**dict(r), "changed_paths": json.loads(r["changed_paths"] or "[]")} for r in rows]


def resolve(item_id: int, state: str):
    db.x("UPDATE review_item SET state=?, resolved_at=? WHERE id=?", (state, time.time(), item_id))


def health(st: dict | None) -> list[dict]:
    """Every status path a lab checks, and whether the collectors report it right now. "Not
    reported" is often normal (readsb stopped); a path that is never reported is a data gap."""
    b = bundle.get() or {}
    paths: dict[str, set] = {}
    for lab in (b.get("labs") or {}).values():
        for s in lab.get("steps") or []:
            c = s.get("check") or {}
            if c.get("path") and c.get("type") in ("status", "computed"):
                paths.setdefault(c["path"], set()).add(lab["id"])
        for p in lab.get("evidence") or []:
            paths.setdefault(p, set()).add(lab["id"])
    out = []
    for p, labs in sorted(paths.items()):
        try:
            get_path(st or {}, p)
            ok = True
        except KeyError:
            ok = False
        out.append({"path": p, "reported": ok, "labs": sorted(labs)})
    return out
