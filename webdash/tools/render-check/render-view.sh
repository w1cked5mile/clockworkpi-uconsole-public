#!/usr/bin/env bash
#
# Headless-render ONE dashboard view by running the REAL main.js with the network neutralized
# (fake status WebSocket delivering one fixture snapshot; fake fetch serving fixtures for the boot
# /api/* calls). Unlike render-actuator.sh, which bypasses main.js, this exercises routing,
# rendering and tab selection exactly as production. See README.md for why the live app hangs.
#
# Usage:  ./render-view.sh [view] [out.png] [WxH] [skin]
#   view     hash path after #/ (default: overview):
#            overview | mesh | gps | power | system | learn | timeline
#            wifi (opens the Kismet tab) | wifi/kismet | wifi/survey | wifi/capture | wifi/wpa
#            sdr (opens ADS-B) | sdr/adsb | sdr/hunt | sdr/listen | sdr/owrx
#            The old top-level #/survey, #/capture, #/wpa still work — they redirect to the
#            matching Wi-Fi tab, same as in the app.
#   out.png  output PNG (default: $TMPDIR/webdash-view/view-<view>-<skin>-<WxH>.png)
#   WxH      window size (default: 1280,480 — the uConsole panel area; 1280,720 is the full panel)
#   skin     "default" or "vintage" (default: default)
#
# Requires: chromium (or set CHROMIUM=/path/to/chrome) and python3.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
static="$(cd "$here/../../app/static" && pwd)"
view="${1:-overview}"
size="${3:-1280,480}"
skin="${4:-default}"
safe="$(printf '%s' "$view" | tr '/' '-')"
out="${2:-${TMPDIR:-/tmp}/webdash-view/view-$safe-$skin-${size/,/x}.png}"

chromium="${CHROMIUM:-$(command -v chromium || command -v chromium-browser \
  || command -v google-chrome || command -v google-chrome-stable || true)}"
if [ -z "$chromium" ]; then
  echo "render-view: no chromium/chrome found; set CHROMIUM=/path/to/chrome" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
ln -s "$static/js" "$tmp/js"
ln -s "$static/styles.css" "$tmp/styles.css"
python3 "$here/fixture-status.py" > "$tmp/fixture-status.js"
python3 - "$static/index.html" "$here/view-harness.html" "$tmp/index.html" <<'PY'
import re, sys
index, harness, dest = sys.argv[1:]
src = open(index, encoding="utf-8").read()
def grab(tag):
    # non-greedy, so <header class="strip">…</header> is the status strip (the first <header>);
    # the tile <header class="tile-head"> blocks live inside <main> and come with it.
    m = re.search(rf"<{tag}\b.*?</{tag}>", src, re.S)
    if not m:
        sys.exit(f"render-view: <{tag}> not found in index.html")
    return m.group(0)
# <main>…</main> stops at the one </main>; the <script src="/static/js/main.js"> tag sits AFTER it
# and is therefore dropped — the shim injects main.js instead.
app = (grab("header") + "\n" + grab("main")).replace("/static/", "./")
page = open(harness, encoding="utf-8").read().replace("<!--APP-->", app)
open(dest, "w", encoding="utf-8").write(page)
PY

mkdir -p "$(dirname "$out")"
"$chromium" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
  --allow-file-access-from-files --hide-scrollbars --force-color-profile=srgb \
  --window-size="$size" --virtual-time-budget=3000 \
  --screenshot="$out" "file://$tmp/index.html?view=$view&skin=$skin" >/dev/null 2>&1
echo "Wrote $out"
