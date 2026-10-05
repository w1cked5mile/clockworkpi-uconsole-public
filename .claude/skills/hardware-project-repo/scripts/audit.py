#!/usr/bin/env python3
"""Mechanical audit of a documentation-first hardware repository.

Covers only what can be checked deterministically, so a reviewing agent or human spends judgment
on what cannot: broken relative links, secret-shaped strings, precise coordinate pairs, staged
configs missing verify/rollback lines, and unfilled template placeholders.

Exit code 1 if any BLOCKING finding is present (secrets, coordinates, broken links).

Usage:
    python3 audit.py [repo-root]
"""

import os
import re
import sys

SKIP_DIRS = {".git", "node_modules", ".venv", "__pycache__", "assets"}

# Meta-documentation describes templates and patterns, so it legitimately contains placeholder
# syntax and example credential strings. Exclude it from the heuristics that would fire on those.
META_PATH_PARTS = ("hardware-project-repo", ".claude/agents")
DOC_EXT = (".md",)
CONFIG_DIRS = ("configs",)

LINK = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

SECRET_PATTERNS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), "private key block"),
    (re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), "AWS access key id"),
    (re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"), "GitHub token"),
    (re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"), "Slack token"),
    (re.compile(r"(?i)\b(?:password|passwd|psk|api[_-]?key|secret|token)\s*[:=]\s*"
                r"['\"]?[A-Za-z0-9+/=_-]{8,}"), "credential assignment"),
    (re.compile(r"(?i)\?psk=|[?&]channel(?:_url)?=[A-Za-z0-9+/=_-]{16,}"), "key embedded in URL"),
]

# Decimal lat/long pair with 4+ decimal places — house-address precision.
COORD = re.compile(r"-?\b\d{1,2}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}\b")

PLACEHOLDER = re.compile(r"\{\{[A-Z_]+\}\}|<procedure>|<board>|<step>|\bTKTK\b")

ESTIMATE_HINT = re.compile(r"(?i)\b(estimate[sd]?|est\.|typical|approx\.?|~\s*\d)")
REPLACEMENT_HINT = re.compile(r"(?i)replace[sd]? (?:with|by)|measure(?:d|ment)|verify with|`[^`]+`")

VERIFY_HINT = re.compile(r"(?i)verif")
ROLLBACK_HINT = re.compile(r"(?i)roll ?back|restore|revert|\.bak")


def walk(root, exts=None):
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if exts and not name.endswith(exts):
                continue
            yield os.path.join(dirpath, name)


def read(path):
    with open(path, encoding="utf-8", errors="replace") as fh:
        return fh.read()


def rel(path, root):
    return os.path.relpath(path, root)


def is_meta(path):
    norm = path.replace(os.sep, "/")
    return any(part in norm for part in META_PATH_PARTS)


def check_links(root):
    out = []
    for path in walk(root, DOC_EXT):
        base = os.path.dirname(path)
        for lineno, line in enumerate(read(path).splitlines(), 1):
            for match in LINK.finditer(line):
                target = match.group(1).split("#")[0].strip()
                if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                    continue
                if not os.path.exists(os.path.normpath(os.path.join(base, target))):
                    out.append("%s:%d broken link -> %s" % (rel(path, root), lineno, target))
    return out


def check_secrets(root):
    out = []
    self_path = os.path.realpath(__file__)
    for path in walk(root):
        if path.endswith((".pyc", ".png", ".jpg", ".pdf")) or is_meta(path):
            continue
        if os.path.realpath(path) == self_path:
            continue  # this script's own patterns are not findings
        try:
            text = read(path)
        except (OSError, UnicodeDecodeError):
            continue
        for lineno, line in enumerate(text.splitlines(), 1):
            for pattern, label in SECRET_PATTERNS:
                if pattern.search(line):
                    out.append("%s:%d possible %s" % (rel(path, root), lineno, label))
                    break
    return out


def check_coordinates(root):
    out = []
    for path in walk(root, DOC_EXT):
        for lineno, line in enumerate(read(path).splitlines(), 1):
            if COORD.search(line):
                out.append("%s:%d precise coordinate pair — repo convention is city/grid only"
                           % (rel(path, root), lineno))
    return out


def check_placeholders(root):
    out = []
    for path in walk(root, DOC_EXT):
        name = os.path.basename(path)
        if name.startswith("TEMPLATE-") or path.endswith(".tmpl") or is_meta(path):
            continue
        for lineno, line in enumerate(read(path).splitlines(), 1):
            if PLACEHOLDER.search(line):
                out.append("%s:%d unfilled placeholder: %s"
                           % (rel(path, root), lineno, line.strip()[:70]))
    return out


def check_config_headers(root):
    out = []
    for base in CONFIG_DIRS:
        cdir = os.path.join(root, base)
        if not os.path.isdir(cdir):
            continue
        for path in walk(cdir):
            name = os.path.basename(path)
            if name.startswith("TEMPLATE-") or name == "README.md":
                continue
            text = read(path)
            missing = []
            if not VERIFY_HINT.search(text):
                missing.append("verify")
            if not ROLLBACK_HINT.search(text):
                missing.append("rollback")
            if missing:
                out.append("%s missing %s line in its header"
                           % (rel(path, root), "/".join(missing)))
    return out


def check_estimates(root):
    out = []
    for path in walk(root, DOC_EXT):
        text = read(path)
        if not ESTIMATE_HINT.search(text):
            continue
        if not REPLACEMENT_HINT.search(text):
            out.append("%s contains estimates but names no measurement that replaces them"
                       % rel(path, root))
    return out


def section(title, findings, blocking=False):
    marker = "BLOCKING" if blocking else "review"
    print("\n## %s (%d, %s)" % (title, len(findings), marker))
    if not findings:
        print("  none")
    for item in findings:
        print("  %s" % item)


def main(root="."):
    root = os.path.abspath(root)
    print("Mechanical audit of %s" % root)

    links = check_links(root)
    secrets = check_secrets(root)
    coords = check_coordinates(root)
    placeholders = check_placeholders(root)
    headers = check_config_headers(root)
    estimates = check_estimates(root)

    section("Secret-shaped strings", secrets, blocking=True)
    section("Precise coordinates", coords, blocking=True)
    section("Broken relative links", links, blocking=True)
    section("Staged configs missing verify/rollback", headers)
    section("Unfilled template placeholders", placeholders)
    section("Estimates with no stated replacement", estimates)

    blocking = len(secrets) + len(coords) + len(links)
    total = blocking + len(headers) + len(placeholders) + len(estimates)
    print("\n%d finding(s), %d blocking." % (total, blocking))
    print("Secret and estimate checks are heuristics — confirm each before acting.")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
