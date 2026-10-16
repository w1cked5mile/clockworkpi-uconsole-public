#!/usr/bin/env bash
#
# Headless-render the webdash "Build log" (#/timeline) view to a PNG, for visual
# verification without running the dashboard.
#
# Why this exists: the live app is behind a login, and loading it headless hangs
# chromium on exit — main.js opens a status WebSocket that reconnects forever, so the
# page never goes idle. The timeline view is static (built by timeline.js from in-file
# data, no API), so this mounts just that view against the REAL timeline.js + styles.css
# and screenshots it.
#
# How: symlinks webdash/app/static/{js,styles.css} into a temp dir next to a copy of
# timeline-harness.html, then renders file://.../index.html. ES-module imports over
# file:// need --allow-file-access-from-files; serving over http instead reintroduces the
# hang (python's single-thread http.server stalls chromium). Symlinks, not copies, so the
# render always tracks the shipping source.
#
# Usage:   ./render-timeline.sh [out.png] [WxH]
#   out.png  output path (default: $TMPDIR/webdash-timeline.png)
#   WxH      chromium window size as W,H (default: 920,3600 — tall enough for all entries)
#
# Requires: chromium (or set CHROMIUM=/path/to/chrome).
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
static="$(cd "$here/../../app/static" && pwd)"
out="${1:-${TMPDIR:-/tmp}/webdash-timeline.png}"
size="${2:-920,3600}"

chromium="${CHROMIUM:-$(command -v chromium || command -v chromium-browser \
  || command -v google-chrome || command -v google-chrome-stable || true)}"
if [ -z "$chromium" ]; then
  echo "render-timeline: no chromium/chrome found; set CHROMIUM=/path/to/chrome" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
ln -s "$static/js" "$tmp/js"
ln -s "$static/styles.css" "$tmp/styles.css"
cp "$here/timeline-harness.html" "$tmp/index.html"

# --no-sandbox: rendering our own local files headless on Linux/Pi, where the chromium
# sandbox often isn't available. --virtual-time-budget lets the module run before capture.
"$chromium" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --allow-file-access-from-files --hide-scrollbars --force-color-profile=srgb \
  --window-size="$size" --virtual-time-budget=5000 \
  --screenshot="$out" "file://$tmp/index.html" >/dev/null 2>&1

echo "Wrote $out ($(file -b "$out" 2>/dev/null || echo image))"
