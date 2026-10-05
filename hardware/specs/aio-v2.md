# OpenSourceSDRLab / HackerGadgets AIO V2 — spec sheet

All-in-one uConsole expansion on the 52-pin extension connector. Per-function power rails are
GPIO-switched — see [`../../docs/reference/pinout-gpio.md`](../../docs/reference/pinout-gpio.md).

Board silkscreen (observed on the received unit, 2026-09-14): **"uConsole AIO extension board
V2" / "Designed by HackerGadgets.com"** — HackerGadgets branding on the PCB itself even though
this unit was purchased through the OpenSourceSDRLab AliExpress listing. Board edge carries
labeled test points `GND` / `D+` / `D-` / `5V` and three connectors: one USB-C and two micro-USB.
u.FL RF pads on the board are silkscreen-labeled **SDR / LoRa / GPS** (left to right).

| Function | Chipset | Key specs | Host interface | Rail (BCM) |
|---|---|---|---|---|
| RTL-SDR | RTL2832U + R860 | 100 kHz – 1.74 GHz, TCXO, 5 V bias tee | USB | 7 (default off; see [`../../docs/logs/decisions.md`](../../docs/logs/decisions.md)) |
| LoRa | Semtech SX1262 | 860–960 MHz, up to 22 dBm, TCXO | SPI1 (`spidev1.0`) | 16 |
| GNSS | **GP-02, BDS+GPS** (dual-constellation, silkscreen-marked on the module) | active or passive antenna | UART `/dev/serial0` (= `ttyS0` on this build) | 27 |
| RTC | NXP PCF85063A | CR1220 backup cell | I²C | always |
| USB hub | — | internal + external Type-C | USB | 23 |
| Ethernet | — | RJ45 jack for the CM4's native gigabit Ethernet (`bcmgenet`; the PHY is on the CM4). Reaches the CM4 through a ribbon into the Adapter Pro's port marked "CM5 USB 3.0"; the uConsole kit's CM4 adapter has no such port. Links at 1 Gbps (2026-09-23), so not USB-bottlenecked. *Owner, 2026-09-25; corrects the earlier "1 Gbps PHY, USB 2.0 bottleneck"* | Ribbon to the CM4 adapter | — |
| USB 3.0 | — | requires CM5 + upgrade-kit adapter | USB | — |

> `rtl_test` identifies the tuner as **"R820T"**, not "R860" (confirmed 2026-09-16 — see
> [`../../docs/logs/build-log.md`](../../docs/logs/build-log.md)). Not treated as a hardware
> discrepancy — most likely just how this `librtlsdr` build's tuner-ID table labels an R860 (same
> R82xx family/register set as the R820T it recognizes by name).

> GNSS UART confirmed as `/dev/serial0` (`ttyS0`), not `/dev/ttyAMA0` — the onboard CM4 Bluetooth
> holds the full PL011 (`ttyAMA1`). Confirmed 2026-09-16 reading live NMEA. See
> [`../../docs/logs/decisions.md`](../../docs/logs/decisions.md).

## Accessory hardware received with this board (AIO V2 parcel, 2026-09-14)

- **7-position SMA bulkhead breakout** (silkscreened `ANT1`–`ANT7`), connected to the AIO board by
  an FPC ribbon — panel-mounts multiple antenna connectors to the case exterior. Which of ANT1–7
  map to which radio (SDR/LoRa/GPS/Wi-Fi/BT) is not yet traced — do this before drilling the case.
- **"Bias-T" bracket** — a separate small panel-mount bracket, silkscreen-labeled "Bias-T", with a
  round antenna-connector hole and a port cutout. Purpose/wiring not yet confirmed; likely exposes
  the RTL-SDR's bias-tee-powered SMA (see Practical limits below) at the case exterior.
- 6 rubber-duck antennas (3 Wi-Fi, 2 Bluetooth marked, 1 LoRa), 1 SDR whip, 1 cylindrical
  puck-style GPS antenna, ~8 u.FL-to-u.FL pigtails (various lengths) + 1 u.FL-to-SMA, and bagged
  spare SMA bulkhead hardware (nuts/washers). Full count in
  [`../../docs/checklists/inventory-and-inspection.md`](../../docs/checklists/inventory-and-inspection.md).

## LoRa (SX1262) control lines

| Signal | BCM GPIO |
|---|---|
| Enable rail | 16 |
| IRQ (DIO1) | 26 |
| Busy | 24 |
| Reset | 25 |

## Practical limits

- **RTL-SDR is 8-bit and receive-only.** ~2.4 MS/s usable bandwidth, and the shared USB 2.0 bus
  on CM4 makes sustained high sample rates lossy — measure with `rtl_test -s`.
- **Below ~24 MHz** the R860 needs the bias tee / an upconverter or direct-sampling mod; treat the
  "100 kHz" figure as conditional, not a flat HF capability.
- **The bias tee outputs 5 V on the SDR SMA.** Do not connect a DC-shorted antenna or a
  bias-tee-powered LNA you have not accounted for.
- **LoRa TX without an antenna can damage the PA.** Attach 915 MHz before enabling the rail.
- SDR rail defaults on in upstream `BOOT_DEFAULTS`; whether CM4 actually asserts it at boot is
  unconfirmed and is bring-up test 0.

Vendor setup guide: https://hackergadgets.com/pages/hackergadgets-uconsole-rtl-sdr-lora-gps-rtc-usb-hub-all-in-one-extension-board-setup-guide
Control client: https://github.com/hackergadgets/aiov2_ctl
