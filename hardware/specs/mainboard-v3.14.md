# ClockworkPi Mainboard v3.14 — spec sheet

Compiled 2026-09-06 from the BOM and upstream repo contents. *Unverified* = confirm against the
board or the schematic PDF at inventory.

| Attribute | Value | Confidence |
|---|---|---|
| Dimensions | 95 × 77 mm | from BOM |
| Core module interface | DDR2-SODIMM style edge connector — accepts a core board (A06/R01) or a CM4/CM5 carrier via adapter | from BOM |
| Expansion interface | 52-pin extension module connector (mini-PCIe form) — carries the AIO V2 | from BOM |
| Display interface | 40-pin MIPI DSI | from BOM |
| GPIO expansion | 40-pin, 0.5 mm FPC | from BOM |
| USB | 3 × USB-A 2.0 | from BOM |
| Ethernet | **No jack on the mainboard.** The CM4's native `bcmgenet` Ethernet (PHY on the CM4 module) reaches the RJ45 on the AIO V2 through the AIO V2's ribbon, which plugs into the HackerGadgets Adapter Pro's port marked "CM5 USB 3.0" | Owner, 2026-09-25 — corrects this row's earlier "RJ45 jack on the mainboard". **Links at 1 Gbps full duplex, 2026-09-23**, once the Adapter Pro (#11953) gave the ribbon a port; the kit's adapter has none, which is why the 2026-09-20 attempt failed. See `docs/logs/known-issues.md` |
| Power in | USB-C (charge) | from BOM |
| Video out | micro-HDMI | from BOM |
| Audio | 3.5 mm jack + onboard stereo amplifier / speakers | from BOM |
| Storage | TF/microSD slot | from BOM |
| PMU | AXP-series PMIC — exposed as `axp20x-battery` / `axp22x-ac` in `/sys/class/power_supply/` | **confirmed on hardware** 2026-09-16: both paths present; `axp20x-battery/voltage_now` read 3886000 µV (3.886 V), consistent with the 1S decision in `decisions.md` |
| Display panel | uConsole 5" IPS, JD9365DA-H3 driver IC (datasheet published in the uConsole repo) | *unverified* panel resolution — confirm from the driver datasheet |
| Input controller (USB) | `idVendor=1eaf` (Leaflabs) `idProduct=0024`, `iManufacturer="ClockworkPI"` `iProduct="uConsole"`, `bcdDevice=2.00`, `iSerial="20230713"` | **confirmed on hardware** via `lsusb -v`, 2026-09-16 — `iSerial` reads as a firmware build-date string, not a per-unit serial (identical across boards on this firmware) |

## Schematics

- `clockwork_Mainboard_V3.14_Schematic.pdf` and `clockwork_Mainboard_V3.14_V5_Schematic.pdf`
- Gerbers: `PCB/CPI_3.14_Mainboard_V5_Gerber.7z`
- All at https://github.com/clockworkpi/uConsole

## Notes

- The PMIC is what `aiov2_ctl --power` and `--status` read for battery voltage/current and AC
  presence — no separate fuel gauge is involved.
- Display backlight is pulled up by GPIO9 at boot on the official image; a dark screen on a
  third-party image usually means that init is missing, not a dead panel.

## As received — first boot 2026-09-16

Kit assembled and CM4 seated; system booted successfully to a desktop session on the uConsole
shell/screen/keyboard. No unique per-board serial is exposed by the mainboard itself — the closest
identifier is the input controller's USB descriptor above. `/dev/nvme*` was **not present** at this
boot (booting from a 29.5 GB microSD instead, see
[`../../docs/checklists/inventory-and-inspection.md`](../../docs/checklists/inventory-and-inspection.md));
confirm whether the NVMe/adapter board is seated.
