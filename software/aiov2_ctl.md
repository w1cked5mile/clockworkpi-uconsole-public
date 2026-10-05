# aiov2_ctl — AIO V2 rail control

Upstream: https://github.com/hackergadgets/aiov2_ctl · CLI surface confirmed against `main`, 2026-09-06.

## Install

```bash
sudo apt update
sudo apt install -y python3 python3-pyqt6 git
git clone https://github.com/hackergadgets/aiov2_ctl.git
cd aiov2_ctl
sudo python3 ./aiov2_ctl.py --install
```

## Full command surface

| Command | Purpose |
|---|---|
| `aiov2_ctl` | Show current GPIO/rail state |
| `aiov2_ctl --status` | Detailed board status including PMIC power data |
| `aiov2_ctl <GPS\|LORA\|SDR\|USB> on\|off` | Toggle a rail |
| `aiov2_ctl --power` | Real-time power monitoring |
| `aiov2_ctl --watch` | Single-line live GPIO + power view |
| `aiov2_ctl --measure` | Measurement mode (use during the power-characterization tests) |
| `aiov2_ctl --gui` | Qt tray/GUI |
| `aiov2_ctl --boot-rail <FEATURE> on\|off` | Persist a rail's state across boots |
| `aiov2_ctl --boot-rails-status` | Show what the boot service will apply |
| `aiov2_ctl --mesh-on-boot` / `--mesh-off-boot` | Meshtastic autostart at boot |
| `aiov2_ctl --sync-rtc` | Write system time to the PCF85063A |
| `aiov2_ctl --add-apps` / `--remove-apps` | Install/remove companion packages |
| `aiov2_ctl --autostart` / `--no-autostart` | Desktop autostart entry |
| `aiov2_ctl --update` / `--check-update` | Self-update |

## What it writes

| Path | Contents |
|---|---|
| `/usr/local/bin/aiov2_ctl` | executable |
| `/usr/local/share/aiov2_ctl/{assets,install.json,config.json}` | assets + system config |
| `/etc/systemd/system/aiov2-rails-boot.service` | applies boot-rail state |
| `/etc/bash_completion.d/aiov2_ctl` | completion |
| `/usr/share/applications/aiov2_ctl.desktop`, `~/.config/autostart/aiov2_ctl.desktop` | launcher/autostart |
| `~/.config/aiov2_ctl/config.json` | per-user config |

## Rail map (upstream `GPIO_MAP`, re-read 2026-09-06; boot default corrected 2026-09-16)

| Feature | BCM | Boot default | Interface |
|---|---|---|---|
| GPS | 27 | off | UART `/dev/serial0` (= `ttyS0` on this build, not `ttyAMA0`) |
| LORA | 16 | off | SPI1 |
| SDR | 7 | off | USB |
| USB | 23 | off | USB |

> The boot default column previously said SDR was **on**, citing `BOOT_DEFAULTS` in `aiov2_ctl.py`.
> That dict is only a state-inference fallback for `--status`; the boot service's actual apply path
> defaults every rail to off with no saved config. See [`../docs/logs/decisions.md`](../docs/logs/decisions.md)
> — one empirical post-reboot check is still outstanding.

Power state comes from the mainboard PMIC via `/sys/class/power_supply/axp20x-battery` and
`axp22x-ac` — not a separate fuel gauge.

## Manual fallback (tool not installed / debugging)

```bash
pinctrl 7 op        # set GPIO as output
pinctrl 7 dh        # drive high  (rail on)
pinctrl 7 dl        # drive low   (rail off)
pinctrl get 7       # read back
```

## First-run sequence on new hardware

```bash
aiov2_ctl --status              # cold-boot rail state — record it (bring-up test 0)
aiov2_ctl --boot-rails-status
aiov2_ctl --boot-rail SDR off   # if SDR is on at boot and nothing needs it
aiov2_ctl --sync-rtc            # after NTP has set system time
```
