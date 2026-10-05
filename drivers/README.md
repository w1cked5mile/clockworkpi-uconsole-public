# drivers/

Kernel modules, device-tree overlays, and driver notes for the AIO V2 (RTL-SDR/LoRa/GPS/RTC) and
the adapter/NVMe boards.

Nothing needs building for this build as specified — every function is served by in-tree drivers
plus overlays. What matters is which module claims which device:

| Function | Module / driver | Notes |
|---|---|---|
| RTL-SDR | userspace `librtlsdr` over `usbfs` | The kernel's `dvb_usb_rtl28xxu` must be blacklisted or it claims the device first — [`../configs/modprobe.d/blacklist-rtl-dvb.conf`](../configs/modprobe.d/blacklist-rtl-dvb.conf) |
| LoRa (SX1262) | `spidev` via `dtoverlay=spi1-1cs` | Meshtastic talks to `/dev/spidev1.0` from userspace |
| RTC (PCF85063A) | `rtc-pcf85063` via `dtoverlay=i2c-rtc,pcf85063a` | Appears as `/dev/rtc0`; `hwclock -r` reads it |
| GNSS | none — plain UART | `/dev/serial0` (`ttyS0` on this build — onboard Bluetooth holds the PL011 as `ttyAMA1`), consumed by gpsd |
| NVMe | `nvme` over PCIe | Requires the adapter's PCIe path; check `lspci` |
| AC1200 (optional) | `mt7921u` + `linux-firmware` | Monitor mode is the reason this card exists here |

Overlay fragments to apply: [`../configs/boot/config-cm4.txt`](../configs/boot/config-cm4.txt).
CM4 vs CM5 overlay differences: [`../docs/reference/pinout-gpio.md`](../docs/reference/pinout-gpio.md).

Kernel sources, if a rebuild ever becomes necessary: https://github.com/clockworkpi/Kernel and the
patches in `Code/patch/` of https://github.com/clockworkpi/uConsole.
