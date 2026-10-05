# Drivers, device nodes and udev

How a chip becomes a file under `/dev`, and how this build steers that. Written 2026-09-25 (gap
P2). References: `udev(7)` and `modprobe.d(5)` (linked in
[`../../../knowledge/README.md`](../../../knowledge/README.md) §Platform references).

## From chip to file

| Layer | What it does | Example on Fancy |
|---|---|---|
| Kernel driver (module) | code in the kernel that knows the chip | `rtc_pcf85063`, `spidev`, `dvb_usb_rtl28xxu` |
| Device node | the file programs open to talk to the driver | `/dev/rtc0`, `/dev/spidev1.0`, `/dev/serial0` |
| udev | a daemon that reacts when a device appears: names it, sets permissions, runs actions | Kismet's nRF rules create `/dev/nrf51822*` symlinks |
| Program | opens the node | gpsd opens `/dev/serial0`; librtlsdr opens the USB device |

List loaded drivers with `lsmod`; see what udev knows about a node with
`udevadm info /dev/rtc0`. Both are read-only.

## Why the DVB-T driver is blacklisted

The RTL2832U is sold as a TV tuner, so the kernel's DVB-T driver claims it on sight. Then
librtlsdr (and rtl_test, readsb) can't. The fix is to tell modprobe never to load it:
[`../../../configs/modprobe.d/blacklist-rtl-dvb.conf`](../../../configs/modprobe.d/blacklist-rtl-dvb.conf).
Check with `lsmod | grep dvb` — no output is right.

## Reading a udev rule

```text
ACTION=="add", SUBSYSTEM=="tty", ATTRS{idVendor}=="1915", ATTRS{idProduct}=="522a", PROGRAM="/bin/sh -c 'echo $$(($$(ls /dev/nrf51822* 2>/dev/null| tail -n1 | sed -e s#/dev/nrf51822## )+1))'", SYMLINK+="nrf51822%c"
```

Keys with `==` are **matches** (all must be true); keys with `=` or `+=` are **actions**. This one
says: when a serial device appears whose USB IDs are 1915:522a, run `PROGRAM` to pick the next
free number, then add a symlink `nrf51822<n>` — `%c` is PROGRAM's output. udev treats `$` as
special, so a literal `$` in the shell command must be written `$$` — the bug this build's copies
of Kismet's rules fix
([`../../../configs/udev/`](../../../configs/udev/)).

## On this build

| Node | Driver | Owner |
|---|---|---|
| `/dev/serial0` → `ttyS0` | the mini-UART | gpsd |
| `/dev/spidev1.0` | `spidev` on SPI1 | meshtasticd |
| `/dev/rtc0` | `rtc_pcf85063` | the kernel / `hwclock` |
| RTL-SDR (USB) | none — librtlsdr talks to it directly | readsb |
