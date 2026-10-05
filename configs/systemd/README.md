# systemd units and overrides

## 1. SPI1 conflict — `devterm-printer`

On some ClockworkPi/DevTerm-derived Bookworm images a `devterm-printer` service holds **SPI1**,
which is the bus the AIO V2's SX1262 uses. Symptom: LoRa silent, or SPI errors from Meshtastic.

```bash
systemctl status devterm-printer 2>/dev/null      # is it even present?
sudo systemctl disable --now devterm-printer
sudo systemctl mask devterm-printer               # keep it from coming back on upgrade
ls /dev/spidev1.*                                 # spidev1.0 should exist
```

The uConsole has no printer; masking it costs nothing on this build.

## 2. Serial console on the GPS UART

If GPS output is intermittent after removing `console=serial0,115200` from `cmdline.txt`, a getty
may still be bound. On this build the GPS UART is `ttyS0` (mini-UART), not `ttyAMA0` -- onboard
Bluetooth holds the PL011 as `ttyAMA1` -- confirm with `ls -l /dev/serial0` before assuming the name:

```bash
sudo systemctl disable --now serial-getty@ttyS0.service
```

## 3. `aiov2-rails-boot.service`

`aiov2_ctl --install` writes `/etc/systemd/system/aiov2-rails-boot.service`, which applies the
saved boot-rail state. Do not hand-edit it; change state through the tool so the stored config
and the unit stay consistent:

```bash
aiov2_ctl --boot-rails-status
aiov2_ctl --boot-rail SDR off
aiov2_ctl --boot-rail GPS on
systemctl status aiov2-rails-boot
```

Config it reads: `/usr/local/share/aiov2_ctl/config.json` (system) and
`~/.config/aiov2_ctl/config.json` (user).

## 4. Services worth enabling explicitly

| Service | Why | Command |
|---|---|---|
| `ssh` | headless access | `sudo systemctl enable --now ssh` |
| `tailscaled` | remote access off-LAN | `sudo tailscale up` |
| `gpsd` | shared GPS for Kismet/PyGPSClient | `sudo systemctl enable --now gpsd` |
| `tar1090` / decoder | ADS-B, installed by `--add-apps` | check unit name after install |

Record anything you enable in [`../../docs/logs/build-log.md`](../../docs/logs/build-log.md).
