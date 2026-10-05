# ClockworkPi uConsole Build

[![License: CC BY 4.0 | MIT](https://img.shields.io/badge/license-CC--BY--4.0%20%7C%20MIT-blue.svg)](https://github.com/w1cked5mile/clockworkpi-uconsole-public/blob/main/LICENSE)
![Platform: ClockworkPi uConsole](https://img.shields.io/badge/platform-ClockworkPi%20uConsole-5a3e85)
![Compute: Raspberry Pi CM4](https://img.shields.io/badge/compute-Raspberry%20Pi%20CM4-c51a4a)
![Focus: SDR · LoRa · GNSS](https://img.shields.io/badge/focus-SDR%20%C2%B7%20LoRa%20%C2%B7%20GNSS-informational)
[![Last commit](https://img.shields.io/github/last-commit/w1cked5mile/clockworkpi-uconsole-public)](https://github.com/w1cked5mile/clockworkpi-uconsole-public/commits/main)

Documentation, software, drivers, firmware, and configuration for a ClockworkPi uConsole build.

## Hardware summary

| Component | Notes |
|---|---|
| ClockworkPi Mainboard v3.14 | Core uConsole mainboard (95×77 mm), modular core-module interface |
| Raspberry Pi CM4 Lite 8GB | Compute module (boots from microSD or NVMe; no onboard eMMC) |
| HackerGadgets NVMe / Adapter Upgrade Kit | CM4/CM5 adapter + NVMe battery board + RJ45/USB 3.0 board |
| OpenSourceSDRLab / HackerGadgets AIO V2 | RTL-SDR (RTL2832U+R860), LoRa (SX1262), GPS/GNSS, RTC, USB hub, RJ45 |

> On CM4, adapter/AIO USB ports run at USB 2.0; USB 3.0 requires CM5.

## Quick start

This repo is documentation-first: you build the **hardware** by following the runbooks, then run
the **webdash** and **learning tracks** on the device. Clone it, then:

```bash
git clone https://github.com/w1cked5mile/clockworkpi-uconsole-public.git
cd clockworkpi-uconsole-public
```

**1 — Build the device.** Source the parts from the [Bill of Materials](docs/bill-of-materials.md),
then work through [assembly](docs/runbooks/assembly.md) →
[imaging & first boot](docs/runbooks/imaging-and-first-boot.md) →
[software install](docs/runbooks/software-install.md) → [first RF checkout](docs/runbooks/first-rf-checkout.md).

**2 — Run the operator dashboard** (on the device, with Docker installed):

```bash
mkdir -p ~/.config/uconsole-webdash          # auth store; first run generates a password + TOTP
cd webdash && sg docker -c 'docker compose up -d --build'
```

Uvicorn binds `127.0.0.1` only; set up a login and expose it deliberately per
[`software/webdash.md`](software/webdash.md). Full panels need the real radios (AIO V2 / AC1200 /
GPS) and the `aiov2_ctl` host bridge attached.

**3 — Build the learning tracks:**

```bash
python3 webdash/host-helpers/learn-compile.py --check   # lint the curriculum
python3 webdash/host-helpers/learn-compile.py           # compile → ~/.local/share/uconsole-webdash/learn/
```

> Bring your own hardware, accounts, and secrets — no keys, PSKs, or order records are in this repo.
> Environment-specific values (tailnet host, GPU crack host, home paths) are placeholders you
> override via env vars. Read [Responsible use](#responsible-use) before any transmit or active test.

## Repository layout

| Path | Contents |
|---|---|
| [`docs/`](docs/) | Bill of materials, documentation reference index |
| [`hardware/`](hardware/) | Schematics, pinouts, expansion-card design files |
| [`firmware/`](firmware/) | Keyboard/expansion/board firmware and flashing notes |
| [`drivers/`](drivers/) | Kernel modules, device-tree overlays, driver notes |
| [`software/`](software/) | App setup: aiov2_ctl, Meshtastic, SDR++, tar1090, PyGPSClient, Kismet, gpsd, aircrack-ng, webdash |
| [`configs/`](configs/) | Staged boot/overlay, modprobe, systemd, gpsd, SDR++, Kismet, Meshtastic configs |
| [`webdash/`](webdash/) | Operator dashboard — Docker app aggregating aiov2_ctl/Kismet/gpsd/meshtasticd/tar1090 status |
| [`images/`](images/) | Build photos and diagrams |
| `presentation/` | Conference talk: deck source, CFP material, demo plan |
| [`.claude/skills/`](.claude/skills/README.md) | Repo-scoped Claude Code skill: build a documentation-first hardware repo |

## Documentation

**Reference**
- [Bill of Materials](docs/bill-of-materials.md) · [Accessories & buy list](docs/accessories.md)
- [Documentation Reference Index](docs/documentation-index.md) — manufacturer docs, GitHub repos, and community resources
- [Pinout & GPIO reference](docs/reference/pinout-gpio.md)
- [Power budget & battery runtime](docs/reference/power-budget.md)
- [Antennas & RF interconnect](docs/reference/antennas-and-rf-connectors.md)
- [webdash architecture & build plan](docs/reference/webdash-architecture.md)
- [webdash redesign and learning layer (proposed)](docs/reference/webdash-design.md)
- [Learning platform plan — the Chart Table (proposed)](docs/reference/learning-platform-plan.md)
- [GPU crack-offload host (Kali WSL tailnet node)](docs/reference/gpu-crack-offload-host.md)
- [Hardware spec sheets](hardware/specs/) · [Datasheet index](hardware/datasheets/README.md) · [Mechanical notes](hardware/mechanical.md)

**Checklists**
- [Inventory & inspection](docs/checklists/inventory-and-inspection.md)
- [Tools & consumables](docs/checklists/tools-and-consumables.md)
- [Module bring-up & tests](docs/checklists/module-bringup-tests.md)

**Runbooks**
- [Assembly](docs/runbooks/assembly.md)
- [Imaging & first boot](docs/runbooks/imaging-and-first-boot.md) → [NVMe boot](docs/runbooks/nvme-boot.md)
- [Software install](docs/runbooks/software-install.md) — per-app notes in [`software/`](software/README.md)
- [First RF checkout](docs/runbooks/first-rf-checkout.md)
- [WPA2 handshake capture & audit](docs/runbooks/wifi-wpa2-handshake-audit.md) — authorized targets only
- [Headless access](docs/runbooks/headless-access.md)
- [Backup & restore](docs/runbooks/backup-and-restore.md)

**Logs & records** (living)
- [Build log](docs/logs/build-log.md) · [Firmware versions](docs/logs/firmware-versions.md) · [Known issues](docs/logs/known-issues.md) · [Decisions](docs/logs/decisions.md)
- [Order & warranty](docs/records/order-and-warranty.md)

**Talk material** — presentation/: Marp deck, abstract and CFP notes, demo plan (DEF CON / BSides / ISSA variants).

See also [TODO.md](TODO.md), [CHANGELOG.md](CHANGELOG.md), and [CLAUDE.md](CLAUDE.md) (repo conventions: where things belong, verify markers, privacy and legal posture).

**Knowledge base** — RF exploration across disciplines, with reference indexes and a documenting structure (learned / configs / runbooks / findings):
- [knowledge/](knowledge/README.md) — start here
- [RF fundamentals](knowledge/rf-fundamentals/README.md) · [SDR](knowledge/sdr/README.md) · [Mesh networks](knowledge/mesh-networks/README.md) · [Wardriving](knowledge/wardriving/README.md) · [Aerospace](knowledge/aerospace/README.md) · [Communications](knowledge/communications/README.md) · [Ham radio](knowledge/ham-radio/README.md)

## License

Docs, knowledge base, curriculum and photos: [CC BY 4.0](LICENSES/CC-BY-4.0.txt). Code and
configs: [MIT](LICENSES/MIT.txt). Both require acknowledgement when reused. Third-party exclusions
are listed in [`LICENSE`](LICENSE).

## Responsible use

This platform is for **receiving, learning, and licensed transmitting**. Wardriving here means
**passive observation only**. Active Wi-Fi auditing (handshake capture/crack) is for **your own
equipment or targets you hold written authorization to test** — nothing else. Do not use this
material to intrude on networks outside that boundary, to decode protected or encrypted
communications, or to transmit without the licence your jurisdiction requires. You are responsible
for the laws that apply to you. See the responsible-use section in
[`knowledge/README.md`](knowledge/README.md).

## Key upstream references

- ClockworkPi uConsole: https://github.com/clockworkpi/uConsole
- HackerGadgets aiov2_ctl: https://github.com/hackergadgets/aiov2_ctl
- Raspberry Pi usbboot (rpiboot): https://github.com/raspberrypi/usbboot
- Community forum: https://forum.clockworkpi.com/c/uconsole/30

See [`docs/documentation-index.md`](docs/documentation-index.md) for the full index.
