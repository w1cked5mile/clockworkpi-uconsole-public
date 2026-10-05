# Inventory & inspection checklist

Complete on arrival, before assembly. Photograph each item as received — matters for
pre-order/warranty/RMA disputes. Cross-reference [`../bill-of-materials.md`](../bill-of-materials.md)
and [`../accessories.md`](../accessories.md).

Three orders, four parcels: Newark (CM4, **delivered 2026-09-04**), AliExpress/OpenSourceSDRLab
(one order that shipped as **two parcels** — AIO V2 **delivered 2026-09-14**, uConsole mainboard kit
**delivered and unboxed 2026-09-15**), HackerGadgets #11953 (upgrade kit, shipped 2026-09-14,
PFC `SPXCLT003022609140031768`, **delivered 2026-09-23**) and HackerGadgets #12253 (AC1200 Wi-Fi
card, shipped 2026-09-21, PFC `SWX001670000180759280`, **received & installed 2026-09-30**). Track shipping state in
[`../records/order-and-warranty.md`](../records/order-and-warranty.md).

## Received items

| Item | Ordered | Received | Undamaged | Photo | Serial / marking | Notes |
|---|---|---|---|---|---|---|
| ClockworkPi Mainboard v3.14 (uConsole kit) | [x] | [x] 2026-09-15 — photographed and assembled; powered/booted 2026-09-16 | [ ] overview frame only | [x] [photos](../../images/inventory/README.md) | silkscreen reads `CPI 3.14` / `V5` (*photo reading, confirm on the board*); USB input controller `idVendor=1eaf idProduct=0024 iSerial=20230713` (firmware marker, not per-unit) captured at first boot — see [`../../hardware/specs/mainboard-v3.14.md`](../../hardware/specs/mainboard-v3.14.md) | ports visible: micro-HDMI, USB-C, USB-A, TF-CARD, GPIOS FPC, SCREEN FPC, AUDIO, ANTENNA |
| uConsole shell / screen / keyboard (kit) | [x] | [x] 2026-09-15 — photographed and assembled; booted to desktop 2026-09-16 | [ ] overview frame only | [x] [photos](../../images/inventory/README.md) | retail box label: `uConsole Kit` / **`NC-D`** / **`NONE`** · **`FCC ID:2A2YT-UC-CM4B`** · MADE IN CHINA | front shell, perforated rear shell, metal mid-plate, display panel + FPC, keyboard assembly, assembly-guidelines booklet |
| ClockworkPi stock battery board (if included with kit) | — | [x] 2026-09-15 — **included** | [ ] overview frame only | [x] [photos](../../images/inventory/README.md) | `clockwork BATT.` — "For 18650 Rechargeable Li-ion Batteries Only." | **Superseded 2026-09-23 by the HackerGadgets NVMe battery board**, which is now installed with the interim 18650 pair in its holder. Ships with a 2-bay 18650 holder fitted; it powered the build from first boot until then |
| Raspberry Pi CM4 Lite 8GB | [x] | [x] delivered 2026-09-04 | [x] no visible damage | [x] [photos](../../images/inventory/README.md) | `<cm4-serial-redacted>` (Rev 1.1) — read at first boot 2026-09-16 | **part code CM4108000 confirmed on the box label**; FCC ID 2ABCB-RPICM4 · IC 20953-RPICM4 · KCC R-R-P2R-CM4; inspected 2026-09-06 |
| HackerGadgets adapter board | [x] | [x] 2026-09-23 (#11953) — installed; owner reports installed and tested | [ ] no damage inspection | [ ] | `Raspberry Pi CM4/5 Adapter Pro for uConsole`, no unit serial | CM4/CM5 variant. Its port marked "CM5 USB 3.0" takes the AIO V2's Ethernet ribbon (checklist 2.2 passes; corrected 2026-09-25). See [`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md) |
| ClockworkPi CM4→CPI3.14 adapter (uConsole kit) | — | [x] 2026-09-15 — **included** | [ ] overview frame only | [x] [photos](../../images/inventory/README.md) | silkscreen `RPI CM4 to CPI V3.14 Adapter` | **Not anticipated in the BOM** — overlaps the HackerGadgets adapter. Decide which is installed; the HackerGadgets one adds PCIe, USB-C eMMC flash, fan and CSI2 headers. **Superseded 2026-09-23** by the HackerGadgets Adapter Pro; it was the fitted adapter from first boot until then |
| ClockworkPi EXT board (uConsole kit) | — | [x] 2026-09-15 — **included** | [ ] overview frame only | [x] [photos](../../images/inventory/README.md) | silkscreen `clockwork EXT`, `SIM Card`, `AUDIO` | Carries a SIM-card slot and an RF-shielded module; **occupies the same mini-PCIe expansion slot as the AIO V2** — they cannot both be installed. Identify the module before deciding |
| 1S LiPo pouch pack | *(not in BOM as received)* | [x] 2026-09-15 — **one present**, provenance unrecorded | [ ] | [x] [photos](../../images/inventory/README.md) | `Meshnology` · `10000mAh` · `3.7V` · `37Wh` · "Lithium Rechargeable Battery" · CE / RoHS / recycle / WEEE. **No model or part number on the labelled face** | **Not the UDIY-0001L (15000 mAh / 55.5 Wh) recorded as the selected pack.** Red/black lead present but its **terminated end is out of frame — JST pitch and polarity still unconfirmed**, as is PCM presence. **Not fitted** — first boot ran on the interim 18650 pair instead, since the stock board is 18650-only. See Discrepancies |
| Copper-foil thermal pad (uConsole kit) | — | [x] 2026-09-15 — **included** | [ ] | [x] [photos](../../images/inventory/README.md) | | Found in the lower tray under the adapter board. Thickness unmeasured — measure before choosing a CM4 pad ([`../accessories.md`](../accessories.md)) |
| HackerGadgets NVMe battery board | [x] | [x] 2026-09-23 (#11953) — installed; root runs from NVMe (checklists 1.5, 1.6), `JP1` open (1.7) | [ ] no damage inspection | [ ] | `uConsole NVMe Battery Board`, no unit serial | Replaces the stock battery board; holds the interim 18650 pair. (`/dev/nvme*` was absent at first boot 2026-09-16, before it arrived) |
| Dual 18650 **holder** | [x] | [x] 2026-09-23 with #11953 | [ ] | [ ] | | holder only — see cells below. The interim 18650 pair now sits in this holder on the NVMe battery board; the stock battery board's own 2-bay holder is out of use |
| **18650 cells ×2** | **not ordered** | [x] 2026-09-15 — **two present and fitted**; already used to power the first boot 2026-09-16, provenance unrecorded | [ ] | [x] [photos](../../images/inventory/README.md) | green wrap, marked **`9900mAh 3.7V`** / `18650 LI-ION RECHARGEABLE BATTERY`. **No brand, model or batch code** | **Capacity claim is not physically achievable** (18650 tops out ≈3500 mAh) — see [`../logs/known-issues.md`](../logs/known-issues.md). Fitted as an interim pack and already used for first boot (PMIC read 3.886 V); weigh, voltage-match and capacity-test now, before any *further* power-up |
| HackerGadgets RJ45 + USB 3.0 board | [x] | [x] 2026-09-23 (#11953) — installed; USB ports verified (checklist 2.3, QinHeng `1a86:8091` hub) | [ ] no damage inspection | [ ] | | |
| OpenSourceSDRLab / HackerGadgets AIO V2 | [x] | [x] 2026-09-14, laid out 2026-09-15 | [ ] no damage inspection | [x] [photos](../../images/inventory/README.md) | label: **`uConsole AIO extension board V2`** / `Designed by HackerGadgets.com`. GNSS module marked **`GP-02 BDS+GPS`** | Antenna breakout carries **7 u.FL→SMA positions, `ANT1`–`ANT7`**, and the 7 jacks are **standard SMA female** (edge-on close-up: external threads, recessed centre socket). On-board u.FL connectors labelled **`SDR`, `LoRa`, `GPS`**. Rear I/O plate marked `Bias-T` beside a small aperture, with USB-C and RJ45 cutouts |
| CR1220 coin cell (RTC backup) | — | [ ] | [ ] | [ ] | | may not be included; cheap to source |
| M.2 NVMe SSD (2230–2280) | on-hand | [x] from stock, fitted 2026-09-23 | [ ] | [ ] | | **Fitted 2026-09-23: WD PC SN730 256 GB, M.2 2280** (seats on the outermost standoff), root since 2026-09-23. SMART `PASSED`, 21% wear. (`/dev/nvme*` was absent at first boot 2026-09-16, before the NVMe board arrived) |
| microSD card | [x] on-hand | [x] flashed 2026-09-15, read-back verified, **booted 2026-09-16** | [ ] | [ ] | `mmcblk0`, CID `0x3832c348`, 29.5 GB, `uConsole_CM4_v3.1_64bit` — see [`../logs/firmware-versions.md`](../logs/firmware-versions.md) | was tracked as "not ordered" — corrected in `TODO.md`/`accessories.md` |
| GPS antenna (cylindrical puck) | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | included in AIO V2 parcel; fitted to `ANT7` 2026-09-15 |
| WiFi antenna | — | [x] ×3 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | marking `Wi-Fi` confirmed ×3 on the fitted edge-on frame 2026-09-15 |
| Bluetooth antenna | — | [x] ×2 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | marking `Bluetooth` confirmed ×2 on the fitted edge-on frame 2026-09-15 |
| LoRa antenna | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | vendor-marked `LoRa`, confirmed 2026-09-15 — supersedes the withdrawn "wrong band" entry in [`../logs/known-issues.md`](../logs/known-issues.md) |
| SDR whip antenna (telescopic) | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | included in AIO V2 parcel; on the bulkhead SMA |
| 7-position SMA bulkhead breakout (ANT1–ANT7, FPC to AIO board) | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | jacks are **standard SMA female**; trace ANT1–7 to radios before drilling case |
| "Bias-T" panel bracket | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | included in AIO V2 parcel; wiring/purpose not yet confirmed |
| RJ45 faceplate | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | included in AIO V2 parcel |
| u.FL to u.FL cables | — | [x] ×8 (various lengths) | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | **7 distinguishable** in the 2026-09-15 close-up, matching the 7 `ANTn` positions — recount in hand |
| u.FL to SMA cable | — | [x] ×1 | [ ] | [x] [photo](../../images/inventory/20260914-aiov2-parcel-contents.jpg) | included in AIO V2 parcel |
| LiPo battery pack (Meshnology, 10000 mAh/37 Wh) | not tracked as an order | [x] received 2026-09-14 | [ ] | [x] [photo](../../images/inventory/20260914-lipo-meshnology-10000mah.jpg) | **pack of record**, replacing UDIY-0001L (dropped for long shipping time) — see [`../logs/decisions.md`](../logs/decisions.md). **Not fitted.** The NVMe battery board it waited on arrived 2026-09-23; it now waits on `JP1` being soldered closed and the PH2.0 connector's type and polarity being confirmed with a meter. First boot ran on the interim 18650 pair instead (PMIC read 3.886 V — consistent with either 1S source, not specific to this pack) |
| 2× 18650 cells (unbranded, wrapped `9900mAh`) | on-hand, no order record | [x] | [ ] | [x] [photo](../../images/inventory/20260916-assembly-trial-fit-18650.jpg) | **fitted 2026-09-15 as an interim pack**; already used to power the first boot 2026-09-16 — capacity claim not physically achievable, see [`../logs/known-issues.md`](../logs/known-issues.md) |
| Screws / standoffs / small parts | [x] | [x] 2026-09-15 | [ ] | [x] [photos](../../images/inventory/README.md) | | two sealed bags (screws/standoffs, plus a second small-parts bag), orange hex key, 2 speakers, power button, white clip, black strips |
| AC1200 Wi-Fi card | [x] HackerGadgets #12253 | [x] received & installed 2026-09-30 | [x] | [x] [front](../../images/inventory/20260930-ac1200-card-front.jpg) / [back](../../images/inventory/20260930-ac1200-card-back-label.jpg) / [box](../../images/inventory/20260930-ac1200-retail-box.jpg) | MT7921AUN; Wi-Fi MAC `aa:bb:cc:dd:ee:32` (`wlan1`), BT `AA:BB:CC:DD:EE:34` (`hci1`); USB `0e8d:7961`; no printed serial, no FCC ID | BOM item 7, specified (not optional) since 2026-09-16 — see [`../logs/decisions.md`](../logs/decisions.md). Verified on Fancy: monitor mode on 2.4/5/6 GHz, BT on `hci1` (USB) — [`../../hardware/specs/ac1200-mt7921.md`](../../hardware/specs/ac1200-mt7921.md) |

## Counts and fit checks

- [ ] **NVMe length** measured (2230 / 2242 / 2260 / 2280) and matching standoff present.
- [ ] **18650 holder internal length** measured — protected cells run ~2–3 mm longer and may not fit.
- [ ] **u.FL lead count** vs radios needing them (SDR, LoRa, GPS). 7 leads and 7 `ANTn` positions
      seen in the close-up; confirm in hand and confirm which of `SDR` / `LoRa` / `GPS` each serves.
- [x] **Antenna bands confirmed by marking** (2026-09-15, edge-on photo of the fitted set): `LoRa`
      ×1, `Bluetooth` ×2, `Wi-Fi` ×3, plus the GNSS puck and the telescopic SDR whip. *Marking, not
      measurement* — a VNA sweep would confirm, but nothing suggests a mismatch. Note the ≈82 mm
      ¼-wave rule applies to straight radiators; these are loaded stubs and are legitimately
      shorter than that.
      Three stubs are unmarked and **none of the 8 antennas carries a `LoRa` marking** in the
      close-up — do not assume one is the LoRa whip.
- [x] **Connector polarity, board side: the 7 breakout jacks are standard SMA female.** An edge-on
      close-up (2026-09-15) puts all 7 faces square to the camera: external threads on each barrel
      and a **recessed centre socket** — a dark aperture in the white PTFE with no metal standing
      proud of it — unambiguous on three of the best-lit jacks. RP-SMA female would show a centre
      *pin* instead. *Photo reading; a mating test or a meter settles it beyond doubt.*
- [ ] **Connector polarity, antenna side.** Not yet read at adequate resolution. If the jacks are
      SMA female then the 8 antennas must be **SMA male (centre pin)** to mate; any that turn out
      to be RP-SMA male (centre socket) will thread on and never make centre contact. Photograph
      or inspect the antenna connectors before assuming the set matches.
- [ ] **Bias-tee control** on the AIO V2 identified (software vs jumper) — record in
      [`../reference/antennas-and-rf-connectors.md`](../reference/antennas-and-rf-connectors.md).
      The rear I/O plate carries a `Bias-T` silkscreen beside a small aperture, but **a panel
      marking is not a control**: establish whether that aperture is an indicator LED, a switch, or
      neither, and whether the rail is switched in software (`aiov2_ctl`) or by a jumper.
- [ ] **`JP1` located on the NVMe battery board**, its as-shipped state recorded (open/closed), and the
      silkscreen wording confirmed against the transcription in
      [`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md).
- [ ] **JST connector pitch and polarity** measured (PH 2.0 vs XH 2.54) if a LiPo pack is planned.
- [ ] **Rear cavity measured** for a LiPo pack: length × width × thickness.

## Inspection points

- [ ] FPC ribbon cables intact, contacts clean, no creases.
- [ ] u.FL / IPEX connectors and pigtails present and undamaged.
- [ ] No bent pins on the CM4 board-to-board connectors or the adapter.
- [ ] NVMe board: battery connector and reverse-polarity LED present. *(LED seen unlit with the 18650s fitted, 2026-09-23; JST connector not yet inspected.)*
- [x] AIO V2: SMA/u.FL pads labelled — `ANT1`–`ANT7` on the breakout, `SDR` / `LoRa` / `GPS` on
      the extension board. **Damage to the RF cans still unchecked.**
- [ ] Screws / standoffs / small parts bag accounted for.
- [ ] Board revisions recorded — vendor guides differ between revisions. AIO V2 reads
      `uConsole AIO extension board V2`; mainboard reads `CPI 3.14` / `V5`. **EXT board and the
      kit's CM4 adapter still unrecorded.**
- [ ] Serial numbers recorded in [`../records/order-and-warranty.md`](../records/order-and-warranty.md).

## Per-item inspection notes

### Raspberry Pi CM4 Lite 8GB — inspected 2026-09-06

- Part code **CM4108000** on the retail box label. Under Raspberry Pi's scheme that decodes as
  wireless = yes, RAM = 8 GB, eMMC = 000 (Lite) — consistent with the BOM and with the board
  itself, which carries no eMMC package.
- Regulatory markings read from the underside: `FCC ID: 2ABCB-RPICM4`, `IC: 20953-RPICM4`,
  `KCC: R-R-P2R-CM4`, plus UKCA, CE, UL/CSA and WEEE marks. Silkscreen "Raspberry Pi 2021",
  "Made in the UK", "Uses Technology Licensed From Proant AB" (the certified antenna design).
- **u.FL/MHF external antenna connector present** on the topside — see the antenna note in
  [`../../hardware/specs/cm4-lite-8gb.md`](../../hardware/specs/cm4-lite-8gb.md).
- Both 100-pin board-to-board connectors show no visible damage or bent pins **in the
  photographs**; confirm under magnification before seating on the adapter.
- No serial number is printed in human-readable form. Captured at first boot (2026-09-16):
  `cat /proc/cpuinfo | grep Serial` → `<cm4-serial-redacted>`, board revision (device tree)
  `Raspberry Pi Compute Module 4 Rev 1.1` — recorded in
  [`../records/order-and-warranty.md`](../records/order-and-warranty.md) and
  [`../../hardware/specs/cm4-lite-8gb.md`](../../hardware/specs/cm4-lite-8gb.md).

Photographs: [`../../images/inventory/`](../../images/inventory/README.md)

### uConsole kit + AIO V2 — unboxed and laid out 2026-09-15

Overview frames only: the box as opened (two trays) and the full contents laid out. **Nothing was
powered, measured, or inspected under magnification**, and every reading below comes off a
photograph — treat all of it as *unverified* until confirmed with the part in hand.

- **Package contents matched the kit + AIO V2 order at the whole-item level.** Shell halves, metal
  mid-plate, keyboard assembly, display panel, mainboard, EXT board, battery board with 18650
  holder, CM4→CPI3.14 adapter, AIO V2 with antennas, u.FL pigtails, speakers, power button, hex
  key, screw bags and the assembly-guidelines booklet are all present in the frames.
- **Mainboard silkscreen reads `CPI 3.14` and `V5`** — the PCB revision the vendor guides key off.
  Confirm it on the board; `V5` is the number to quote when a runbook step differs by revision.
- **The kit's battery board arrived with its 2-bay 18650 holder fitted**, silkscreened "For 18650
  Rechargeable Li-ion Batteries Only." With the HackerGadgets NVMe battery board (unshipped) also
  carrying a holder, **two 18650 holders are now expected** — one gets retired.
- **A CM4→CPI3.14 adapter shipped with the kit.** The BOM only anticipated the HackerGadgets
  adapter, so this is a second, overlapping part. The HackerGadgets board is the one that exposes
  PCIe (needed for the NVMe battery board), a USB-C eMMC flash port, and fan/CSI2 headers — a
  straight swap to the kit adapter would give up NVMe boot. Decide at assembly, not before.
- **The EXT board and the AIO V2 both target the mainboard's 52-pin mini-PCIe expansion slot**, so
  they are mutually exclusive. The AIO V2 is the build's purpose; the EXT board becomes a spare
  unless testing says otherwise. *Slot conflict inferred from the board form factor in the frames
  and the mainboard's single expansion header — confirm by trial fit.*
- **Antennas and interconnect, recounted from the close-up:** **8 antennas** — 6 stubs, 1
  telescopic whip, and 1 cylindrical screw-base puck (the "black cylinder" of the layout frames) —
  plus **7 u.FL pigtails**, which matches the 7 `ANTn` positions. Only three stubs carry a
  marking *in that frame*: `Wi-Fi` ×2 and `Bluetooth` ×1 — the other three faced away from the
  camera. **Corrected 2026-09-15:** an edge-on photo of the fitted set reads all six, and they are
  `LoRa` ×1, `Bluetooth` ×2, `Wi-Fi` ×3. The intermediate claim here that no antenna was marked
  `LoRa` was a partial count mistaken for a complete one, and it wrongly overturned a correct
  earlier reading. Physical length was never evidence either way: the ≈82 mm ¼-wave figure applies
  to straight radiators, and these are loaded stubs. Connector gender is **resolved on the board
  side only** — the breakout jacks are SMA female
  (see the AIO V2 note below); the antenna connectors themselves have not been read at adequate
  resolution, so whether the set actually mates is still open.
- **AIO V2, from the close-up frame:** the board is labelled **`uConsole AIO extension board V2`
  / `Designed by HackerGadgets.com`** — that is the revision the vendor guides key off, and it
  matches the "V2" in the BOM. It presents a mini-PCIe card edge. Three on-board u.FL connectors
  are labelled **`SDR`, `LoRa`, `GPS`**, and the GNSS module is marked **`GP-02 BDS+GPS`**. The
  antenna breakout is a separate strip carrying **7 u.FL connectors, `ANT1`–`ANT7`**, each feeding
  an edge SMA jack; a short orange FPC marked `5V` at both ends links the two. An edge-on frame of
  the breakout held in hand shows all 7 jack faces square to camera and settles their gender:
  **external threads with a recessed centre socket — standard SMA female**, not RP-SMA. The jack
  count in that frame is 7, corroborating `ANT1`–`ANT7`. The rear I/O plate
  has USB-C and RJ45 cutouts and a **`Bias-T` silkscreen beside a small aperture** — see the
  bias-tee item under *Counts and fit checks*; the marking locates the function, it does not
  establish how the rail is controlled. **No damage inspection was done on any of this.**
- **Not seen in any frame:** CR1220 coin cell, microSD card. The CR1220 remains open
  ([`../accessories.md`](../accessories.md)); the microSD was separately sourced and flashed
  2026-09-15, so it is not a blocker.
- **Retail box SKU label transcribed:** `uConsole Kit` / `NC-D` / `NONE`, a QR code,
  `FCC ID:2A2YT-UC-CM4B`, "MADE IN CHINA", and FCC / CE / RoHS / PC / ABS marks. This is the
  **kit's own** FCC grant (grantee `2A2YT`), separate from the CM4's `2ABCB-RPICM4` — two
  certified assemblies in one device. Look the grant up at
  https://www.fcc.gov/oet/ea/fccid if the filing's internal photos are wanted for comparison.
- **`NC-D` and `NONE` are not decoded.** The order line described the kit as "WiFi only,
  non-core", which makes `NC` = non-core plausible and `NONE` = no compute module supplied
  consistent with what arrived — **but that is inference, not a source.** The QR code on the
  label, or the vendor's variant listing, settles it. Record the decode here once one of those
  does, and do not quote it as fact before then.
- **Packaging:** kraft outer carton marked Keep Dry / Handle With Care / ATTENTION Electrostatic
  Sensitive Devices, enclosing the printed retail box, which holds two vac-formed trays. Both
  cartons are intact in the frames. Keep the retail box with its label until the AliExpress
  dispute window closes — it carries the only SKU and FCC marking on the kit.

Photographs: [`../../images/inventory/`](../../images/inventory/README.md) — the ten `20260916-*`
frames: outer carton, retail box faces, both trays as opened, and the contents laid out.
### AIO V2 parcel — received 2026-09-14

Unboxed as its own parcel, ahead of the uConsole mainboard (still in transit). Contents counted
against the packing list, not yet photographed or fitted:

| Item | Qty |
|---|---|
| GPS antenna (cylindrical puck-style) | 1 |
| WiFi antenna (rubber duck, SMA) | 3 |
| Bluetooth antenna (rubber duck, SMA) | 2 |
| LoRa antenna (rubber duck, SMA) | 1 |
| SDR whip antenna | 1 |
| 7-position SMA bulkhead breakout (`ANT1`–`ANT7`, FPC to AIO board) | 1 |
| AIO V2 board itself ("uConsole AIO extension board V2", HackerGadgets-branded, GP-02 BDS+GPS module, u.FL pads labeled SDR/LoRa/GPS) | 1 |
| "Bias-T" panel bracket | 1 |
| RJ45 faceplate | 1 |
| u.FL to u.FL cable | 8 (various lengths, unsorted) |
| u.FL to SMA cable | 1 |
| Bagged spare SMA bulkhead hardware (nuts/washers) | 1 bag |

Identified from a photo of the unboxed contents (2026-09-14) — see
[`../../hardware/specs/aio-v2.md`](../../hardware/specs/aio-v2.md) for full board detail. What
was initially logged as "antenna board" is the 7-position SMA breakout, and "USB extension board"
is the AIO V2 board itself (its own silkscreen reads "uConsole AIO extension board V2").

Photographs: [`../../images/inventory/20260914-aiov2-parcel-contents.jpg`](../../images/inventory/20260914-aiov2-parcel-contents.jpg)

Not yet done: confirm no shipping damage, trace which of `ANT1`–`ANT7` on the breakout maps to
which radio, confirm the Bias-T bracket's wiring/purpose, sort the 8 u.FL-to-u.FL cables by
length, and count u.FL leads against radios needing them (SDR, LoRa, GPS, Wi-Fi ×3, BT ×2 — this
resolves the "count what arrived" open item in [`../accessories.md`](../accessories.md)'s antenna
table). The AIO V2 board itself has not been inspected under magnification for shipping damage
yet.

### LiPo battery pack — received 2026-09-14

Label reads "Meshnology, 10000 mAh, 3.7 V, 37 Wh, Lithium Rechargeable Battery" — CE/RoHS marked.
This is the **selected pack**, replacing the UDIY-0001L (15000 mAh, 55.5 Wh) decided 2026-09-07 —
a deliberate swap due to that pack's long shipping time (confirmed 2026-09-14, see
[`../logs/decisions.md`](../logs/decisions.md)). Runtime estimates updated in
[`../reference/power-budget.md`](../reference/power-budget.md).

Photographs: [`../../images/inventory/20260914-lipo-meshnology-10000mah.jpg`](../../images/inventory/20260914-lipo-meshnology-10000mah.jpg)

## Cells: safety check before first install

**These were not done before the cells were fitted on 2026-09-15, and the device was powered on and
booted 2026-09-16 without them.** They are now owed before any *further* power-up, and the wrap
marking makes them load-bearing rather than routine — see
[`../logs/known-issues.md`](../logs/known-issues.md).

- [ ] **Each cell weighed.** A genuine 3000–3500 mAh 18650 is ≈45–48 g; substantially lighter means
      less active material. Cheapest check that bears on the `9900mAh` marking.
- [ ] Resting voltage of each cell measured (expect ~3.6–3.8 V storage charge, both within 0.05 V).
- [ ] **Capacity tested** at ≈0.2 C (≈0.6 A) to 2.5 V. This number replaces every runtime estimate
      in [`../reference/power-budget.md`](../reference/power-budget.md).
- [ ] Same make, model, capacity, and age. **Currently unmeetable** — the wrap carries no brand,
      model or batch code, so "matched" cannot be established by inspection, only by measurement.
- [ ] Orientation verified against the holder markings **before** power-up.

## Discrepancies

Record missing/damaged/wrong items here with photos, then open an RMA/vendor ticket:

Nothing here is a vendor fault or an RMA candidate — these are mismatches between what the
photographs of 2026-09-15 show and what this repository recorded. Each is resolved by the owner
supplying provenance, not by a ticket.

- **Two 18650 cells are present**, green wrap, flat-top in appearance. Every record in this repo
  says 18650 cells were *not ordered* and lists them as a blocker. Origin unknown — kit inclusion,
  a separate purchase, or on-hand stock. Make, model, and capacity are not legible in the frame.
  Resolve by identifying them; until then they are unusable, because a parallel 1S pair needs a
  matched, known pair (see *Cells: safety check* above).
- **A 1S LiPo pouch pack labelled `Meshnology 10000mAh 3.7V 37Wh` is present** — read from a clean
  close-up of the label, not inferred: `Meshnology`, `10000mAh`, `3.7V`, `37Wh`, "Lithium
  Rechargeable Battery", CE / RoHS / recycle / WEEE marks, and no model or part number on that
  face. 10 Ah × 3.7 V = 37 Wh, so the label is internally consistent. It replaced
  the **UDIY-0001L, 15000 mAh / 55.5 Wh** chosen 2026-09-07 and is now the pack of record
  ([`logs/decisions.md`](../logs/decisions.md), 2026-09-14).
  [`../reference/power-budget.md`](../reference/power-budget.md) was re-sized to 37 Wh on
  2026-09-23. The pack's dimensions still need measuring for the rear-cavity question in
  [`../../hardware/mechanical.md`](../../hardware/mechanical.md).
- **A CM4→CPI3.14 adapter shipped with the kit**, which the BOM did not anticipate. Not a defect —
  it duplicates the (unshipped) HackerGadgets adapter and forces an install decision. See the
  inspection note above.
- **Board-level damage has not been assessed.** The 2026-09-15 frames are overview shots; FPC
  contacts, u.FL connectors, board-to-board pins, and the AIO V2's RF cans all remain unchecked.
  The *Inspection points* boxes above are still open for that reason, and the RMA window is
  finite — do the per-board pass before assembly day.
