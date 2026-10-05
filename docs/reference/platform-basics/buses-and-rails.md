# Buses, rails and who owns what

How the AIO V2's radios connect to the CM4, what a "rail" is, and why only one program can use
each device at a time. Written 2026-09-24 (gap P4). Pin facts come from
[`../pinout-gpio.md`](../pinout-gpio.md) and [`../../../software/aiov2_ctl.md`](../../../software/aiov2_ctl.md).

## Four ways to talk to a chip

| Bus | Wires | Speed | Addressing | Good for |
|---|---|---|---|---|
| UART (serial) | TX, RX | slow (the GPS runs at 9600 baud) | none — one device per port | streams of text, like NMEA |
| SPI | clock, MOSI, MISO, chip select | fast (MHz) | one chip-select line per device | radios that move packets, like the SX1262 |
| I²C | clock, data | slow (100–400 kHz) | a 7-bit address per device on a shared pair | small peripherals, like the RTC |
| USB | differential pair | 480 Mbit/s on the CM4 (USB 2.0) | enumerated | bulk data, like SDR samples |

## Where each AIO V2 device sits

| Device | Chip | Bus | Linux sees it as | Enabled by |
|---|---|---|---|---|
| GNSS receiver | multi-GNSS module | UART | `/dev/serial0` (= `ttyS0`, the mini-UART, on this build) | `enable_uart=1` in `config.txt` |
| LoRa radio | SX1262 | SPI1 | `/dev/spidev1.*`, driven by meshtasticd | `dtoverlay=spi1-1cs` |
| RTC | PCF85063A | I²C | `/dev/rtc0` | `dtoverlay=i2c-rtc,pcf85063a` |
| SDR | RTL2832U + R820T/R860 | USB | a USB device claimed by librtlsdr | nothing — it enumerates when powered |

The overlays are in [`../../../configs/boot/config-cm4.txt`](../../../configs/boot/config-cm4.txt).

## What a rail is

Each radio also has a **power rail**: a supply line switched by a GPIO pin. Driving the pin high
powers the radio; low cuts it off completely.

| Rail | GPIO (BCM) | Powers | Boots |
|---|---|---|---|
| GPS | 27 | the GNSS receiver | on (boot config since 2026-09-22) |
| LORA | 16 | the SX1262 | on (same) |
| SDR | 7 | the RTL-SDR | off |
| USB | 23 | the board's internal USB | off |

`aiov2_ctl <RAIL> on|off` drives the pin; webdash's switches go through the same command via the
bridge. With a rail off, the chip's data connection still exists but nothing answers on it — which is why
readsb crash-loops with the SDR rail off, and why gpsd reports no fix with the GPS rail off.

## One owner per device

A device node or a single-client socket can only be used by one program at a time. Most of this
build's confusing failures are two programs wanting the same thing:

| Resource | Owner | What goes wrong if something else takes it | Fix |
|---|---|---|---|
| RTL-SDR (USB) | readsb | `rtl_test` / `rtl_fm` fail with `usb_claim_interface error -6` | stop readsb first (`sudo systemctl stop readsb`), start it after |
| RTL-SDR (USB), at boot | the kernel's DVB-T driver | librtlsdr can't claim the dongle | blacklisted in [`../../../configs/modprobe.d/blacklist-rtl-dvb.conf`](../../../configs/modprobe.d/blacklist-rtl-dvb.conf) |
| `/dev/serial0` | gpsd | reading it directly (`cat /dev/serial0`) interleaves with gpsd | read through gpsd: `gpspipe -r` |
| `/dev/serial0`, at boot | the serial console | GPS sentences are swallowed by a login prompt | `console=serial0` removed from `cmdline.txt` |
| meshtasticd TCP 4403 | webdash | the `meshtastic` CLI connects and webdash's mesh client is dropped (and vice versa) | read the journal instead; if you do use the CLI, webdash reconnects on its next poll after you close it |
| SPI1 | meshtasticd | on some ClockworkPi images a `devterm-printer` service also takes SPI1 | not installed on this image (`systemctl is-enabled devterm-printer` → `not-found`, 2026-09-24); elsewhere, disable and mask it ([`../../../configs/systemd/README.md`](../../../configs/systemd/README.md)) |
