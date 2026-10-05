#!/bin/sh
# first-packet-alert — one-shot alert when meshtasticd hears its first LoRa packet
#
# meshtasticd logs its LocalStats counters every ~15 min:
#   num_packets_tx=1, num_packets_rx=0, num_packets_rx_bad=0
# This follows the journal and fires on the first line with rx > 0 (a decoded packet) or
# rx_bad > 0 (LoRa heard but not decoded): desktop notification + a line in the log file below,
# then disables its own service. Counters reset when meshtasticd restarts; that's fine, any
# nonzero value counts.
#
# Install:
#   install -m 755 first-packet-alert.sh ~/.local/bin/meshtastic-first-packet-alert
#   install -m 644 first-packet-alert.service ~/.config/systemd/user/
#   systemctl --user daemon-reload && systemctl --user enable --now first-packet-alert
# Verify:
#   systemctl --user status first-packet-alert       # active (running)
#   printf 'num_packets_tx=1, num_packets_rx=2, num_packets_rx_bad=0\n' \
#     | ALERT_DRY_RUN=1 ~/.local/bin/meshtastic-first-packet-alert --stdin   # prints the alert
# Roll back:
#   systemctl --user disable --now first-packet-alert
#   rm ~/.config/systemd/user/first-packet-alert.service ~/.local/bin/meshtastic-first-packet-alert

LOG="${ALERT_LOG:-$HOME/meshtastic-first-packet.log}"

alert() {
    title="$1"; body="$2"
    if [ -n "$ALERT_DRY_RUN" ]; then
        echo "ALERT: $title — $body"
        return
    fi
    printf '%s  %s — %s\n' "$(date -u +%FT%TZ)" "$title" "$body" >> "$LOG"
    notify-send -u critical -a Meshtastic -i network-wireless "$title" "$body" 2>/dev/null || true
    systemctl --user disable first-packet-alert.service 2>/dev/null || true
}

if [ "$1" = "--stdin" ]; then
    src="cat"
else
    src="journalctl -u meshtasticd -f -n 0 -o cat"
fi

$src | while IFS= read -r line; do
    case "$line" in
        *num_packets_rx=*) ;;
        *) continue ;;
    esac
    rx=$(printf '%s' "$line" | sed -n 's/.*num_packets_rx=\([0-9]*\).*/\1/p')
    bad=$(printf '%s' "$line" | sed -n 's/.*num_packets_rx_bad=\([0-9]*\).*/\1/p')
    if [ "${rx:-0}" -gt 0 ]; then
        alert "Meshtastic: first packet received" \
            "$rx packet(s) decoded since meshtasticd started. Run: meshtastic --host localhost --nodes (stop the webdash bridge first)."
        exit 0
    elif [ "${bad:-0}" -gt 0 ]; then
        alert "Meshtastic: LoRa heard, not decoded" \
            "$bad bad packet(s): something is transmitting in range but too weak or garbled to decode."
        exit 0
    fi
done
