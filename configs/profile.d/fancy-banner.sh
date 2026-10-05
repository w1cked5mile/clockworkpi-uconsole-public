#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# uConsole logon banner (fancy)
# Install: sudo cp configs/profile.d/fancy-banner.sh /etc/profile.d/fancy-banner.sh
#          sudo chmod 644 /etc/profile.d/fancy-banner.sh
#          sudo apt-get install -y figlet
# Verify:  open a new interactive login shell (re-login, or `bash -i -l`) — the banner prints;
#          or run `bash /etc/profile.d/fancy-banner.sh` directly to render it once.
# Rollback: sudo rm /etc/profile.d/fancy-banner.sh — login returns to the default with no banner
#          (nothing else sources this file; figlet can stay or be removed with `sudo apt-get remove figlet`).
# ──────────────────────────────────────────────────────────────────────────────

# Interactive shells only
[[ $- != *i* ]] && return

# ── ANSI colours ──────────────────────────────────────────────────────────────
R=$'\033[0m'        # reset
G=$'\033[0;32m'     # green
BG=$'\033[1;32m'    # bright green
Y=$'\033[1;33m'     # yellow
BR=$'\033[1;31m'    # bright red
BC=$'\033[1;36m'    # bright cyan
W=$'\033[1;37m'     # bright white
DIM=$'\033[2m'      # dim

SEP="${G}  ─────────────────────────────────────────────────────────────────────${R}"

clear

HOST_RAW=$(hostname)
HOST_LC=$(echo "$HOST_RAW" | tr '[:upper:]' '[:lower:]')
# fancy -> Fancy
TITLE=$(echo "$HOST_LC" | sed -E 's/(^|-)([a-z])/\1\U\2/g')

# ── Title ─────────────────────────────────────────────────────────────────────
echo -e "${BG}"
if command -v figlet >/dev/null 2>&1; then
    figlet -f slant "$TITLE"
else
    echo "    $TITLE"
fi
echo -e "${DIM}       [ uConsole · CM4 · SDR · LoRa · GNSS  |  operator: w1cked5mile ]${R}"
echo ""

# ── System info ───────────────────────────────────────────────────────────────
echo -e "${SEP}"
echo ""

MODEL=$(tr -d '\0' < /proc/device-tree/model 2>/dev/null)
KERNEL=$(uname -r)
UPTIME=$(uptime -p 2>/dev/null | sed 's/up //' || uptime | sed 's/.*up \([^,]*\).*/\1/')
LOAD=$(awk '{print $1"  "$2"  "$3}' /proc/loadavg)
MEM=$(free -h | awk '/^Mem:/{printf "%s / %s", $4, $2}')
TEMP=$(awk '{printf "%.1f°C", $1/1000}' /sys/class/thermal/thermal_zone0/temp 2>/dev/null)
IP_LAN=$(ip route get 1.1.1.1 2>/dev/null | awk '{print $7; exit}')
IP_VPN=$(ip addr show tailscale0 2>/dev/null | awk '/inet /{print $2}' | cut -d/ -f1)

printf "  ${W}%-12s${R}  ${BC}%s${R}\n"   "hostname"  "${HOST_RAW}"
[[ -n "$MODEL" ]] && printf "  ${W}%-12s${R}  ${G}%s${R}\n" "model" "${MODEL}"
printf "  ${W}%-12s${R}  ${G}%s${R}\n"    "kernel"    "${KERNEL}"
printf "  ${W}%-12s${R}  ${G}%s${R}\n"    "uptime"    "${UPTIME:-unknown}"
printf "  ${W}%-12s${R}  ${G}%s${R}\n"    "load"      "${LOAD}"
printf "  ${W}%-12s${R}  ${G}%s${R}\n"    "mem free"  "${MEM}"
[[ -n "$TEMP" ]]    && printf "  ${W}%-12s${R}  ${G}%s${R}\n"                      "soc temp" "${TEMP}"
[[ -n "$IP_LAN" ]]  && printf "  ${W}%-12s${R}  ${G}%s${R}\n"                      "lan"      "${IP_LAN}"
[[ -n "$IP_VPN" ]]  && printf "  ${W}%-12s${R}  ${Y}%s  ${DIM}(tailscale)${R}\n"   "vpn"      "${IP_VPN}"

echo ""

# ── Battery ───────────────────────────────────────────────────────────────────
BAT=$(upower -i "$(upower -e 2>/dev/null | grep -m1 -i battery)" 2>/dev/null \
      | awk -F: '/percentage/{gsub(/ /,"",$2); print $2}')
if [[ -n "$BAT" ]]; then
    printf "  ${W}%-12s${R}  ${G}%s${R}\n" "battery" "${BAT}"
    echo ""
fi

# ── AIO V2 roster ─────────────────────────────────────────────────────────────
echo -e "  ${W}AIO V2 ROSTER${R}"
echo -e "${SEP}"

live()  { printf "  ${BG}[LIVE]${R}  %-14s  %s\n"        "$1" "$2"; }
dead()  { printf "  ${DIM}[----]  %-14s  %s${R}\n"       "$1" "$2"; }

# RTL-SDR (RTL2832U + R860) — present on the USB bus?
if lsusb 2>/dev/null | grep -qiE '0bda:283[28]|RTL283'; then
    live "rtl-sdr" "RTL2832U · R860 · 24–1766 MHz"
else
    dead "rtl-sdr" "RTL2832U · R860 · 24–1766 MHz"
fi

# LoRa SX1262 — driven by meshtasticd over SPI, no character device to test
if systemctl is-active --quiet meshtasticd 2>/dev/null; then
    live "lora" "SX1262 · Meshtastic · US915"
else
    dead "lora" "SX1262 · Meshtastic · US915"
fi

# GNSS on the AIO UART
if [[ -e /dev/serial0 ]]; then
    live "gnss" "AIO GNSS · /dev/serial0"
else
    dead "gnss" "AIO GNSS · /dev/serial0"
fi

# Hardware RTC
if [[ -e /dev/rtc0 ]]; then
    live "rtc" "hardware clock · /dev/rtc0"
else
    dead "rtc" "hardware clock · /dev/rtc0"
fi

# uConsole MCU (keyboard + power controller)
if [[ -e /dev/ttyACM0 ]]; then
    live "uconsole mcu" "keyboard · power · /dev/ttyACM0"
else
    dead "uconsole mcu" "keyboard · power · /dev/ttyACM0"
fi

# Wi-Fi interfaces that are actually up
for IFACE in $(ls /sys/class/net 2>/dev/null | grep '^wlan'); do
    if [[ "$(cat /sys/class/net/$IFACE/operstate 2>/dev/null)" == "up" ]]; then
        SSID=$(iwgetid -r "$IFACE" 2>/dev/null)
        [[ -z "$SSID" ]] && SSID=$(nmcli -t -f DEVICE,CONNECTION dev 2>/dev/null                                    | awk -F: -v d="$IFACE" '$1==d{print $2}')
        live "$IFACE" "wi-fi${SSID:+ · $SSID}"
    else
        dead "$IFACE" "wi-fi · down"
    fi
done

echo ""

# ── Services ──────────────────────────────────────────────────────────────────
echo -e "  ${W}SERVICES${R}"
echo -e "${SEP}"

for SVC in meshtasticd tar1090 gpsd kismet tailscaled lighttpd; do
    if ! systemctl list-unit-files "${SVC}.service" &>/dev/null \
       || ! systemctl cat "${SVC}.service" &>/dev/null; then
        continue
    fi
    if systemctl is-active --quiet "$SVC" 2>/dev/null; then
        printf "  ${BG}[UP]${R}    %-20s  ${G}%s${R}\n" "$SVC" "active"
    else
        printf "  ${BR}[--]${R}    %-20s  ${DIM}%s${R}\n" "$SVC" "$(systemctl is-active "$SVC" 2>/dev/null)"
    fi
done

echo ""
echo -e "${SEP}"
echo -e "  ${DIM}uConsole field unit. Authorized use only.${R}"
echo ""
