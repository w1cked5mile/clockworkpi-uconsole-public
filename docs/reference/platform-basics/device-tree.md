# Device tree, overlays and config.txt

How the Pi learns which hardware is attached to its pins. Written 2026-09-25 (gap P3).
Reference: Raspberry Pi documentation on `config.txt` and device trees (linked in
[`../../../knowledge/README.md`](../../../knowledge/README.md) §Platform references).

## The idea

Unlike a PC, the Pi can't probe its pins to discover what's connected. The **device tree** is a
description of the hardware that the bootloader hands to the kernel. **Overlays** are patches to
it that switch on a bus or declare a chip. They're listed in `/boot/firmware/config.txt`.

## This build's lines

From [`../../../configs/boot/config-cm4.txt`](../../../configs/boot/config-cm4.txt):

| Line | Effect | Needed by |
|---|---|---|
| `dtparam=i2c_arm=on` | turns on the I²C bus on the header pins | the RTC |
| `dtoverlay=i2c-rtc,pcf85063a` | declares the PCF85063A clock chip on it → `/dev/rtc0` | RTC, time without network |
| `enable_uart=1` | turns on the header serial port → `/dev/serial0` | GPS |
| `dtparam=spi=on` | turns on SPI0 (not the LoRa bus) | nothing on this build; kept from the stock config |
| `dtoverlay=spi1-1cs` | turns on SPI1 with one chip-select line → `/dev/spidev1.0` | the SX1262 (`spi1-2cs`/`-3cs` would add unused chip selects) |

## The serial console

`cmdline.txt` can put a login console on the same serial port the GPS uses
(`console=serial0,115200`). Then the GPS sentences are swallowed. This build removes that entry
([`../../../configs/boot/cmdline-notes.md`](../../../configs/boot/cmdline-notes.md)).

## Checking, read-only

```bash
ls -l /dev/serial0 /dev/spidev1.0 /dev/rtc0
grep -v '^#' /boot/firmware/config.txt | grep -E 'dtoverlay|dtparam|enable_uart'
cat /proc/cmdline
```

Editing `config.txt` or `cmdline.txt` can stop the device booting — make a backup and follow the
repo's staged copies rather than editing by hand.
