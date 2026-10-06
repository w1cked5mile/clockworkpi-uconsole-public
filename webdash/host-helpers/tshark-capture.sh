#!/usr/bin/env bash
# Passive packet capture + address-free summary for webdash troubleshooting, driven by the webdash
# via tshark-bridge.py. Runs as root (installed root-owned to /usr/local/sbin and invoked through a
# scoped sudoers entry — see tshark-capture.sudoers).
#
# PASSIVE ONLY. This script never transmits: it runs `dumpcap` in a bounded ring buffer and reads
# the newest segment back with `tshark` to compute aggregate counts. There is no injection, no
# deauth, no active probing — this is a troubleshooting tap for the hang/dropout investigation.
#
# Two things keep it safe for the status payload:
#   - Disk is bounded by the ring buffer (ringsize * ringfiles), so a long capture can never fill
#     the SD card. pcaps land in OUTDIR (default ~/labs/tshark) for GUI deep-dives.
#   - The JSON summary written to STATEFILE is ADDRESS-FREE (counts, rates, protocol names only) —
#     it never carries a MAC or IP, matching the webdash status-payload rule in collectors/net.py.
#     The on-disk pcap does contain addresses; that is the point of keeping it for Wireshark.
set -uo pipefail

IFACE=""; OUTDIR=""; STATEFILE=""; CANCELFILE=""; FILTER=""
RINGSIZE=10240; RINGFILES=10; DURATION=0; STATS_INTERVAL=10

while [ $# -gt 0 ]; do
  case "$1" in
    --iface) IFACE="$2"; shift 2;;
    --outdir) OUTDIR="$2"; shift 2;;
    --statefile) STATEFILE="$2"; shift 2;;
    --cancelfile) CANCELFILE="$2"; shift 2;;
    --filter) FILTER="$2"; shift 2;;
    --ringsize) RINGSIZE="$2"; shift 2;;        # KB per ring file
    --ringfiles) RINGFILES="$2"; shift 2;;      # number of ring files kept
    --duration) DURATION="$2"; shift 2;;        # overall cap in seconds, 0 = until cancelled
    --stats-interval) STATS_INTERVAL="$2"; shift 2;;
    *) echo "unknown arg: $1" >&2; exit 2;;
  esac
done

DUMP_PID=""; CAP_PREFIX=""; CAP_USER=""

emit() {  # emit <stage> <message> [json-fragment]
  local stage="$1" msg="$2" frag="${3:-}"
  [ -n "$STATEFILE" ] || return 0
  python3 - "$STATEFILE" "$stage" "$msg" "$IFACE" "$FILTER" "$frag" <<'PY' 2>/dev/null || true
import json, sys, time
path, stage, msg, iface, flt, frag = sys.argv[1:7]
out = {"stage": stage, "message": msg, "iface": iface, "filter": flt or None,
       "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
if frag:
    try:
        out.update(json.loads(frag))
    except Exception:
        pass
json.dump(out, open(path, "w"))
PY
}

cancelled() { [ -n "$CANCELFILE" ] && [ -f "$CANCELFILE" ]; }
cleanup() {
  [ -n "$DUMP_PID" ] && kill "$DUMP_PID" 2>/dev/null
  # runuser does not forward signals to its child, so also stop dumpcap by its unique output path.
  [ -n "$CAP_PREFIX" ] && pkill -f "dumpcap.*$CAP_PREFIX" 2>/dev/null
}
trap cleanup EXIT
fail() { emit "error" "$1"; exit 1; }

# 1) Validate the interface — it must be a real interface on this host with a safe name. This holds
#    the gate at the privileged edge (the bridge checks too), so capture can never be pointed at an
#    arbitrary string passed through from the browser.
emit "validating" "checking interface $IFACE"
echo "$IFACE" | grep -qE '^[A-Za-z0-9._-]{1,15}$' || fail "bad interface name"
[ -e "/sys/class/net/$IFACE" ] || [ "$IFACE" = "any" ] || fail "no such interface: $IFACE"
# Capture filters are passed to dumpcap -f; keep to characters a BPF expression actually uses so a
# crafted value can't smuggle anything past dumpcap's own parser.
if [ -n "$FILTER" ]; then
  echo "$FILTER" | grep -qE '^[][()A-Za-z0-9 ._:/<>=!&|-]{0,200}$' || fail "unsupported capture filter"
fi
echo "$RINGSIZE$RINGFILES$DURATION$STATS_INTERVAL" | grep -qE '^[0-9]+$' || fail "numeric args must be integers"
cancelled && { emit "cancelled" "cancelled before start"; exit 0; }

# 2) Start the bounded ring-buffer capture. dumpcap (not full tshark) does the privileged work —
#    less code runs as root. -b caps disk; -q keeps it quiet.
mkdir -p "$OUTDIR"
TS="$(date +%Y%m%d-%H%M%S)"
CAP_PREFIX="$OUTDIR/fancy-$IFACE-$TS"
# dumpcap drops CAP_DAC_OVERRIDE once it has the capture socket, so as root it cannot traverse a
# mode-700 home to write the pcap. Run it instead AS the directory's owner, who (via the wireshark
# group) has dumpcap's capture capability and owns OUTDIR — so the pcaps are user-owned and
# readable for a Wireshark deep-dive. Fall back to the sudo invoker, then root.
CAP_USER="$(stat -c %U "$OUTDIR" 2>/dev/null)"
[ -n "$CAP_USER" ] && [ "$CAP_USER" != "UNKNOWN" ] || CAP_USER="${SUDO_USER:-root}"
DUMP=(dumpcap -i "$IFACE" -q -w "$CAP_PREFIX.pcapng"
      -b "filesize:$RINGSIZE" -b "files:$RINGFILES")
[ -n "$FILTER" ] && DUMP+=(-f "$FILTER")
DERR="$OUTDIR/.dumpcap-$TS.err"
emit "capturing" "ring buffer on $IFACE (${RINGSIZE}KB x $RINGFILES)"
if [ "$CAP_USER" != "root" ] && command -v runuser >/dev/null 2>&1; then
  runuser -u "$CAP_USER" -- "${DUMP[@]}" >/dev/null 2>"$DERR" &
else
  "${DUMP[@]}" >/dev/null 2>"$DERR" &
fi
DUMP_PID=$!
sleep 2
# dumpcap keeps running under a ring buffer, so a live PID means it opened the device and the file.
if ! pgrep -f "dumpcap.*$CAP_PREFIX" >/dev/null 2>&1 && ! kill -0 "$DUMP_PID" 2>/dev/null; then
  fail "dumpcap failed to start: $(tr -s ' \n' ' ' < "$DERR" 2>/dev/null | tail -c 200)"
fi

# 3) Periodically read the NEWEST ring segment back and compute address-free aggregates. Reading
#    only the current segment bounds the cost (each segment is <= RINGSIZE KB), so this stays cheap
#    even on a long capture on the Pi.
newest_seg() { ls -1t "$OUTDIR/fancy-$IFACE-$TS"_*.pcapng 2>/dev/null | head -1; }

# The aggregator lives in its own file, not a heredoc on python's stdin: summarize pipes tshark's
# output INTO python, so python's stdin must be that pipe, and the program must come from a file
# (a `python3 - <<PY` heredoc would instead feed the program on stdin and leave tshark's output
# unread — silently zeroing every count).
PARSER="$OUTDIR/.tshark-summarize.py"
write_parser() {
  mkdir -p "$OUTDIR"
  cat >"$PARSER" <<'PY'
import os, sys, collections, json
seg = sys.argv[1]
protos = collections.Counter()
retx = dupack = reset = unreach = total = 0
for line in sys.stdin:
    total += 1
    p, rt, da, rst, icmp = (line.rstrip("\n").split("|") + ["", "", "", "", ""])[:5]
    if p:
        protos[p] += 1
    if rt:
        retx += 1
    if da:
        dupack += 1
    if rst == "1":
        reset += 1
    if icmp == "3":
        unreach += 1
seg_kb = round(os.path.getsize(seg) / 1024, 1) if os.path.exists(seg) else None
print(json.dumps({
    "segment_packets": total,
    "segment_kb": seg_kb,
    "findings": {"tcp_retransmit": retx, "tcp_dup_ack": dupack,
                 "tcp_reset": reset, "icmp_unreachable": unreach},
    "protocols": [{"name": n, "packets": c} for n, c in protos.most_common(8)],
}))
PY
}

summarize() {  # -> JSON fragment on stdout, address-free
  local seg; seg="$(newest_seg)"
  [ -n "$seg" ] && [ -r "$seg" ] || { echo ""; return; }
  [ -f "$PARSER" ] || write_parser
  # One pass over the segment; aggregate in python. Fields chosen for the dropout hunt: protocol
  # mix, TCP retransmits / dup-acks / resets, ICMP unreachables. No endpoint fields are requested.
  tshark -r "$seg" -T fields -E separator='|' \
    -e _ws.col.Protocol \
    -e tcp.analysis.retransmission \
    -e tcp.analysis.duplicate_ack \
    -e tcp.flags.reset \
    -e icmp.type 2>/dev/null \
  | python3 "$PARSER" "$seg"
}

# Stop dumpcap, let the newest segment finalize, then emit a FINAL summary — so a finished or
# cancelled capture reports its true totals instead of leaving the last mid-write (often zero on a
# quiet link) numbers on screen.
finish() {  # finish <stage> <message>
  cleanup
  sleep 1
  emit "$1" "$2" "$(summarize)"
  exit 0
}

START="$(date +%s)"
while kill -0 "$DUMP_PID" 2>/dev/null; do
  cancelled && finish "cancelled" "cancelled during capture"
  if [ "$DURATION" -gt 0 ] && [ $(( $(date +%s) - START )) -ge "$DURATION" ]; then
    finish "done" "capture complete (${DURATION}s)"
  fi
  FRAG="$(summarize)"
  elapsed=$(( $(date +%s) - START ))
  emit "capturing" "capturing on $IFACE (${elapsed}s)" "$FRAG"
  sleep "$STATS_INTERVAL"
done

finish "done" "capture stopped (dumpcap exited)"
