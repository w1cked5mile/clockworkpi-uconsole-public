# Decisions log

Record choices and their rationale so future changes have context.

| Date | Decision | Rationale | Alternatives considered |
|---|---|---|---|
| 2026-10-03 | **GPS-coupled NOAA picker selects by `power / distance²`, not nearest station, from a bundled static NWR table.** 1035-transmitter dataset ([`nwr-stations.json`](../../webdash/app/static/data/nwr-stations.json)) captured once from the NWS `ccl-data.js` and read locally — no runtime internet egress | Nearest-by-distance picks the wrong channel: at grid FM03 the nearest is WNG628 162.500 (Georgetown, 300 W, 33 km) which measured at the noise floor, while the on-air-strongest is KEC95 162.400 (Aynor, 1000 W, 40 km). `power/distance²` (free-space received-power proxy) reproduces the measurement. Owner approved a one-time authoring-time fetch; dashboard stays static at runtime | Nearest-by-distance (wrong here); fetch NWR data live (violates no-egress); owner supplies the file; seed with confirmed stations only |
| 2026-10-03 | **SDR rail is power-only; ADS-B is a chosen application, not an auto-start.** `readsb` is `systemctl-disabled`; turning the SDR rail on no longer starts ADS-B. The webdash SDR view presents three mutually-exclusive applications sharing the single tuner — ADS-B (readsb), broadcast/airband hunt, and listen — with an explicit Start/Stop ADS-B control. The host SDR bridge serializes them via `_busy` and no longer silently restarts readsb after a hunt/listen | Owner request ("don't make adsb automatic after turning on the SDR rail; choose between the different applications"). The old model made ADS-B the implicit tuner owner (it crash-looped until the rail powered it, then grabbed the dongle), which also caused the `rtl_test error -6` confusion. One radio = one application at a time, so an explicit chooser is clearer than silent bracketing | Keep readsb enabled and only change the UI label (rail still implies ADS-B); auto-restart ADS-B after every hunt/listen (silent, surprising) |
| 2026-10-02 | **GPS receiver has one owner — `gpsd` — and consumers read from it; Meshtastic position is pushed in over its API, not by handing it the port.** A host bridge ([`mesh-gps-bridge.py`](../../webdash/host-helpers/mesh-gps-bridge.py)) feeds gpsd's fix to `meshtasticd` via `setFixedPosition`; `position.gps_mode` set to `NOT_PRESENT`. chrony likewise disciplines the clock from gpsd's SHM | Keeps one receiver shared across gpsd/Kismet/PyGPSClient/webdash/chrony and still gives Meshtastic position. meshtasticd's native GPS opens the raw UART and can't share it, so enabling it would evict everything else. `setFixedPosition` (node adopts + rebroadcasts) chosen over `sendPosition` (one-shot, node doesn't adopt — `getMyNodeInfo` stayed empty) | Hand `/dev/serial0` back to `meshtasticd` (the 2026-09-18→21 setup; breaks all other GPS consumers); run two GPS daemons (can't, exclusive port) |
| 2026-09-25 | **Radio roles: the onboard combo chip is for Fancy's own use; recon uses the AC1200.** Onboard `wlan0` (`brcmfmac`) carries the network link and onboard `hci0` serves normal Bluetooth (paired devices). All survey work uses the AC1200 on the USB rail (GPIO23): its Wi-Fi interface (`wlan1` or whatever it comes up as) and its own Bluetooth controller. Until it arrives, the RT5370 on an external USB port is the Wi-Fi test adapter; passive BLE (LAB-21) waits for the AC1200. NetworkManager manages only `brcmfmac` ([`wifi-onboard-only.conf`](../../configs/networkmanager/wifi-onboard-only.conf), deployed) | Owner decision. Isolates the network link from survey work: with the RT5370 plugged in, NetworkManager had joined it to the home network through an auto-created "EvilLair 1" profile, giving two default routes, and a managed adapter probes actively. Passive BLE on `hci0` needs `bluetoothd`'s background scan paused and restarted, which briefly drops paired devices | Survey on onboard `hci0` (verified to work 2026-09-25, but disrupts paired devices); unmanage the RT5370 by driver only (would not cover the AC1200) |
| 2026-09-24 | **Learning-platform D1–D6 adopted as recommended** when the owner asked to build the MVP: learner state in SQLite on Fancy (reverses the `localStorage` choice in `webdash-design.md`); curriculum in `webdash/curriculum/`, compiled to a bundle outside `/static`; soft prerequisite gating (hard only for transmit steps and legal items); endorsements now, certificates later; tracks themed Seamanship / Listening Watch / Master's Ticket; lesson prose in `system-ui` | Recommendations in [`learning-platform-plan.md`](../reference/learning-platform-plan.md) §Decisions, adopted by default. Easy to revisit before content grows | `localStorage` only; curriculum under `/static` |
| 2026-09-24 | **Repository licence: CC BY 4.0 for docs and media, MIT for code and configs** | Owner asked for a licence that covers personal education and does not allow integration into other work without acknowledgement. Both require attribution; CC BY suits prose and photos, MIT suits code (Creative Commons advises against CC for software). Kismet-derived udev rules excluded (GPL-2.0) | CC BY-NC 4.0 (would also bar commercial reuse — not asked for); GPL/CC BY-SA (would force derivatives to share alike — not asked for) |
| 2026-09-24 | **Security gaps found in the learning-platform analysis are accepted** (tailnet `:2501`/`:9443`, unauthenticated `/static`, client-side location hiding, no rate limit) | Owner decision: the owner is the only user and the only audience. Revisit if the device is ever shared | Fix before building the learning platform |
| 2026-09-24 | **Lab outputs are gitignored** (`*.wav`, `*.csv`, `*.raw`, `*.kismet-journal`) | Owner decision; no tracked file matched. Labs still write to `~/labs/` | Rely on labs writing outside the repo |
| 2026-09-24 | **`senior-rf-engineer` agent added to the project team** for technical review of RF content | Owner request; the learning plan needed a check that every exercise fits the hardware | — |
| 2026-09-24 | **Remote shell access is tailnet-only (Tailscale SSH); no LAN `sshd`** | Owner decision. Tailscale SSH already works (verified from `gpu-host`), access is gated by tailnet identity, and nothing listens on :22 on the home LAN. Checklist 2.5's criterion changed from "LAN and tailnet" to tailnet-only. To add LAN SSH later: `sudo apt install openssh-server`, keys only (see `docs/runbooks/headless-access.md` §1) |
| 2026-09-23 | **Meshtastic primary channel is `SCMesh`** (924.125 MHz), with `NCMesh` as secondary; `LongFast` dropped | The primary channel's name sets the frequency slot, and the owner's Heltec V3 and M5Stack run an SCMesh primary. On the old LongFast primary the node heard nothing for hours. It linked with the Heltec (traceroute and acknowledged DMs, both ways) as soon as it moved. Matches the owner's nodes; scmesh.us guidance *unverified* |
| 2026-09-23 | webdash shows GPS position as a Maidenhead grid square by default; precise coordinates only after an explicit reveal, for that page load | Matches the repo rule (location as city or grid only); the dashboard is reachable over the tailnet. Recommendation adopted by default when the owner asked for phase 3 | Show coordinates always |
| 2026-09-23 | webdash embeds only the tar1090 map; Kismet and meshtasticd are linked, not framed | tar1090 is same-origin and proxied; Kismet framing was never confirmed and meshtasticd's web UI doesn't start. Recommendation adopted by default | Keep all frames |
| 2026-09-23 | webdash stations carry themed subtitles ("LoRa · hailing"), plain technical names first | Creative-director concept; plain names stay primary so learners learn the real terms. Easy to drop | No subtitles |
| 2026-09-04 | CM4 Lite 8GB as compute module | Per build plan; boot from microSD/NVMe | CM5, Radxa CM5 |
| 2026-09-04 | NVMe boot as target | Speed/reliability over microSD | microSD-only |
| 2026-09-05 | Documented AIO V2 GPIO map as GPS=27, LoRa=16, SDR=7, USB=23 (BCM) | Sourced from `GPIO_MAP`/`BOOT_DEFAULTS` in aiov2_ctl.py (commit `c21ca74`); SDR rail defaults **on** at boot, unlike the other three | N/A — confirm against hardware once received |
| 2026-09-05 | LoRa region is a **software/Meshtastic config setting**, not a hardware SKU choice | AIO V2's SX1262 covers the full 860–960 MHz band; region (US915/EU868/etc.) is set in Meshtastic's Config → LoRa tab, not by ordering a different board | N/A — closes this as an open question, no purchase decision needed |
| 2026-09-05 | Battery variant confirmed as **Dual 18650 Holder** | HackerGadgets order #11953 (2026-09-03) line item specifies "Raspberry Pi CM4/CM5 / With Dual 18650 Batteries Holder / NONE" — see [`../records/order-and-warranty.md) | 2×21700, LiPo (no holder) — not selected |
| 2026-09-05 | uConsole kit + AIO V2 found: bought together from seller **OpenSourceSDRLab on AliExpress**, order 8214326520279843 (2026-09-02, $326.84 combined) | The AliExpress account uses a Gmail address behind an Apple "Hide My Email" relay, not the `example.com` M365 address — that's why the earlier mailbox search found nothing. See [`../records/order-and-warranty.md) | N/A — closes this open question |
| 2026-09-05 | NVMe SSD sourced from **on-hand stock**, not purchased | Already owned; no new order needed | Buying new — not needed |
| 2026-09-06 | Of six drives pulled from old devices, **four NVMe candidates confirmed usable, two SATA drives rejected** | The NVMe battery board only wires PCIe/NVMe ([`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md)); Samsung PM871 and SanDisk X400 are SATA-only and will not function on it. WD PC SN730, 2× Samsung PM961 and a Toshiba SSD (all 256 GB NVMe) remain as candidates — serials in [`../records/order-and-warranty.md`](../records/order-and-warranty.md) | Buying a new NVMe SSD — not needed, four working candidates on hand |
| 2026-09-06 | microSD sourced from **on-hand stock**, not purchased | Micro Center–branded 32 GB card already owned | Buying new — not needed. *Flashed 2026-09-15* |
| 2026-09-06 | 18650 cells to be **purchased from a known-good maker; the on-hand unmarked pair rejected** | The two on-hand cells are unmarked and labelled 9900 mAh/3.7 V, physically impossible for the form factor (real cells top out ≈3500 mAh); with no identifiable manufacturer their safety and quality cannot be assessed | Using the on-hand unmarked cells — rejected on safety grounds. **Reversed 2026-09-15, see below** |
| 2026-09-06 | Nitecore NL1836HP evaluated as the 18650 candidate — genuine spec confirmed (3600 mAh, protected, 8 A), but **length is the problem, not capacity** | Verified across independent battery retailers rather than marketing copy. Nitecore is reputable, so the mAh figure is trustworthy — separate from whether it physically fits | Generic cells — rejected on trust grounds |
| 2026-09-06 | 18650 **purchase put on hold pending a holder measurement** | ClockworkPi documents a 65–69 mm holder envelope ([uconsole.net](https://uconsole.net/how-to-find-18650-batteries-for-your-uconsole/), not independently confirmed for the third-party HackerGadgets board). NL1836HP is 69.8 mm ±0.3 — at or over that limit, and protected button-tops cluster at 68–70 mm market-wide, so there is no meaningfully shorter protected option | Buying NL1836HP blind — too risky; dropping to an unprotected cell without measuring — premature |
| 2026-09-09 | **Bare-18650 purchase abandoned in favour of a 1S LiPo pack** (Meshnology 1163115, 10000 mAh, PH2.0) | Plugs straight into the NVMe battery board's JST connector, so no cell has to clear the 65–69 mm cavity — the holder-fit blocker is sidestepped rather than solved. Amazon order #114-7650902-4482665, $42.79 for the pair. An earlier UNIKARO 15000 mAh pack (#114-0580414-3922617, $14.99) was cancelled same-day over its shipping estimate | Continuing to wait on a holder measurement — dropped. **This decision assumed the NVMe battery board would arrive before assembly; it did not — see 2026-09-15** |

| 2026-09-07 | System is **1S**; the two 18650 positions are **parallel**, and the board also accepts a **1S LiPo pack on a JST connector** selected by `JP1` | Mainboard PMIC is an AXP228 (single-cell) per `clockwork_Mainboard_V3.14_Schematic.pdf`, corroborated by `aiov2_ctl`'s `axp20x-battery`/`axp22x-ac` sysfs paths; a board photograph shows the JST connector, a 3.85 V 10 Ah pack, and the JP1 silkscreen. Corrects an earlier claim in `power-budget.md` that the pack was 2 × 18650 in series at 7.4 V | 2 × 18650 in parallel (≈22 Wh) vs 1S LiPo (≈38.5 Wh at 10 Ah) — **still open, see below** |

| 2026-09-07 | Battery is a **1S LiPo pack — UDIY-0001L, 15000 mAh, 3.7 V, 55.5 Wh** on the JST connector, `JP1` soldered closed | ≈ 2.5× the energy of two 18650s (~47 Wh usable vs ~18 Wh) with no cell matching; an identical pack is already proven in another build. Buying a second unit rather than transplanting the one in the Pi 5 cyberdeck, so both builds keep a pack | 2 × 18650 in parallel (≈22 Wh) — rejected on energy; pulling the existing pack — rejected to leave the other build intact |
| 2026-09-07 | **Case modification accepted** to fit the pack if needed | Energy is worth the rework; the rear cover is the least structural part of the shell. Rules and the measure-first sequence are in [`../../hardware/mechanical.md`](../../hardware/mechanical.md) | Smaller pack that drops in — rejected, that was the 10 Ah option |

| 2026-09-14 | **Battery pack changed to Meshnology 10000 mAh / 3.7 V / 37 Wh**, replacing the UDIY-0001L (15000 mAh / 55.5 Wh) decided 2026-09-07 | Deliberate swap: the UDIY-0001L had a long shipping time; the Meshnology pack was already on hand. Confirmed by the user 2026-09-14, not a mismatched purchase | UDIY-0001L — rejected on lead time, not spec; still an option for a future capacity upgrade |
| 2026-09-22 | *(corroboration, not a new decision)* The Meshnology swap is confirmed in the order record: Amazon **114-7650902-4482665**, $42.79/pair, ordered 2026-09-09T11:50:32Z, delivered 2026-09-10 | The repeat UNIKARO order was cancelled at 11:46:58Z and this one placed **3 min 34 s later** — the swap was deliberate and same-session, matching the owner's account of rejecting UNIKARO on lead time | N/A — closes battery provenance |

## Open questions

| 2026-09-16 | **AC1200 MT7921AUN is part of the build**, not an optional add-on — BOM item 7 promoted from optional/qty 0–1 to specified/qty 1 | Ordered separately from HackerGadgets as #12253 (2026-09-15, $63.00 delivered). The antenna port mapping depends on its four IPEX leads for `ANT2`/`ANT3`/`ANT5`/`ANT6`, and monitor mode is what the wardriving discipline needs — the CM4's onboard radio cannot do it reliably | N/A — closes the BOM/mapping disagreement. **Card has not arrived**; those four positions stay reserved until it does |
| 2026-09-15 | **Antenna port mapping fixed**: SDR → bulkhead SMA; LoRa → `ANT1`; BT1/BT2 → `ANT2`/`ANT3`; Wi-Fi 1 (CM4 onboard) → `ANT4`; Wi-Fi 2/3 → `ANT5`/`ANT6`; GPS → `ANT7` | The strip is a passive 1:1 fanout, so the numbers carry no function — the mapping is the assignment. SDR stays off the strip because it is the bias-tee port and being physically distinct means it cannot be confused by feel. **GPS at `ANT7` was forced by clearance, not chosen.** Full table and consequences: [`../reference/antennas-and-rf-connectors.md`](../reference/antennas-and-rf-connectors.md) | Only if the strip turns out not to be 1:1 (untraced), or `ANT7` proves a poor GPS position |

### Interim state set by the first assembly, 2026-09-15

These are stand-ins, taken because the HackerGadgets kit has not shipped. None of them closes the
corresponding open question below.

| Date | Interim choice | Why | Re-decide when |
|---|---|---|---|
| 2026-09-15 | **Kit's `RPI CM4 to CPI V3.14 Adapter`** carries the CM4 | The HackerGadgets adapter has not shipped; this is the only adapter on hand. *Inferred from shipping state — the adapter is under the CM4 in the photograph* | The HackerGadgets adapter arrives. It is still the one that exposes PCIe for NVMe boot, which is a standing decision of this build. **Closed 2026-09-23:** the HackerGadgets adapter is installed and the system boots from NVMe |
| 2026-09-15 | **ClockworkPi stock battery board** with the 2-bay 18650 holder | The NVMe battery board has not shipped. Consequence: **`JP1` does not exist in this configuration**, so the JP1 watch-list item is dormant, not satisfied | The NVMe battery board arrives. **Closed 2026-09-23:** the NVMe battery board is installed. `JP1` is now live and must be open while 18650s are fitted (*not yet checked*) |
| 2026-09-15 | **Two `9900mAh`-marked 18650s** as the pack | Interim power until the NVMe board arrives. **The marking is not physically achievable** and the cells are unbranded — see [`known-issues.md`](known-issues.md) | Cells are weighed and capacity-tested, or replaced with a matched named pair |
| 2026-09-15 | **The 2026-09-06 rejection of the on-hand cells is knowingly overridden for interim use** | The JST LiPo pack needs the HackerGadgets NVMe battery board, which shipped 2026-09-14 and has not arrived; the stock board now fitted is 18650-only and has no `JP1`. The choice was the rejected cells or no battery at all. They are in **temporary service only** — the safety objection from 2026-09-06 stands undischarged. **The weigh / voltage-match / capacity-test gate was meant to apply before first power-up, but the device was already booted once on these cells, 2026-09-16, before it was done** — that check is now urgent, not preventive | #11953 arrives: fit the NVMe battery board, swap in the Meshnology pack, and the cells come out |
| 2026-09-15 | **AIO V2 occupies the mini-PCIe slot**, EXT board set aside | The AIO V2 is the build's purpose | Only if a trial fit shows the slot conflict was misread |
| 2026-09-21 | **CM4 antenna: external u.FL, not onboard PCB** | `dtparam=ant2` A/B tested — commented out ~16:28 with the antenna lead off the module's u.FL pad, restored ~16:38 with the lead back on it. No signal-quality numbers from the comparison were captured this session, so this closes the *selection* but not the *performance* half of the open question below | Re-open if link-quality data later favors the onboard antenna |

### Opened 2026-09-15 by the kit unboxing

- **Which CM4 adapter is installed.** *Interim answer as of 2026-09-15: the kit's, by elimination —
  see the table above.* The uConsole kit shipped its own `RPI CM4 to CPI V3.14 Adapter`; the
  HackerGadgets adapter (still unshipped, order #11953) is the one that exposes PCIe, a USB-C eMMC
  flash port, and fan/CSI2 headers. Choosing the kit adapter gives up NVMe boot, which is a
  standing decision of this build (2026-09-04). Default is the HackerGadgets board; revisit only if
  it arrives damaged or does not fit. **2026-09-22 addition, per the device owner:** the kit's
  adapter is an older, CM4-only model that also has no port for the AIO V2's Ethernet ribbon (the
  RJ45 is on the AIO V2; its ribbon plugs into the Adapter Pro's port marked "CM5 USB 3.0" —
  corrected 2026-09-25, first recorded as a ribbon missing from the adapter), which explains the checklist 2.2 failure diagnosed 2026-09-20 as
  a possible mainboard fault — see [`known-issues.md`](known-issues.md). So the interim adapter
  currently costs this build **both** NVMe boot and onboard Ethernet, not NVMe boot alone; both are
  expected to resolve together once #11953 arrives. **Both resolved 2026-09-23:** the system boots from
  NVMe, and Ethernet links at 1 Gbps through the HackerGadgets adapter.
- **Which board occupies the mini-PCIe expansion slot.** The kit's EXT board (SIM slot + shielded
  module) and the AIO V2 both target the mainboard's single 52-pin expansion header, so they are
  mutually exclusive. The AIO V2 is the build's purpose; the EXT board becomes a spare unless a
  trial fit says the conflict is not real. *Conflict inferred from board form factor and the single
  header — confirm by trial fit.*
- **Which battery actually goes in.** *Interim as of 2026-09-15: two unbranded `9900mAh`-marked
  18650s are fitted, pending the NVMe board.* *Updated 2026-09-23: the pack of record is the Meshnology 37 Wh (decided 2026-09-14), and
  the power budget is now sized to it.* The original note follows. The pack of record is a UDIY-0001L (15000 mAh /
  55.5 Wh, to be bought). What is physically on hand is a `Meshnology 10000mAh 3.7V 37Wh` pack — confirmed
  from a clean label close-up, with no model or part number printed on it — plus two 18650 cells,
  none of which appear in any order record. Until provenance is settled, the runtime
  figures in [`../reference/power-budget.md`](../reference/power-budget.md) and the cavity work in
  [`../../hardware/mechanical.md`](../../hardware/mechanical.md) are written against a pack that
  may not be the one installed. Settle provenance first, then re-run the numbers.
- **Which 18650 holder is retired.** Both the kit's battery board and the HackerGadgets NVMe
  battery board carry one. Falls out of the adapter/battery-board decision above.
- ~~**What drives BT1/BT2 and Wi-Fi 2/3**~~ — **closed 2026-09-16: the AC1200 card**, ordered as
  HackerGadgets #12253. Not yet delivered, so the four positions are reserved.
- ~~**Where the LoRa antenna comes from.**~~ — **closed 2026-09-15: the kit supplied one.** An
  edge-on photo of the fitted set reads all six stub markings — `LoRa` ×1, `Bluetooth` ×2,
  `Wi-Fi` ×3 — and the `LoRa` stub is on `ANT1` as mapped. The intermediate claim that no
  LoRa-marked antenna existed came from a frame showing only three of six markings. Confirmed by
  marking, not measurement; a VNA sweep of 902–928 MHz would settle it beyond doubt.


- **How much case modification the pack needs** — unknown until the pack and the rear cavity are
  both measured. Options run from drop-in, through trimming the cover, to printing a replacement
  rear cover.
- **JST pitch** — the Meshnology listing states a **Micro PH 2.0 plug**, so pack-side pitch is
  answered *as a vendor claim*. Board-side pitch and **polarity on both** are still unverified;
  polarity gets a meter before the first connection regardless of what any listing says.
- ~~**Whether the pack carries a protection circuit**~~ — the Meshnology listing states "with
  Protection Board". *Vendor claim, not inspection;* confirm under the tape at the tab end if it
  matters.

- **CM4 antenna selection:** the module has both an onboard PCB antenna and a u.FL connector
  (confirmed present 2026-09-06). `dtparam=ant2` selects the external one, and that's the setting
  in service (see the 2026-09-21 A/B-test row above and
  [`build-log.md`](build-log.md)). Which performs better inside the uConsole shell is still
  unknown — no link-quality numbers were captured during the 2026-09-21 test — so the
  comparison itself remains open even though the selection does not. **Separate finding,
  2026-09-22:** with the external u.FL selection already decided, connectivity was still spotty
  because the lead was plugged into a u.FL connector on the mainboard (`CPI 3.14`) rather than the
  one on the CM4 module itself — moving it to the module's own connector fixed Wi-Fi outright. See
  [`known-issues.md`](known-issues.md)'s 2026-09-22 update to the "Networking 'spotty'" entry.
  This settles that the module's own connector is the correct mating point going forward; it does
  not settle the onboard-vs-external RF comparison above.

- **18650 cells:** ~~assume none shipped~~ — **two cells are on hand as of 2026-09-15**, green wrap, flat-top in appearance, origin unrecorded and make/model/capacity not legible in the photograph. They are unusable until identified: a parallel 1S pair needs a matched, known pair. Protected vs unprotected remains a fit question — measure the holder before trusting them to seat.
- **Redundant battery board:** confirmed 2026-09-15 — the uConsole kit's own battery board arrived, holder fitted; the HackerGadgets NVMe board also carries the battery. Decide which is installed (and whether the other is kept as a spare) at assembly.
- **SDR rail default on CM4 — near-settled 2026-09-16, one empirical check outstanding.** The
  earlier citation of `BOOT_DEFAULTS = {7: True, ...}` as "the boot default" was a misreading of
  `aiov2_ctl.py`: that dict is only consulted by the `--status` state-inference path when
  `pinctrl get` returns an undriven level (`~line 750`). The systemd boot service
  (`aiov2-rails-boot.service`, installed 2026-09-16) actually runs `apply_rails_on_boot()`, which
  reads `_rails_on_boot_from_config()` (`~line 109`) — every rail defaults to **off** when no
  `rails_on_boot` key exists in `/usr/local/share/aiov2_ctl/config.json`, which is this build's
  state (no config file at all). HackerGadgets' own AIO V2 setup guide independently states GPS,
  LoRa, and SDR are "off by default — this is intentional to save battery." Live
  `aiov2_ctl --boot-rails-status` right after install reports all four rails off, matching both.
  **Settled 2026-09-16**: the device was rebooted (to apply the RTC/GPS/LoRa overlays below) and
  a post-reboot `aiov2_ctl --status`/`--boot-rails-status` confirms all four rails (GPS, LoRa,
  SDR, USB) off after a cold boot, matching both the code reading and the vendor doc. See
  [`../logs/build-log.md`](../logs/build-log.md)'s 2026-09-16 "Software bring-up" entry and
  [`../logs/known-issues.md`](../logs/known-issues.md)'s corrected watch-list line.
  `../reference/pinout-gpio.md`, `../../software/aiov2_ctl.md`, and
  `../../hardware/specs/aio-v2.md` all cited the old (wrong) reading and have been corrected.
  **Superseded 2026-09-17, confirmed intentional 2026-09-22**:
  `/usr/local/share/aiov2_ctl/config.json` now carries `"rails_on_boot": {"GPS": true,
  "LORA": true, "SDR": false, "USB": false}` (file mtime 2026-09-17 23:42). `aiov2_ctl
  --boot-rails-status` on 2026-09-22 confirms GPS/LoRa now boot on; SDR/USB still boot off. The
  only code path that writes `rails_on_boot` is the `aiov2_ctl` GUI tray app's per-rail "start on
  boot" checkbox (no CLI equivalent) — this was toggled deliberately, to keep `meshtasticd`/`gpsd`
  fed across reboots without a manual `aiov2_ctl GPS on; aiov2_ctl LORA on` every time, confirmed
  by the user 2026-09-22 (it had simply gone unlogged for 5 days). **This is now the standing
  cold-boot state for this build**: GPS + LoRa on, SDR + USB off. The original "all rails off at
  cold boot" fact still describes the as-shipped/no-config default, not this build's current
  state. See [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md)
  test 0.
- **GPS UART is `/dev/serial0` (`ttyS0`), not `/dev/ttyAMA0`** — every doc/config in this repo
  assumed `/dev/ttyAMA0` for the AIO V2's GNSS module (vendor-guide convention for GPIO14/15).
  Confirmed 2026-09-16, after applying the RTC/GPS/LoRa overlays and rebooting: `aiov2_ctl GPS on`
  followed by `stty -F /dev/serial0 9600; cat /dev/serial0` streams full NMEA plus
  `$GPTXT,...,ANTENNA OK`. `/dev/ttyAMA0` does not exist on this image — `dmesg` shows the CM4's
  onboard Bluetooth (BCM4345C0) bound to the PL011, which registers as `ttyAMA1`, so the
  GPIO14/15 header UART falls back to the mini-UART (`ttyS0`), symlinked as `/dev/serial0`. This
  is standard Raspberry Pi behavior whenever onboard Bluetooth is enabled, not specific to this
  build, and not a fault. `configs/gpsd/gpsd.default`'s `DEVICES=` line would otherwise have
  pointed gpsd at a device that doesn't exist — fixed to use the stable `/dev/serial0` symlink
  rather than a hardcoded tty name, so it survives a future image changing the assignment. All
  other doc references corrected to match (`pinout-gpio.md`, `software/gps.md`,
  `software/aiov2_ctl.md`, `hardware/specs/aio-v2.md`, `docs/runbooks/first-rf-checkout.md`,
  `docs/checklists/module-bringup-tests.md`, `configs/boot/config-cm4.txt`,
  `configs/boot/cmdline-notes.md`, `configs/systemd/README.md`).
- NVMe form factor of the on-hand drive (2230/2242/2260/2280) — confirm it fits the NVMe battery board during inventory/inspection.
- LoRa region for Meshtastic: resolved as a config-time setting (see decision above) — just need to know deployment country/region when configuring, not before ordering.
