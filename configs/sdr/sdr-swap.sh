#!/bin/bash
# sdr-swap.sh — toggle the AIO V2's single RTL-SDR between ADS-B tracking (readsb)
# and freed-for-other-use (rtl_fm, gqrx, sdrpp, etc.). Only one can use the dongle
# at a time — it's a single-tuner device, not just a software lock.
#
# Usage:
#   sudo bash sdr-swap.sh            # toggle current state
#   sudo bash sdr-swap.sh adsb       # force ADS-B tracking on
#   sudo bash sdr-swap.sh free       # force SDR freed (stop readsb)
#   sudo bash sdr-swap.sh status     # just report current state, change nothing
#
# Install: copy onto the device and chmod +x, e.g. `cp sdr-swap.sh ~/sdr-swap.sh`, or drop it on
#   PATH (`/usr/local/bin/sdr-swap`) to drop the `bash` prefix. No sudo needed if the scoped
#   sudoers rule in ../../software/adsb-tar1090.md is installed.
# Verify: `sdr-swap.sh status` reports the current mode; `systemctl status readsb` should match.
# Roll back: nothing persistent to undo — it only starts/stops the readsb service. As of 2026-10-03
#   readsb is systemctl-DISABLED (ADS-B is a chosen application, not an auto-start — see
#   ../../software/adsb-tar1090.md), so it does NOT come back on reboot; `adsb` here starts it for
#   this session only. This is the CLI equivalent of the dashboard's Start/Stop ADS-B control.

set -e

mode="${1:-toggle}"

is_active() {
  systemctl is-active --quiet readsb
}

to_adsb() {
  systemctl start readsb
  ip=$(hostname -I | awk '{print $1}')
  echo "readsb started — RTL-SDR now tracking ADS-B."
  echo "Map: http://${ip}/tar1090"
}

to_free() {
  systemctl stop readsb
  echo "readsb stopped — RTL-SDR free for rtl_fm / gqrx / sdrpp / etc."
}

case "$mode" in
  status)
    if is_active; then echo "ADS-B tracking (readsb active)"; else echo "SDR free (readsb stopped)"; fi
    ;;
  adsb|on)
    to_adsb
    ;;
  free|off)
    to_free
    ;;
  toggle|"")
    if is_active; then to_free; else to_adsb; fi
    ;;
  *)
    echo "Usage: $0 [toggle|adsb|free|status]" >&2
    exit 1
    ;;
esac
