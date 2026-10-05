"""The compiled curriculum bundle: load it, notice when a new one lands, and hand out the parts a
browser may see.

The bundle is written on the host by host-helpers/learn-compile.py into a directory mounted
read-only at /learn (WEBDASH_LEARN_DIR). `current.json` is a relative symlink the compiler swaps
atomically, so checking where it points on each request is enough to pick up a recompile without
restarting the container. Nothing here is served from /static, which has no login.
"""
import json
import os
import threading
from pathlib import Path

LEARN_DIR = Path(os.environ.get("WEBDASH_LEARN_DIR", "/learn"))
_LOCK = threading.Lock()
_STATE: dict = {"target": None, "bundle": None, "error": None}


def get() -> dict | None:
    """The current bundle, or None if none has been compiled yet (or it can't be read)."""
    current = LEARN_DIR / "current.json"
    try:
        target = os.path.realpath(current)
        mtime = os.stat(target).st_mtime
    except OSError as exc:
        _STATE.update(target=None, bundle=None, error=f"no bundle: {exc.strerror}")
        return None
    key = (target, mtime)
    if _STATE["target"] == key:
        return _STATE["bundle"]
    with _LOCK:
        if _STATE["target"] != key:
            try:
                with open(target) as f:
                    bundle = json.load(f)
                _STATE.update(target=key, bundle=bundle, error=None)
            except (OSError, ValueError) as exc:
                # Keep serving the previous bundle if the new one is unreadable.
                _STATE["error"] = f"bundle unreadable: {exc}"
    return _STATE["bundle"]


def error() -> str | None:
    return _STATE["error"]


def public_assessment(a: dict) -> dict:
    """An assessment without answers or explanations — grading happens server-side (S7)."""
    hidden = {"answer", "tolerance", "explanation"}
    return {**{k: v for k, v in a.items() if k != "items"},
            "items": [{k: v for k, v in it.items() if k not in hidden} for it in a.get("items", [])]}


def catalog(b: dict) -> dict:
    """Everything the learning home and module list need, without lesson bodies."""
    modules = {}
    for mid, m in b["modules"].items():
        modules[mid] = {
            **{k: m.get(k) for k in ("id", "title", "themed_title", "discipline", "station",
                                     "prerequisites", "today", "objectives", "est_minutes",
                                     "assessment", "content_hash")},
            "lessons": [{"id": lid, "title": b["lessons"][lid]["title"],
                         "est_minutes": b["lessons"][lid].get("est_minutes")} for lid in m["lessons"]],
            "labs": [{"id": x, "title": b["labs"][x]["title"], "themed_title": b["labs"][x].get("themed_title"),
                      "transmits": bool(b["labs"][x].get("transmits"))} for x in m["labs"]],
        }
    return {
        "meta": {k: b["meta"].get(k) for k in ("bundle_sha", "commit", "compiled_at", "source", "counts")},
        "tracks": b["tracks"],
        "modules": modules,
        "glossary": {g: {k: v for k, v in e.items() if k != "blocks"} for g, e in b["glossary"].items()},
    }
