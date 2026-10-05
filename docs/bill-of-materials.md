# Bill of Materials — ClockworkPi uConsole Build

Revision E · 2026-09-23 · Owner: Raymond Overman

Prices are approximate reference values as of the document date and exclude shipping, duties, and taxes. Several HackerGadgets items ship on pre-order.

## Core build — specified components

| # | Component | Description / Key Specifications | Qty | Vendor | Est. Unit Price / Notes |
|---|---|---|---|---|---|
| 1 | ClockworkPi Mainboard v3.14 | Core uConsole/DevTerm mainboard, 95×77 mm. Modular DDR2-SODIMM core-module interface (accepts CM carrier via adapter). 3× USB-A 2.0, USB-C charge, micro-HDMI, 3.5 mm audio, TF/microSD, onboard PMU + stereo amp. 52-pin mini-PCIe expansion header, 40-pin MIPI display, 40-pin GPIO FPC. | 1 | ClockworkPi | ~$39 (ships in uConsole kit) |
| 2 | HackerGadgets NVMe / Adapter Upgrade Kit | CM4/CM5 adapter board exposing PCIe + USB-C eMMC flash port; PWM fan and CSI2 camera headers. NVMe battery board: PCIe M.2 NVMe SSD, sizes 2230–2280, reverse-polarity protection w/ LED. RJ45 + USB 3.0 board: 1 Gbps Ethernet, USB 3.0-A/-C (USB 2.0 on CM4), 17-pin GPIO header. | 1 | HackerGadgets / Sapsan | Adapter ~$23 (NVMe + RJ45 boards priced separately) |
| 3 | OpenSourceSDRLab / HackerGadgets AIO V2 SDR Board | All-in-one uConsole expansion. RTL-SDR: RTL2832U + R860, 100 kHz–1.74 GHz, TCXO, 5V bias tee. LoRa/Meshtastic: SX1262, 860–960 MHz, 22 dBm, TCXO. GPS/BDS/GNSS (active or passive antenna). RTC: PCF85063A + CR1220. USB hub (int/ext Type-C), RJ45 1 Gbps, USB 3.0 (CM5 + upgrade kit). Per-function GPIO power switching (SDR/GPS/LoRa/USB off by default). | 1 | OpenSourceSDRLab / HackerGadgets | ~$163 |

## Supporting / required to complete the build

| # | Component | Description | Qty | Vendor | Est. Unit Price / Notes |
|---|---|---|---|---|---|
| 4 | Raspberry Pi CM4 Lite 8GB | CM4, 8GB RAM, Lite (no onboard eMMC — boots from microSD or NVMe). Planned module per build notes (preferred over CM5 / Radxa CM5). | 1 | Raspberry Pi / authorized reseller | ~$75, market-dependent |
| 5 | **M.2 NVMe SSD — WD PC SN730 256 GB** *(selected and fitted 2026-09-23)* | Six drives pulled from old devices are on hand; **four are NVMe candidates** (WD PC SN730 256GB, 2× Samsung PM961 256GB, Toshiba NVMe 256GB) and **two are SATA and incompatible** (Samsung PM871, SanDisk X400) — serials in [`records/order-and-warranty.md`](records/order-and-warranty.md). **The SN730 was the one fitted:** `SDBQNTY-256G-1001`, M.2 **2280**, PCIe NVMe, **OPAL** self-encrypting, Lenovo-channel part (LEN P/N `SSS0L24774`, FRU `5SS0V26411`), FW `11130101`, HW `0A`, mfg 19DEC2019. The other three stay as spares. **Booting as root since 2026-09-23:** SMART `PASSED`, 25,560 power-on h, 47.48 TB written, 21% used. It is not OPAL-locked. | 1 (of 4 candidates) | On-hand stock (not purchased) | $0 — reused. 2280 seats on the board's outermost standoff, so the form-factor question is closed. **OPAL:** if the drive was ever locked in its previous host it needs unlocking or a factory revert before it will take an image — *unverified, check before assuming a blank drive*. |
| 6 | Battery **holder** — Dual 18650 | Holder that mounts to the NVMe battery board. Ordered as the "With Dual 18650 Batteries Holder" variant of item 2. The board takes 2 × 18650 in **parallel** *or* a 1S LiPo on the JST connector; `JP1` selects (open = 18650, soldered = JST). A second holder arrived fitted to the uConsole kit's own stock battery board. | 1 | HackerGadgets (bundled with item 2) | Included in item 2 — **holder only**. **Arrived with #11953 on 2026-09-23.** Battery options are items 6a, 6c, 6d. |
| 6a | Battery — **1S LiPo pack, Meshnology 1163115** (pack of record); 2 × 18650 parallel is the interim | `Meshnology 2pcs 3.7V 10000mAh … 1S LiPo Battery with Protection Board … Micro PH2.0 Plug`, **2 pcs supplied**. The board takes either; `JP1` selects the mode (open = 18650, soldered = JST LiPo). The listing states a **protection board** and a **PH 2.0 plug** — *vendor-listing claims, not meter readings*. | 1 (of 2 on hand) | **On hand** — Amazon [114-7650902-4482665](records/order-and-warranty.md) (2026-09-09, $42.79/pair, delivered 2026-09-10) | 10000 mAh / 3.7 V / **37 Wh**. Supersedes the UNIKARO 15000 mAh / 55.5 Wh, never bought. **Not yet fitted** — the NVMe battery board it needs arrived 2026-09-23, so this is now unblocked; confirm JST type and polarity first. See [`reference/power-budget.md`](reference/power-budget.md). |
| 6b | microSD card | 32 GB+, A1/A2, UHS-I | 1 | **On hand — flashed 2026-09-15** | `uConsole_CM4_v3.1_64bit`, read-back verified. **Fallback only since 2026-09-23.** Root is on NVMe. The card was removed 2026-09-23 after NVMe-only boot passed, and is kept as a spare boot fallback. |
| 6c | 18650 cells ×2 (unbranded, `9900mAh`-wrapped) | **Interim pack, fitted 2026-09-15; powered the first boot 2026-09-16.** Rejected on safety grounds 2026-09-06; in service only until the LiPo swap. Weigh / voltage-match / capacity-test before any further power-up. | 2 | On hand, no purchase record | $0 — provenance unknown; a matched named pair is the replacement if they fail the checks. |
| 6d | ~~Battery — 1S LiPo, UNIKARO 3.7 V 15000 mAh~~ | Superseded, never fitted. Two delivered 2026-06-18 (predates this build); a repeat order was **cancelled 2026-09-09** over the shipping estimate and replaced by 6a minutes later. Retained so the 55.5 Wh figures still standing in [`reference/power-budget.md`](reference/power-budget.md) have a traceable source. | — | Amazon — UNIKARO | Not the plan of record. |
| 7 | **AC1200 USB-C Wi-Fi Card** | MediaTek MT7921AUN, monitor mode, Wi-Fi 6/6E + BT 5.2, USB-C 3.2 Gen1, **4× IPEX antenna** — confirmed on the card 2026-09-30: 2 on the component side (Wi-Fi), 2 on the back silkscreened `BT0`/`BT1` (Bluetooth); see [`../hardware/specs/ac1200-mt7921.md`](../hardware/specs/ac1200-mt7921.md). Supplies the antenna leads mapped to `ANT2`/`ANT3` (BT) and `ANT5`/`ANT6` (Wi-Fi). | 1 | HackerGadgets | **Received & installed 2026-09-30 — HackerGadgets [#12253](records/order-and-warranty.md), $63.00 incl. shipping** (shipped 2026-09-21, PFC `SWX001670000180759280`). Verified on Fancy: `wlan1` (`mt7921u`) monitor mode on 2.4/5/6 GHz, Bluetooth `hci1` (USB). On CM4 it runs at USB 2.0. |

## Notes

- CM4 Lite has no onboard eMMC; boot from microSD or the NVMe board. On CM4, adapter/AIO USB ports run at USB 2.0 — USB 3.0 requires CM5.
- NVMe SSD reused from on-hand stock — **identified and fitted 2026-09-23**: WD PC SN730 256 GB, M.2 2280, which the board's 2280 standoff position accepts. It is an **OPAL** drive; if it was locked in a previous host that has to be dealt with before it will take an image.
- Battery variant ordered was the Dual 18650 **holder** — the holder is not the cells, and the board also accepts a 1S LiPo pack on its JST connector (see items 6a–6c). The system is **1S**: the mainboard PMIC is an AXP228 single-cell part, so the two 18650 positions are in parallel, not series.
- **Battery history, rev D.** The plan moved 18650s → 15000 mAh LiPo (UNIKARO, 2026-09-07 decision) → 10000 mAh LiPo (Meshnology, ordered 2026-09-09 **three and a half minutes after** the repeat UNIKARO order was cancelled the same morning). What is *physically fitted right now* is neither: two unbranded `9900mAh`-marked 18650s, as an interim pack. Energy figures in [`reference/power-budget.md`](reference/power-budget.md) are written against 55.5 Wh and are **stale for every one of those three options** — 37 Wh for the Meshnology, unmeasured for the 18650s.
- The uConsole kit itself normally ships with ClockworkPi's own battery board, which is redundant with the HackerGadgets NVMe battery board. Decide which one is installed at inventory and record it in [`logs/decisions.md`](logs/decisions.md).
- **Item 7 moved from optional to specified (rev C, 2026-09-16).** The AC1200 is part of the build:
  it was ordered from HackerGadgets as a separate line, **order #12253**, and the antenna port
  mapping in [`reference/antennas-and-rf-connectors.md`](reference/antennas-and-rf-connectors.md)
  depends on its four IPEX leads. It **arrived and was installed 2026-09-30** and is verified on
  Fancy (`wlan1` / `hci1`, monitor mode, 2.4/5/6 GHz), so those four `ANTn` positions are now
  populated.
- **Do not confuse it with the upgrade kit.** Order #11953's product title reads "…/AC1200 WiFi(with
  monitor mode supported)…", but its variant line ends in `NONE` — that is the card option, so no
  card ships with the kit. Two orders, two vendors' worth of confusion in one product name.
- Accessories, antennas, and optional add-ons are tracked separately in [`accessories.md`](accessories.md).

## Actual orders placed

Every purchase that bears on this build, in date order, including the one that was cancelled.
Cross-reference [`records/order-and-warranty.md`](records/order-and-warranty.md) for shipping state.

| Date | Item | Vendor / order | Status |
|---|---|---|---|
| 2026-06-17 | UNIKARO 3.7 V 15000 mAh 1S LiPo × 2 | Amazon — UNIKARO | **Delivered 2026-06-18.** Predates this build; probably the "UDIY-0001L" of earlier notes (*inferred from matching specs*) |
| 2026-09-02 | uConsole kit (v3.14) + AIO V2 | AliExpress — OpenSourceSDRLab, 8214326520279843 | Delivered; unboxed 2026-09-16 |
| 2026-09-03 | CM4 Lite 8GB | Newark, 10397194 | Delivered 2026-09-04 |
| 2026-09-03 | Adapter / NVMe / RJ45 upgrade kit (Dual 18650 holder variant) | HackerGadgets, [#11953](records/order-and-warranty.md) | **Delivered 2026-09-23**; shipped 2026-09-14, PFC `SPXCLT003022609140031768` |
| 2026-09-09 11:46Z | ~~UNIKARO 3.7 V 15000 mAh~~ (repeat purchase) | Amazon — UNIKARO | **Cancelled.** Placed after the 2026-09-07 decision to buy a second 15000 mAh pack |
| 2026-09-09 11:50Z | **Meshnology 2pcs 3.7 V 10000 mAh 1S LiPo**, protection board, PH 2.0 plug | Amazon — Meshnology, [114-7650902-4482665](records/order-and-warranty.md) | **$42.79. Delivered 2026-09-10.** Placed **3 min 34 s after** the UNIKARO cancellation above — a direct swap |
| 2026-09-23 | *(no purchase)* WD PC SN730 256 GB selected from the four on-hand NVMe candidates and fitted | — | Identified on installation; three NVMe spares remain |
| 2026-09-15 | **AC1200 USB-C Wi-Fi card** | HackerGadgets, [#12253](records/order-and-warranty.md) | **Received & installed 2026-09-30** (separate order from the upgrade kit; shipped 2026-09-21, PFC `SWX001670000180759280`) |

Not purchased: the M.2 NVMe SSD (on-hand stock) and the microSD (item 6b, no order record). The
microSD was flashed 2026-09-15 and booted 2026-09-16, and is now a spare since root moved to NVMe. The two `9900mAh`-marked 18650s now fitted appear in **no** order record —
their provenance is still unaccounted for.

*Sourced from mailbox sweeps of both accounts on 2026-09-16 and 2026-09-22. Amazon's
order-confirmation emails name only a category ("Ordered 1 item: Toys & Games" is the Meshnology
battery order), so these lines are keyed by order number rather than found by product name. The
2026-06-17 UNIKARO line still lacks an order number, and its $14.99 is not distinguishable as unit
or line total from the confirmation.*

## Sources

- ClockworkPi v3.14: https://www.clockworkpi.com/product-page/clockworkpi-v3-14
- HackerGadgets Upgrade Kit (adapter/NVMe/RJ45): https://hackergadgets.com/products/uconsole-upgrade-kit
- AIO V2: https://opensourcesdrlab.com/products/opensourcesdrlab-uconsole-aio-v2-rtl-sdr-lora-gps-rtc-usb-hub-usb-30-rj45-ethernet
