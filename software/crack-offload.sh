#!/usr/bin/env bash
# Offload a captured WPA/WPA2 handshake from Fancy to a remote GPU host for cracking.
# Fancy captures; a bigger machine cracks. AUTHORIZED-AUDIT USE ONLY: your own capture,
# your own network or a documented engagement. See:
#   docs/runbooks/wifi-wpa2-handshake-audit.md  (section 5b, the manual version)
#   docs/reference/gpu-crack-offload-host.md     (how the remote Kali/WSL node is set up)
#
# Usage:
#   CRACK_HOST=gpu-host-wsl ./crack-offload.sh ~/labs/wpa/handshake-01.cap
#
# Optional env:
#   SSH_PORT     (default 22)
#   WORDLIST     remote path (default /usr/share/wordlists/rockyou.txt; if only a .gz exists it is
#                expanded to ~/<name> on the remote automatically)
#   HASHCAT_OPTS extra hashcat flags (default "-O -w 3"; -O = optimized kernel, big WPA speedup;
#                bump to -w 4 for max throughput on a dedicated host)
set -euo pipefail

CRACK_HOST="${CRACK_HOST:?set CRACK_HOST to your GPU host ssh target, e.g. gpu-host-wsl}"
SSH_PORT="${SSH_PORT:-22}"
WORDLIST="${WORDLIST:-/usr/share/wordlists/rockyou.txt}"
HASHCAT_OPTS="${HASHCAT_OPTS:--O -w 3}"
CAP="${1:-}"

[ -n "$CAP" ] || { echo "usage: CRACK_HOST=<target> $0 <capture.cap>" >&2; exit 2; }
[ -r "$CAP" ] || { echo "no readable capture: $CAP (root-owned? chown it to yourself first)" >&2; exit 2; }

SSH=(ssh -p "$SSH_PORT" -o BatchMode=yes -o ConnectTimeout=25 -o ServerAliveInterval=10 "$CRACK_HOST")
base="$(basename "$CAP")"; stem="${base%.*}"

echo "[1/4] reachable? ssh $CRACK_HOST:$SSH_PORT"
"${SSH[@]}" 'echo ok' >/dev/null 2>&1 \
  || { echo "  FAIL: cannot SSH (host/WSL up? tailscaled running? ssh ACL set to accept?)" >&2; exit 1; }

echo "[2/4] remote tools present?"
"${SSH[@]}" 'command -v hcxpcapngtool hashcat >/dev/null' \
  || { echo "  FAIL: remote needs hcxtools + hashcat (Kali: sudo apt install -y hcxtools hashcat)." >&2; exit 1; }

echo "[3/4] copying $base -> $CRACK_HOST:~/wpa-offload/"
"${SSH[@]}" 'mkdir -p "$HOME/wpa-offload"'
scp -P "$SSH_PORT" -q "$CAP" "$CRACK_HOST:wpa-offload/$base"

echo "[4/4] resolve wordlist, convert, crack (hashcat -m 22000 $HASHCAT_OPTS). Ctrl-C is safe; hashcat resumes via its potfile."
# Quoted heredoc = literal remote script; values come in as positional args ($HASHCAT_OPTS is
# passed UNQUOTED so its flags become separate args, captured as "$@" after the first three).
"${SSH[@]}" bash -s -- "$base" "$stem" "$WORDLIST" $HASHCAT_OPTS <<'REMOTE'
set -e
base="$1"; stem="$2"; WORDLIST="$3"; shift 3   # "$@" now holds the hashcat opts
cd "$HOME/wpa-offload"

WL="$WORDLIST"
if [ ! -r "$WL" ] && [ -r "$WORDLIST.gz" ]; then
  WL="$HOME/$(basename "$WORDLIST")"
  [ -r "$WL" ] || zcat "$WORDLIST.gz" > "$WL"
fi
[ -r "$WL" ] || { echo "  FAIL: no wordlist at $WORDLIST (or .gz) on the remote"; exit 4; }
echo "  wordlist: $WL"

echo "  device(s) hashcat will use:"
hashcat -I 2>/dev/null | grep -E 'Backend Device|Name' | sed 's/^/    /' || true

hcxpcapngtool -o "$stem.hc22000" "$base" >/dev/null 2>&1
[ -s "$stem.hc22000" ] || { echo "  no usable handshake/PMKID in the capture"; exit 3; }

hashcat -m 22000 "$@" --status --status-timer=20 "$stem.hc22000" "$WL" || true
echo "=== result (BSSID:STATION:ESSID:PSK if cracked; blank = not in wordlist) ==="
hashcat -m 22000 --show "$stem.hc22000" "$WL" 2>/dev/null || echo "  (nothing recovered - passphrase not in the wordlist)"
REMOTE

echo "done. Remote copy stays in ~/wpa-offload on $CRACK_HOST - delete it when finished."
