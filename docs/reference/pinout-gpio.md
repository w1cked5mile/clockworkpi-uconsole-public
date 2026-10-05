# Pinout & GPIO reference

Working reference for the expansion interface and the GPIOs the AIO V2 uses.

## Sources to confirm against

- ClockworkPi v3.14 mainboard: https://www.clockworkpi.com/product-page/clockworkpi-v3-14 (open hardware schematics)
- uConsole wiki (schematics): https://github.com/clockworkpi/uConsole/wiki
- aiov2_ctl (GPIO usage in source): https://github.com/hackergadgets/aiov2_ctl
- Raspberry Pi CM4 datasheet: https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf

## Mainboard expansion interfaces (v3.14)

- 52-pin extension module interface (mini-PCIe connector) — carries the AIO/adapter signals.
- 40-pin GPIO expansion (0.5 mm FPC).
- 40-pin MIPI display interface.

## AIO V2 power-rail GPIOs (per aiov2_ctl)

Sourced from `GPIO_MAP` / `BOOT_DEFAULTS` in [`aiov2_ctl.py`](https://github.com/hackergadgets/aiov2_ctl/blob/main/aiov2_ctl.py), commit `c21ca74` (2026-03-03). **Re-check against the installed copy** — pins are per-firmware, not per-hardware, and could change between releases.

| Feature | Control | BCM GPIO | Default at boot | Interface |
|---|---|---|---|---|
| GPS | `aiov2_ctl GPS on/off` | 27 | off | serial (`/dev/serial0`, = `ttyS0` on this build) |
| LoRa | `aiov2_ctl LORA on/off` | 16 | off | SPI |
| SDR | `aiov2_ctl SDR on/off` | 7 | off | USB |
| USB (internal) | `aiov2_ctl USB on/off` | 23 | off | USB |

> **Corrected 2026-09-16** — an earlier reading of this table cited `BOOT_DEFAULTS = {7: True, ...}`
> in `aiov2_ctl.py` as the boot-applied default. That dict is only a state-inference fallback for
> `--status` reporting; the actual boot service defaults every rail to off absent a saved config,
> and this build has no saved config. **Settled 2026-09-16**: a post-reboot `aiov2_ctl --status`
> confirmed all four rails off after a cold boot. See [`../logs/decisions.md`](../logs/decisions.md).

> **Corrected 2026-09-16** — GPS was documented as `/dev/ttyAMA0`, the vendor guide's assumed
> device name. On this build GPIO14/15 gets the mini-UART (`ttyS0`) because the CM4's onboard
> Bluetooth holds the full PL011 (it registers as `ttyAMA1`, not `ttyAMA0` — that node doesn't
> exist here). NMEA sentences were confirmed streaming on `/dev/serial0` (the stable symlink to
> whichever tty is actually the header UART) after `aiov2_ctl GPS on`. Use `/dev/serial0` in
> configs and commands rather than hardcoding a tty name. See
> [`../logs/decisions.md`](../logs/decisions.md).

## Manual rail control (no `aiov2_ctl` installed)

Enable/disable a rail directly with `pinctrl`:

```
pinctrl <GPIO> op        # set as output
pinctrl <GPIO> dh        # drive high (on)
pinctrl <GPIO> dl        # drive low (off)
```

## LoRa (SX1262) pin map

Beyond the GPO enable line (GPIO 16), the SX1262 module itself uses:

| Signal | BCM GPIO |
|---|---|
| IRQ (DIO1) | 26 |
| Busy | 24 |
| Reset | 25 |

**Conflict:** SPI1 is also used by the DevTerm printer service on Rex's Bookworm image — stop `devterm-printer` before using LoRa.

## Chipset quick reference

| Function | Chip | Notes |
|---|---|---|
| RTL-SDR | RTL2832U + R860 | 100 kHz–1.74 GHz, TCXO, 5V bias tee |
| LoRa | SX1262 | 860–960 MHz, 22 dBm, TCXO |
| RTC | PCF85063A | CR1220 backup; I²C |
| GPS | multi-GNSS (GPS/BDS/GNSS) | active or passive antenna |

## Device-tree overlays / `config.txt` (per HackerGadgets setup guide)

Confirmed handled via `config.txt`, not the control script — differs by compute module:

| Function | CM4 | CM5 |
|---|---|---|
| RTC | `dtparam=i2c_arm=on`<br>`dtoverlay=i2c-rtc,pcf85063a` | `dtparam=rtc=off`<br>`dtoverlay=i2c-rtc,pcf85063a,i2c_csi_dsi0` |
| GPS (serial) | `enable_uart=1` | `dtparam=uart0` |
| LoRa (SPI1) | `dtparam=spi=on`<br>`dtoverlay=spi1-1cs` | `dtoverlay=spi1-1cs` |

**CM4 GPS gotcha:** remove `console=serial0,115200` from `cmdline.txt`, or GPS won't work continuously (console grabs the UART).

## Software install

The vendor's quick path, `sudo apt install hackergadgets-uconsole-aio-board`, **does not work on this image**: the package isn't published anywhere reachable (confirmed 2026-09-16; see [`known-issues.md`](../logs/known-issues.md)). This build installs the pieces one at a time instead — see [`../runbooks/software-install.md`](../runbooks/software-install.md).

## Notes

- Boot-rail defaults can be changed with `aiov2_ctl --boot-rail <FEATURE> on`.
- **CM4 column verified on this device 2026-09-23:** `/boot/firmware/config.txt` has `enable_uart=1`, `dtparam=spi=on`, `dtoverlay=spi1-1cs`, `dtparam=i2c_arm=on` and `dtoverlay=i2c-rtc,pcf85063a`, and `console=serial0` is absent from `cmdline.txt`. RTC, GPS and LoRa all work (checklists 3.2, 3.8–3.10). The CM5 column is still from the vendor guide and forum reports, *unverified*.
