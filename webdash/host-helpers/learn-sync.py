#!/usr/bin/env python3
"""Keep the learning platform's bundle in step with `main`, and flag lessons whose sources moved.

Runs on the host (git + the compiler), from the systemd user timer learn-sync.timer every 15 min,
or by hand. It compiles only what is committed on main — never the working tree — so checking out a
feature branch cannot change what learners see. See docs/reference/learning-platform-plan.md §3.4.

For each new main commit it writes changes/<commit>.json next to the bundle:
  content_changed  a module's own curriculum files changed (republished; finishers see "updated")
  source_drift     a knowledge/ or software/ doc the module draws on changed, but the module didn't
                   — someone should check the lesson still matches (goes to the owner review queue)
webdash reads those files and turns them into review items.

  learn-sync.py            sync if main moved
  learn-sync.py --force    recompile even if main hasn't moved
"""
import argparse
import fnmatch
import importlib.util
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
OUT = Path.home() / ".local/share/uconsole-webdash/learn"
STATE = Path.home() / ".local/share/uconsole-webdash/learn-state.json"
BRANCH = "main"
CUR = "webdash/curriculum/"

_spec = importlib.util.spec_from_file_location("learn_compile", HERE / "learn-compile.py")
LC = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(LC)


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True, check=True).stdout


def load_state(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return {}


def changed_paths(old: str | None, new: str) -> tuple[list[str] | None, list[str]]:
    """(paths, commit subjects). paths None means "unknown" (first run or rewritten history)."""
    if not old:
        return None, []
    try:
        git("merge-base", "--is-ancestor", old, new)
    except subprocess.CalledProcessError:
        return None, []
    paths = [p for p in git("diff", "--name-only", "-z", old, new).split("\0") if p]
    subjects = [l for l in git("log", "--format=%h %s", f"{old}..{new}").splitlines() if l]
    return paths, subjects


def classify(bundle: dict, paths: list[str] | None, old_hashes: dict) -> list[dict]:
    items = []
    for mid, m in bundle["modules"].items():
        own = f"{CUR}modules/{mid}/"
        own_items = [mid, *m["lessons"], *m["labs"], *([m["assessment"]] if m.get("assessment") else [])]
        content = any(old_hashes.get(i) and old_hashes.get(i) != bundle["hashes"].get(i) for i in own_items)
        if paths is not None:
            content = content or any(p.startswith(own) for p in paths)
            drift = sorted({p for p in paths for g in m.get("sources") or [] if fnmatch.fnmatch(p, g)})
        else:
            drift = []
        if content:
            items.append({"module": mid, "reason": "content_changed", "paths": [p for p in (paths or []) if p.startswith(own)]})
        elif drift:
            items.append({"module": mid, "reason": "source_drift", "paths": drift})
    return items


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--branch", default=BRANCH, help="branch to follow (default main; others for testing)")
    ap.add_argument("--state", type=Path, default=STATE)
    args = ap.parse_args(argv)
    branch, state_file = args.branch, args.state

    try:
        new = git("rev-parse", branch).strip()
    except subprocess.CalledProcessError as exc:
        print(f"learn-sync: can't read {branch}: {exc.stderr.strip()}", file=sys.stderr)
        return 2
    state = load_state(state_file)
    old = state.get("last_compiled_commit")
    if new == old and not args.force:
        return 0

    rc = LC.main(["--ref", branch, "--out", str(OUT), "--quiet"])
    if rc != 0:
        # The previous bundle stays live; the errors were printed by the compiler.
        print(f"learn-sync: {branch}@{new[:7]} failed to compile; previous bundle kept", file=sys.stderr)
        return rc
    bundle = json.loads((OUT / "current.json").read_text())
    paths, subjects = changed_paths(old, new)
    items = classify(bundle, paths, state.get("hashes", {}))

    changes = OUT / "changes"
    changes.mkdir(exist_ok=True)
    record = {"from": old, "to": new, "at": time.time(), "bundle_sha": bundle["meta"]["bundle_sha"],
              "subjects": subjects[:50], "items": items, "first_run": old is None}
    tmp = changes / f".{new}.tmp"
    tmp.write_text(json.dumps(record, indent=1))
    os.replace(tmp, changes / f"{new}.json")
    for old_rec in sorted(changes.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[50:]:
        old_rec.unlink()

    state_file.write_text(json.dumps({"last_compiled_commit": new, "hashes": bundle["hashes"], "at": time.time()}))
    print(f"learn-sync: {branch}@{new[:7]} compiled ({bundle['meta']['bundle_sha']}); "
          f"{len(items)} module(s) flagged")
    return 0


if __name__ == "__main__":
    sys.exit(main())
