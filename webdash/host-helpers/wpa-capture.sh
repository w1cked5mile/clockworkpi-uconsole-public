#!/usr/bin/env bash
# Authorized WPA/WPA2 handshake capture on wlan1 (the AC1200 on the USB rail), driven by the
# webdash via wpa-audit-bridge.py. Runs as root (installed root-owned to /usr/local/sbin and
# invoked through a scoped sudoers entry — see wpa-capture.sudoers).
#
# AUTHORIZED EQUIPMENT ONLY. This script independently re-checks the target BSSID against the
# webdash allowlist (own gear or a documented engagement) and refuses anything not on it, BEFORE it
# touches the radio — so the gate holds here, at the privileged edge, not just in the browser. See
# the repo's knowledge/README.md responsible-use section and software/aircrack-ng.md.
#
# Deauth is BOUNDED and targeted (a few frames per round, a small number of rounds) to elicit a
# handshake from an AP you are authorized to test. It is never a continuous flood — that would be a
# DoS, which is out of scope.
set -uo pipefail

BSSID=""; ALLOWLIST=""; OUTDIR=""; STATEFILE=""; CANCELFILE=""
CHANNEL=""; DEAUTH_PER_ROUND=5; MAX_ROUNDS=4; ROUND_WAIT=6; CAPTURE_TIMEOUT=90; NO_DEAUTH=0
IFACE="wlan1"

while [ $# -gt 0 ]; do
  case "$1" in
    --bssid) BSSID="$2"; shift 2;;
    --allowlist) ALLOWLIST="$2"; shift 2;;
    --outdir) OUTDIR="$2"; shift 2;;
    --statefile) STATEFILE="$2"; shift 2;;
    --cancelfile) CANCELFILE="$2"; shift 2;;
    --channel) CHANNEL="$2"; shift 2;;
    --deauth) DEAUTH_PER_ROUND="$2"; shift 2;;
    --rounds) MAX_ROUNDS="$2"; shift 2;;
    --timeout) CAPTURE_TIMEOUT="$2"; shift 2;;
    --iface) IFACE="$2"; shift 2;;
    --no-deauth) NO_DEAUTH=1; shift;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

MON=""; DUMP_PID=""; CAP_PREFIX=""
BSSID_UC="$(printf '%s' "$BSSID" | tr 'a-f' 'A-F')"

emit() {  # emit <stage> <message> [handshake] [cap]
  local stage="$1" msg="$2" hs="${3:-false}" cap="${4:-}"
  [ -n "$STATEFILE" ] || return 0
  python3 - "$STATEFILE" "$stage" "$msg" "$hs" "$cap" "$BSSID_UC" "$CHANNEL" <<'PY' 2>/dev/null || true
import json, sys, time
path, stage, msg, hs, cap, bssid, ch = sys.argv[1:8]
json.dump({"stage": stage, "message": msg, "handshake": hs == "true",
           "cap": cap, "bssid": bssid, "channel": ch,
           "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())},
          open(path, "w"))
PY
}

cancelled() { [ -n "$CANCELFILE" ] && [ -f "$CANCELFILE" ]; }

cleanup() {
  [ -n "$DUMP_PID" ] && kill "$DUMP_PID" 2>/dev/null
  if [ -n "$MON" ]; then airmon-ng stop "$MON" >/dev/null 2>&1; fi
}
trap cleanup EXIT

fail() { emit "error" "$1"; exit 1; }

# 1) Authorization gate — independent of the webdash, before any RF.
emit "validating" "checking authorization for $BSSID_UC"
echo "$BSSID_UC" | grep -qE '^([0-9A-F]{2}:){5}[0-9A-F]{2}$' || fail "bad BSSID format"
[ -r "$ALLOWLIST" ] || fail "allowlist not readable: $ALLOWLIST"
python3 - "$ALLOWLIST" "$BSSID_UC" <<'PY'
import json, sys
try:
    entries = json.load(open(sys.argv[1])).get("entries", [])
except Exception:
    sys.exit(3)
sys.exit(0 if any(e.get("bssid", "").upper() == sys.argv[2] for e in entries) else 3)
PY
[ $? -eq 0 ] || fail "$BSSID_UC is NOT on the authorized allowlist — refusing"
cancelled && { emit "cancelled" "cancelled before start"; exit 0; }

# 2) Monitor mode. Reconcile any leftover wlan1mon, then start fresh.
emit "starting_monitor" "putting $IFACE into monitor mode"
airmon-ng stop wlan1mon >/dev/null 2>&1 || true
airmon-ng start "$IFACE" >/dev/null 2>&1 || fail "airmon-ng start $IFACE failed"
MON="$(iw dev 2>/dev/null | awk '/Interface/{i=$2} /type monitor/{print i; exit}')"
[ -n "$MON" ] || MON="${IFACE}mon"
iw dev "$MON" info >/dev/null 2>&1 || fail "no monitor interface after airmon-ng start"

mkdir -p "$OUTDIR"
TS="$(date +%Y%m%d-%H%M%S)"
CAP_PREFIX="$OUTDIR/wpa-$TS"

# 3) Channel — use the given one, else a short scan to find the target's channel.
if [ -z "$CHANNEL" ]; then
  emit "scanning_channel" "scanning for $BSSID_UC to find its channel"
  SCAN="$OUTDIR/.scan-$TS"
  airodump-ng --bssid "$BSSID_UC" -w "$SCAN" --output-format csv --write-interval 1 "$MON" \
    >/dev/null 2>&1 &
  sp=$!
  for _ in $(seq 1 12); do
    sleep 1; cancelled && { kill "$sp" 2>/dev/null; emit "cancelled" "cancelled during scan"; exit 0; }
    CHANNEL="$(awk -F, -v b="$BSSID_UC" 'toupper($1) ~ b {gsub(/ /,"",$4); print $4; exit}' "$SCAN"*.csv 2>/dev/null)"
    [ -n "$CHANNEL" ] && break
  done
  kill "$sp" 2>/dev/null; rm -f "$SCAN"*.csv 2>/dev/null
  [ -n "$CHANNEL" ] || fail "could not find $BSSID_UC on any channel (in range? powered on?)"
fi

# 4) Capture, locked to the target BSSID + channel.
emit "capturing" "capturing on channel $CHANNEL"
airodump-ng --bssid "$BSSID_UC" -c "$CHANNEL" -w "$CAP_PREFIX" --output-format pcap "$MON" \
  >/dev/null 2>&1 &
DUMP_PID=$!
sleep 3

CAPFILE="$CAP_PREFIX-01.cap"
have_handshake() { [ -r "$CAPFILE" ] && aircrack-ng "$CAPFILE" 2>/dev/null | grep -qiE 'handshake'; }

# 5) Bounded deauth rounds + handshake polling (or passive wait if --no-deauth / dry run).
deadline=$(( $(date +%s) + CAPTURE_TIMEOUT ))
round=0
while [ "$(date +%s)" -lt "$deadline" ]; do
  cancelled && { emit "cancelled" "cancelled during capture"; exit 0; }
  if have_handshake; then
    emit "captured" "handshake captured" "true" "$CAPFILE"; exit 0
  fi
  if [ "$NO_DEAUTH" -eq 0 ] && [ "$round" -lt "$MAX_ROUNDS" ]; then
    round=$((round + 1))
    emit "deauthing" "bounded deauth round $round/$MAX_ROUNDS ($DEAUTH_PER_ROUND frames)"
    aireplay-ng --deauth "$DEAUTH_PER_ROUND" -a "$BSSID_UC" "$MON" >/dev/null 2>&1 || true
  else
    emit "waiting_handshake" "waiting for a client to reconnect"
  fi
  sleep "$ROUND_WAIT"
done

if have_handshake; then
  emit "captured" "handshake captured" "true" "$CAPFILE"; exit 0
fi
emit "no_handshake" "no handshake within ${CAPTURE_TIMEOUT}s (no client reconnected?)"
exit 0
