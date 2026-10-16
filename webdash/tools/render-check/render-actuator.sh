#!/usr/bin/env bash
#
# Headless-render the mesh transmit control (actuator.js driven by the real mesh.js) in every
# state, for visual verification without the live dashboard. See README.md for why the live app
# can't be rendered headless.
#
# How: stages actuator-harness.html in a temp dir with symlinks to app/static/{js,styles.css},
# a fixtures.js generated from the real mesh_radio.py, and the actuator markup copied out of
# index.html, then screenshots one PNG per state.
#
# Usage:   ./render-actuator.sh [out-dir] [WxH] [skin]
#   out-dir  where PNGs go (default: $TMPDIR/webdash-actuator)
#   WxH      window size (default: 1280,720)
#   skin     "default" or a data-skin name, e.g. "vintage" (default: default)
#
# Requires: chromium (or set CHROMIUM=/path/to/chrome) and python3.
set -euo pipefail

here="$(cd "$(dirname "$0")" && pwd)"
static="$(cd "$here/../../app/static" && pwd)"
out="${1:-${TMPDIR:-/tmp}/webdash-actuator}"
size="${2:-1280,720}"
skin="${3:-default}"

chromium="${CHROMIUM:-$(command -v chromium || command -v chromium-browser \
  || command -v google-chrome || command -v google-chrome-stable || true)}"
if [ -z "$chromium" ]; then
  echo "render-actuator: no chromium/chrome found; set CHROMIUM=/path/to/chrome" >&2
  exit 1
fi

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
ln -s "$static/js" "$tmp/js"
ln -s "$static/styles.css" "$tmp/styles.css"
python3 "$here/actuator-fixtures.py" > "$tmp/fixtures.js"
python3 - "$static/index.html" "$here/actuator-harness.html" "$tmp/index.html" "$skin" <<'PY'
import re, sys
index, harness, dest, skin = sys.argv[1:]
src = open(index, encoding="utf-8").read()
m = re.search(r'<svg hidden aria-hidden="true"><symbol id="g-antenna".*?id="mesh-mqtt".*?</details>\s*</div>', src, re.S)
if not m:
    sys.exit("render-actuator: actuator markup not found in index.html")
page = open(harness, encoding="utf-8").read().replace("<!--ACTUATOR-->", m.group(0))
if skin != "default":
    page = page.replace('<html lang="en">', f'<html lang="en" data-skin="{skin}">', 1)
open(dest, "w", encoding="utf-8").write(page)
PY

mkdir -p "$out"
states=$(python3 -c "import re,sys; print(' '.join(re.findall(r'^ \"([\w-]+)\": \{', open(sys.argv[1]).read(), re.M)))" "$tmp/fixtures.js")
for st in $states; do
  png="$out/actuator-$st-$skin-${size/,/x}.png"
  "$chromium" --headless=new --no-sandbox --disable-gpu --disable-dev-shm-usage \
    --allow-file-access-from-files --hide-scrollbars --force-color-profile=srgb \
    --window-size="$size" --virtual-time-budget=3000 \
    --screenshot="$png" "file://$tmp/index.html?state=$st" >/dev/null 2>&1
  echo "Wrote $png"
done
