# configs/

Dotfiles, boot configs, systemd units, and reproducible system configuration for this build.
Everything here was staged before the hardware arrived and applied during bring-up; each file's
header says how to apply it, verify it and roll it back.

| Path | Purpose | Apply to |
|---|---|---|
| [`boot/config-cm4.txt`](boot/config-cm4.txt) | Device-tree overlays for RTC / GPS / LoRa (CM4) | append to `/boot/firmware/config.txt` |
| [`boot/cmdline-notes.md`](boot/cmdline-notes.md) | Remove the serial console so GPS keeps the UART | edit `/boot/firmware/cmdline.txt` |
| [`modprobe.d/blacklist-rtl-dvb.conf`](modprobe.d/blacklist-rtl-dvb.conf) | Stop the DVB-T driver claiming the RTL2832U | `/etc/modprobe.d/` |
| [`systemd/`](systemd/) | SPI1 conflict fix, rail-boot service notes | `/etc/systemd/system/` |
| [`gpsd/gpsd.default`](gpsd/gpsd.default) | Point gpsd at the AIO GNSS UART | `/etc/default/gpsd` |
| [`gpsd/gpsd-nmea-relay.py`](gpsd/gpsd-nmea-relay.py) | Serve gpsd's NMEA on TCP 127.0.0.1:50010 for PyGPSClient | `~/.local/bin/gpsd-nmea-relay` |
| [`chrony/chrony-gps.conf`](chrony/chrony-gps.conf) | GPS disciplines the system clock offline (chrony reads gpsd SHM); replaces systemd-timesyncd. Deployed 2026-10-02 | `/etc/chrony/conf.d/gps.conf` |
| [`sdrpp/README.md`](sdrpp/README.md) | Band/gain starting points for SDR++ | app config |
| [`kismet/kismet_site.conf`](kismet/kismet_site.conf) | Passive Wi-Fi survey with GPS tagging | `/etc/kismet/` |
| [`networkmanager/wifi-onboard-only.conf`](networkmanager/wifi-onboard-only.conf) | NetworkManager manages only the onboard radio (`brcmfmac`, `wlan0`); every other Wi-Fi adapter is left unmanaged for survey work, so it never joins networks or probes. Deployed 2026-09-25 | `/etc/NetworkManager/conf.d/` (must sort after `wgpia.conf`), then `sudo nmcli general reload` |
| [`meshtastic/us915.yaml`](meshtastic/us915.yaml) | Meshtastic region/channel baseline | `meshtastic --configure` |
| [`meshtastic/first-packet-alert.sh`](meshtastic/first-packet-alert.sh) + [`.service`](meshtastic/first-packet-alert.service) | One-shot desktop alert on the first LoRa packet heard | `~/.local/bin/`, `~/.config/systemd/user/` |
| [`profile.d/fancy-banner.sh`](profile.d/fancy-banner.sh) | Logon banner: system info, AIO V2 roster, service status | `/etc/profile.d/` (mode 644) |
| [`udev/99-kismet-*.rules`](udev/) | Fixed Kismet nRF/KW41Z sniffer rules (`$$` escaping, missing comma) | `/etc/udev/rules.d/` (mode 644), then `udevadm control --reload` |

Order of application after first boot: boot config + cmdline → reboot → modprobe blacklist →
systemd → per-app configs.
