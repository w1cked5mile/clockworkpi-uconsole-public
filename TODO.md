# TODO

## Before hardware arrives
- [x] microSD acquired, flashed with `uConsole_CM4_v3.1_64bit` (read-back verified, 2026-09-15),
      and **booted successfully 2026-09-16** (`mmcblk0`, CID `0x3832c348`, 29.5 GB). See
      [`docs/accessories.md`](docs/accessories.md).
- [x] **18650 cells: in interim service, and already powered on.** The two on-hand cells powered the build from the stock battery board until 2026-09-23, and now sit in the HackerGadgets NVMe battery board's holder (`JP1` open, correct for 18650s). They stay *temporarily*, until the Meshnology LiPo swap below. See [`docs/accessories.md`](docs/accessories.md).
- [ ] **Weigh, voltage-match and capacity-test the fitted 18650s now — they already powered on once, unverified.** They are wrapped `9900mAh` — ≈2.8× what an 18650 physically holds — with no brand or batch code, in a parallel 1S pair. Cheapest check is the scale: a real 3000–3500 mAh cell is ≈45–48 g. See [`docs/logs/known-issues.md`](docs/logs/known-issues.md).
- [ ] If the cells fail those checks, replace the interim pack with a matched pair from a named manufacturer rather than waiting on #11953.
- [ ] Swap the interim 18650s for the Meshnology LiPo pack. The NVMe battery board is fitted (2026-09-23); first solder `JP1` **closed** (it is open for the 18650s) and confirm the pack's PH2.0 connector type and polarity with a meter.
- [x] LiPo pack resolved: **Meshnology** 10000 mAh / 37 Wh (on hand) replaces the UDIY-0001L, dropped for a long shipping time. See [`docs/logs/decisions.md`](docs/logs/decisions.md). **Not yet fitted.** The battery board it waited on arrived 2026-09-23; it now waits on `JP1` and the connector check above. The build runs on the interim 18650 pair.
- [x] Locate the Meshnology pack's order record — Amazon #114-7650902-4482665, 2026-09-09, $42.79/pair. The 18650 cells still have none.
- [ ] **Confirm the NVMe battery board's JST connector is PH2.0**, and its polarity, before plugging the Meshnology pack in. A direct JST pack has no holder to prevent a reversed connection.
- [x] **Correct the power budget to the pack of record.** Done 2026-09-23: runtimes re-sized to 37 Wh on the measured ~5.0 W idle; stale 55.5 Wh notes fixed across the repo. Original item: [`docs/reference/power-budget.md`](docs/reference/power-budget.md) and [`docs/accessories.md`](docs/accessories.md) still carry UDIY-0001L figures (15000 mAh / 55.5 Wh); the Meshnology pack is 37 Wh and the interim 18650 pack is unmeasured.
- [ ] Measure the pack and the uConsole rear cavity; decide drop-in vs trim vs printed rear cover ([`hardware/mechanical.md`](hardware/mechanical.md)).
- [ ] Confirm the antenna/pigtail count at inventory; order what's missing. RTC cell: **none on hand or fitted** (2026-09-23) — order one.
- [ ] Pick one of the 4 NVMe candidates (WD PC SN730, 2× Samsung PM961, Toshiba SSD — serials in `docs/records/order-and-warranty.md`) by SMART health, and confirm its M.2 form factor (2230–2280) fits the NVMe battery board — `/dev/nvme*` was absent at first boot 2026-09-16 (booted from microSD instead), so confirm the drive/board is actually seated.
- [ ] **Weigh, voltage-match and capacity-test the fitted 18650s.** Wrapped `9900mAh` — ≈2.8× what an 18650 physically holds — no brand or batch code, parallel 1S pair. Cheapest check is the scale: a real 3000–3500 mAh cell is ≈45–48 g. [`docs/logs/known-issues.md`](docs/logs/known-issues.md)
- [x] **Rewrite [`docs/reference/power-budget.md`](docs/reference/power-budget.md) against 37 Wh** (done 2026-09-23), not 55.5 Wh — every runtime figure there describes a pack that was never bought.
- [ ] Verify the Meshnology pack's **JST polarity with a meter** before first connection. Pitch (PH 2.0) and protection board are vendor-listing claims, not measurements.
- [x] ~~Pull the on-hand NVMe SSD and confirm its M.2 form factor~~ — WD PC SN730 256 GB, **2280**, selected from four candidates and fitted 2026-09-23.
- [x] **Done 2026-09-23: links at 1 Gbps full duplex, checklist 2.2 passes.** Original item: **Retest Ethernet now that the CM4/5 Adapter Pro is in hand** — it has the port (marked "CM5 USB 3.0") for the AIO V2's Ethernet ribbon, which the interim adapter lacks (corrected 2026-09-25). **Installed as of 2026-09-23:** `eth0` is up and the PHY reads over MDIO, but no cable was plugged in at test time, so this is still to do. If the link comes up, the "mainboard hardware fault" diagnosis was wrong.
- [ ] **Record `JP1`'s board location** (photo) before fitting the LiPo. State: **open**, confirmed 2026-09-23.
- [ ] **Record the adapter DIP state** (`1:nRPIBOOT`, `2:EEPROM_nWP`) before flashing; note it in [`docs/logs/firmware-versions.md`](docs/logs/firmware-versions.md).
- [x] ~~Confirm the OPAL drive is not locked~~ — it is the root device and boots, so it is not locked (2026-09-23).
- [x] ~~Paste the output of the "tested" session~~ — captured directly on the device 2026-09-23; checklist 1.5/1.6 closed. See the build log.
- [ ] Prepare imaging PC (Raspberry Pi Imager, usbboot/rpiboot), verify a data USB-C cable.
- [x] Read the vendor guides linked in the runbooks; note any board-revision differences. (device-tree overlays, CM4 vs CM5 differences, and forum gotchas captured in `pinout-gpio.md` and `known-issues.md`)
- [x] Fill exact GPIO pins in `docs/reference/pinout-gpio.md` from the aiov2_ctl source/schematics.

## On arrival
- [x] Photograph the AliExpress kit + AIO V2 as received (2026-09-15) — `images/inventory/`.
- [ ] **Per-board inspection pass** — FPC contacts, u.FL connectors, board-to-board pins, AIO V2 RF cans. Not done; the 2026-09-15 frames are overview shots only, and the AliExpress dispute window is finite.
- [x] Read the **AIO V2 board revision** and the `ANTn` labels — `uConsole AIO extension board V2`; breakout carries `ANT1`–`ANT7`; on-board u.FL marked `SDR` / `LoRa` / `GPS`; GNSS module `GP-02 BDS+GPS`.
- [ ] Recount antennas and u.FL pigtails in hand (photo count: 8 antennas, 7 pigtails).
- [ ] **Check the antenna connectors' gender.** The 7 breakout jacks are standard SMA female (confirmed from the edge-on close-up), so the antennas must be SMA male to mate. Any RP-SMA male antenna will thread on and never make centre contact.
- [x] ~~Identify or buy a LoRa antenna~~ — the kit supplied one; the stub on `ANT1` is vendor-marked `LoRa`. Confirmed by marking 2026-09-15.
- [ ] *Optional:* VNA sweep 902–928 MHz on `ANT1` to confirm the marking by measurement (expect better than 2:1). Not a suspicion — a confirmation step.
- [ ] Establish how the AIO V2 **bias tee** is controlled (software vs jumper) and what the `Bias-T` aperture on the rear I/O plate actually is (LED, switch, neither).
- [ ] Complete the rest of `docs/checklists/inventory-and-inspection.md`; HackerGadgets rows stay open until #11953 ships — mainboard/shell now confirmed powered and booted, but still not visually/damage-inspected.
- [x] Record serials in `docs/records/order-and-warranty.md` — CM4 serial captured 2026-09-16 at first boot; mainboard, AIO V2, and EXT board have no printed per-unit serial (mainboard's USB input-controller identity recorded instead — see `hardware/specs/mainboard-v3.14.md`).
- [ ] Resolve the two new install decisions in `docs/logs/decisions.md`: kit adapter vs HackerGadgets adapter, and EXT board vs AIO V2 for the single mini-PCIe slot.

## Build
- [x] First assembly 2026-09-15: mainboard, CM4 on the kit adapter, AIO V2, stock battery board with interim 18650 pack, screen FPC landed, one SMA through the shell.
- [x] Finish assembly 2026-09-15 — display, keyboard, shell closed, all 8 antennas fitted, `ANT1`–`ANT7` strip installed.
- [x] **Powered on and booted 2026-09-16** — see `docs/logs/build-log.md` "First boot" entry.
- [ ] Confirm the `SCREEN` FPC latch at `J302` is closed and the u.FL leads are landed per the [port mapping](docs/reference/antennas-and-rf-connectors.md).
- [x] `dtparam=ant2` confirmed set in `/boot/firmware/config.txt` at first boot 2026-09-16 — `ANT4`/CM4 external u.FL is live.
- [ ] **Label the *jacks*** — the antennas are self-labelling (`LoRa`, `Bluetooth` ×2, `Wi-Fi` ×3), but the SMA jacks are not. Remove a stub and the port is unidentifiable except via the mapping table. Lower priority than it was.
- [x] Check for DC on the `ANT7` centre pin with `aiov2_ctl GPS on` — decides whether an active GPS antenna can be used there. **Resolved 2026-09-16**: the GNSS module's own status sentence, `$GPTXT,01,01,01,ANTENNA OK`, reports the antenna-bias circuit healthy (these modules report `ANTENNA OK`/`OPEN`/`SHORT` based on detecting proper current draw from the bias voltage they supply) — `ANT7` does carry the DC bias an active antenna needs, and it's working, not open or shorted.
- [ ] Trace the breakout strip: continuity from each `ANTn` centre to its adjacent SMA centre, confirming the 1:1 fanout the mapping assumes.
- [x] Reconcile the BOM with the mapping — resolved: the AC1200 (HackerGadgets #12253) drives BT1/BT2 and Wi-Fi 2/3. BOM item 7 promoted to a specified component.
- [x] ~~Track HackerGadgets #11953~~ — **delivered 2026-09-23**.
- [x] **`JP1` state recorded: open** (owner, 2026-09-23), correct for the 18650s. Solder closed before the JST LiPo goes on; location still to photograph (see above).
- [ ] **Record the adapter DIP switch state** (`1:nRPIBOOT`, `2:EEPROM_nWP`) before flashing; note it in `docs/logs/firmware-versions.md`.
- [x] ~~Confirm the OPAL drive is not locked~~ (WD PC SN730, ex-Lenovo) — boots as root, 2026-09-23.
- [x] ~~Paste the output of whatever "tested" covered~~ — captured 2026-09-23 (build log). CM4 serial reads `<cm4-serial-redacted>`, matching the 2026-09-16 record, so it is the same module.
- [x] ~~Track HackerGadgets #12253 (AC1200)~~ — **received & installed 2026-09-30** (shipped 2026-09-21, PFC `SWX001670000180759280`).
- [x] ~~On AC1200 arrival: land its 4 IPEX leads and confirm monitor mode~~ — **done 2026-09-30.** Verified on Fancy: `wlan1` (`mt7921u`), monitor mode (incl. active monitor) on 2.4/5/6 GHz; Bluetooth `hci1` (USB). See [`hardware/specs/ac1200-mt7921.md`](hardware/specs/ac1200-mt7921.md).
- [x] ~~Verify passive-BLE behaviour on `hci1`~~ — **done 2026-09-30.** `bluetoothd` auto-scans/connects neither (bring-up issued no `LE Set Scan Enable`/`Create Connection`, no bonds); passive scan runs (`Type: Passive 0x00`, no `Command Disallowed`, 304 adverts/16 advertisers). Note: `hcitool lescan --passive` needs `bluetoothd` stopped first (else "Broken pipe"). See [`hardware/specs/ac1200-mt7921.md`](hardware/specs/ac1200-mt7921.md). **All AC1200 checks now closed.**
- [x] Image + first boot per `docs/runbooks/imaging-and-first-boot.md` — booted 2026-09-16, though not the full checklist pass (software-only identifier pull; no visual/damage inspection).
- [x] Install software per `docs/runbooks/software-install.md` — **`aiov2_ctl` installed,
      SDR-rail-verified 2026-09-16, and the RTC/GPS/LoRa overlay + `cmdline.txt` step applied and
      reboot-verified 2026-09-16** (see `docs/logs/build-log.md`). The `--add-apps` companion
      packages are a dead end on this image (not published anywhere reachable — see
      `docs/logs/known-issues.md`); falling back to installing pieces individually (`rtl-sdr`
      done; `meshtastic` **CLI installed 2026-09-16** via a no-`sudo` venv, but it's a client, not
      a radio driver — needs `meshtasticd` to actually talk to the SX1262, which needs a new apt
      repo + `sudo`, still pending; `gpsd` also still pending, same `sudo` blocker).
      **Update 2026-09-23:** every bundle function now has a substitute — `meshtasticd`, `gpsd`,
      `readsb`/`tar1090` all installed and running, and **PyGPSClient installed** (venv + TCP
      NMEA relay from gpsd, connected and showing a 3D fix; see `software/gps.md`). Only open question: whether the plain `sdrpp` is the `-brown` fork.
- [x] **Install Kismet** for passive Wi-Fi/BT survey — **installed and verified 2026-09-21** from
      Kismet's own apt repo (`kismet-core` 2025-09-R1). Found a **Ralink RT5370 USB dongle**
      already attached (`wlan1`, monitor mode confirmed) standing in for the AC1200 (then on
      pre-order, shipped 2026-09-21); group-based capture (no `sudo`) tested end to end. Details:
      [`software/kismet.md`](software/kismet.md), [`docs/logs/build-log.md`](docs/logs/build-log.md).
- [x] **Install `aircrack-ng`** for authorized WPA/WPA2 auditing — **installed and verified
      2026-09-21** from Debian's own repos (`aircrack-ng` 1.7). Own network / written
      authorization only — the one deliberate exception to this repo's passive-only posture,
      made explicit in `CLAUDE.md` and `knowledge/README.md`. Verified `airmon-ng start`/`stop`
      cleanly toggles monitor mode on the same RT5370 (`wlan1`) Kismet uses. Details:
      [`software/aircrack-ng.md`](software/aircrack-ng.md), [`docs/logs/build-log.md`](docs/logs/build-log.md).
- [x] **Enable `gpsd`** — done 2026-09-21, swapped back from `meshtasticd`'s direct serial
      ownership (which meant giving up meshtasticd's GPS-sourced position — LoRa mesh itself is
      unaffected). Confirmed reading the receiver correctly (NMEA flowing, `gpspipe -w` responds).
      **No satellite fix after ~5 minutes** — `SKY` showed zero tracked satellites the whole time;
      reads as no sky view (indoors), not a fault, since the antenna was confirmed healthy
      2026-09-16. **Fix obtained 2026-09-23** (3D, 9 satellites used; checklist 3.3 passes). TTFF cold-start run still open — see the next item. Details:
      [`software/gps.md`](software/gps.md), [`docs/logs/build-log.md`](docs/logs/build-log.md).
- [ ] **Measure time to first fix from a cold start.** The 2026-10-04 fix finding
      ([`knowledge/rf-fundamentals/findings/2026-10-04-first-fix.md`](knowledge/rf-fundamentals/findings/2026-10-04-first-fix.md))
      records 15 SVs / HDOP 0.7 but **no TTFF** — the capture opened already fixed, so there was no
      cold-start reference. Cold-reset the GNSS (power-cycle the GPS rail, or `ubxtool` cold reset),
      start a timer, and record the interval to the first `$GNGGA` with non-zero fix quality; then
      fill in the finding and the build-log entry. Relates to LAB-04 TTFF.
- [x] **`webdash` operator dashboard — planned and built 2026-09-21.** Docker installed
      (`docker.io`/`docker-compose` from Debian's own repos); a Docker app aggregating
      `aiov2_ctl`/Kismet/gpsd/meshtasticd/readsb status behind TOTP-gated login, modeled on
      [`w1cked5mile/CyberDeck`](https://github.com/w1cked5mile/CyberDeck)'s `webdash` but scoped
      down (read-only v1, no device ownership — everything here already runs as its own service).
      Verified end-to-end on this hardware: setup → login → dashboard → `/api/status` →
      `/ws/status`, all five service collectors returning correct real/idle state. App itself
      still binds loopback-only; **exposed tailnet-wide via `tailscale serve` same day** —
      `https://fancy.example-tailnet.ts.net/`, real cert, confirmed tailnet-only (not `funnel`).
      Branded **Fancy Dashboard** (tagline: named for *The Fancy*, Henry Every's frigate, 1695).
      **Redesigned and extended 2026-09-21**: panels grouped into Platform (System, aiov2_ctl
      rails) / Services (Kismet, GPS, ADS-B, Meshtastic) sections, less-crowded panel styling;
      AIOv2 rails are now real toggle switches (`POST /api/aiov2/rail`, past v1's original
      read-only scope); tar1090's ADS-B map is reverse-proxied through the dashboard at
      `/apps/tar1090/` (it has no login of its own — this is a real access-control improvement);
      Kismet and meshtasticd's own web UIs got their own `tailscale serve` mappings (`:2501`,
      `:9443`) and are linked from their panels. Also fixed a real bug found while testing: the
      mesh collector was reconnecting every ~15s and racing the `meshtastic` library's own
      teardown, spamming broken-pipe tracebacks into the logs — now holds one persistent
      connection for the app's lifetime. Plan:
      [`docs/reference/webdash-architecture.md`](docs/reference/webdash-architecture.md).
      Setup/ops: [`software/webdash.md`](software/webdash.md). Code: [`webdash/`](webdash/).
- [x] **Onboard Ethernet (checklist 2.2): PASS 2026-09-23** at 1 Gbps/full. It was never a mainboard fault. Earlier notes: The HackerGadgets adapter
      was installed 2026-09-23, giving the AIO V2's Ethernet ribbon a port to plug into (the RJ45
      is on the AIO V2; corrected 2026-09-25). The first check had no cable plugged in, so
      it is not yet a pass or a fail. *Superseded 2026-09-20 text follows:* ~~looks like a hardware fault on the mainboard,
      not a config issue.~~ Overlay/device-tree/MDIO all check out, forced-mode negotiation still
      shows no link, and a known-good cable/port is confirmed. Next step is a physical inspection
      of the RJ45 jack/solder, or an RMA against the base kit mainboard. See
      [`docs/logs/known-issues.md`](docs/logs/known-issues.md).
- [ ] Run `docs/checklists/module-bringup-tests.md`; log failures. **17 of 22 pass as of 2026-09-24:**
      1.1 (display), 1.3 (audio: speaker tone audible 2026-09-16 with `PCM` raised to 100%; the
      default 80% was inaudible), 1.5/1.6 (NVMe root and link), 1.7 (battery: discharge and charge
      measured, `JP1` open), 2.1 (Wi-Fi), 2.2 (Ethernet, 1 Gbps), 2.3 (USB hub), 2.5 (Tailscale SSH, tailnet-only by design), 3.2/3.3 (GPS rail
      and 3D fix), 3.4/3.5/3.6 (SDR rail, sample integrity, PPM ≈ +1), 3.8/3.9/3.10 (LoRa rail, radio, and
      link with a second node). **Still open (5):** 1.2 (keyboard — needs a person at the device),
      1.4 (thermals — idle ran warm, 62–63 °C, see known-issues), 2.4 (AC1200 — arrived & installed 2026-09-30, monitor mode verified; formal checklist run still pending), 3.1 (RTC — needs a CR1220 cell)
      and 3.7 (ADS-B end to end). Headphone-jack auto-switch (1.3) still
      untried.

- [ ] **Follow-ups from the 2026-09-23 NVMe migration** (see `docs/logs/build-log.md`):
  - [x] Power-cycle with the **microSD removed** to prove NVMe-only boot (runbook step 5). Passed 2026-09-23; `resize` flag also dropped from `cmdline.txt`.
  - [x] Connect a charger and confirm charging on the NVMe battery board (checklist 1.7). Charges at 1.96 A, 2026-09-23. Reverse-polarity LED not lit (owner, 2026-09-23) — checklist 1.7 passes.
  - [x] Confirm which pack is in the NVMe battery board and that `JP1` is **open** for 18650s. 18650 pair, `JP1` open, 2026-09-23.
  - [x] Plug a USB device into the RJ45 + USB3 board to confirm the QinHeng `1a86:8091` hub is its hub. Confirmed 2026-09-23: the device enumerated at 480M behind it.
  - [x] **Install the fixed Kismet udev rules** from `configs/udev/` — installed and verified 2026-09-23.
  - [ ] **Buy and fit the RTC coin cell** — owner confirmed 2026-09-23 that none is fitted (listed as CR1220; *verify the holder size*). Then run checklist 3.1.

## After acceptance
- [x] **GPS time sync + Meshtastic position from gpsd — done 2026-10-02.** chrony disciplines the
      clock from gpsd's SHM refclocks (fixes offline TOTP/TLS; see
      [`configs/chrony/chrony-gps.conf`](configs/chrony/chrony-gps.conf)), and `mesh-gps-bridge`
      feeds the fix to `meshtasticd` so the node shares position — `gpsd` stays sole owner of
      `/dev/serial0`. (Separate from fitting the RTC backup cell, still a build blocker.)
- [ ] `mesh-gps-bridge` follow-ups: optional accuracy gate (skip sends above an HDOP/eph
      threshold — indoors a confident-but-wrong fix got pushed once); confirm peer reception
      outdoors with a second node.
- [x] **EEPROM found updated 2026-09-23: `2026/05/17`, `BOOT_ORDER=0xf416`.** The flash itself was not logged. Original item: **Update the CM4 bootloader EEPROM** — was `2023/01/11`, ~3 years stale (confirmed
      2026-09-20 via `vcgencmd bootloader_version`; see
      [`docs/logs/firmware-versions.md`](docs/logs/firmware-versions.md)). Needs `rpiboot` from a
      second PC with the module in USB boot mode — not an in-place `apt`/OS-side update.
      **Deliberately not done yet.** Relevant to NVMe boot reliability, so worth doing before or
      alongside the NVMe board bring-up once #11953 arrives.
- [x] Back up the baseline image. Done 2026-09-23: file-level backup (partition table, boot and root
      tarballs) on `backup-host:~/backups/fancy/2026-09-23-baseline/`, integrity-tested, checksums in the
      build log.
- [ ] Commit configs to `configs/`; note firmware versions.
- [x] Decide LICENSE. Done 2026-09-24: docs and media CC BY 4.0, code and configs MIT, Kismet-derived
      udev rules excluded ([`LICENSE`](LICENSE)). A distributed webdash image carries GPL-3.0 terms
      via `meshtastic`.
- [ ] Learning platform MVP (built 2026-09-25; merged to `main`, learn-sync timer installed, team
      review applied on `claude/track-a-review-20260925`): run LAB-02, LAB-06 and LAB-08 for real.
- [x] Learning platform, deferred items from the Track A review — done 2026-09-25 on
      `claude/learn-deferred-20260925`: phone bottom sheet, station links and ⓘ, search and keys,
      in-place lab updates with announcements, concept tags, finding steps, LAB-04 TTFF, LAB-03,
      21 glossary terms, gap docs G7/G8/P2/P3/P5/P7.
- [x] Learning platform: build the roadmap modules M9, M10, M11, M12 — done 2026-10-05 (PR #21,
      merged to `main`), verified live in webdash. M12 (land-mobile & maritime, LAB-18), M10 (ham
      bands/APRS/licensing, LAB-13) and M9 (satellite passes, LAB-19) are `ready`; M11 (capstone,
      LAB-20) is built but its 2 h battery lab stays `blocked` on the power gate (interim 18650s
      unverified, JP1 open — flip to `ready` once the pack is verified or the Meshnology pack is
      fitted with JP1 closed). Track B (RF curious) and Track C (Ham-bound) are now complete; M7's
      Bluetooth/5 GHz half is unblocked (AC1200 fitted). All 15 modules pass `learn-compile --check`.
- [ ] Learning platform, still open: M2 (and making it a soft prerequisite of M4/M6); gap doc P6
      (Tailscale); a finding step for LAB-02 (its result belongs in `power-budget.md`); `[` to
      move focus between main area and dock. Optional: `sudo loginctl enable-linger wicked5mile` so the
      timer also runs while nobody is logged in.
- [x] Learning platform: make the ten owner decisions in
      [`learning-platform-plan.md`](docs/reference/learning-platform-plan.md) §Decisions, then build
      from S1 (close the tailnet `:2501`/`:9443` exposure — see known issues).
