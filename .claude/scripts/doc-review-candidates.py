#!/usr/bin/env python3
"""List every status claim the doc-review agent must give a verdict on.

A candidate is a line in a Markdown file that uses status wording which goes stale as the build
progresses ("pending", "not yet installed", "in transit", "still inserted", ...). Dated journals
are skipped because they record history, not current state. Struck-through and "Superseded" lines
are skipped for the same reason.

    python3 .claude/scripts/doc-review-candidates.py [repo-root]

Output: one "path:line: text" per candidate, then a count. The agent must account for every line.
"""
import re
import sys
from pathlib import Path

STATUS = re.compile(
    r"pending|not (yet )?(installed|arrived|fitted|run|tested|verified|configured|bought|purchased)"
    r"|in transit|awaiting|on order|not shipped|pre-?order|not arrived"
    r"|still (open|missing|unbought|blocking|inserted|pending|in the mail)"
    r"|has(n't| not) (arrived|shipped|been (run|tested|installed|fitted))"
    r"|once it (lands|arrives)|until .{0,40} arrives|blocked on",
    re.IGNORECASE,
)
# Dated history, or definitions that talk about status words rather than make status claims.
SKIP_FILES = {"docs/logs/build-log.md", "CHANGELOG.md", "docs/logs/decisions.md"}
SKIP_DIRS = (".claude/", ".git/", "docs/records/invoices/", "node_modules/")
SKIP_LINE = re.compile(r"~~|superseded", re.IGNORECASE)


def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    n = 0
    for p in sorted(root.rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if rel in SKIP_FILES or rel.startswith(SKIP_DIRS):
            continue
        for i, line in enumerate(p.read_text(errors="replace").splitlines(), 1):
            if STATUS.search(line) and not SKIP_LINE.search(line):
                print(f"{rel}:{i}: {line.strip()[:220]}")
                n += 1
    print(f"-- {n} candidates")


if __name__ == "__main__":
    main()
