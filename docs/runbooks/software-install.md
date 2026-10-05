# Software install runbook

Install the AIO V2 control client and companion apps. Do this after a configured first boot.

> Source: hackergadgets/aiov2_ctl — https://github.com/hackergadgets/aiov2_ctl (verify commands against the current README; they change).
> OS requirement: Debian / Raspberry Pi OS, Bookworm or Trixie.

## 1. aiov2_ctl (power/feature control)

```bash
sudo apt update
sudo apt install -y python3 python3-pyqt6 git
git clone https://github.com/hackergadgets/aiov2_ctl.git
cd aiov2_ctl
sudo python3 ./aiov2_ctl.py --install
```

Verify:

```bash
aiov2_ctl            # launches control (CLI/tray)
aiov2_ctl --status   # current rail states
```

Module power (all rails off by default **except SDR** — see the boot-default note below):

```bash
aiov2_ctl GPS  on|off
aiov2_ctl LORA on|off
aiov2_ctl SDR  on|off
aiov2_ctl USB  on|off
aiov2_ctl --boot-rail <FEATURE> on|off   # state applied at boot
aiov2_ctl --boot-rails-status            # what the boot service will apply
```

Power and diagnostics:

```bash
aiov2_ctl --power      # real-time power monitoring (mainboard PMIC)
aiov2_ctl --watch      # single-line live GPIO + power view
aiov2_ctl --measure    # measurement mode — use for the power-characterization tests
aiov2_ctl --sync-rtc   # write system time to the PCF85063A
```

> Upstream `BOOT_DEFAULTS` sets the SDR rail on at boot. On this build that is ~1.5 W of budget
> before anything is running — confirm with `aiov2_ctl --status` after a cold boot and turn it off
> with `aiov2_ctl --boot-rail SDR off` if nothing needs it. Full command surface and the files the
> installer writes: [`../../software/aiov2_ctl.md`](../../software/aiov2_ctl.md).

## 2. Companion apps

```bash
sudo aiov2_ctl --add-apps
```

Deploys:

| Package | Purpose |
|---|---|
| hackergadgets-uconsole-aio-board | Core GPIO / power-rail integration |
| meshtastic-mui | LoRa / Meshtastic GUI (SX1262) |
| sdrpp-brown | Preconfigured SDR++ for the AIO RTL-SDR |
| tar1090 | ADS-B aircraft tracking |
| pygpsclient | GPS monitoring / diagnostics GUI |

> **On this image `--add-apps` fails — none of these packages are published anywhere reachable**
> ([`../logs/known-issues.md`](../logs/known-issues.md)). What replaced each one on this build:
>
> | Bundle package | Substitute | Notes |
> |---|---|---|
> | hackergadgets-uconsole-aio-board | `aiov2_ctl` (section 1) | covers rail control |
> | meshtastic-mui | `meshtasticd` + `meshtastic` CLI + `gtk-meshtastic-client` | [`../../software/meshtastic.md`](../../software/meshtastic.md) |
> | sdrpp-brown | plain `sdrpp` (provenance unknown) + `rtl-sdr`, `gqrx-sdr` | [`../../software/sdr-stack.md`](../../software/sdr-stack.md) |
> | tar1090 | `readsb` + `tar1090` from wiedehopf's installers | [`../../software/adsb-tar1090.md`](../../software/adsb-tar1090.md) |
> | pygpsclient | pip venv + `gpsd-nmea-relay` (TCP, from gpsd) | [`../../software/gps.md`](../../software/gps.md#pygpsclient) |

## 3. Apply the staged configuration

Configs written before the hardware arrived, in [`../../configs/`](../../configs/README.md):

```bash
# device-tree overlays for RTC / GPS / LoRa, then reboot
sudo tee -a /boot/firmware/config.txt < ../../configs/boot/config-cm4.txt
# remove console=serial0,115200 so GPS keeps the UART — see configs/boot/cmdline-notes.md

# stop the kernel DVB driver claiming the RTL2832U
sudo cp ../../configs/modprobe.d/blacklist-rtl-dvb.conf /etc/modprobe.d/

# free SPI1 for LoRa if the printer service exists on this image
sudo systemctl mask devterm-printer 2>/dev/null || true

# gpsd against the AIO GNSS UART
sudo cp ../../configs/gpsd/gpsd.default /etc/default/gpsd && sudo systemctl enable --now gpsd
```

Per-app notes: [`../../software/`](../../software/README.md).

## 4. Kismet (passive Wi-Fi/BT survey)

Not part of `aiov2_ctl --add-apps`; installed from Kismet's own apt repo.

```bash
wget -O - https://www.kismetwireless.net/repos/kismet-release.gpg.key --quiet \
  | gpg --dearmor | sudo tee /usr/share/keyrings/kismet-archive-keyring.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/kismet-archive-keyring.gpg] https://www.kismetwireless.net/repos/apt/release/trixie trixie main' \
  | sudo tee /etc/apt/sources.list.d/kismet.list
sudo apt update
echo "kismet-common kismet-common/install-setuid boolean true" | sudo debconf-set-selections
sudo DEBIAN_FRONTEND=noninteractive apt install -y kismet
sudo usermod -aG kismet "$USER"   # log out/in to pick up the new group
sudo cp ../../configs/kismet/kismet_site.conf /etc/kismet/kismet_site.conf
mkdir -p ~/kismet-logs
```

> `kismet-capture-linux-bluetooth`'s postinst asks whether to install suid-root helpers —
> preseeding as above avoids it hanging a non-interactive install. Full command surface, what
> gets written, and the current capture-source interface (a stand-in USB adapter, not the AC1200
> yet): [`../../software/kismet.md`](../../software/kismet.md).

Verify:

```bash
sg kismet -c 'kismet --no-ncurses-wrapper'   # or plain `kismet` after re-login
# http://localhost:2501/ — set the admin username/password on first run
```

## 5. Optional extras

- [ ] Meshtastic firmware/region config (set the correct LoRa region for 860–960 MHz use; respect local regulations).
- [ ] `rtl-sdr` tools (`rtl_test`, `rtl_fm`) if not pulled in by sdrpp-brown: `sudo apt install -y rtl-sdr`.
- [ ] gpsd if you want a system GPS daemon: `sudo apt install -y gpsd gpsd-clients`.

## Next

- Verify each module: [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md).
- First light for each radio: [`first-rf-checkout.md`](first-rf-checkout.md).
- Baseline the working system: [`backup-and-restore.md`](backup-and-restore.md).
