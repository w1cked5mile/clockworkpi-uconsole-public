# Accessories — required, decided, and optional

Revision A · 2026-09-06 · Companion to [`bill-of-materials.md`](bill-of-materials.md).

The BOM covers the boards that were ordered. This file covers everything *else* the build
needs or can take, with a buy/no-buy status so nothing is discovered missing on assembly day.

Status key: **BLOCKER** = first boot or battery operation is impossible without it ·
**VERIFY** = may already be in the box, confirm at inventory · **OPTIONAL** = capability add-on.

> **Note, updated 2026-09-23.** The AliExpress kit + AIO V2 have arrived and been
> photographed. The battery rows below now describe the pack of record, the
> `Meshnology 10000mAh 3.7V 37Wh` (the UDIY-0001L chosen 2026-09-07 was dropped), and **its order
> record has been located** — Amazon #114-7650902-4482665, 2026-09-09, $42.79 for the pair
> ([`records/order-and-warranty.md`](records/order-and-warranty.md)). The two 18650 cells still have
> no purchase record and their provenance is unknown. The 22 Wh 18650 estimate does not describe
> the cells fitted today — see Discrepancies in
> [`checklists/inventory-and-inspection.md`](checklists/inventory-and-inspection.md). Several
> **VERIFY** rows below are now answerable from the photographs: antennas, u.FL pigtails and a
> copper-foil thermal pad arrived; a CR1220 did not appear in any frame.
> **Update 2026-09-23:** the NVMe battery board arrived with #11953, so the LiPo swap is unblocked.
> Current ordering and battery rows live in [`bill-of-materials.md`](bill-of-materials.md) items
> 6/6a–6d and its *Actual orders placed* table.

## Required to reach first boot / battery operation

| Item | Spec that matters | Status | Notes |
|---|---|---|---|
| microSD card | 32 GB+, A1/A2, UHS-I | **Resolved** — flashed 2026-09-15, booted successfully 2026-09-16 | Path A first boot and recovery media. `mmcblk0`, CID serial `0x3832c348`, 29.5 GB usable (nominal 32 GB card), written with `uConsole_CM4_v3.1_64bit` and read-back verified — see [`logs/firmware-versions.md`](logs/firmware-versions.md). Speed class/A1-A2 rating not yet confirmed off the card body; check it if first boot is sluggish. |
| **Battery — one of the two below** | The board takes 2 × 18650 (parallel) **or** a 1S LiPo pack on a JST connector; `JP1` selects the mode | **BLOCKER** — nothing was supplied with the kit | The order line reads "With Dual 18650 Batteries **Holder**" — a holder is not cells. Comparison: [`reference/power-budget.md`](reference/power-budget.md) |
| **→ Pack of record: 1S LiPo, Meshnology** | 10000 mAh, 3.7 V, **37 Wh**, Li-ion pouch, model 1163115, **PH2.0** connector, CE/RoHS marked | **ON HAND, NOT FITTED** (received 2026-09-14; Amazon #114-7650902-4482665, 2026-09-09) | ≈ 31 Wh usable: ~6 h terminal use, ~4.7–5 h SDR receiving on the measured ~5.0 W idle (see [`reference/power-budget.md`](reference/power-budget.md)). The NVMe battery board it needs **arrived 2026-09-23 and is fitted**, currently holding the interim 18650s with `JP1` open. Before this pack goes on, `JP1` must be soldered **closed**. Replaced the UDIY-0001L (15000 mAh/55.5 Wh), dropped for its shipping time. **Whether the board connector is also PH2.0 is unverified** — confirm type and polarity before connecting; a direct JST pack has no holder to mechanically prevent a reversed connection. Fit is still open — case modification accepted. |
| → **Fitted now (interim): 18650 cells ×2** | Unbranded, wrapped `9900mAh 3.7V`, no make/model/batch code, in the stock board’s 2-bay holder, **parallel** (1S) | **FITTED 2026-09-15 — temporary; powered the first boot 2026-09-16** | In service only until #11953 brings the NVMe battery board, then the Meshnology pack replaces them. These are the cells **rejected on safety grounds 2026-09-06**; that objection is undischarged, not withdrawn — the choice was these or no battery at all. **Weigh, voltage-match and capacity-test now — they already powered on once, before this was done** ([`logs/known-issues.md`](logs/known-issues.md)); a real 3000–3500 mAh cell is ≈45–48 g. Pack energy is **unmeasured** — not 37 Wh, and not the 22 Wh a matched pair would give. |
| USB-C data cable | Must carry data, not charge-only | **VERIFY** | `rpiboot` fails silently on charge-only cables — see [`checklists/tools-and-consumables.md`](checklists/tools-and-consumables.md). |
| USB-C power supply | 5 V ≥ 3 A (15 W) | **VERIFY** | Charging plus an active SDR rail draws more than a phone charger comfortably supplies. |
| CR1220 coin cell | 3 V, for the PCF85063A RTC backup | **MISSING** — none fitted or on hand (confirmed 2026-09-23); order one | Without it the RTC loses time across a full power-down and the RTC bring-up test cannot pass. |

## Antennas and RF interconnect

Which of these ship with the AIO V2 varies by listing and revision — count what arrives
against [`checklists/inventory-and-inspection.md`](checklists/inventory-and-inspection.md)
before ordering. See [`reference/antennas-and-rf-connectors.md`](reference/antennas-and-rf-connectors.md)
for what each function actually needs.

| Item | Spec | Status | Notes |
|---|---|---|---|
| LoRa antenna | 915 MHz (US), SMA or u.FL pigtail, ~1/4 λ ≈ 82 mm whip | **RECEIVED** ×1 (AIO V2 parcel, 2026-09-14) | Required before any Meshtastic TX. Transmitting into no antenna risks the SX1262 PA. Band/length not yet verified against spec. |
| GPS antenna | Active patch (3.3 V bias) or passive ceramic, u.FL | **RECEIVED** ×1 (AIO V2 parcel, 2026-09-14) | Active + clear sky is the difference between a 60-second and a never fix. Active vs passive not yet confirmed. |
| SDR antenna | Telescopic dipole (~25–1000 MHz usable) plus 1090 MHz whip for ADS-B | **RECEIVED** ×1 whip (AIO V2 parcel, 2026-09-14) | A dedicated 1090 MHz collinear is still the single biggest ADS-B range upgrade — this covers the general-purpose case only. |
| WiFi antenna | — | **RECEIVED** ×3 (AIO V2 parcel, 2026-09-14) | Not previously tracked as a line item; came with the AIO V2's onboard Wi-Fi radio. |
| Bluetooth antenna | — | **RECEIVED** ×2 (AIO V2 parcel, 2026-09-14) | Not previously tracked as a line item; came with the AIO V2's onboard BT radio. |
| u.FL → SMA pigtails | 1.13 mm coax, keep short | **RECEIVED** ×1 u.FL-to-SMA + ×8 u.FL-to-u.FL, various lengths (AIO V2 parcel, 2026-09-14) | u.FL connectors survive limited mating cycles (~30), so the spares are useful; sort the 8 by length once assembly starts. |
| 50 Ω SMA terminator | DC–3 GHz | **OPTIONAL** | Safe dummy load for TX experiments and noise-floor baselines. |

## Thermal and mechanical

| Item | Spec | Status | Notes |
|---|---|---|---|
| Thermal pad for CM4 | 1.0–1.5 mm typical; confirm against shell clearance | **VERIFY** (on tools list) | Measure the gap during trial fit before committing to a thickness. |
| M.2 SSD thermal pad / heatspreader | ≤1 mm | **OPTIONAL** | NVMe under a sealed shell runs hot; a thin pad to the shield is usually enough. |
| PWM fan | 5 V, fits the adapter's fan header | **OPTIONAL** | Only worth it for sustained CPU load; adds noise and current draw. |
| Spare M2/M2.5 screws + standoffs | Match kit hardware | **OPTIONAL** | Small-parts loss is the most common assembly-day stall. |
| Case / plates / mounts | 3D printed | **OPTIONAL** | https://www.printables.com/search/models?q=uconsole |

## Capability add-ons

| Item | Spec | Status | Notes |
|---|---|---|---|
| AC1200 Wi-Fi card | MediaTek MT7921AUN, monitor mode, Wi-Fi 6/6E + BT 5.2, USB-C, 4× IPEX | **RECEIVED & INSTALLED 2026-09-30** — BOM item 7, HackerGadgets [#12253](records/order-and-warranty.md) (shipped 2026-09-21, PFC `SWX001670000180759280`). Verified on Fancy: `wlan1` (`mt7921u`) with monitor mode on 2.4/5/6 GHz, Bluetooth on `hci1` (USB). See [`../hardware/specs/ac1200-mt7921.md`](../hardware/specs/ac1200-mt7921.md). | Now part of the build, not an add-on. Monitor mode is what the wardriving discipline needs; the CM4's onboard Wi-Fi cannot do it reliably. On CM4 it runs at USB 2.0. Its 4 IPEX leads feed `ANT2`/`ANT3` (BT) / `ANT5`/`ANT6` (Wi-Fi). |
| CSI camera module | Ribbon to the adapter's CSI2 header | **OPTIONAL** | Header exists on the HackerGadgets adapter. |
| Second Meshtastic node | Any supported SX1262 device | **OPTIONAL but needed for the LoRa test** | The bring-up checklist's LoRa row requires a second node to TX/RX against. |
| USB-C hub / Ethernet | — | **OPTIONAL** | The RJ45 board already covers wired Ethernet (USB 2.0 speeds on CM4). |

## Decisions still open

- ~~18650s or a LiPo pack~~ — **resolved 2026-09-07: 1S LiPo,** then **re-resolved 2026-09-14: the
  Meshnology 10000 mAh/37 Wh pack** (in hand) replaces the originally selected UDIY-0001L
  (15000 mAh/55.5 Wh), which had a long shipping time. `JP1` gets soldered closed; the silkscreen
  reads "Solder JP1 for disperse current when using JST for Lipo battery pack. Must let it open
  for 18650 batteries."
- **Pack fit and case modification.** Pack and rear-cavity dimensions are both unmeasured. Measure
  each, then decide how much material comes out — case modification is accepted to create the space.
  Constraints that do not bend: never compress a pouch cell to close a cover, keep strain relief on
  the leads and route them clear of screw bosses, and do not seat the pack against the CM4 or the
  NVMe drive. Planning notes: [`../hardware/mechanical.md`](../hardware/mechanical.md).
- **JST pitch and polarity unconfirmed** — PH 2.0 vs XH 2.54 on both the pack and the board, and
  polarity verified with a meter before the first connection.
- **Protection circuit on the pack unconfirmed** — check for a PCM under the tape at the tab end.
- If 18650s: protected vs unprotected. The board has reverse-polarity protection and charge management; protected cells add a layer at the cost of fit (~2–3 mm longer, may not seat in the holder). **Measure the holder before ordering.**
- microSD capacity: 32 GB (cheap, sufficient) vs 64 GB+ (room for captures on the recovery card).
- Whether to keep the stock ClockworkPi battery board as a spare or retire it — see the open question in [`logs/decisions.md`](logs/decisions.md).
