# Changelog

All notable changes to this build and its docs. Format loosely follows Keep a Changelog.

## [Unreleased]

### Knowledge base
- **GNSS first-fix recorded as a finding, 2026-10-04.** Logged a 3D fix (gpsd 3.25, NMEA over
  `/dev/serial0`) as [`knowledge/rf-fundamentals/findings/2026-10-04-first-fix.md`](knowledge/rf-fundamentals/findings/2026-10-04-first-fix.md):
  **15 SVs used** (10 GPS + 5 GLONASS), **HDOP 0.7** (PDOP 1.1 / VDOP 0.9), fix quality 1, grid
  **EM94**. The raw gpsd/NMEA dump carried precise coordinates, so it is **not committed** (grid-only
  policy) — kept off-repo at `~/gnss-captures/` on Fancy and referenced in the finding by path +
  sha256. **Time to first fix is left unverified**: the capture opened already fixed, so there was
  no cold-start reference; a cold-reset timed run is tracked in [`TODO.md`](TODO.md) (Build), and
  the session is logged in [`docs/logs/build-log.md`](docs/logs/build-log.md). Also added a
  `knowledge/` row to [`docs/documentation-index.md`](docs/documentation-index.md), which had
  omitted the RF knowledge base from its in-repo references.

### Time sync
- **GPS now disciplines the system clock, 2026-10-02.** Installed `chrony` to replace
  `systemd-timesyncd` (an SNTP client that cannot read a refclock) so the clock is correct offline:
  chrony reads GPS time from gpsd's shared-memory refclocks (NMEA + PPS-when-present), with the
  Debian NTP pool still preferred when online. Fixes offline **TOTP 2FA** failures (30 s-step HMAC
  over the clock) and bad TLS/log timestamps. Verified end to end with a 3D fix — the `NMEA`
  refclock became reachable. Root cause of the bad offline clock confirmed: the PCF85063A RTC logs
  `Power loss detected, invalid time` at boot, i.e. a dead/unseated CR1220 backup cell (replacement
  pending; a warm RTC also speeds GPS acquisition). Config staged at
  [`configs/chrony/chrony-gps.conf`](configs/chrony/chrony-gps.conf); see
  [`software/gps.md`](software/gps.md).

### Meshtastic
- **Node now gets GPS position from gpsd, without giving up the port, 2026-10-02.** New host
  service [`mesh-gps-bridge`](webdash/host-helpers/mesh-gps-bridge.py) reads gpsd and pushes the
  fix into `meshtasticd` over its localhost admin API (`setFixedPosition`), so the node shares
  location on the mesh while messaging — and `gpsd` stays the sole owner of `/dev/serial0`, keeping
  Kismet, PyGPSClient, webdash and the chrony clock discipline working. Set `position.gps_mode` to
  `NOT_PRESENT`; resolves the 2026-09-21 gpsd-*or*-Meshtastic-position tradeoff. Verified end to
  end (live 3D fix adopted as the node's fixed position). Updates are gated to ≥100 m / ≤900 s.
  Precise coordinates go over RF by design but are never committed (grid only). See
  [`software/meshtastic.md`](software/meshtastic.md).

### Hardware
- **AC1200 Wi-Fi card arrived, installed, and verified on Fancy, 2026-09-30.** BOM item 7
  (HackerGadgets #12253) is received — the last outstanding component. Confirmed on-device: it is a
  MediaTek **MT7921AUN** (`lsusb 0e8d:7961`, driver `mt7921u`), enumerates as `wlan1`
  (MAC `aa:bb:cc:dd:ee:32`) with **monitor mode** (incl. active monitor) across **2.4 / 5 / 6 GHz**,
  and brings a Bluetooth controller up as **`hci1` on USB** (BD `AA:BB:CC:DD:EE:34`). The onboard
  `brcmfmac` (`wlan0`) still has no monitor mode (re-confirmed). The interim Ralink RT5370 that held
  `wlan1` has been removed. Inventory photos committed under `images/inventory/` (card front, back
  label silkscreened `BT0`/`BT1`, retail box). Spec rewritten from vendor-claim to verified
  ([`hardware/specs/ac1200-mt7921.md`](hardware/specs/ac1200-mt7921.md)); status flipped in the BOM,
  `accessories.md`, and `order-and-warranty.md`; `kismet_site.conf` source `name=` corrected
  `rt5370` → `mt7921` and `software/kismet.md` updated; `CLAUDE.md` build-state and the "four
  antennas have no radio" blocker closed. **Passive-BLE on `hci1` since verified (2026-09-30):**
  `bluetoothd` issues no scan-enable/auto-connect on bring-up, no bonds, and a passive scan runs
  (`Type: Passive 0x00`, no `Command Disallowed`); `hcitool lescan --passive` needs `bluetoothd`
  stopped first (else "Broken pipe"). **All AC1200 checks are now closed.**

### webdash
- **SDR broadcast/airband hunt + listening, 2026-10-01.** The SDR view gained a receive-only band
  hunt (FM 88–108 MHz / airband 118–137 MHz AM, an `rtl_power` sweep → station list) and live
  listening (`rtl_fm → ffmpeg` MP3 streamed to a browser `<audio>`, with a NOAA weather channel
  picker). A new host bridge [`webdash/host-helpers/sdr-bridge.py`](webdash/host-helpers/sdr-bridge.py)
  runs the tools, brackets readsb (shared tuner), and serializes hunt vs listen; no new sudoers
  (readsb control already granted). Broadcast AM is out of reach (R860 floor ~24 MHz); airband
  replaces it. Verified on real RF. See
  [`docs/reference/webdash-architecture.md`](docs/reference/webdash-architecture.md) and
  [`software/sdr-stack.md`](software/sdr-stack.md).
- **Authorized WPA audit pipeline, 2026-10-01.** The Wi-Fi view gained a BSSID **allowlist**
  (own gear / documented engagement, server-enforced) and an authorized handshake-**capture**
  pipeline (monitor → channel scan → bounded targeted deauth → handshake detection), run by a new
  host `wpa-audit-bridge` that brackets Kismet and is scoped by sudoers to one root capture script.
  Captures stay in gitignored `~/labs/wpa`. Verified against an owned BSSID. In scope under the Cyber
  Verification Program; see [`docs/reference/webdash-architecture.md`](docs/reference/webdash-architecture.md)
  "WPA audit" and [`software/aircrack-ng.md`](software/aircrack-ng.md).
- **WPA crack-offload wired into the dashboard, 2026-10-01.** A captured handshake can be cracked
  with one click: the `wpa-audit-bridge` runs `crack-offload.sh` (SSH to `gpu-host-wsl` →
  `hashcat -m 22000`) as a background job and streams progress → result. Only a `wpa-*.cap` this
  webdash captured is accepted; the recovered PSK stays in the bridge's memory (shown to the session,
  never persisted). Pipeline verified end to end bar a successful crack (needs the GPU host online).
- **Kismet Start/Stop button, 2026-10-01.** The Wi-Fi view can now start and stop Kismet, via a
  user systemd service driven through the `aiov2-bridge` (`systemctl --user`, no root — the capture
  helpers' file caps and `kismet`-group membership suffice). New
  [`webdash/host-helpers/kismet-user.service`](webdash/host-helpers/kismet-user.service); the bridge
  gained `POST /kismet` and `XDG_RUNTIME_DIR`; lingering enabled for `wicked5mile`. Rationale in
  [`docs/reference/webdash-architecture.md`](docs/reference/webdash-architecture.md) "Kismet
  start/stop"; the manual-start note in [`software/kismet.md`](software/kismet.md) and the crash-loop
  entry in [`docs/logs/known-issues.md`](docs/logs/known-issues.md) updated accordingly.
- **Kismet panel authenticates, 2026-10-01.** The status collector now reads Kismet's own
  `kismet_httpd.conf` (read-only bind-mount) and sends Basic auth, so the panel shows live device
  counts instead of "can't connect" whenever Kismet requires a login.
- **Pi under-voltage throttle + 1 h average CPU temp surfaced, 2026-10-01** in the System/Power
  views (`rpi_volt` hwmon alarm via HOSTFS; history-derived mean). Supports the Fancy hang/drop
  under-voltage hypothesis.
- **Webapp UIs open in a new tab, 2026-10-01.** The ADS-B/tar1090 map no longer embeds in an
  `<iframe>`; it opens in its own tab like the Kismet and Meshtastic UI links.

### Knowledge base
- **WiGLE upload publish-boundary learned doc, 2026-10-04.** New
  [`knowledge/wardriving/learned/wigle-upload-and-publish-boundary.md`](knowledge/wardriving/learned/wigle-upload-and-publish-boundary.md)
  captures the reasoning the WiGLE workflow's mechanics (`software/kismet.md` §WiGLE export, the
  build-log, and `wigle-upload.{py,service,timer}`) left implicit: uploading is irreversible
  publishing of BSSID/SSID/coordinates; it is forbidden for near-home household survey and allowed
  for away-from-home drive capture, with the home-radius filter as the mechanical enforcement that
  reconciles the survey runbook's "never upload" rule with the auto-upload path. Also records the
  fail-closed / over-broad-by-default design principles and the WiGLE `file/upload` `transid`
  gotcha. Indexed in the `learned/` README.

### Learning platform
- **First LAB-15 run, 2026-09-25.** Passive 2.4 GHz survey on the RT5370 worked end to end
  ([finding](knowledge/wardriving/findings/2026-09-25-wifi-survey.md)). `kismet_site.conf` adds
  `httpd_bind_address=127.0.0.1`: `tailscale serve` on `:2501` blocked Kismet's web server bind —
  very likely the service crash loop's cause (service start not yet re-tested). Docs corrected:
  Kismet adds a separate `wlan1mon` and leaves it after exit (`sudo iw dev wlan1mon del`); data
  and EAPOL frames verified absent from the packet log; sqlite3 output format verified. LAB-15
  gains a log-based `json_extract` alternative for the `look` step.
- **M7 knowledge: passive Wi-Fi and BLE, 2026-09-25.** New gap docs
  [`ble-passive-observation.md`](knowledge/wardriving/learned/ble-passive-observation.md) (B10:
  advertising channels, passive vs active, address types, and the passive scan method verified on
  Fancy — pause bluetoothd's background scan, `hcitool lescan --passive`, restore) and
  [`80211-identifiers-and-regdom.md`](knowledge/wardriving/learned/80211-identifiers-and-regdom.md)
  (B11: OUI/BSSID/SSID, the locally administered bit, the two blocks of `iw reg get`, DFS, OUI
  false positives). `kismet_site.conf` now sets `kis_log_data_packets=false` and
  `dot11_keep_eapol=false`, drops `dot11_process_body` (not a Kismet option), fixes the channel
  example to 2.4 GHz and forbids a Bluetooth source; re-copy it to `/etc/kismet/`. Fixed: onboard
  Wi-Fi "not dependable" → has no monitor mode; per-network MAC randomisation; 5 GHz to ch 177;
  survey runbook preconditions, foreground Kismet, EM95, restore check; AC1200 spec status and
  vendor claims; `82:6B:F2` flagged as locally administered. Plan M7 row and LAB-21 added.
  `.gitignore` now excludes `*.pcap`, `*.pcapng`, `*.btsnoop`, `*.snoop`.
- **Deferred review items built, 2026-09-25** (branch `claude/learn-deferred-20260925`): LAB-04
  times a first fix after a GPS rail cycle; LAB-04, LAB-06 and LAB-12 end by filing a finding in
  `knowledge/`; new LAB-03 (heat and throttling); quiz items carry concept tags; 21 more glossary
  terms; station tiles link to their module and fact labels get ⓘ; search (`/`) and keys (`r`,
  `n`, `]`); labs update in place and announce passed steps; a bottom sheet on phones. New docs:
  the frequency-slot hash, Part 15 detail, drivers and udev, device tree, Docker, TOTP.
- **Track A team review applied, 2026-09-25** (branch `claude/track-a-review-20260925`). All
  seven agents reviewed Track A. Fixed: two collector bugs that made labs unpassable (GPS
  satellite counts read 0 on most ticks; mesh packets from new nodes weren't counted), an M1
  quiz item that graded the wrong answer (YAML commas; now a compiler lint), LAB-06's dry-run
  command, the claim that Fancy transmits only on Send (meshtasticd beacons and relays on its
  own), the RSSI/no-decode diagnosis, a dangerous uncommented `--ch-set psk` excerpt, and many
  numbers and terms. Engine hardened: runs keep their own lab copy and are isolated from each
  other, safety stops also fire when their reading goes missing and keep their reason, file checks
  resolve symlinks and cap reads, stricter grading. UI: lab steps and controls first, human
  labels, plain names before themed ones, a Continue card, a plain-labels toggle, keyboard and
  race fixes. Tests: 22, now against a temporary database.
- **MVP built, 2026-09-25** (branch `claude/learning-mvp-20260924`): status fields, curriculum
  compiler, `#/learn` pages, SQLite progress, lab engine, graded checks, review queue, notes,
  endorsements, content sync, Owner view, and Track A (M0, M1, M1b, M3, M4, M6; 8 labs; 20
  lessons). New gap docs: `knowledge/rf-fundamentals/learned/gnss-basics.md`,
  `knowledge/mesh-networks/learned/reading-packets.md`,
  `knowledge/ham-radio/learned/maidenhead-grid.md`, `docs/reference/platform-basics/`, and a
  "Reading the power numbers" section in `power-budget.md`. RF review of Track A still pending.
- **Learning platform plan, 2026-09-24** — [`docs/reference/learning-platform-plan.md`](docs/reference/learning-platform-plan.md).
  Proposed, not built. Six-agent analysis: 38 concepts with a dependency graph, 28 gaps, 3 tracks /
  15 modules, 21 labs with automated validation, content model, lab execution, content sync,
  architecture, security, metrics, MVP and build order. Ten owner decisions are listed in it.
- **External references for the gap modules** added to each `knowledge/<discipline>/README.md`
  and to `knowledge/README.md` (platform group). Each link was reachability-checked on 2026-09-24;
  four sites block scripted checks and are marked for a browser check.
- Fixed: dead `linux-sunxi.org/AXP` link in `hardware/datasheets/README.md`; `knowledge/README.md`
  wrongly said `.gitignore` excludes `*.wav`.
- New known issue: `tailscale serve` exposes Kismet `:2501` and meshtasticd `:9443` to the tailnet
  without webdash's login. Accepted by the owner (sole user).
- **`senior-rf-engineer` agent added** to the project team, and its hardware-scope review applied
  to the plan (new §2.0): NOAA APT removed (NOAA-15/18/19 decommissioned 2025), M9 re-based on the
  ISS packet station (145.825 or 437.825 MHz), BLE limited to passive observation (active scanning
  transmits; no sniffer on hand), M12 no longer claims "encrypted" is observable, M7 ready on the
  RT5370 (2.4 GHz), and number fixes (LoRa margin 51 dB not 57, LAB-02/08/09/11 thresholds,
  capstone power estimate). Everything beyond the hardware on hand is marked as an extension that
  names what it needs.
- Knowledge fixes from that review: `db-and-link-budget.md` margin; NOAA status in
  `weather-satellites.md` and `noaa-apt-reception.md`; ISS frequency and whip notes in the ham
  VHF/UHF runbook.

### Repository
- **Mechanical audit cleared to 0 findings, 2026-10-04.** Addressed the five non-blocking audit
  "review" items so `audit.py .` now reports none. Two staged configs gained the missing
  verify/rollback header lines ([`configs/networkmanager/wifi-onboard-only.conf`](configs/networkmanager/wifi-onboard-only.conf)
  rollback; [`configs/profile.d/fancy-banner.sh`](configs/profile.d/fancy-banner.sh) verify +
  rollback). Three curriculum/glossary files that used estimate language now name the live source
  that replaces the figure: M3 DOP lesson (gpsd `SKY`/`TPV` via `gpspipe -w`), M6 module (the
  `readsb`/tar1090 message rate), and the charge-capacity glossary (`upower -i` pack voltage).
  Comment/clarification only — no behaviour or numbers changed; link check and curriculum lint
  both clean.
- **Licence added, 2026-09-24:** docs, knowledge, curriculum and photos CC BY 4.0; code and configs
  MIT; Kismet-derived udev rules excluded ([`LICENSE`](LICENSE), [`LICENSES/`](LICENSES/)).
- `.gitignore` now excludes lab outputs: `*.wav`, `*.csv`, `*.raw`, `*.kismet-journal`.

### Presentation
- **Deck updated after bring-up, 2026-09-23.** The pre-arrival predictions are kept as written,
  and each finding now has an outcome next to it. Also updated: measured power (idle ~5.0 W,
  ~1.5 W above the estimate), a 12-of-22 acceptance-test scorecard, the $667.83 cost ledger, and
  the list of closed and open items. The abstract, README and demo plan match. Demo B is now a
  real option. The deck has not been re-rendered.

### Hardware bring-up
- **Checklist 1.7 passes, 2026-09-23.** `JP1` is open (correct for the 18650s fitted) and the
  reverse-polarity LED is unlit.
- **Baseline backup taken, 2026-09-23.** A file-level backup (partition table, boot and root
  archives, 3.3 GiB) is on `homeserver`, integrity-tested with checksums in the build log. It has not
  been test-restored.
- **Power budget re-sized to the 37 Wh pack, 2026-09-23.** Runtimes now start from the measured
  ~5.0 W idle; terminal work is ~6 h, not ~9 h. Boot-log warnings triaged: the SPI0 pinctrl warning
  is harmless, and fixed Kismet udev rules are staged in `configs/udev/` (not yet installed).
- **NVMe-only boot passes, 2026-09-23.** Booted with the microSD removed; root and boot both on
  NVMe. Dropped the unused `resize` flag from `cmdline.txt`. The RTC power-loss issue is explained:
  no backup cell is fitted. See `docs/logs/build-log.md`.
- **RJ45 + USB3 board USB ports verified, 2026-09-23.** A device plugged into the board
  enumerated at 480M behind the QinHeng `1a86:8091` hub, which confirms the hub is on that board.
  It is powered independently of the AIO `USB` rail. See `docs/logs/build-log.md`.
- **Onboard Ethernet passes, charging confirmed, 2026-09-23.** `eth0` links at 1 Gbps full duplex
  through the AIO V2's Ethernet ribbon, now plugged into the HackerGadgets adapter. That closes checklist 2.2 and the
  "mainboard fault" question: it was the interim adapter. With the charger re-plugged, the pack
  charges at 1.96 A (checklist 1.7; only the reverse-polarity LED check is left). See
  `docs/logs/build-log.md`.
- **HackerGadgets kit installed and root migrated to NVMe, 2026-09-23.** Fitted the adapter, the
  NVMe battery board and the RJ45 + USB3 board (#11953), with the WD PC SN730 as root. Ran the
  storage, NIC, USB and power tests. **Passed:** 1.5/1.6 (NVMe root at Gen2 ×1, 398 MiB/s seq
  read, SMART `PASSED`), 2.3 and 3.5 re-verified. **Measured:** the first real discharge reading,
  ~5.3 W, plus per-rail deltas. **Still open:** Ethernet link (no cable at test time), charging,
  NVMe-only boot with the card removed, and `JP1`/pack confirmation. Also new: an RTC power-loss
  issue and a note about `readsb` holding the SDR. See `docs/logs/build-log.md`.

### Reconciled
- **doc-review agent added, and its first findings fixed, 2026-09-23.** `.claude/agents/doc-review.md`
  checks that documented claims are still true against newer dated evidence and the live device.
  It gives every line from `.claude/scripts/doc-review-candidates.py` a verdict. A hook counts
  active working time and asks for a review every 8 h. Two runs found about 20 stale claims, now
  fixed in 17 files: NVMe/#11953 still "pending", the microSD still "inserted" and "unbought",
  the kit boards "not received", AC1200 "pre-order" or "not purchased", checklist items shown open
  after they passed, the old LongFast channel layout, the JP1 watch-list item, and more.

### Software bring-up
- **Checklist 2.5 passes, tailnet-only by design, 2026-09-24.** Tailscale SSH from `gpu-host`
  works. The owner chose not to run a LAN `sshd`, so the criterion is now tailnet-only. The
  scorecard is 17 of 22.
- **First real reception and SDR PPM measured, 2026-09-24.** NOAA Weather Radio voice heard on
  162.475 MHz. `rtl_test -p` settled at ≈ +1 ppm, so checklist 3.6 passes and the scorecard is 16
  of 22. The runbooks default to `PPM=1`.
- **SDR runbooks runnable as written, 2026-09-23.** `-p <ppm>` was a bash redirect, so every
  `rtl_fm` command in six `knowledge/` docs failed. They now set `PPM=0`, stop `readsb`, use
  `aplay -t raw`, and name the packages they need. The VHF/UHF runbook explains PPM and
  RepeaterBook's "Access" tone.
- **Meshtastic fixed: it was on the wrong frequency, 2026-09-23.** SCMesh and NCMesh had been
  added only as secondary channels, and the primary channel's name sets the frequency. So the
  node sat on LongFast (906.875 MHz) while the owner's nodes were on SCMesh (924.125 MHz). With
  SCMesh made primary, a traceroute to the owner's Heltec V3 went both ways and the first-packet
  alert fired. Direct messages then went both ways with ACKs. Checklists 3.9 and 3.10 pass, so
  the scorecard is now 15 of 22.
- **Meshtastic first-packet alert, 2026-09-23.** The node has received 0 packets in ~4 h, and an
  SDR scan shows almost nothing on the LongFast channel. A one-shot user service,
  `configs/meshtastic/first-packet-alert.*`, sends a desktop notification the first time
  meshtasticd reports a received packet. See [`software/meshtastic.md`](software/meshtastic.md).
- **PyGPSClient connected to gpsd, 2026-09-23.** New `configs/gpsd/gpsd-nmea-relay.py` serves
  gpsd's NMEA on TCP `127.0.0.1:50010`, PyGPSClient's default socket. PyGPSClient connected and
  showed a 3D fix with 11 satellites used.
- **Checklist 3.3 (GPS fix) passes, 2026-09-23.** gpsd held a steady 3D fix with 9 of 12
  satellites used (GPS + GLONASS), HDOP 0.9, grid EM95. Time to first fix was not measured. The
  scorecard is now 13 of 22.
- **PyGPSClient installed, 2026-09-23.** v1.7.6 from PyPI in `~/.venvs/pygpsclient`, which
  replaces the unpublished `--add-apps` package. It has no gpsd client, so a wrapper
  (`pygpsclient-gpsd`) serves gpsd's NMEA on TCP `127.0.0.1:50010` through
  `configs/gpsd/gpsd-nmea-relay.py`. A menu entry was added. **Corrected the same day:** the
  first version relayed over UDP with `gps2udp`, which PyGPSClient can't receive. See [`software/gps.md`](software/gps.md#pygpsclient).
- **webdash can send and receive Meshtastic text messages, 2026-09-23.** The Meshtastic panel now
  has a message log and a send box that use `meshtasticd`'s TCP API, the way CyberDeck's webdash
  does. It replaces the broken web UI for messaging. Over-the-air send and receive are unverified.
- **webdash redesign proposed, 2026-09-23.** Six new agents (design planning, creative, web UI,
  syllabus, tutor, guided learning) reviewed webdash. The result is
  [`docs/reference/webdash-design.md`](docs/reference/webdash-design.md): one station per radio, a
  learning layer with explainers, a 12-module syllabus and missions checked by live data, and an
  8-phase build plan. Not built. The review's four messaging bugs are fixed.
- **webdash redesign phase 3 built, 2026-09-23.** An overview of six station tiles with their rail
  switches fits the uConsole screen with no scrolling. Each station has its own detail view, and a
  status strip stays at the top. GPS shows a grid square unless revealed. Only the ADS-B map is
  still embedded.
- **webdash redesign phases 1–2 built, 2026-09-23.** Status is now a word and glyph, not colour
  alone, and reflects the rail. The dead Meshtastic frame is gone. Rail switches work from the
  keyboard. One shared collection loop replaces per-client polling. `/api/history` keeps 2 h of
  vitals.
- **`aircrack-ng` installed, 2026-09-21.** First tool on this build capable of active Wi-Fi
  actions (deauth, handshake capture, cracking) — the boundary for that is now explicit rather
  than implied: own network or documented written authorization, nothing else, spelled out in
  `CLAUDE.md`, `knowledge/README.md`, and `knowledge/wardriving/README.md`. Verified monitor mode
  toggles cleanly on the same RT5370 Kismet already uses. New `software/aircrack-ng.md`; added
  capture-file extensions to `.gitignore`. See `docs/logs/build-log.md`.
- **`webdash` redesigned and extended, 2026-09-21.** Panels grouped by use case (Platform:
  System + aiov2_ctl rails; Services: Kismet/GPS/ADS-B/Meshtastic) with less-crowded styling.
  AIOv2 rails are now toggle switches (`POST /api/aiov2/rail`) — real hardware control, past the
  original v1 read-only scope, verified end-to-end. tar1090's ADS-B map is reverse-proxied
  through the app at `/apps/tar1090/`; Kismet and meshtasticd's web UI get their own `tailscale
  serve` mappings and are linked instead (both assume they own the URL root). Fixed a real bug
  found while testing: the mesh collector's per-poll reconnect raced the `meshtastic` library's
  teardown, spamming broken-pipe tracebacks — now holds one persistent connection. See
  `docs/logs/build-log.md`.
- **`webdash` exposed tailnet-wide via `tailscale serve`, 2026-09-21.** Reachable at
  `https://fancy.example-tailnet.ts.net/` with a real Tailscale-issued cert; confirmed
  tailnet-only, not `funnel`. The app's own Uvicorn bind stays loopback-only — `tailscale serve`
  does the proxying. See `docs/logs/build-log.md`.
- **`webdash` operator dashboard planned and built, 2026-09-21.** Docker-based, TOTP-gated
  dashboard aggregating `aiov2_ctl`/Kismet/gpsd/meshtasticd/readsb status, modeled on a sibling
  build's dashboard architecture (`w1cked5mile/CyberDeck`) but scoped to aggregation rather than
  device ownership, since this build's peripherals already run as independent services. Installed
  Docker from Debian's own repos; verified end-to-end (setup → login → dashboard →
  `/api/status`/`/ws/status`) against every real service on this hardware. `aiov2_ctl --status`
  turned out to need a small host-side bridge service rather than a container bind-mount (GPIO
  device access); found and fixed a WebSocket close-code bug during testing. New
  `docs/reference/webdash-architecture.md`, `software/webdash.md`, `webdash/`. See
  `docs/logs/build-log.md`.
- **`gpsd` re-enabled, swapped back from `meshtasticd`, 2026-09-21.** So Kismet and other tools
  can share the GPS receiver again; `meshtasticd`'s GPS config disabled (kept, not deleted) and
  it was restarted to release `/dev/serial0` — LoRa mesh itself is unaffected, only its
  GPS-sourced position stopped. `gpsd` confirmed reading the receiver correctly, but **no
  satellite fix after ~5 minutes** (zero tracked satellites throughout) — reads as no sky view
  (indoors), not a hardware fault. `software/gps.md` and `software/meshtastic.md` updated with
  the current owner and revert steps. See `docs/logs/build-log.md`.
- **Kismet installed and verified, 2026-09-21.** From Kismet's own apt repo (not in Debian's
  default repos); group-based (no-`sudo`) capture confirmed working end to end. Found a Ralink
  RT5370 USB dongle already attached and monitor-capable, standing in for the still-pre-order
  AC1200 — `configs/kismet/kismet_site.conf` corrected to match (its `log_prefix` also still named
  a nonexistent `pi` user). New `software/kismet.md`; runbook and config-rationale docs updated to
  match. See `docs/logs/build-log.md`.
- **RTC/GPS/LoRa overlays applied and reboot-verified, 2026-09-16.** RTC (`pcf85063a`) enumerates
  on I2C with system/RTC time in sync; GPS rail streams full NMEA plus `ANTENNA OK` (also answers
  the `ANT7` DC-bias TODO item); LoRa rail exposes `spidev1.0`. Module bring-up checklist items
  0 (baseline rail state), 3.2, and 3.8 pass; 3.1 partially confirmed. Settles the SDR-boot-default
  question from "near-settled" to settled — see `docs/logs/decisions.md`.
- **Corrected the GPS device path repo-wide: `/dev/serial0` (`ttyS0`), not `/dev/ttyAMA0`.** Every
  doc and config assumed `/dev/ttyAMA0`; the CM4's onboard Bluetooth actually holds the full PL011
  (registered as `ttyAMA1`), so the GPIO14/15 header UART is the mini-UART. Fixed in
  `configs/gpsd/gpsd.default` (would otherwise have pointed gpsd at a non-existent device),
  `docs/reference/pinout-gpio.md`, `software/gps.md`, `software/aiov2_ctl.md`,
  `hardware/specs/aio-v2.md`, `docs/runbooks/first-rf-checkout.md`,
  `docs/checklists/module-bringup-tests.md`, `drivers/README.md`, `presentation/uconsole-build-talk.md`,
  and the `configs/boot`/`configs/systemd` runbook notes. See `docs/logs/decisions.md`.
- Logged a benign `rtl_test -t` warning (`[R82XX] PLL not locked!`) so it isn't mistaken for a
  regression later — plain `rtl_test` streams samples normally. See `docs/logs/known-issues.md`.
- **`aiov2_ctl` installed and the SDR rail verified end-to-end, 2026-09-16** — first hands-on
  software work on the booted device. Module bring-up checklist items 2.3, 3.4, and 3.5 pass.
- **Corrected the SDR-rail boot-default claim across three files** (`docs/reference/pinout-gpio.md`,
  `software/aiov2_ctl.md`, `hardware/specs/aio-v2.md`): SDR is off by default at boot on this
  build, not on — the earlier claim misread `aiov2_ctl.py`'s `BOOT_DEFAULTS` as the boot-apply
  default when it's actually only a `--status` state-inference fallback. See `docs/logs/decisions.md`.
- **Corrected a known-issues entry**: `hackergadgets-uconsole-aio-board` and its companion
  packages fail because they aren't published in any repo reachable from this image — not because
  of a dpkg error as previously guessed.
- **Fixed an unrelated, pre-existing `apt`/dpkg breakage** (`initramfs-tools`/`rpd-plym-splash`
  half-configured) hit while installing the runbook's dependencies; not a boot risk, but would
  have blocked further installs.

### Reconciled
- **Two parallel documentation lines merged, 2026-09-16.** The imaging line (microSD flashed
  2026-09-15) and the assembly/inventory line (unboxing, assembly, antennas — physically done
  2026-09-15, documented by a session that ran 2026-09-16) were written without knowledge of each
  other and contradicted each other in three places, all now settled against the newer evidence:
  the microSD is **bought and flashed**, not "unbought"; the AliExpress mainboard parcel is
  **delivered**, not "in transit"; and #11953 is **shipped** (PFC `SPXCLT003022609140031768`), not
  "unshipped". The stale claims in the build-log entries are corrected in place with a bracketed
  note rather than rewritten, since they record what was believed at the time.
- **Assembly date corrected: 2026-09-15, not 2026-09-16.** Confirmed directly by the builder. The
  assembly/inventory session that wrote the unboxing, first-assembly, and shell-closed/antenna
  entries ran on 2026-09-16 and used its own run-date throughout — the `20260916-*` image
  filenames and the earlier date on these entries reflect when the files were supplied to that
  session, not when the physical work happened. Corrected across `build-log.md`, `decisions.md`,
  `known-issues.md`, `TODO.md`, `CLAUDE.md`, the inventory checklist, and
  `docs/reference/antennas-and-rf-connectors.md`; `images/inventory/README.md` carries an explicit
  note about the filename/event-date mismatch. Research-only entries dated 2026-09-16 (the AC1200
  mailbox sweep, the BOM revision it drove) are left as-is — only physical assembly events moved.
- **The interim 18650 pack is interim on purpose.** The fitted cells are in **temporary service
  until the NVMe battery board arrives with #11953** — that board is what the Meshnology JST LiPo
  pack needs, and the stock board now fitted is 18650-only. Earlier notes framed the cells as
  abandoned in favour of the LiPo; that was the plan, not the current state.
- **Card number removed** from the #12253 invoice record.

### Added
- **HackerGadgets #11953 delivered 2026-09-23** and the on-hand NVMe fitted. Five photographs, BOM
  rev E, order record updated to delivered with the drive's serial and part numbers.
- **NVMe SSD identified:** WD PC SN730, 256 GB, **M.2 2280**, **OPAL** self-encrypting,
  ex-Lenovo channel part, FW `11130101`, manufactured 19DEC2019. Closes the form-factor question
  open since the BOM was written — 2280 seats on the board's outermost standoff.
- **Four board silkscreen findings new to the repo**, in `hardware/specs/upgrade-kit-boards.md`:
  the adapter's RTC-battery JST is **CM5-only** and must not be connected on this CM4 build; the
  DIP switch is `1:nRPIBOOT` / `2:EEPROM_nWP`; **`GPIO4` is routed to an IPEX `RPITX` connector**
  instead of to the mainboard, with a 0Ω link position to restore normal routing; and the battery
  board has an optional `R14`/`J6` manual battery on/off modification that must not be applied
  speculatively.

### Security
- **The SSD label frame carries the drive's factory revert code and it is not transcribed
  anywhere.** For an OPAL drive that code authorises a cryptographic-erase revert, it is a reset
  credential under the repo's no-secrets rule, and it cannot be regenerated — the printed label is
  the only copy. The image README says to read it off the physical drive and not to re-upload the
  full-resolution original.

### Still open
- **What "tested" covered is unrecorded** — no command output was supplied, so no bring-up row is
  closed and the CM4 serial owed since 2026-09-06 is still owed. `CLAUDE.md` now says "no device
  behaviour is documented" rather than "nothing has been powered on", which is the honest state.
- **`JP1` has still never been seen.** The battery-mode jumper the assembly runbook depends on is
  not legible in any frame, and the board is now installed.
- **The OPAL drive may be locked** from its previous host; that has to be settled before imaging.


### Changed
- **BOM revision D.** Row 7 (AC1200) now reads "Ordered — HackerGadgets #12253, $63.00 incl.
  shipping" and records the 2026-09-21 despatch (PFC `SWX001670000180759280`); its quantity was
  already 1. The `4× IPEX antenna` figure is kept but marked as a vendor-listing count to confirm
  against the card on arrival.
- **New Notes subsection, "Actual orders placed"** — every purchase bearing on the build in date
  order, including the cancelled one, with shipping state and the gaps named.
- **Battery rows rebuilt (6a–6d).** The single "UDIY-0001L / 2 × 18650" row became: **6a**
  Meshnology 10000 mAh 1S LiPo (the pack of record), **6b** the unbranded `9900mAh` 18650s actually
  fitted, **6c** the superseded UNIKARO 15000 mAh with its cancelled repeat order, **6d** microSD.
  Row 6 (the holder) now states the parallel-18650-or-JST-LiPo choice and points at 6a–6c.

### Resolved
- **Meshnology order fully sourced** once the order number was supplied: Amazon
  **114-7650902-4482665**, placed 2026-09-09, **$42.79**, shipped 2026-09-10, **delivered
  2026-09-10**. New invoice record. It was placed **3 min 34 s after** the UNIKARO repeat order was
  cancelled that morning — a deliberate same-session swap, which is why the 2026-09-07 "buy a second
  15000 mAh pack" decision never took effect. The order's own Amazon subject line is "Ordered 1
  item: Toys & Games", which is why product-name searches missed it.
- **Battery provenance**, open since 2026-09-16. A mailbox sweep found the Meshnology packs on
  Amazon — `2pcs 3.7V 10000mAh … 1163115 1S LiPo … with Protection Board … Micro PH2.0 Plug`,
  delivered on or before 2026-09-11 — and a **UNIKARO 15000 mAh repeat order cancelled 2026-09-09**,
  placed just after the 2026-09-07 decision to buy a second 15000 mAh pack. The UNIKARO is probably
  what earlier notes called "UDIY-0001L" (*identity inferred from matching specs, not confirmed*).
- **Two long-open battery questions answered as vendor claims:** the listing states a protection
  board and a **PH 2.0** plug. Board-side pitch and polarity on both ends are still unverified, and
  polarity still gets a meter before first connection.

### Still wrong, now flagged
- **`power-budget.md` is stale against every option.** Its figures assume 55.5 Wh; the pack of
  record is 37 Wh and what is fitted is unmeasured. Not rewritten here — that is its own edit.
- **The fitted 18650s appear in no order record**, so their provenance remains open even though the
  LiPo question is closed.
- ~~The Meshnology order number, date and price were not captured.~~ **Closed 2026-09-22** — see
  *Resolved* above.


### Added
- **Mechanical assembly complete, 2026-09-16.** Shell closed with display and keyboard installed
- **First boot, 2026-09-16.** After assembly (below), the device was powered on and booted to the
  uConsole desktop — on the interim 18650 pair fitted to the stock battery board, not the Meshnology
  LiPo pack, which is still unfitted. Captured every hardware identifier the running system exposes:
  CM4 serial `<cm4-serial-redacted>` (Rev 1.1), its Wi-Fi/Ethernet MACs, the mainboard's USB
  input-controller identity, and the in-use microSD's CID serial. Closes the "read at first boot"
  serial placeholder and the "not ordered" microSD status (both now stale, corrected across
  `TODO.md` and `docs/accessories.md`). Confirms two previously-unverified claims on real hardware:
  the PMIC reads 3.886 V (1S, not 2S), and `dtparam=ant2` selects the external u.FL antenna. No
  `/dev/nvme*` detected this boot, consistent with the NVMe battery board not being installed yet.
  **Safety note:** the interim 18650 cells (see below) powered on before being weighed,
  voltage-matched, or capacity-tested — that check is now owed retroactively, before any further
  power-up, not merely as a pre-condition.
- **Mechanical assembly complete, 2026-09-15.** Shell closed with display and keyboard installed
  and all 8 antennas fitted — the 7-way `ANT1`–`ANT7` breakout strip (absent from the earlier
  assembly frame) plus the telescopic whip on the SDR bulkhead. Powered on and booted the next day
  (above).
- **Port mapping corroborated by the physical build:** the two `Bluetooth`-marked stubs landed on
  `ANT2`/`ANT3` and the GNSS puck on `ANT7`, exactly as specified. Independent evidence the mapping
  was applied as written.

### Corrected
- **Retracted: the claim that `ANT1` had a wrong-band antenna.** An edge-on photograph of the
  fitted set reads all six stub markings — **`LoRa` ×1, `Bluetooth` ×2, `Wi-Fi` ×3** — in exactly
  the mapped order. `ANT1` carries a vendor-marked `LoRa` antenna supplied with the kit, and the
  open question about sourcing one is closed.
  Two mistakes produced the false alarm, both now written into the records they polluted: an
  inventory close-up showed only **three of six** markings, the others facing away, and that
  partial count was written up as a complete one — overturning a correct earlier reading of a
  dimmer frame in the process. The supporting length argument was independently unsound: "shorter
  than an 82 mm ¼-wave, therefore not 915 MHz" holds only for a **straight** radiator, and these
  are **loaded stubs**, routinely half or less of the free-space ¼-wave at their design frequency.
  The `known-issues.md` entry is struck through rather than deleted, with the reasoning error
  spelled out.
- What survives unchanged: LoRa TX into an empty or badly matched port can damage the SX1262 PA, so
  an antenna stays on `ANT1` whenever the rail is enabled.

### Noted
- **An antenna fitted is not a radio connected.** `ANT2`/`ANT3`/`ANT5`/`ANT6` now have antennas on
  them but the AC1200 that feeds all four is still on pre-order. The mapping table says so per row.
- **Shell closed before first boot**, against the assembly runbook's advice. `TF` and `ON/OFF` are
  externally accessible so a microSD does not require reopening; `rpiboot` re-flashing would.
- **Exterior labelling is partial.** Every stub is labelled by function, so the assembled device is
  self-documenting; the SMA **jacks** are not, so a removed antenna leaves an unidentifiable port
  and the mapping table is the only record.


### Added
- **First assembly recorded, 2026-09-15.** Mainboard in the shell, CM4 on the kit's
  `RPI CM4 to CPI V3.14 Adapter`, AIO V2 in the mini-PCIe slot, ClockworkPi's stock battery board
  with an interim 2×18650 pack, `SCREEN` FPC landed at `J302`, one SMA bulkhead through the shell.
  **Nothing powered on.** `decisions.md` gains an interim-state table separating these stand-ins
  from the open questions they do not close; `CLAUDE.md`'s build state, the build log and TODO
  follow.

### Added
- **AC1200 promoted to a build component.** BOM item 7 moves from optional / qty 0–1 to specified /
  qty 1: the card was ordered from HackerGadgets as **#12253** (2026-09-15, $45.00 + $18.00 EURPOST
  = $63.00), and the antenna port mapping depends on its four IPEX leads. New invoice record, and
  `accessories.md` reclassified from OPTIONAL to ORDERED. This closes the BOM/mapping disagreement
  logged in the previous batch.
- **Order #11953 shipped 2026-09-14** — PFC tracking `SPXCLT003022609140031768`. Found in the same
  mailbox sweep; the repo had carried "not yet shipped" since 2026-09-05. That parcel holds the
  NVMe battery board, adapter and RJ45 board, so its arrival re-opens the adapter, battery-board
  and `JP1` decisions.

### Noted
- **The AC1200 has not arrived.** #12253 is a pre-order with no ship notice, so `ANT2`/`ANT3`/
  `ANT5`/`ANT6` are **reserved, not populated** — the port mapping describes the finished state,
  and only `ANT1`, `ANT4`, `ANT7` and the SDR bulkhead have a radio behind them today.
- **Order #11953's product title names AC1200 WiFi but its variant ends in `NONE`** — that is the
  card option, so no card ships with the upgrade kit. Recorded in both invoice files and the BOM
  because the two orders are easy to conflate.
- **Orders are split across two mailboxes.** #12253 is in Gmail; #11953, Newark and AliExpress are
  in the `example.com` mailbox. The order record now says to search both.

### Added
- **Antenna port mapping recorded** in `docs/reference/antennas-and-rf-connectors.md`: SDR on the
  bulkhead SMA, LoRa `ANT1`, BT1/BT2 `ANT2`/`ANT3`, Wi-Fi 1 (CM4 onboard) `ANT4`, Wi-Fi 2/3
  `ANT5`/`ANT6`, GPS `ANT7`. The strip is a passive 1:1 fanout, so the numbers carry no function of
  their own and the table *is* the assignment. The assembly runbook's single line about u.FL leads
  becomes a full routing procedure — handling, bend radius, keep-out zones, dry-fit, and exterior
  labelling.
- Three consequences of the mapping written up where they will be read: `ANT4` is inert until
  `dtparam=ant2` is set and fails silently; `ANT7` carries no bias because the bias tee is on the
  SDR path, so an active GPS antenna has no supply there; `ANT1` is the only transmitting port and
  currently has no 915 MHz antenna to attach.
- **BOM/mapping disagreement logged:** the mapping allocates five Wi-Fi and Bluetooth positions
  beyond the CM4's own, while the BOM lists the 4-antenna AC1200 as optional and not ordered.

### Safety
- **The fitted 18650 cells are wrapped `9900mAh 3.7V` with no brand, model or batch code.** No
  18650 holds that: mass-production parts top out near 3500 mAh, so the label overstates by roughly
  2.8×. The two holder positions are in **parallel**, which is the configuration the repo's
  matched-pair rule exists to protect, and "matched" cannot be established by inspection here
  because there are no markings to match on. New `known-issues.md` entry with the checks that
  settle it, cheapest first: weigh each cell (a real 3000–3500 mAh 18650 is ≈45–48 g), compare
  resting voltages, then capacity-test at ≈0.2 C to 2.5 V. The *Cells* checklist section now records
  that none of these was done before the cells were fitted.

### Changed
- **`JP1` watch-list item marked dormant, not satisfied.** `JP1` is on the HackerGadgets NVMe
  battery board, which has not shipped; the stock board now fitted is 18650-only and has no such
  jumper. The item re-arms when the NVMe board is installed.
- **`power-budget.md` left as written and flagged stale in both columns.** Its ≈22 Wh two-18650
  figure assumed ≈3000 mAh cells and its 37 Wh column describes a pack that is not installed. Pack
  energy is unmeasured; rewriting it against an unmeasured number would only move the error.


### Added
- **uConsole kit + AIO V2 arrival record, 2026-09-15.** Twelve photographs under
  `images/inventory/` (outer carton, both retail-box faces, both trays as opened, full contents
  laid out twice, and three close-ups — the AIO V2 board group, the LiPo pack label, and the
  antenna breakout edge-on), downscaled
  to 1600 px with checksums of the supplied files. The inventory checklist gains rows and an inspection note for everything the
  kit supplied beyond the BOM — its own battery board with an 18650 holder, an EXT board with a SIM
  slot, a **CM4→CPI3.14 adapter**, a copper-foil thermal pad, speakers and a power button — plus the
  mainboard revision `CPI 3.14` / `V5` read off the silkscreen. Order record, build log, TODO and
  the decisions log follow.
- **Kit retail-box markings transcribed:** `uConsole Kit` / `NC-D` / `NONE` and
  `FCC ID:2A2YT-UC-CM4B`. The kit carries its own FCC grant, separate from the CM4's
  `2ABCB-RPICM4`. `NC-D` and `NONE` are recorded verbatim and **left undecoded** — the reading
  "non-core, no compute module" matches what arrived but has no vendor source behind it; the label
  QR or the variant listing settles it. The box is the only SKU and FCC marking on the kit, so the
  order record now says to keep it until the AliExpress dispute window closes.
- Two install decisions opened by the unboxing, both recorded in `docs/logs/decisions.md`: which CM4
  adapter is installed (the kit's, or the HackerGadgets one that carries PCIe for NVMe boot), and
  which board takes the mainboard's single mini-PCIe slot (the EXT board or the AIO V2 — they are
  mutually exclusive).

- **AIO V2 identified from the close-up frame**, closing several items the overview shots left
  open: board label `uConsole AIO extension board V2` / `Designed by HackerGadgets.com`; antenna
  breakout of 7 u.FL→SMA positions `ANT1`–`ANT7`; on-board u.FL connectors labelled `SDR`, `LoRa`,
  `GPS`; GNSS module `GP-02 BDS+GPS`; rear I/O plate with USB-C and RJ45 cutouts and a `Bias-T`
  silkscreen beside a small aperture. Antenna count recorded as 8 (6 stubs, 1 telescopic, 1 puck)
  with 7 pigtails.

### Corrected
- **Breakout jack gender is readable after all: standard SMA female.** An edge-on frame of the
  antenna breakout held in hand shows external threads and a recessed centre socket on all 7 jacks,
  and corroborates the count. An earlier entry recorded polarity as not resolvable by photography —
  that was true of the frames then available, not of the question. The antenna-side connectors
  remain unread, and SMA female jacks require SMA male antennas to make centre contact.
- **No LoRa-marked antenna is present.** An earlier reading of the dim layout frame recorded a
  stub marked `LoRa`; the close-up shows only `Wi-Fi` ×2 and `Bluetooth` ×1, and the stubs are far
  shorter than a 915 MHz ¼-wave. The checklist, decisions log and TODO now carry this as a blocker
  on LoRa transmit rather than a satisfied line item.

### Still open after the close-ups
- **SMA vs RP-SMA, antenna side.** The board jacks are settled (below); the antenna connectors have
  not been read at adequate resolution, so whether the set mates is open.
- **The `Bias-T` marking locates the function, it does not establish control.** Whether the rail is
  switched by `aiov2_ctl` or a jumper, and what the adjacent aperture is, remain open.
- **The LiPo pack's lead termination has not been photographed**, so JST pitch, polarity and PCM
  presence are unchanged from before.

### Discrepancies logged
- Items photographed that no order record accounts for: **two 18650 cells** (recorded everywhere as
  not ordered) and a **`Meshnology 10000mAh 3.7V 37Wh` LiPo pack** — not the UDIY-0001L
  (15000 mAh / 55.5 Wh) recorded as the selected battery on 2026-09-07. Provenance is unresolved, so
  the runtime figures in `docs/reference/power-budget.md` are **left as they are** rather than
  rewritten against a pack that may not be the one installed.
- Everything read off the 2026-09-15 frames is a photo reading, not a measurement, and is marked as
  such. **No per-board damage inspection has been done**; the AIO V2's revision silkscreen and the
  `ANTn` jack labels are not legible at the supplied resolution.

### Added
- **First microSD flashed.** `uConsole_CM4_v3.1_64bit` written to the build's 32 GB card and
  verified by reading the card back and comparing SHA-256 against the image (2026-09-15). Both
  image checksums, the image's partition geometry, and the as-flashed row are recorded in
  `docs/logs/firmware-versions.md`. Booted successfully 2026-09-16 (see above).
- Windows flashing procedure captured in `docs/logs/known-issues.md`: raw `\\.\PhysicalDriveN`
  access requires Administrator, `Set-Disk -IsOffline` fails on removable media (lock and dismount
  the volumes with `FSCTL_LOCK_VOLUME`/`FSCTL_DISMOUNT_VOLUME` and hold the handles instead), and
  PowerShell's Int32 hex-literal parsing silently corrupts `0xC0000000` in P/Invoke calls.
- microSD cleared as a blocker in `TODO.md`, `docs/accessories.md`, and `CLAUDE.md`.

### Fixed
- **Image format corrected.** The CM4 v3.1 image is distributed as `.img.bz2`, not the `.img.7z`
  recorded in `docs/logs/firmware-versions.md` and `docs/runbooks/imaging-and-first-boot.md` —
  `.7z` applies only to the 2023 v0.1b xfce image. `.gitignore` had no `*.bz2` rule either, so the
  real image format was not actually excluded from commits. Path A of the imaging runbook now
  carries runnable download/extract/flash commands and notes that ClockworkPi publishes no
  upstream checksum.
- **Battery topology corrected.** The system is 1S: the mainboard PMIC is an AXP228 single-cell
  part (per `clockwork_Mainboard_V3.14_Schematic.pdf`, corroborated by `aiov2_ctl`'s
  `axp20x-battery`/`axp22x-ac` paths), so the two 18650 positions are in **parallel**, not series
  at 7.4 V as `power-budget.md` previously claimed. Pack energy is unchanged; the voltage and the
  failure modes are not.

### Added
- Battery decision recorded: a **1S LiPo pack (UDIY-0001L, 15000 mAh, 55.5 Wh)** on the board's JST
  connector, `JP1` soldered closed — ≈2.5× the energy of two 18650s, ~13.5 h of terminal use or
  ~8.5 h receiving. A second unit gets bought rather than moving the pack in the Pi 5 cyberdeck.
  Case modification accepted to fit it; `hardware/mechanical.md` gains a cavity-measurement table,
  the rules a pouch cell imposes, and a measure-first sequence.
- Second supported battery option documented: a **1S LiPo pack on the board's JST connector**,
  selected by the `JP1` solder jumper (open for 18650s, closed for JST). A 10 Ah pack is ≈38.5 Wh
  against ≈22 Wh for two 18650s — runtime tables now carry both columns. JP1 added to the assembly
  runbook, the known-issues watch-list, and the inventory checklist, alongside cavity and JST-pitch
  measurements.
- First hands-on record: CM4 unboxed, photographed, and inspected 2026-09-06. Variant confirmed as
  CM4108000 (wireless / 8 GB / Lite) against the box label, regulatory IDs transcribed, and a u.FL
  external-antenna connector found on the module — which opens an antenna-selection question
  (`dtparam=ant2`) now tracked in the decisions log. Inventory photographs under
  `images/inventory/` as downscaled copies with checksums of the originals.
- `.claude/agents/hw-research.md` and `.claude/agents/repo-audit.md`: two read-only subagents wired
  into the skill's phase 3 (per-component sourcing, spawned one per component in parallel) and
  phase 9 (adversarial audit before committing a batch). The skill documents why the rest of the
  method stays in one context.
- `scripts/audit.py` in the skill: mechanical audit for broken links, secret-shaped strings,
  precise coordinates, staged configs missing verify/rollback lines, unfilled placeholders, and
  estimates that name no replacement. Copied into scaffolded repos alongside the link checker.

### Changed
- Staged configs now carry explicit verify and rollback lines — found by running the new audit
  against this repository.
- `.claude/skills/hardware-project-repo/`: a repository-scoped Claude Code skill that generalizes
  this build's method — the four scoping questions, a `scaffold.py` that creates the tree and seeds
  23 document templates, a link checker, and reference files covering conventions, the research
  playbook (including reading the vendor's own control software), document types, and knowledge-base
  structure. Encodes the nine phases from order reality through hygiene, and the findings that
  motivated them.
- `presentation/`: conference talk material — a 36-slide Marp deck (`uconsole-build-talk.md`) on
  documentation-first hardware work, with speaker notes and inline cut lists; abstract, bio
  template, and per-venue CFP notes for DEF CON / BSides / ISSA; and a demo plan with three
  fallbacks and a pre-flight checklist. Rendered output is not committed.
- `CLAUDE.md`: repo conventions — where each kind of document belongs, verify/estimate markers,
  UTC and general-location rules, secrets and binary policy, living-document update triggers, and
  the link-check command.
- Knowledge base populated across all seven disciplines (20 learned notes, 7 config references,
  9 runbooks): dB/link budget, antennas, sampling and IQ, modulation field guide, receiver
  performance, signal-ID workflow, US spectrum law; RTL-SDR limits and calibration; LoRa airtime
  and Meshtastic architecture with a range-test runbook; Wi-Fi passive-capture fundamentals and a
  survey session runbook; ADS-B and weather-satellite theory with reception runbooks; digital
  voice/trunking and AIS; US licensing path, band plans, and receive-only digital modes.
- Per-discipline indexes in each `knowledge/*/README.md`; population table in `knowledge/README.md`.
- Pre-arrival reference build-out (Tier 1 + 2): accessory buy list (`docs/accessories.md`),
  power budget and runtime estimates, antenna/RF-connector reference, per-board hardware spec
  sheets, datasheet/schematic index, and mechanical notes.
- Staged configuration under `configs/`: CM4 device-tree fragment, `cmdline.txt` notes, RTL-DVB
  modprobe blacklist, systemd notes (SPI1/devterm-printer, rail-boot service), gpsd defaults,
  SDR++ band/gain starting points, Kismet passive-survey config, Meshtastic US915 baseline.
- Per-application setup notes under `software/` (aiov2_ctl, SDR stack, ADS-B/tar1090, Meshtastic,
  GPS), including the full aiov2_ctl command surface (`--power`, `--watch`, `--measure`,
  `--sync-rtc`, boot-rail management) and the files its installer writes.
- Runbooks: NVMe boot, backup & restore, headless access, first RF checkout.
- Firmware and driver READMEs: image/EEPROM/keyboard flashing procedure with checksum discipline;
  which driver claims which device.
- Bring-up checklist rewritten with exact commands, pass criteria, and a power-characterization
  pass; inventory checklist extended with counts, fit checks, serials, and cell safety checks.
- Firmware-version log pre-filled with upstream targets (uConsole CM4 v3.1, Linux 6.12.62).

### Changed
- BOM corrected: the HackerGadgets line item supplies an 18650 **holder**, not cells; cells and a
  microSD are unpurchased blockers. Flagged the stock ClockworkPi battery board as redundant with
  the NVMe battery board.
- Device-tree overlay / `config.txt` reference for RTC/GPS/LoRa (CM4 vs CM5) in `pinout-gpio.md`,
  sourced from the HackerGadgets AIO setup guide.
- SX1262 LoRa pin map (IRQ/Busy/Reset) and `pinctrl` manual rail-control commands.
- Forum-sourced gotchas in `known-issues.md`: CM4 GPS/console conflict, LoRa/devterm-printer SPI1
  conflict, `hackergadgets-uconsole-aio-board` package dpkg errors on Trixie/Bookworm, AIO V2
  reseating issue, CM5-specific SDR default-on behavior.
- Decision: LoRa region is a Meshtastic config-time setting, not a board SKU choice — closes that
  open question. Battery variant options expanded (2×18650 / 2×21700 / LiPo, no separate SKU).
- Bill of materials and documentation reference index.
- Repo scaffold (hardware/firmware/drivers/software/configs/images).
- Setup starter docs: inventory & inspection, tools & consumables, assembly runbook,
  imaging & first-boot runbook, software-install runbook, module bring-up tests,
  pinout/GPIO reference, and living logs (build, firmware versions, known issues, decisions),
  plus order/warranty records.
- Knowledge base (`knowledge/`): reference indexes for seven disciplines (RF fundamentals,
  SDR, mesh networks, wardriving, aerospace, communications, ham radio), a per-discipline
  documenting structure (learned/configs/runbooks/findings), capture templates
  (finding, runbook, config, session-log, signal-id), and a responsible-use/legal note.
