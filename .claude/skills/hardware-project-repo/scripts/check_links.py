#!/usr/bin/env python3
"""Report broken relative links in Markdown files.

Run from the repository root before committing. Exits non-zero if any link is broken, so it can be
wired into a pre-commit hook or CI step.
"""

import os
import re
import sys

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__"}


def main(root="."):
    broken = []
    checked = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if not name.endswith(".md"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            for match in LINK.finditer(text):
                target = match.group(1).split("#")[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                checked += 1
                resolved = os.path.normpath(os.path.join(dirpath, target))
                if not os.path.exists(resolved):
                    broken.append("%s -> %s" % (path, target))

    print("checked %d relative links; broken: %d" % (checked, len(broken)))
    for item in broken:
        print("  %s" % item)
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
