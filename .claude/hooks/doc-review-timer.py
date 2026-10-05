#!/usr/bin/env python3
"""Count active working time in this repo and ask for a doc-review every 8 h of it.

Called by Claude Code hooks (UserPromptSubmit and Stop, see .claude/settings.json) with the hook
JSON on stdin. Time between consecutive events counts as work when the gap is 30 min or less;
longer gaps count as idle and add nothing. Once 8 h accumulate, every UserPromptSubmit injects a
reminder to run the doc-review agent until someone records a review:

    .claude/hooks/doc-review-timer.py --reset       # after a review: zero the clock, record HEAD
    .claude/hooks/doc-review-timer.py --status      # accumulated time, last review

State is per machine, kept out of the repo: ~/.local/state/clockworkpi-uconsole/doc-review.json
"""
import json
import os
import subprocess
import sys
import time
from pathlib import Path

THRESHOLD_S = 8 * 3600
IDLE_CAP_S = 30 * 60
STATE = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "clockworkpi-uconsole/doc-review.json"
PROJECT = os.environ.get("CLAUDE_PROJECT_DIR") or str(Path(__file__).resolve().parents[2])


def load():
    try:
        return json.loads(STATE.read_text())
    except (OSError, ValueError):
        return {"active_s": 0, "last_event": None, "last_review_commit": None, "last_review_at": None}


def save(s):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(s, indent=1))
    tmp.replace(STATE)


def head():
    try:
        return subprocess.run(["git", "-C", PROJECT, "rev-parse", "--short", "HEAD"],
                              capture_output=True, text=True, timeout=5).stdout.strip() or None
    except (OSError, subprocess.SubprocessError):
        return None


def hours(sec):
    return f"{sec / 3600:.1f} h"


def main():
    s = load()
    now = time.time()
    if "--reset" in sys.argv:
        s.update(active_s=0, last_event=now, last_review_commit=head(),
                 last_review_at=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)))
        save(s)
        print(f"doc-review clock reset; last review = {s['last_review_commit']} at {s['last_review_at']}")
        return
    if "--status" in sys.argv:
        print(f"active since last review: {hours(s['active_s'])} of {hours(THRESHOLD_S)}; "
              f"last review: {s['last_review_commit'] or 'never'} at {s['last_review_at'] or '-'}")
        return

    try:
        event = json.load(sys.stdin).get("hook_event_name", "")
    except ValueError:
        event = ""
    if s["last_event"] is not None:
        gap = now - s["last_event"]
        if 0 < gap <= IDLE_CAP_S:
            s["active_s"] += gap
    s["last_event"] = now
    save(s)

    if event == "UserPromptSubmit" and s["active_s"] >= THRESHOLD_S:
        since = s["last_review_commit"]
        context = (
            f"DOC REVIEW DUE: {hours(s['active_s'])} of active working time since the last "
            f"documentation review (last review: {since or 'never'}). Before other work, or "
            f"alongside it if the user's request is urgent, run the `doc-review` agent "
            f"(Agent tool, subagent_type \"doc-review\") with the prompt: \"Review for "
            f"discrepancies since commit {since or '(none; review everything)'}.\" Then tell the "
            f"user what it found and offer to fix it. After the review has run, reset the clock "
            f"with `.claude/hooks/doc-review-timer.py --reset`. Mention this in one line; don't "
            f"let it derail the user's request."
        )
        print(json.dumps({
            "systemMessage": f"Doc review due ({hours(s['active_s'])} of work since the last one).",
            "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context},
        }))


if __name__ == "__main__":
    try:
        main()
    except Exception:  # a broken timer must never block a prompt
        pass
