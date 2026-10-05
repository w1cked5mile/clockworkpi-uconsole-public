# HackerGadgets upgrade kit — adapter / NVMe battery / RJ45+USB3 boards

Three boards, ordered together as order #11953 (variant: CM4/CM5 + Dual 18650 holder).
**Delivered and inspected 2026-09-23.** Board names as silkscreened: `Raspberry Pi CM4/5 Adapter
Pro for uConsole` and `uConsole NVMe Battery Board`, both "Designed by HackerGadgets.com".
Photographs: [`../../images/inventory/`](../../images/inventory/README.md) (`20260923-*`).

## Adapter board (CM4/CM5 → ClockworkPi v3.14)

Silkscreened **`Raspberry Pi CM4/5 Adapter Pro for uConsole`**.

| Attribute | Value | Source |
|---|---|---|
| Accepts | Raspberry Pi CM4 / CM5 (and Radxa CM5 per vendor) | vendor |
| Exposes | `PCIe`, `Flash` USB-C (rpiboot), `CM5 FAN`, `CSI1`, `CM5 USB 3.0`, `RPITX` IPEX | **board silkscreen, 2026-09-23** |
| Presents | uConsole core-module edge interface to the v3.14 mainboard | vendor |
| Config DIP | 2-position: **`1:nRPIBOOT`**, **`2:EEPROM_nWP`** | **board silkscreen** |
| RTC battery JST | Present, marked **"RTC Battery for CM5. Don't connect when using CM4"** | **board silkscreen** |
| Marked IC | `UM82409S`, date-code-like `2628` — *function not identified* | board photo, unverified |
| Ethernet ribbon port | **Corrected 2026-09-25 (owner):** the port marked **"CM5 USB 3.0"** takes the AIO V2's Ethernet ribbon, which connects the CM4's gigabit Ethernet to the RJ45 on the AIO V2. The ribbon comes with the AIO V2, not this board; the uConsole kit's `RPi CM4 to CPI v3.14 Adapter` has no such port, which is what was interim-fitted. Earlier text below said this board "carries the RGMII ribbon" to "the mainboard's RJ45 jack"; both were wrong. **This board arrived 2026-09-23, so the hypothesis is now testable**: install it and retest Ethernet. If the link comes up, the 2026-09-16 "mainboard hardware fault" diagnosis was wrong and the interim adapter was the cause. See [`../../docs/logs/known-issues.md`](../../docs/logs/known-issues.md). *Still unverified.* **Installed 2026-09-23.** `eth0` comes up and the PHY reads over MDIO, but the link is *unverified*: no cable was plugged in at the first test. **Confirmed 2026-09-23:** with a live cable, `eth0` links at 1 Gbps/full through this adapter (checklist 2.2 passes). | owner, unverified |

The USB-C flash port is the `rpiboot` path. On a **Lite** module there is no eMMC to flash — the
port's use here is host-side access to the attached NVMe.

### Two adapter settings that bite before first boot

- **Do not connect an RTC backup cell to the adapter's JST.** The silkscreen restricts it to CM5;
  **this build is a CM4**. Nothing in the repo previously recorded that the adapter has its own RTC
  connector at all, and it is adjacent to other 2-pin JSTs on neighbouring boards.
- **The DIP switch positions are `nRPIBOOT` and `EEPROM_nWP`**, both active-low by name. `nRPIBOOT`
  is what forces the module into USB boot for `rpiboot`; `EEPROM_nWP` gates bootloader-EEPROM
  writes, which matters when setting NVMe boot order. **As-shipped switch state is not recorded** —
  photograph or read it before flashing, and record it in
  [`../../docs/logs/firmware-versions.md`](../../docs/logs/firmware-versions.md).

### `RPITX` — GPIO4 is routed to an IPEX connector

The board carries an IPEX connector labelled `RPITX` and this silkscreen note:

> "GPIO4 was connected to the IPEX connector for radio transmit. If you want to connect it to the
> uConsole main board, solder a 0Ω resistor as the arrow point to."

So **GPIO4 does not reach the mainboard by default on this board** — it terminates at the IPEX
connector instead, and a 0Ω link at the marked position restores the normal routing. That is a
functional difference from a plain adapter and is worth knowing before debugging anything that
expects GPIO4 on the 40-pin header.

On the transmit provision itself: driving RF straight off a GPIO pin produces a square wave, so
the output is rich in harmonics across the spectrum and is not a clean carrier. Radiating it
requires an amateur licence or equivalent authorisation for the band in question, plus appropriate
filtering — see the responsible-use section in
[`../../knowledge/README.md`](../../knowledge/README.md). This repo records the connector as a
hardware fact; it does not carry operating procedure for it.

## NVMe battery board

| Attribute | Value | Confidence |
|---|---|---|
| SSD support | M.2 **M-key** NVMe, standoff positions silkscreened `2230` `2242` `2260` `2280` | **board silkscreen, 2026-09-23** |
| Slot marking | `NVMe M key PCIe 1x` — **single lane** | **board silkscreen** |
| Indicators | `ACT` and `PWR` LEDs on the board edge | **board silkscreen** |
| Battery positions | `BAT1` and `BAT2` 18650 holders, **in parallel** (the system is 1S — mainboard PMIC is an AXP228) | schematic + board photo |
| Alternative battery | **2-pin JST connector for a 1S LiPo pack** | board photo |
| Mode select | `JP1` solder jumper — **open for 18650, soldered closed for the JST LiPo pack** | board silkscreen, transcribed from a photograph |
| Protection | Reverse-polarity protection with indicator LED | vendor page |
| Link | PCIe Gen2 ×1 from the CM4 via the adapter | vendor page |

## JP1 — battery mode jumper

The silkscreen beside the BAT2 position reads, as transcribed from a photograph of an assembled
board:

> "Solder JP1 for disperse current when using JST for Lipo battery pack. Must let it open for
> 18650 batteries."

**Confirm the wording and the jumper's location on the physical board before applying power.** Set
it to match the battery actually fitted; this is a current-path setting on the battery rail, not a
preference.

Energy comparison and safety notes for each option:
[`../../docs/reference/power-budget.md`](../../docs/reference/power-budget.md).

Treat the reverse-polarity LED as a diagnostic, not a safety net: verify cell orientation, JST
polarity, and holder contact before first power-up.

**Status 2026-09-23:** the board is in hand, but the `JP1` silkscreen quoted above is **not legible
in any photograph taken so far**. A two-pad solder-jumper footprint is visible beside the `BAT2`
marking, consistent with it. The board also carries a `Reverse Warning` label at that edge. **Update 2026-09-23:** the owner read the board directly. `JP1` is **open**, correct for the
18650s now fitted, and the reverse-polarity LED is unlit (checklist 1.7). `JP1`'s exact board
location is still unrecorded; a legible photo would settle it.

## Manual battery on/off — `R14` / `J6`

Silkscreen on the underside, transcribed 2026-09-23:

> "To enable manual on/off control of the batteries. Desolder R14 and connect a push-lock switch to
> J6. The battery will be turned on when the switch is locked. And turn off when the switch is
> released."

An optional modification, not required for normal operation: `R14` is fitted from the factory and
holds the battery path enabled. Desoldering it without wiring a switch to `J6` leaves the pack
permanently off — **do not remove `R14` speculatively**. Nothing in this build currently needs it;
it is recorded because it is irreversible-ish and easy to misread as a jumper to change.

## RJ45 + USB 3.0 board

| Attribute | Value |
|---|---|
| Ethernet | RJ45, 1 Gbps PHY |
| USB | USB 3.0 Type-A and Type-C |
| GPIO | 17-pin header |
| On this build | **Installed 2026-09-23.** A QinHeng `1a86:8091` USB hub appeared that is in no earlier `lsusb` record, and is **confirmed as this board's hub 2026-09-23**: a device plugged into the board enumerated behind it at 480M. It is powered independently of the AIO V2 `USB` rail (it works with GPIO23 off). It sits on port 4 of the Genesys `05e3:0608` hub. No USB Ethernet device enumerates: the working Ethernet is the CM4's own `bcmgenet`, through the AIO V2's RJ45 and its ribbon into the Adapter Pro (corrected 2026-09-25). |
| CM4 caveat | Both Ethernet and USB run at **USB 2.0** rates; USB 3.0 needs CM5 |

Product page: https://hackergadgets.com/products/uconsole-upgrade-kit
Adapter rpiboot thread: https://forum.clockworkpi.com/t/using-rpiboot-on-the-hackergadgets-cm4-5-adapter/21767
