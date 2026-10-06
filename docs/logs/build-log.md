# Build log

Dated journal of what was done. Newest entries at the top. Link photos in [`../../images/`](../../images/).

## 2026-10-06 — webdash: passive packet-capture tap (tshark) + M14 curriculum

- **What:** Installed Wireshark/tshark 4.4.19 on Fancy and added a passive, receive-only
  packet-capture tap to the webdash for the hang/dropout investigation: a localhost host bridge
  (`tshark-bridge.py`, 127.0.0.1:8768) driving a bounded `dumpcap` ring buffer through a
  scoped-sudoers root wrapper (`tshark-capture.sh`), an address-free collector + System-view tile,
  and curriculum module **M14** ("Reading a packet capture") + **LAB-23**, checked against live
  `tshark` data. Deployed to the live container (`docker compose up -d --build`) and
  installed/enabled `tshark-bridge.service`.
- **Result:** Verified end-to-end on `wlan0` — capture runs, `segment_packets` rises, findings
  (TCP retransmit/dup-ack/reset, ICMP-unreachable) and protocol mix populate, the final summary
  lands on "done", and the pcap is user-owned in `~/labs/tshark`. Two bring-up bugs found and
  fixed: dumpcap exited immediately because it drops `CAP_DAC_OVERRIDE` and so, as root, could not
  write into the mode-700 home — it now runs **as the user** via `runuser`, which requires the
  capture user in the `wireshark` group (added this session); and the summary read back zero
  because a heredoc fed the program on python's stdin, starving it of tshark's output — the
  aggregator moved to its own file, plus a final-summary pass after the capture loop. Captures land
  on the 234 GB NVMe, never the microSD. The senior-rf-engineer review was applied to the M14
  wording (SD→NVMe, the retransmit-counts-not-measured caveat, the step-1-only-proves-reachable
  note, and the post-power-save clean-baseline framing).
- **Photos:** none this session.
- **Next:** Point the tap at the open hang / under-voltage watchdog hypothesis; a short
  `ss`/`conntrack`/`iw-link` collector would complement it. PRs for `feat/webdash-tshark-tap` are
  pushed but not opened.

## 2026-10-04 — GNSS: first fix recorded as a finding

- Captured a GNSS fix over gpsd 3.25 (`/dev/serial0`, NMEA 0183 @ 9600 bps) and logged it as
  [`knowledge/rf-fundamentals/findings/2026-10-04-first-fix.md`](../../knowledge/rf-fundamentals/findings/2026-10-04-first-fix.md).
  3D fix at ~18:27 UTC: **15 SVs used** (10 GPS + 5 GLONASS), **HDOP 0.7** (PDOP 1.1 / VDOP 0.9),
  fix quality 1, several SVs at 35–40 dB-Hz. `$GPTXT` reported `ANTENNA OK`.
- Location recorded as grid **EM94** only. The raw gpsd/NMEA dump carried precise coordinates, so
  it was **not committed** (grid-square-only policy); kept off-repo, referenced by location.
- **Time to first fix not measured** — the capture opened already fixed, so there was no cold-start
  reference. TTFF stays *unverified* until a cold-reset timed run is done.

## 2026-10-04 — webdash: second skin ("vintage" / Simpson analog meter)

- Added a selectable skin alongside the default dark "chart room" look. The new **vintage** skin
  styles the dashboard as a mid-century Simpson Electric panel meter: aged-ivory faceplate tiles in
  dark bakelite bezels, sepia ink, oxblood needle-red accents, and an engraved-nameplate type voice
  (italic GFS Didot Classic wordmark/titles, C059 Century-Schoolbook body, monospace kept only for
  live readings). Font inspiration was the Simpson logo on simpsonelectricnc.com.
- Implementation is token-only: the skin re-points the existing `:root` CSS variables under
  `:root[data-skin="vintage"]` plus a few font/texture rules (`webdash/app/static/styles.css`); no
  markup changed and the default skin is untouched. All faces are **already-installed on-device
  fonts** (`fc-match` confirmed: GFS Didot Classic, C059, Nimbus Mono PS), so the skin stays fully
  offline — no CDN, no bundled webfont.
- Switcher: a **Skin** toggle in the Learn head cycles chart ⇄ vintage, persisted in
  `localStorage` (`fancy.v1.skin`); an inline loader in `index.html` applies it before first paint
  so a reload never flashes the wrong skin. Mirrors the existing "Plain labels" pattern.
- Verified by rendering `styles.css` with representative tile markup in headless Chromium at
  uConsole width (1280 px); both skins confirmed. Not yet viewed in the live app on the device.

## 2026-10-04 — webdash: ADS-B tile no longer says "starting" when the SDR rail is on

- Owner report: the overview ADS-B tile misrepresented the SDR rail. With the rail on and readsb
  stopped it read **"starting"** — left over from when the rail auto-started readsb (changed
  2026-10-03). It now reads **"ADS-B off"** (`views.js` `stationStatus`); rail off still reads
  "rail off". The status snapshot has no tuner-busy field, so a running hunt/listen also shows
  "ADS-B off" on the tile.
- Confirmed on hardware: SDR rail on for 15 s → readsb stayed `inactive`; rail switched back off.
  Container rebuilt; the new `views.js` is being served.

## 2026-10-04 — WiGLE: home area set, first upload

- Owner gave the home location as a town; Fancy was ~188 km from it and the drive capture ~227 km,
  so the GPS position was not used. Home set to the town centre with an 8 km radius in
  `~/.config/wigle/env` (not committed).
- Home filter on synthetic rows: 0.5 km and 7 km dropped, 26 km kept, no-fix dropped.
- First real upload: 229 rows, accepted as WiGLE transaction `20261004-01348` (queued). The script
  logged `transid None` — fixed to search the response for the id; state entry filled in from
  `/api/v2/file/transactions`. A rerun sent nothing.

## 2026-10-04 — WiGLE: automatic upload with home-area filter

- Added `webdash/host-helpers/wigle-upload.{py,service,timer}`. The hourly user timer uploads each
  finished `.wiglecsv` once, with rows within 500 m of home dropped. It uploads nothing until a
  home position and API token are in `~/.config/wigle/env`. Timer installed and enabled.
- Tested: with no home set it refuses (exit 0); `--set-home-from-gps` writes the env file 600 in a
  700 directory; `--dry-run` reads the first capture (229 rows).
- The Kismet track shows the first capture was taken at ~80 km/h over 2.2 km, about 13 km from
  where the device sat during this test. That spot can't be assumed to be home, so the stored home
  point was removed. The owner needs to run `--set-home-from-gps` at home.
- Not verified: a real upload (no API token yet), and the filter dropping home rows on real data.

## 2026-10-04 — Kismet: WiGLE CSV export enabled and verified

- `configs/kismet/kismet_site.conf`: `log_types=kismet` → `log_types=kismet,wiglecsv`; deployed to
  `/etc/kismet/kismet_site.conf`.
- USB rail was off (`wlan1` absent); `aiov2_ctl USB on` brought the AC1200 back as `wlan1`. GPS rail
  on, gpsd `"mode":3` (3D fix).
- 90 s run via `systemctl --user start kismet`: `~/kismet-logs/uconsole-20261004-14-40-01-1.wiglecsv`
  written alongside the kismetdb — `WigleWifi-1.4` header, 215 `WIFI` rows, none missing
  coordinates. Kismet stopped afterwards, `wlan1mon` cleared. The CSV is not committed.
- Not done: no upload to wigle.net (needs the owner's account; the file includes home-area
  networks). Setup notes: [`../../software/kismet.md`](../../software/kismet.md) §WiGLE export.

## 2026-10-03 — webdash: airband scanner shows the active frequency (bridge-driven hop)

- **Feature:** while scanning, the SDR view now shows which channel the scanner is parked on
  (`▶ 120.500 MHz — traffic`) or that it's still sweeping — polled from a new `/scan/status`.
- **Why the rework:** `rtl_fm`'s native multi-`-f` scanner plays audio but never reports which
  channel it stopped on (confirmed: it prints "Tuned to" once at startup only). So the bridge now
  **drives the hop itself** — one `rtl_fm` per channel; since `rtl_fm` with a squelch emits bytes
  *only while squelch is open* (a quiet channel produces nothing), activity = any output within a
  `select()` probe window. It parks on an active channel, streaming until quiet for 1.5 s, feeding a
  persistent ffmpeg encoder (silence between hops keeps the MP3 flowing) and publishing the live
  frequency in `_scan_state`. This supersedes the native-scanner note in the entry below.
- **Squelch default 80 → 150:** characterised on-device — at 80 even band noise broke squelch (the
  scanner locked on the first channel); ≥250 rejected even a real carrier. ~150–160 cleanly
  separated noise from signal here. It's gain/antenna/signal dependent, so the UI field stays
  adjustable. Verified end-to-end at the bridge: a 3-channel scan skipped the quiet guard/ATIS
  channels and parked on the live 162.400 carrier, `/scan/status` reporting `active=162.400 MHz`.
- **Path:** `sdr-bridge.py` (`_scan_controller`, `_handle_scan`, `/scan/status`) →
  `app/sdr/hunt.py` `scan_status()` → `/api/sdr/scan/status` (`main.py`) → `sdr.js` `pollScanStatus`.
- **Trade-off:** per-hop `rtl_fm` restart (~0.3–0.5 s device init each) makes cycling slower than the
  native scanner and can miss very brief transmissions; the gain is knowing the frequency. Browser
  click-through unverified (TOTP).

## 2026-10-03 — webdash: airband scanner (scan channels, pause on traffic)

- **Feature:** a "▶ Scan airband" control in the SDR view cycles airband channels and pauses on any
  with traffic, playing the audio, then resumes — a classic scanner. Squelch is adjustable (default
  80). Stop ends it (shared with Listen). Receive-only.
- **How:** no custom scan loop — `rtl_fm` does it natively (*"use multiple -f for scanning (requires
  squelch)"*, ranges supported). The bridge's `/listen` now also accepts `scan=<comma freqs>` or
  `scan=airband` + `squelch`, and runs `rtl_fm -f … -M am -l <sq> -t 20` into the same ffmpeg→MP3
  stream. `_busy="scan"` makes it mutually exclusive with hunt/listen/ADS-B on the single tuner.
- **Hunt → Scan:** if an Airband hunt has run, Scan cycles just the live channels it found (fast and
  local-signal-aware); otherwise it sweeps the whole 118–137 MHz range at 25 kHz (slower). The
  frontend remembers the last airband hunt's frequencies.
- **Path:** `sdr-bridge.py` `_handle_listen` (scan branch) → `app/sdr/listen.py` `stream(scan,
  squelch)` → `POST`… `/api/sdr/listen?scan=…&squelch=…` (`main.py`) → `sdr.js` `scanAirband()`.
- **Verified:** bridge streamed valid MP3 (`codec=mp3, 48 kHz`, 45 KB/6 s) scanning 3 channels incl.
  121.5 guard, then released the tuner; `/api/sdr/listen?scan=` returns 401 (registered); deployed
  `sdr.js`/`index.html`/`listen.py` carry the scan path. Bridge restarted, container rebuilt.
  Browser click-through unverified (TOTP login). Squelch default may need tuning per antenna/gain.

## 2026-10-03 — webdash: GPS-coupled NOAA picker with a bundled static NWR table

- **Feature:** the NOAA weather picker now auto-selects the predicted-strongest local transmitter
  from the device's GPS fix, with a manual override. Caption reads e.g.
  `GPS → KEC95 162.400 (Aynor, SC · 40 km · 1000W)`; picking a channel by hand switches to
  `manual · ↻ use GPS`. Station name/grid shown, never raw coordinates.
- **Static data (one-time authoring fetch, owner-approved):** bundled
  [`webdash/app/static/data/nwr-stations.json`](../../webdash/app/static/data/nwr-stations.json) —
  **1035 US NWR transmitters** (`call, freq_hz, lat, lon, site, st, pw`), parsed from the NWS
  `ccl-data.js` county-coverage dataset (fetched 2026-10-03 from
  `https://www.weather.gov/source/nwr/JS/ccl-data.js`; per-county SAME arrays dropped, coords to
  4 dp). **No runtime egress** — the dashboard reads only this local file. Provenance + refresh
  steps in [`webdash/app/static/data/README.md`](../../webdash/app/static/data/README.md).
- **Selection heuristic:** rank by `power / distance²` (free-space received-power proxy), **not**
  nearest-by-distance. Validated against the on-air measurement: at grid FM03 the top pick is
  KEC95 162.400 (Aynor SC, 1000 W, 40 km), matching what the SDR actually received — whereas the
  nearest site, WNG628 162.500 (Georgetown SC, 300 W, 33 km), measured at the noise floor.
- **Verified end-to-end:** headless browser drove the deployed `sdr.js` with a fake FM03 fix →
  auto-selected 162.400 (WX2) with the right caption; a manual change to 162.550 stuck and flipped
  the caption to manual. Container rebuilt; JSON + JS + caption all served.

## 2026-10-03 — webdash: NOAA default → WX2 162.400, confirmed by on-device listen test

- **Change:** the webdash NOAA weather picker now defaults to **WX2 / 162.400 MHz** (was WX3 /
  162.475). The channel set is unchanged — a static 7-option `<select>`; only the `selected` option
  moved.
- **Why:** checked against the device's own GPS/location using **nothing but static radio — no
  internet egress**. GPS: 3D fix, grid **FM03** (coastal SC). An on-device `rtl_power` sweep of the
  NWR band (162.35–162.60 MHz) found WX2 162.400 the only channel above the noise floor; the old
  default WX3 162.475 sat at the floor (dead here).
- **Listen test (confirms it):** 8 s of `rtl_fm` NFM captured at each frequency and compared.
  162.400 was **8× quieter** (RMS 0.017 vs 0.134 — FM quieting by a real carrier) with **12× higher
  envelope variation** (0.385 vs 0.033 — speech dynamics); 162.475 was flat full-scale open-squelch
  noise. Envelope plot archived in the session scratchpad. Signal is **weak** (marginal `rtl_power`
  SNR, consistent with the SDR whip indoors), so treat as a confirmed-but-weak NWR carrier.
- **Egress audit:** every call in the SDR/NOAA/listen path is localhost (`hunt.py`/`listen.py` →
  bridge `127.0.0.1:8767`, `adsb.py` → local tar1090); audio is on-device `rtl_fm`; GPS from gpsd
  on `localhost:2947`. No static NWR station table exists on-device and none was fetched.

## 2026-10-03 — webdash: SDR view title names the chosen application

- **Change:** the SDR view heading is no longer the static "SDR — pick an application"; it names
  whichever application owns the single tuner — `SDR — Listen`, `SDR — ADS-B`, `SDR — Scanning` —
  falls back to `SDR — pick an application` when the tuner is free, and `SDR — rail off` when the
  SDR rail has no power.
- **How:** `sdr.js` — `updateSdrTitle()` sets `#sdr-title` from local state (listening / polling,
  set the instant the operator acts) and the shared status snapshot (ADS-B running, rail state via
  `railOn`). Wired into `syncSdr()` (every tick) and the listen/scan/stop paths (immediate). Order:
  Listen > ADS-B > Scanning > rail-off > pick-an-app. `railOn` returns null before data arrives, so
  the `=== false` guard shows "pick an application", never a false "rail off".
- **Verified:** branch truth table matches the table above; `updateSdrTitle` present in the served
  `sdr.js` (5 refs); static HTML keeps the pick-an-app default for pre-JS render. Container rebuilt.

## 2026-10-03 — webdash: overview row-2 tiles go quarter-width above mobile

- **Change:** the four rail-station tiles (GPS / SDR / Mesh / Wi-Fi) on the overview now sit at a
  quarter of the page width each on any screen above mobile, not only ≥900px. System and Power keep
  the top row at half width each. Phones (≤640px) still stack single-column full-width.
- **How:** `styles.css` — the `.tiles` 4-column grid media query breakpoint lowered from
  `min-width: 900px` to `min-width: 641px` (641 = just above this repo's 640px phone breakpoint).
  The uConsole height-fit block stays at 900px (the panel is 1280px wide, so unaffected).
- **Verified (headless Chromium, live served CSS):** at 700px → row1 49/49%, row2 24/24/24/24%;
  at 1280px → 50/50%, 25% each; at 600px → single column, 100% each. Container rebuilt and serving
  on `127.0.0.1:8090`.

## 2026-10-03 — webdash: fix panel rows overflowing the screen

- **Symptom:** text in the Meshtastic panel stretched its box off the right of the page.
- **Cause:** `#mesh-body` renders label/value pairs as flex `.row`s, but the base `.row .k`/`.v`
  had no `min-width: 0`. A flex item defaults to `min-width: auto`, so a long unbroken value (a
  node long-name, or the joined **Channels** list) couldn't shrink and forced the row — and the
  whole panel — wider than the screen.
- **Fix:** `styles.css` `.row .k`/`.v` get `min-width: 0; overflow-wrap: anywhere` plus a row
  `gap`, so long values wrap instead of overflowing. Also fixes the GPS/Power/System panels, which
  share `.row`. Tiles keep their own more-specific `.facts .row .v` (nowrap + ellipsis), so they
  are unaffected.
- **Deployed 2026-10-03:** webdash container rebuilt; served `styles.css` on `127.0.0.1:8090`
  confirmed to carry the new rule. Browser render not eyeballed (TOTP login) — hard-reload to pick
  it up. *CSS verified served; visual render unconfirmed.*

## 2026-10-03 — SDR rail made power-only; ADS-B is now a chosen application

- **Change:** the SDR rail coming on no longer auto-starts ADS-B. `readsb` is `systemctl-disabled`;
  ADS-B is one of three mutually-exclusive SDR applications (ADS-B / broadcast-airband hunt /
  listen) chosen in the webdash SDR view. See [`decisions.md`](decisions.md).
- **Device step (applied 2026-10-03):** `sudo systemctl disable --now readsb` — confirmed
  `systemctl is-enabled readsb` → `disabled`, `is-active` → `inactive`. The existing NOPASSWD rule
  already permits on-demand start/stop; no sudoers change needed.
- **Webdash:** new `POST /api/sdr/adsb {action}` → host `sdr-bridge.py` `/adsb`, which claims/
  releases the single tuner via `_busy` (hunt/listen refuse while ADS-B holds it). The bridge no
  longer silently restarts readsb after a hunt/listen — the tuner is left free and the operator
  re-selects an app. SDR view retitled "SDR — pick an application" with a Start/Stop ADS-B control.
- **Deployed 2026-10-03:** `sdr-bridge.service` restarted (new `/adsb` endpoint answers on
  `127.0.0.1:8767`); webdash container rebuilt with `docker compose up -d --build` and serving on
  `127.0.0.1:8090` — `/api/sdr/adsb` returns 401 (auth gate, i.e. registered, not 404), and the new
  `sdr.js` / index.html (chooser title + `adsb-start`) are served.
- **Docs:** [`../../software/adsb-tar1090.md`](../../software/adsb-tar1090.md),
  [`known-issues.md`](known-issues.md) (the `error -6` entry), and the `crash-loop` / `rail`
  glossary entries updated to the new behaviour.
- **Mechanism verified on hardware 2026-10-03** by driving the host bridges directly (`:8765` rail,
  `:8767` SDR — the same calls the dashboard buttons make server-side), SDR rail on throughout:
  - SDR rail on with no app chosen → `readsb inactive` — **ADS-B no longer auto-starts** (the fix).
  - Start ADS-B → `readsb active`, `tar1090/data/aircraft.json` → 200.
  - Scan while ADS-B running → refused `SDR is busy (adsb)` (mutual exclusion).
  - Stop ADS-B → `readsb inactive`, tuner released.
  - Scan with tuner free → ran, `13 signal(s) found`, `busy` hunt→None.
  - After the hunt → `readsb` stayed `inactive` (no silent auto-restart — the other change).
  - Restored to as-found: SDR rail on, `readsb` disabled+inactive, tuner free.
- **Still unverified:** only the literal in-browser click-path (dashboard login needs an operator
  TOTP second factor, which this session does not drive). The webdash layer above the bridges is
  otherwise confirmed: container serves the new `sdr.js` / chooser HTML and `/api/sdr/adsb` returns
  401 behind the auth gate. *Backend flow verified on hardware; browser UI click-path unverified.*

## 2026-10-02 — Meshtastic gets GPS position from gpsd (bridge), without giving up the port

- **What:** Stood up [`../../webdash/host-helpers/mesh-gps-bridge.py`](../../webdash/host-helpers/mesh-gps-bridge.py)
  + its systemd unit so the node shares location on the mesh while `gpsd` keeps `/dev/serial0`.
  The bridge reads gpsd (127.0.0.1:2947) and pushes the fix into `meshtasticd` over its localhost
  admin API (127.0.0.1:4403) via the `meshtastic` library's `setFixedPosition()`. Set
  `position.gps_mode NOT_PRESENT` on the node once so the firmware stops expecting a serial GPS.
- **Why:** Meshtastic's native GPS wants to own the raw UART, which would evict gpsd and break
  Kismet/PyGPSClient/webdash sharing and the new chrony clock discipline. Pushing position over the
  API keeps gpsd as the single owner and still gives the node position. Resolves the 2026-09-21
  either/or (gpsd *or* Meshtastic position) documented in `software/gps.md` / `software/meshtastic.md`.
- **Result:** Service `active`/`enabled`; `journalctl -u mesh-gps-bridge` shows `sent position`.
  Verified end to end — a live 3D fix (grid `FM03cv`, eph ~13 m, HDOP 0.7) was pushed and read back
  as the node's own fixed position (`fixed_position: True`). `sendPosition()` was tried first but
  the node doesn't adopt an outbound one-shot (`getMyNodeInfo` stayed empty), so `setFixedPosition`
  is used. Airtime/write-gated: update on ≥100 m move or ≤900 s. **Caveat:** position is only as
  good as the fix; indoors an early send landed a grid field away before the fix settled.
- **Next:** Optional accuracy gate (skip sends above an HDOP/eph threshold); confirm peer reception
  outdoors with a second node. Docs: [`../../software/meshtastic.md`](../../software/meshtastic.md).

## 2026-10-02 — GPS disciplines the system clock (chrony); offline-clock root cause found

- **What:** Set up GPS-sourced time maintenance so the clock is correct with no network. Installed
  `chrony` (the image default `systemd-timesyncd` is an SNTP client only and cannot read a
  refclock), staged [`../../configs/chrony/chrony-gps.conf`](../../configs/chrony/chrony-gps.conf)
  as `/etc/chrony/conf.d/gps.conf`, disabled `systemd-timesyncd`, enabled `gpsd chrony`. chrony
  reads GPS time from gpsd's SHM refclocks (NMEA unit 0; PPS unit 1 when present). Online, the
  Debian NTP pool still wins; offline, GPS sets the clock.
- **Why:** Offline, TOTP 2FA codes were rejected — a 30 s-step HMAC fails on a wrong clock. Traced
  to the RTC: the board has a PCF85063A (`/dev/rtc0`, `rtc-pcf85063`) with a CR1220 backup, but
  `dmesg` shows `rtc rtc0: Power loss detected, invalid time` at boot — the backup cell is
  dead/unseated, so the clock boots invalid and nothing offline corrects it.
- **Result:** chrony synced (pool, `Leap: Normal`). With a 3D fix at the window, the `NMEA`
  refclock became **reachable** (`chronyc sources`), proving GPS→gpsd→SHM→chrony end to end. It
  stayed unselected only because the online pool was more accurate at the time; offline it is the
  sole reachable source. **PPS not exported by gpsd** in this test despite `/dev/pps0` + `pps_ldisc`
  — config carries no `prefer` on PPS so it never blocks sync; wiring PPS is left as future work.
- **Next:** Replace the CR1220 backup cell for fast warm GPS starts; optionally wire gpsd to
  `/dev/pps0` for sub-microsecond time. Docs: [`../../software/gps.md`](../../software/gps.md).

## 2026-10-01 — webdash: WPA crack-offload wired into the dashboard (Phase 2)

- **What:** Finished the WPA audit feature — a captured handshake can now be cracked from the
  dashboard. The `wpa-audit-bridge` gained `POST /crack` + `GET /crack/status`: it runs the existing
  `crack-offload.sh` (SSH to `gpu-host-wsl` → `hcxpcapngtool` → `hashcat -m 22000`) as a
  background job, parses its `[n/4]` steps and result, and streams progress to a new **Send to
  gpu-host (crack)** button that appears once a capture completes. The crack only accepts a
  `wpa-*.cap` under `~/labs/wpa` (path re-validated), and the recovered PSK is held **in the bridge's
  memory only** — shown to the session, never written to disk or the audit log.
- **Result:** Verified the pipeline end to end except a successful crack (which needs the GPU host
  online): path validation rejects non-allowed paths; a crack against a cap with `gpu-host-wsl`
  offline stepped to `[1/4]` and returned the exact `FAIL: cannot SSH` error with correct result
  fields. A real captured handshake from the earlier owned-BSSID test (`wpa-20261001-152420-01.cap`)
  is on hand to crack once the GPU host is up. See
  [`../reference/webdash-architecture.md`](../reference/webdash-architecture.md) "WPA audit" and
  [`../../software/aircrack-ng.md`](../../software/aircrack-ng.md).
- **Next:** With `gpu-host-wsl` online, crack a real captured handshake from the dashboard to
  confirm the success path (PSK display).

## 2026-10-01 — webdash: SDR broadcast/airband hunt + NOAA/FM/airband listening

- **What:** Expanded the SDR rail's use beyond ADS-B. A new receive-only host bridge
  (`sdr-bridge.py`, `127.0.0.1:8767`) adds a **band hunt** (`rtl_power` sweep of FM 88–108 MHz or
  airband 118–137 MHz AM → station list) and **listening** (`rtl_fm → ffmpeg` MP3 streamed to a
  browser `<audio>` element, incl. a NOAA weather 7-channel picker). The one tuner is shared with
  readsb, so every operation brackets it (stop → use → restart) and needs the SDR rail on; a
  single-tuner lock makes hunt and listen mutually exclusive. Broadcast AM was dropped as
  impossible on this front end (R860 floor ~24 MHz — `rtl-sdr-limits.md`); airband replaces it.
- **Result:** Verified end to end on real RF. A live FM sweep (SDR rail on) found 4 stations
  (89.9 / 96.9 / 106.6 / 107.4 MHz), readsb bracketed cleanly, rail restored to off. The listen
  pipeline produced valid browser MP3 (`MPEG layer III, 64 kbps 48 kHz mono`) off a live FM station
  and released the tuner + restored readsb on disconnect. No new sudoers needed (readsb control
  already granted; rtl tools need no root). See
  [`../reference/webdash-architecture.md`](../reference/webdash-architecture.md) "SDR
  broadcast/airband" and [`../../software/sdr-stack.md`](../../software/sdr-stack.md).
- **Next:** Confirm the browser `<audio>` playback from the dashboard (rail on → NOAA → Listen);
  the bridge stream + format are verified, the UI click isn't. True broadcast AM would need an
  upconverter.

## 2026-10-01 — webdash: authorized WPA audit pipeline (allowlist + capture)

- **What:** Added an authorized WPA handshake-capture pipeline to the webdash Wi-Fi view, gated to a
  BSSID allowlist. The operator enters a BSSID (own gear / documented engagement, with a basis);
  active auditing can only ever target an allowlisted BSSID, re-enforced on the host. A new
  `wpa-audit-bridge` (`127.0.0.1:8766`, able to sudo exactly one root capture script) brackets
  Kismet (shared `wlan1`) and runs: monitor mode → channel scan → **bounded, targeted deauth** (not
  a flood) → handshake detection → cleanup. Captures go to gitignored `~/labs/wpa`; per-run audit
  log. Design and the one-time host install (scoped sudoers + service) are in
  [`../reference/webdash-architecture.md`](../reference/webdash-architecture.md) "WPA audit" and
  [`../../software/aircrack-ng.md`](../../software/aircrack-ng.md). In scope under the owner's Cyber
  Verification Program approval; receive/learn posture unchanged elsewhere.
- **Result:** Allowlist gate unit-tested (rejects dup/no-basis/broadcast/multicast/garbage) and the
  capture path verified end to end **against an owned BSSID** (owner, 2026-10-01): deauth + handshake
  capture succeeded, Kismet bracketed, radio restored. Host install (sudoers + bridge service) was
  performed by the owner — the safety classifier correctly held those privileged, RF-transmitting
  steps for explicit authorization rather than letting the session do them.
- **Next:** Wire the gpu-host GPU crack-offload of a captured handshake into the dashboard as a
  one-click step (Phase 2).

## 2026-10-01 — webdash: Kismet auth fix, under-voltage/temp, new-tab links, Start/Stop Kismet

- **What:** A webdash session on Fancy, four changes. (1) The Kismet panel read "can't connect"
  while Kismet was capturing: the REST API requires a login and the collector sent none. The
  collector now reads Kismet's own `~/.kismet/kismet_httpd.conf` (bind-mounted read-only) and sends
  Basic auth. (2) Surfaced Pi under-voltage throttle (`rpi_volt` hwmon `in0_lcrit_alarm` via HOSTFS)
  and a 1-hour mean CPU temp in the System/Power views. (3) The ADS-B/tar1090 map now opens in its
  own browser tab (its existing "Open map" link) instead of embedding in an `<iframe>`, matching the
  Kismet/Meshtastic UI links. (4) **Added a Start/Stop Kismet button** to the Wi-Fi view.
- **Result:** Kismet panel reads live again (authenticated). The Start/Stop control runs Kismet as a
  **user** systemd service via the `aiov2-bridge` (`systemctl --user`, no `sudo` — the capture
  helpers' file caps + `kismet` group are enough); start→Kismet + `kismet_cap_linux_wifi` up,
  stop→down, verified repeatedly end-to-end. See
  [`../reference/webdash-architecture.md`](../reference/webdash-architecture.md) "Kismet start/stop"
  and [`../../software/kismet.md`](../../software/kismet.md).
- **Host changes applied to Fancy (device state, not just repo):** enabled lingering for
  `wicked5mile` (`loginctl enable-linger`); installed `~/.config/systemd/user/kismet.service` from
  [`kismet-user.service`](../../webdash/host-helpers/kismet-user.service); added
  `Environment=XDG_RUNTIME_DIR=/run/user/1000` to the `uconsole-aiov2-bridge` unit and restarted it.
  The container image was rebuilt/recreated for each code change.
- **Confirmed 2026-10-01:** the owner clicked the Start/Stop button in a browser — works end to end
  (the whole path, button → bridge → `systemctl --user` → Kismet, now verified from the UI, not just
  the endpoint).
- **Next:** The root `kismet.service` stays disabled — don't run it alongside the user
  service (`:2501` contention). The under-voltage field depends on `/hostfs/sys/class/hwmon`
  propagating through the `/:/hostfs:ro` bind mount; confirm the Throttle row shows `none` rather
  than `—` once logged in, else add an explicit `hwmon` mount.

## 2026-09-30 — AC1200 verified on-device; weak onboard Wi-Fi link mitigated

- **AC1200 arrived, installed, and verified on Fancy.** MediaTek MT7921AUN on `wlan1` (`mt7921u`),
  monitor mode (incl. active monitor) across 2.4/5/6 GHz, Bluetooth controller `hci1` on USB; onboard
  `brcmfmac` (`wlan0`) still has no monitor mode. Inventory photos landed under
  [`../../images/inventory/`](../../images/inventory/). Full detail in the spec
  ([`../../hardware/specs/ac1200-mt7921.md`](../../hardware/specs/ac1200-mt7921.md)) and the
  [`../../CHANGELOG.md`](../../CHANGELOG.md).
- **Passive-BLE on `hci1` verified** (closes the last AC1200 check). Under `btmon`: `bluetoothd`
  brings `hci1` up with no `LE Set Scan Enable` and no `Create Connection` (accept/resolving lists
  cleared), no bonds; a `hcitool -i hci1 lescan --passive` ran as `Type: Passive (0x00)` with no
  `Command Disallowed` (304 adverts / 16 advertisers, counts only). Finding: `lescan --passive`
  needs `bluetoothd` stopped first or it fails with "Broken pipe" (safe here — `hci0` had no active
  connections/bonds). `hci1` left idle under `bluetoothd`, no bonds created.
- **Diagnosed a degraded onboard Wi-Fi link.** `wlan0` stayed associated to the AP but showed 20–30%
  ping loss and 70 ms+ latency at −69/−71 dBm (2.4 GHz ch 1, tx rate down to 5.5 Mbit/s, ~3.8k
  `tx failed`). Ruled out tailscale (fancy online) and the AC1200 (`wlan1` down, separate bus).
- **Mitigated:** disabled `wlan0` power save (`iw dev wlan0 set power_save off`) → **0% loss, ~20 ms**.
  Made it persistent with [`../../configs/networkmanager/wifi-powersave-off.conf`](../../configs/networkmanager/wifi-powersave-off.conf)
  (`wifi.powersave = 2`), deployed to `/etc/NetworkManager/conf.d/` and `nmcli general reload`'d.
  Underlying weak signal remains — antenna re-seat / closer to AP / Ethernet — see
  [`known-issues.md`](known-issues.md).

## 2026-09-29 — Tailnet exposure of the loginless Kismet/meshtasticd UIs: closed, then restored per owner

- **Closed first:** removed the two `tailscale serve` mappings that put loginless UIs on the whole
  tailnet (`sudo tailscale serve --https=2501 off`, `--https=9443 off`; tailscale 1.102.4), leaving
  only the TOTP-gated dashboard (`:443` → `localhost:8090`).
- **Found while verifying:** meshtasticd also binds its webserver to `0.0.0.0:9444`, so it was
  **still directly reachable on the tailnet IP** after the `:9443` proxy was gone
  (`https://100.x.y.z:9444/` → `200`, no auth). Its `Webserver:` block has no bind-address
  option, so closing it fully needs the webserver disabled (commented block + restart), which was
  done and verified (`ss` showed nothing on `9443`/`9444`). Kismet's `:2501` is loopback-only
  (`httpd_bind_address=127.0.0.1`) and fully closed by the proxy removal alone.
- **Then restored, same day, at the owner's request** — the UIs are wanted on the tailnet and the
  owner is the sole tailnet member (accepted risk; reaffirms 2026-09-24). Re-enabled meshtasticd's
  `Webserver:` (restored `config.yaml` from `config.yaml.bak-20260929`, restart → listening on
  `9444`) and re-added both mappings. `serve status` lists `:443`/`:2501`/`:9443`; verified from the
  tailnet: meshtasticd `:9443` → `200`, dashboard `:443` → `307`, Kismet `:2501` → `502` (expected,
  Kismet service was off).
- **Left open:** meshtasticd's `:4403` client API is `0.0.0.0`-bound and unauthenticated — larger
  surface, kept because the dashboard/CLI use it over loopback. Noted in
  [`known-issues.md`](known-issues.md).

## 2026-09-26 — GPU crack-offload validated (gpu-host-wsl, RTX 3070 Ti)

- **What:** Stood up the crack-offload path from runbook §5b end to end. gpu-host's **Kali WSL2**
  now joins the tailnet as its **own node** `gpu-host-wsl` (systemd enabled, `tailscaled` in
  kernel-TUN mode, Tailscale SSH). Fancy SSHes straight in and runs
  [`software/crack-offload.sh`](../../software/crack-offload.sh): reachability check → `scp` the
  capture → `hcxpcapngtool` → `hashcat -m 22000`.
- **Result:** the handshake from the 2026-09-26 LAB-22 dry-run (own AP "EvilLair") converted cleanly
  and ran against full `rockyou` (14.3M) on the **RTX 3070 Ti** in **~46 s** (`-O -w 3`, ~210 kH/s)
  vs ~14 min CPU-only on Fancy. **Not cracked** — the passphrase isn't in `rockyou` (a good sign for
  the owner's PSK). Full pipeline confirmed on real GPU hardware. Setup and gotchas documented in
  [`docs/reference/gpu-crack-offload-host.md`](../reference/gpu-crack-offload-host.md).
- **Hurdles cleared (all in the reference doc):** Tailscale SSH does **not** serve in
  `--tun=userspace-networking` (TCP connects, SSH hangs) — needs kernel mode; WSL had no systemd, so
  enabled it via `/etc/wsl.conf`; the tailnet SSH ACL was `action: check` (browser re-auth, blocks
  automation) → changed to `accept` for own devices; renamed the Kali user to `wicked5mile` to match
  Fancy; hashcat saw only the CPU until the **driverless CUDA toolkit (NVRTC)** was installed in WSL
  — and Kali's Sequoia apt rejected NVIDIA's repo over its **SHA-1 signing key**, worked around with
  `[trusted=yes]` on that one repo.
- **Note:** the `gpu-host-wsl` node is only online while its WSL distro is running. GPU speed
  (~210 kH/s) is modest for a 3070 Ti; `-O -w 4` goes faster.
- **Next:** none required — M13's GPU-offload item is closed.

## 2026-09-26 — LAB-22 hardware dry-run: authorized WPA2 handshake capture on own AP

- **What:** First hands-on run of the new M13 / LAB-22 authorized active Wi-Fi audit, against the
  owner's **own** AP (SSID "EvilLair", WPA2-PSK, 2.4 GHz ch 11) and a client the owner owns (an
  iPhone). RT5370 (`wlan1`→`wlan1mon`, `rt2800usb`), `aircrack-ng` 1.7. Monitor mode came up without
  `airmon-ng check kill`; `airodump-ng` was locked to the BSSID/channel; one targeted
  `aireplay-ng --deauth 3 -a <BSSID> -c <iPhone> wlan1mon` forced the reconnect.
- **Result:** handshake captured — `aircrack-ng handshake-01.cap` → `EvilLair  WPA (1 handshake)`.
  The full LAB-22 path validated on real hardware: monitor-up (rename to `wlan1mon`,
  `net.monitor_ifaces`=1), capture (`.cap` written), deauth, verify (the `[1-9][0-9]* handshake`
  check flips 0→1 as designed), teardown (`wlan1` back to managed, no monitor iface). `wlan0` stayed
  associated to EvilLair throughout — the session link never dropped. Capture kept off-repo in
  `~/labs/wpa/` (root-owned; `*.cap` is gitignored); the crack was not run on-device.
- **Safety catch:** the "natural" deauth target `aa:bb:cc:dd:ee:04` turned out to be
  **gpu-host** — the owner's SSH source — matched via `tailscale status` (direct endpoint
  `192.168.x.y`) against the neighbour table. Deauthing it would have dropped the SSH session.
  Retargeted to the owner's iPhone (`aa:bb:cc:dd:ee:03`, Apple OUI). `wlan0`
  (`aa:bb:cc:dd:ee:7e`) and gpu-host were both held on a never-deauth list; no broadcast deauth.
- **Findings folded into LAB-22 / the runbook:** (1) Fancy's default locale is empty, so
  `airodump-ng` prints a non-UNICODE-terminal warning — added `export LANG=C.UTF-8` to the
  workdir/capture step. (2) the `~/labs/wpa` working dir must exist before capture (already created
  by the workdir step; skipping it fails with a clear `Could not create "…csv"`).
- **Photos:** none this session.
- **Next:** optional — validate the GPU crack-offload path (runbook 5b) with hashcat against the
  kept capture on gpu-host/homeserver (hashcat setup is out of this repo's scope).

## 2026-09-25 — Correction: why onboard Ethernet didn't link until 2026-09-23

- **What:** The device owner corrected the recorded cause of the checklist 2.2 failure. The RJ45
  jack is on the **AIO V2**, not the mainboard. The AIO V2's Ethernet ribbon plugs into the port
  marked **"CM5 USB 3.0"** on the HackerGadgets CM4/5 Adapter Pro (#11953, the dual-18650-holder
  kit). The uConsole kit's `RPi CM4 to CPI v3.14 Adapter` has no such port, so the ribbon had
  nowhere to plug in until the Adapter Pro arrived.
- **Result:** Docs that said the adapter "lacked the RGMII ribbon" and that `eth0` used "the
  mainboard's RJ45 jack" are corrected: `known-issues.md`, `decisions.md`, checklist 2.2, `TODO.md`,
  `CHANGELOG.md`, the mainboard, AIO V2 and upgrade-kit specs, the earlier entries in this log, and
  the talk. The corrected account fits the 2026-09-20 observations better: the PHY is on the CM4
  module, so it answered over MDIO, but its line side had no path to the AIO V2's jack, whose
  LEDs stayed lit with no cable because nothing behind them was connected. Which signals the
  ribbon carries is *unverified*.

## 2026-09-25 — First passive Wi-Fi survey (LAB-15, RT5370)

- **What:** The owner ran LAB-15 on Fancy, 17:10–17:20 UTC, EM95, indoors: the RT5370 (`wlan1`,
  `rt2800usb`) on an external USB port, NetworkManager leaving it unmanaged, Kismet 2025.09.0 in
  the foreground with the staged site config, 2.4 GHz channels 1–11 at 5 hops/s. The GPS rail was
  off, so no fix. Finding:
  [`2026-09-25-wifi-survey.md`](../../knowledge/wardriving/findings/2026-09-25-wifi-survey.md).
- **Result (counts only):** 4 Wi-Fi APs, 23 clients, 4 bridged. APs: 2 WPA2-PSK, 2 unknown (heard
  without a beacon); APs on channels 1, 3, 10, 11. Monitor mode held in all 58 ten-second samples.
  Packet log: 1,400 packets — 651 management, 749 control, **0 data, 0 EAPOL** — so
  `kis_log_data_packets=false` with `dot11_keep_eapol=false` keeps both out of the log. The
  device-type query returns sqlite3 list rows like `IEEE802.11|Wi-Fi AP|4`. `sqlite3` installed.
  The `.kismet` log was deleted after the counts were taken.
- **Problem 1 — Kismet couldn't start:** `FATAL: Could not initialize HTTP server on 0.0.0.0:2501,
  could not bind socket - Address already in use`. `tailscale serve` holds `:2501` on the tailnet
  address, the same clash as meshtasticd's `:9443`. Fixed with `httpd_bind_address=127.0.0.1` in
  [`kismet_site.conf`](../../configs/kismet/kismet_site.conf) (deployed); `tailscale serve` still
  proxies `http://localhost:2501`. Very likely the root cause of the service crash loop
  ([`known-issues.md`](known-issues.md)); `systemctl start kismet` not yet re-tested.
- **Problem 2 — `wlan1mon` left behind:** Kismet does not rename `wlan1`; it adds a separate
  `wlan1mon` monitor interface (`wlan1` stays managed — webdash counted `monitor_ifaces=1`,
  `wlan1` managed) and left it up after a clean Ctrl-C exit (still there 55 s later). Removed with
  `sudo iw dev wlan1mon del`; LAB-15, lesson M7.3, the survey runbook and
  [`software/kismet.md`](../../software/kismet.md) now say so.
- **Next:** re-test `sudo systemctl start kismet` with the adapter in; a GPS-tagged survey; 5 GHz
  once the AC1200 arrives.

## 2026-09-25 — Learning platform MVP built (S3–S10)

- **What:** Built the rest of the MVP on `claude/learning-mvp-20260924`: curriculum compiler and
  lints (S3), `#/learn` pages (S4), SQLite progress (S5), server-side lab engine (S6), server-graded
  checks (S7), review queue, notes and endorsements (S8), content sync from `main` with an Owner
  view (S9), and Track A content — M0, M1, M1b, M3, M4, M6 with 8 labs — plus six gap docs (S10).
- **Result:** Verified on the device: LAB-12 end to end from live readsb (SDR rail on, 9.2 msg/s,
  aircraft with position, rail off, pass); LAB-01, LAB-05 end to end; LAB-04 up to its paste step
  (regex fixed afterwards); grading with required items; endorsements; drift detection on a
  throwaway branch; 10 unit tests pass. All test progress was cleared afterwards. **Not verified:**
  LAB-02 (needs the charger unplugged), LAB-06 (needs a packet from another node — the mesh has
  been quiet, `num_packets_rx=0`), LAB-08 (not run, to avoid stopping readsb unattended). The
  senior-rf-engineer review of Track A was cut off by a usage limit and still has to run.
- **Next:** merge to `main`, then install the learn-sync timer
  (`webdash/host-helpers/learn-sync.service` header) — until then it would fail, because `main` has
  no curriculum.
- **Update, same night:** merged to `main` (`3a5593f`) and pushed. A manual `learn-sync.py` run
  compiled `main` cleanly (0 modules flagged). The user timer `learn-sync.timer` is installed and
  enabled (15 min cadence; first timed run exited 0). Lingering is off, so it runs only while the
  owner is logged in.

## 2026-09-24 — Learning-platform S2: new status fields; first webdash-side ADS-B decode

- **What:** Build step S2 of [`learning-platform-plan.md`](../reference/learning-platform-plan.md).
  The aiov2 bridge gained a read-only `GET /services` (fixed `systemctl show` for readsb, gpsd,
  meshtasticd, Kismet). `/api/status` gained `aiov2.power_num` (numbers), `gps.hdop`/`pdop`/
  `eph_m`/`tpv_age_s`/`grid`, `adsb.messages_per_s`, `mesh.rx_packets`/`rx_nodes`/`last_rx_*`, and
  `services.*` (`active`, `sub`, `n_restarts`, `crash_looping`). Bridge restarted, container rebuilt.
- **Result:** Verified on the device: readsb reported `crash_looping: true` with the SDR rail off
  (357+ restarts, the normal state); GPS 3D fix, 12 of 17 satellites used, HDOP 1.1, grid EM95;
  power 4.2 V / 0.84 W on AC. With the SDR rail switched on for ~80 s: readsb went `active`,
  2–3 aircraft, 2 with position, **7.5–18.5 messages/s**; rail switched back off. The aircraft
  data means checklist 3.7 should pass, but the tar1090 map itself was not looked at, so it stays
  open. `mesh.rx_packets` read 0 during the test — the mesh was quiet — so the counter itself is
  still *unverified*.
- **Note:** a `docker exec` that imported the collectors opened a second meshtasticd client,
  which briefly displaces webdash's (single-client API). Test through `/api/status` instead.
- **Next:** S3 (curriculum compiler).

## 2026-09-24 — Checklist 2.5 passes: Tailscale SSH, tailnet-only by design

- **What:** The owner logged in from `gpu-host` (Windows, `100.x.y.z`) over the tailnet.
  On the device: `RunSSH: true` in the Tailscale prefs, and `tailscaled be-child ssh` holds the
  login shell (started 19:52:17). `ssh`/`sshd` are inactive and nothing listens on :22, so there
  is no LAN SSH (LAN address `192.168.x.y` on `wlan0`).
- **Result:** The owner chose **tailnet-only by design** over installing `openssh-server`. The
  2.5 criterion changed from "LAN and tailnet" to tailnet-only (`decisions.md`), and
  `headless-access.md` §1 is marked not used. **Checklist 2.5 passes; the scorecard is 17 of 22.**

## 2026-09-24 — SDR PPM measured: ≈ +1 ppm; checklist 3.6 passes

- **What:** The owner ran `rtl_test -p` with `readsb` stopped, for 12.5 min warm, straight after
  the first real reception (NOAA Weather Radio, below).
- **Result:** The cumulative PPM settled between **0 and +2**, so the figure is **≈ +1 ppm**. The
  occasional single readings of −5 or −17 recovered on the next line. That pattern is USB timing
  jitter on the CM4's shared USB 2.0 bus (`rtl_test -p` measures samples delivered against the
  system clock), not crystal drift. 0–2 ppm is excellent for an RTL-SDR (common dongles read
  20–60 ppm) and fits the clear weather-radio audio at `-p 0`. Recorded in
  `knowledge/sdr/configs/gain-and-sample-rate-profiles.md`. The runbooks now default to `PPM=1`.
  **Checklist 3.6 passes; the scorecard is 16 of 22.**
- **Next:** `readsb` back on (`sudo systemctl start readsb`). The deck scorecard text is updated,
  but the deck has not been re-rendered.

## 2026-09-24 — SDR decoder packages installed

- **What:** Installed the tools the SDR runbooks pipe into: `multimon-ng` 1.3.1, `sox` 14.4.2,
  `rtl-ais` 0.3 and `direwolf` 1.7, all from Debian apt (plus `libsox3` and its ALSA/base
  format modules). Compared enabled systemd units before and after.
- **Result:** All four binaries are on PATH. **No new service enabled.** `direwolf` ships
  `direwolf.service`, which stays disabled and inactive, so nothing new competes with `readsb`
  for the SDR or with `aplay` for the sound card. Updated the runbooks' notes from "needs: apt
  install" to "uses: … (installed)".
- **Not verified:** none of the four has decoded a real signal yet (APRS, NOAA, AIS).

## 2026-09-23 — SDR runbooks: `<ppm>` placeholder broke every `rtl_fm` command

- **What:** Running the VHF/UHF runbook, the owner got `No such file or directory` and
  `read_header: 2964: read error`. Bash read `-p <ppm>` as input redirection from a file named
  `ppm`, so `rtl_fm` never started, and `aplay` (no `-t raw`) found no header on the empty pipe.
  Fixed six `knowledge/` docs: they set `PPM=0` (unmeasured, checklist 3.6) and use `-p "$PPM"`,
  stop `readsb` first, use `aplay -t raw ... -c 1`, and replace `<repeater-output>` with a
  `REPEATER=` variable. Each names the missing packages it needs (`multimon-ng`, `sox`,
  `rtl-ais`, `direwolf`; all in apt, none installed). Added PPM and RepeaterBook "Access"
  explanations to the VHF/UHF runbook.
- **Result:** With the fix, the pipeline starts and `aplay` reads raw audio. The first test found
  no SDR: the owner had switched the SDR rail off from webdash (`gpu-host`, 23:13:58). Rail
  back on, the dongle re-enumerated, and `readsb` restarted cleanly (R820T found).
- **Audio path verified (owner, 2026-09-24):** static heard on every frequency tried with the
  fixed command, which proves SDR → `rtl_fm` → `aplay` → speaker end to end. **Not yet verified:**
  a real transmission (voice on a repeater output, or an APRS decode). Static alone doesn't prove
  reception.
- **First real reception (owner, 2026-09-24):** NOAA Weather Radio voice heard clearly on
  **162.475 MHz** with `rtl_fm -M fm -s 24k -g 35 -p 0` into `aplay -t raw`. The whole receive
  chain works on a real signal. Intelligible NBFM with no PPM correction suggests the dongle's
  error is modest, but it's still *unmeasured* (checklist 3.6).

## 2026-09-23 — doc-review agent; ~20 stale claims fixed

- **What:** Added a read-only `doc-review` agent (`.claude/agents/doc-review.md`) that checks
  documented claims against the newest dated evidence and the live device. It is triggered every
  8 h of active working time by `.claude/hooks/doc-review-timer.py` (project hooks on
  `UserPromptSubmit` and `Stop`). Ran it twice over the whole repo. The first run missed
  `webdash-architecture.md:22` ("NVMe board (#11953) is still pending"). So I added
  `.claude/scripts/doc-review-candidates.py`, which lists every line with stale-prone status
  wording (77 at the time), and made a verdict on each line mandatory. The second run caught line
  22, but passed two microSD lines that the first run had correctly flagged. **Verdicts vary
  between runs; treat an "ok" as likely, not proven.**
- **Result:** Fixed the union of both runs' findings in 17 files. Where a fix states device state,
  I confirmed it on the device: no `mmcblk0`, root on `nvme0n1p2` with ~208 GB free, and the
  `config.txt` overlays match the CM4 column of `pinout-gpio.md`. The candidate count went from
  77 to 68. Timer baseline recorded at `3e084fd`.
- **Next:** The timer asks for the next review after 8 h of active work. It counts only Claude
  Code sessions started inside this repo.

## 2026-09-23 — Meshtastic silence was a frequency mismatch; moved to SCMesh primary

- **What:** The owner plugged a Heltec V3 (CP2102, `/dev/ttyUSB0`) into the USB port.
  `meshtastic --port /dev/ttyUSB0 --info` showed it on US `LONG_FAST` with an **SCMesh primary**.
  It had heard the owner's M5Stack C6L "Wicked5" (SNR 6 dB) and nothing else. Hashing the channel
  names put the Heltec at slot 88 (924.125 MHz) and this node's LongFast primary at slot 19
  (906.875 MHz), which matches meshtasticd's own `ch=19` log line. Stopped the webdash container
  to free meshtasticd's single API slot and saved `--info`. Then `--ch-index 0 --ch-set name
  SCMesh` and `--ch-index 1 --ch-del` (the old SCMesh secondary). NCMesh is now index 1.
  Restarted webdash.
- **Result:** meshtasticd logged `Set radio: region=US, name=SCMesh, ch=88` and `Radio freq=924.125`.
  It then logged `Received nodeinfo from=0x433ef4a8` (the Heltec).
  `meshtastic --traceroute '!433ef4a8'` got a route both ways (6.5 dB out, 6.25 dB back). **The
  receiver works; the earlier silence was the frequency, not the area and not the hardware.** The
  21:39 stats line showed `num_packets_rx=2`. The first-packet alert fired, logged its line to
  `~/meshtastic-first-packet.log` and disabled itself. Checklist 3.9 passes. The first DM NAKed
  `PKI_SEND_FAIL_PUBLIC_KEY` because node info hadn't been exchanged yet. Once it had, **direct
  messages went both ways with ACKs** (21:44). meshtasticd logged `Received text msg
  from=0x433ef4a8`. **Checklist 3.10 passes.** The webdash container was stopped for each CLI
  session and restarted afterwards.
- **Also seen:** the Heltec reports `rebootCount: 28833`, which suggests a past reboot loop
  (often brown-out on weak USB power). *Unverified.*
- **Next:** None for the LoRa link. The scorecard moves to 15 of 22 (3.9 and 3.10); the deck has
  not been re-rendered.

## 2026-09-23 — Meshtastic: nothing heard; first-packet alert installed

- **What:** Checked why the mesh looks empty. Read meshtasticd's LocalStats in the journal, then
  paused `readsb` for a 3-minute `rtl_power` scan of 905.6–908.2 MHz (1 s intervals, 25 kHz bins)
  on the AIO SDR. `readsb` was restarted afterwards. Then wrote and installed a one-shot
  first-packet alert (`configs/meshtastic/first-packet-alert.*`) as an enabled user service.
- **Result:** Over ~4 h of uptime on US LongFast (906.875 MHz), meshtasticd reported
  `num_packets_rx=0`, `num_packets_rx_bad=0`, `channel_utilization=0.0` and a noise floor of
  -93 dBm. It reported `num_total_nodes=2`, so one other node was probably heard at some point.
  The radio initialized cleanly (`SX126x init result 0`). The SDR scan found the LongFast channel
  more than 10 dB above its neighbours in only 2 of 180 s, with ISM activity across the whole
  span. That reads as no mesh in range of an indoor stub antenna, but a receive fault is not ruled
  out. The alert's parser passed dry runs (decoded, bad, none, and a real stats line). A
  notification sent from a user-service context reached the desktop, and the service can read
  meshtasticd's journal.
- **Not verified:** the alert firing on a real packet.
- **Next:** Check a public node map for nodes near EM95. Put the device by a window or outdoors
  for an hour. A second node (checklist 3.10) would settle whether receive works.

## 2026-09-23 — PyGPSClient connected to gpsd (TCP relay replaces UDP)

- **What:** Set out to connect PyGPSClient to the `gps2udp` relay from the entry below, and found
  it could never work. PyGPSClient's UDP mode is a client: it `connect()`s to the server port and
  sends an empty datagram. It never binds 50010, so the datagrams `gps2udp` sent there went
  nowhere. Wrote `configs/gpsd/gpsd-nmea-relay.py` to replace it: a stdlib-only TCP server on
  `127.0.0.1:50010` that opens a gpsd session per client with `?WATCH={"nmea":true}` and forwards
  only NMEA. Installed it to `~/.local/bin/gpsd-nmea-relay` and pointed the `pygpsclient-gpsd`
  wrapper at it.
- **Result:** `nc` receives NMEA. `pynmeagps` (PyGPSClient's parser) decoded every sentence type
  (GGA, RMC, GSA, GSV, VTG, ZDA, GLL, TXT). A second client connects cleanly after the first
  disconnects. PyGPSClient itself, launched on `:0` with its default socket settings (TCP IPv4,
  `localhost`, `50010`) and connected through its own socket-connect handler, reported a **3D fix,
  11 of 12 satellites used, HDOP 1.0** after 20 s. No PyGPSClient config file was needed.
- **Not verified:** clicking the connect button by hand (the handler was called from a script,
  with no `xdotool` on the image). It is the same code path.
- **Next:** None for PyGPSClient.

## 2026-09-23 — Checklist 3.3 (GPS fix) passes

- **What:** Ran checklist 3.3 against gpsd (`/dev/serial0`, GPS rail on). Sampled `gpspipe -w`
  for 30 s, then turned the averaged position into a Maidenhead grid square so no raw coordinates
  were written down.
- **Result:** **Pass.** All 150 TPV reports were a 3D fix (`mode 3`). `SKY` showed 12 satellites
  visible and 9 used (8 GPS, 1 GLONASS; SNR 15–33 dB-Hz), with HDOP 0.9 and PDOP 1.9. Estimated
  error was about 17 m horizontal and 37 m vertical, and the position stayed within 1 m over the
  run. Grid **EM95**, altitude about 189 m MSL. Both are plausible for this location. GPS time
  matched system time.
- **Not measured:** time to first fix. The receiver was already warm, so it doesn't show
  cold-start behaviour.
- **Next:** Measure a cold-start fix time under open sky if it matters for field use.

## 2026-09-23 — PyGPSClient installed, fed from gpsd over UDP

- **What:** Audited the `aiov2_ctl --add-apps` companion apps against what's installed. Four of
  the five have substitutes; only `pygpsclient` was missing. Installed it (v1.7.6) from PyPI into
  `~/.venvs/pygpsclient` and symlinked it to `~/.local/bin/pygpsclient`. No `sudo` needed; `pipx`
  isn't installed, so this uses the same venv pattern as the `meshtastic` CLI.
  PyGPSClient has no gpsd client, and opening `/dev/serial0` directly would compete with gpsd. So
  added `~/.local/bin/pygpsclient-gpsd`, which runs `gps2udp -n -u 127.0.0.1:50010` for as long as
  PyGPSClient is open, plus a `.desktop` menu entry that launches it.
- **Result:** The venv imports cleanly and the GUI opens on `:0` (ran until the test timeout).
  The wrapper kills the relay on exit. A `nc -u` listener got 48 NMEA lines on UDP 50010 in 4 s.
  gpsd reported a **3D fix** (`TPV mode 3`) during this session, the first logged fix since gpsd
  was re-enabled 2026-09-21. Not recorded against checklist 3.3 yet.
- **Next:** Connect PyGPSClient to Socket → UDP IPv4 → `127.0.0.1:50010` in the GUI and save the
  config. Run checklist 3.3 properly (satellite count, fix time).

## 2026-09-23 — webdash redesign phase 3: stations, router, status strip

- **What:**
  - Replaced the two-section panel page with an overview of six station tiles and a hash-routed
    detail view per station.
  - Added a sticky status strip (power, CPU temp, rail chips) and put each rail switch on its
    station tile.
  - Split `app.js` into ES modules under `app/static/js/`.
  - Removed the Kismet frame. The tar1090 frame now loads only on `#/sdr`.
  - GPS shows a grid square by default.
  - The Mesh tile counts unread messages and names the other nodes known.
- **Merged first:** `claude/mesh-messaging-20260923` and `claude/webdash-phase1-2-20260923` into
  `main`.
- **Verified in headless Chromium on the device:**
  - The overview's scroll height is exactly 480 px at 1280×480, so nothing scrolls.
  - Each of the six routes shows only its own view and moves focus to that view's heading.
  - Back and forward work, and an unknown hash falls back to the overview.
  - All 11 rail switches match the bridge's rail state.
  - The tar1090 frame stays unloaded off `#/sdr`.
  - No console errors (after adding an empty favicon; `/favicon.ico` was 404ing).
- **Not verified:** a real rail toggle from a tile. Rails were left as they were.

## 2026-09-23 — webdash redesign phases 1–2

- **Phase 1:**
  - Removed the Meshtastic iframe and replaced it with a known-issue note. The link shows only if
    a TCP probe of `:9443` succeeds.
  - Panel status is now colour, glyph and word, combining each service with its rail. With the
    LORA rail off, Meshtastic reads "rail off" instead of green.
  - Rail switches are `button[role=switch]` with a visible focus ring and an inline error on
    failure.
  - Every panel's values are built with `textContent` (no `innerHTML` left in `app.js`).
  - The CPU % reading is primed so the first value isn't 0.
  - Fixed the unclosed `<span>`s in `index.html`.
  - The ADS-B "Open map" link is hidden until readsb runs.
  - The mesh panel spans two columns at ≥900 px.
- **Phase 2:** one collection task every 3 s shared by all clients; `GET /api/history` (2 h at
  30 s, in memory).
- **Verified on the device**, with headless Chromium through DevTools, logged in with a session
  cookie:
  - Screenshots at 1440 px, 1280×480 and 390 px.
  - Tab reaches `rail-GPS` with `role=switch`, name "GPS", and a solid `#facc15` outline.
  - Statuses read `○ off` (Kismet), `◐ searching` (GPS), `○ rail off` (ADS-B), `● live` (mesh).
  - `/api/history` needs a session (401 without one).
  - gpsd connections per minute were 18 with no clients and 16 with three extra WebSocket
    clients.
- **Not verified:** the mesh dot going to "rail off" was checked by code path only; the LORA rail
  was not switched off, to avoid interrupting the mesh.

## 2026-09-23 — webdash design review by six agents; four messaging bugs fixed

- **What:** Added six agent definitions to `.claude/agents/`: design-planner, creative-director,
  web-ui-engineer, syllabus-designer, tutor and guided-learning. Ran all six read-only against
  webdash plus screenshots taken on the device (headless Chromium at 1440 px, 1280×480 and 390 px).
  Merged their reports into [`../reference/webdash-design.md`](../reference/webdash-design.md).
- **Fixed from the review** (in the mesh-messaging change, same day):
  - The message log froze at 200 messages. Messages now carry a monotonic `id`. Checked in the
    container by appending 205 messages: 200 kept, last `id` 205.
  - The browser now checks the byte limit.
  - Send no longer defaults silently to channel 0.
  - Mesh panel values are escaped.
  - Meshtastic battery 101 shows as "external power".
  - SNR shows units, and RSSI is shown.
- **Not verified:** no message sent or received over the air yet; redesign not built.

## 2026-09-23 — webdash: mesh text messaging

- **What:** Added a message log and send box to webdash's Meshtastic panel, because the embedded
  Meshtastic web UI is still down (see [`known-issues.md`](known-issues.md)). Modelled on
  CyberDeck's webdash; design in
  [`../reference/webdash-architecture.md`](../reference/webdash-architecture.md#mesh-text-messaging).
- **Radio state before the change:** `meshtasticd` running, `sx1262 init success`, US / LongFast
  906.875 MHz, LORA rail on. Its telemetry showed `num_packets_tx=2, num_packets_rx=0` and 0
  nodes online after about 5.5 h. The radio has not yet heard another node.
- **Verified on the device:** container rebuilt and connected to `127.0.0.1:4403`. Both new routes
  return `401` without a session. `GET /api/mesh/messages` returns the channels `LongFast`,
  `SCMesh` and `NCMesh`. A 300-byte message is rejected before sending and an empty one returns
  `422`. The primary channel now shows its preset name (`LongFast`) instead of `channel-0` in the
  status panel as well.
- **Not verified:** nothing was transmitted. Over-the-air send and receive need a second node in
  range.

## 2026-09-23 — Private Internet Access and LastPass CLI installed

- **What:** Installed two owner-requested tools. Not part of bring-up.
- **PIA:** official ARM64 app `pia-linux-arm64-3.7.2-08420.run` from
  `installers.privateinternetaccess.com` (SHA-256
  `3956d1ed9b6977f24ca960e78dd60572edd435f71b2a554e5c5d00f94603eeb9`; makeself MD5 check passed).
  Run as the extracted `install.sh` because the `.run` wrapper tries to open an X terminal when it
  has no TTY. Installs to `/opt/piavpn`, `piavpn.service` enabled and active, `piactl` 3.7.2.
  **Not logged in and not connected.** Tailscale still works with PIA installed but disconnected;
  *unverified* whether Tailscale and webdash's `tailscale serve` survive a PIA connection,
  especially with PIA's kill switch or its DNS on.
- **LastPass CLI:** `lastpass-cli` is not packaged for Debian 13, so v1.6.1 was built from
  `github.com/lastpass/lastpass-cli` (source in `~/src/lastpass-cli`) and installed to
  `/usr/local/bin/lpass`. Not logged in. Updates are manual: `git pull`, rebuild, reinstall.
- **Discord:** there is no official ARM64 Linux client, so it runs as the official web app in a
  Chromium app window. The launcher is `~/.local/share/applications/discord-web.desktop`
  (`chromium --app=https://discord.com/app`). Third-party clients (Vesktop, Legcord) were not
  used, because they carry client mods that break Discord's terms.
- **Node.js 20 + marp-cli 4.5.1:** Node is from Debian; marp-cli is installed per-user under `~/.local`.
  Used to render the talk deck (see `presentation/README.md`).

## 2026-09-23 — `JP1` open, reverse-polarity LED unlit; checklist 1.7 passes

- **What:** The device owner looked at the NVMe battery board with the interim 18650 pair fitted.
- **Result:** `JP1` is **open**, the correct setting for 18650s. The reverse-polarity LED is **not
  lit**, so both cells are the right way round. That was the last part of checklist 1.7, which now
  passes. The LED is a diagnostic, not a fuse ([`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md)).
- **Not recorded:** `JP1`'s location on the board (no photo), and the JST connector's pitch and
  polarity.
- **Next:** before the Meshnology LiPo goes in, solder `JP1` closed and meter the JST polarity at
  both ends. The 18650 weigh/voltage checks are still open.

## 2026-09-23 — Baseline backup to `homeserver`

- **What:** File-level baseline backup of the NVMe install, streamed over SSH (tailnet) to
  `homeserver:~/backups/fancy/2026-09-23-baseline/`, 02:49–03:41 UTC. File-level rather than a raw
  `dd` because the system was live and the reused drive's free space holds old data.
- **Contents:** `nvme0n1.sfdisk` (partition table, `sfdisk -d`), `blkid.txt` (PARTUUIDs
  `e10af45d-01/-02`), `boot-firmware.tar.zst` (31 MiB), `rootfs.tar.zst` (3.3 GiB, 213 338
  entries; `--one-file-system --xattrs --acls --numeric-owner`, excludes `/var/swap` and cached
  `.deb`s). The live root had 213 968 entries at the check afterwards — the difference is the
  exclusions plus files written during the run.
- **Verification:** `zstd -t` passes on both archives; `tar -t` reads the root archive to the end;
  spot-checked `etc/fstab`, this repo, `/var/lib/docker/`, the meshtasticd LoRa config,
  `cmdline.txt` and `config.txt`. **A test restore has not been done.**

  ```
  6828fe22f37c93ca4f1ab53c8645f3bb2dd2cb941995ae4d1c433b46cb54956e  boot-firmware.tar.zst
  ba15a153eb89e2915a51c2719fa9107760b056c90b709bd2f35462d4d7fcecab  rootfs.tar.zst
  7cb118820fb709a26fd3c526296861cb45796023850878c4a546ff85e34f4ccc  nvme0n1.sfdisk
  ccf36e8d4d7387e4bf8f19d60d9a829b47ad921d4a7fc2618566f19dc7201f11  blkid.txt
  ```

- **Findings:** `tar` exited 1 on `./sys: file changed as we read it` (the mountpoint, harmless),
  which stopped the script before its checksum step; checksums were run by hand. The tailnet path
  to `homeserver` is relayed — `tailscale ping homeserver` gets no reply — so throughput was ~1.1 MB/s
  average. A LAN path would be much faster for the next backup.
- **Restore outline:** `sfdisk /dev/nvme0n1 < nvme0n1.sfdisk`, `mkfs.vfat` p1 and `mkfs.ext4` p2,
  extract each archive with `tar --numeric-owner --xattrs --xattrs-include='*' --acls -xpf`. The
  partition table carries the disk ID, so the PARTUUIDs in `cmdline.txt` and `fstab` match again.
- **Next:** do a test restore onto the spare microSD or another drive.
- **Also this session:** installed the fixed Kismet udev rules from `configs/udev/`
  (`udevadm verify` 3/3 pass on the installed files; udev reloaded).

## 2026-09-23 — Power budget re-sized to 37 Wh; boot-log warnings triaged

- **What:** Software-only follow-ups, no hardware touched.
- **Power budget:** [`../reference/power-budget.md`](../reference/power-budget.md) runtimes rebuilt
  on the measured ~5.0 W cell-side idle plus measured rail deltas, against the Meshnology 37 Wh
  pack. Terminal work drops from the earlier ~9 h estimate to **~6 h**. Measured charge rate
  (1.96 A) added. Stale 55.5 Wh notes corrected in `accessories.md`, `mechanical.md`,
  `inventory-and-inspection.md`, `decisions.md` and the Meshnology invoice note.
- **SPI warning:** from SPI0, not the LoRa bus; `sx1262 init success` this boot. Harmless — see
  [`known-issues.md`](known-issues.md).
- **Kismet udev rules:** root cause found (`$` needs doubling in udev `PROGRAM`). Fixed copies in
  [`../../configs/udev/`](../../configs/udev/) pass `udevadm verify`. **Not installed** — the
  write to `/etc` was blocked in this session; needs the owner to run the install line.
- **Next:** install the udev fix; back up the baseline image.

## 2026-09-23 — NVMe-only boot verified; `resize` dropped; no RTC cell fitted

- **What:** The device owner removed the microSD and rebooted. This session checked the boot at
  01:48 UTC (uptime ~1 min). Runbook step 5 of [`../runbooks/nvme-boot.md`](../runbooks/nvme-boot.md).
- **Result — NVMe-only boot (PASS):** No `mmcblk0` device present. `/` is `nvme0n1p2` and
  `/boot/firmware` is `nvme0n1p1`. `/proc/cmdline`, `cmdline.txt` and `/etc/fstab` all reference
  `PARTUUID=e10af45d-01/-02`, the NVMe partitions. `BOOT_ORDER=0xf416` (NVMe, SD, USB, repeat).
  `systemctl --failed` is empty. This boot's error-level log holds only pre-existing noise: the
  three `99-kismet-*.rules` udev rules are rejected for invalid `PROGRAM` syntax, and
  `spi-bcm2835 fe204000.spi: prop pinctrl-0 index 1 invalid phandle` (*unverified* whether that
  affects the SX1262 on SPI1). The card is kept as a fallback; with NVMe first in the boot order it
  only boots if the NVMe fails.
- **Change — `cmdline.txt`:** removed the leftover `resize` flag. Root already fills the drive, so
  it did nothing. Backup at `/boot/firmware/cmdline.txt.bak`. Takes effect next boot.
- **Finding — RTC:** the owner reports **no coin cell is fitted** in the RTC holder. That settles
  the cause of the 2026-09-23 RTC power-loss issue. This boot was a warm reboot, so the RTC kept
  its time (`setting system clock to 2026-09-23T01:47:19 UTC`); it will lose it on any full power
  removal. `accessories.md` lists the cell as a CR1220 — *verify the holder size before buying*.
- **Photos:** none this session.
- **Next:** Fit the RTC cell and run checklist 3.1. Remaining follow-ups: `JP1`/pack, the
  reverse-polarity LED, and the 18650 weigh/voltage/capacity checks.

## 2026-09-23 — RJ45 + USB3 board USB ports verified

- **What:** The device owner plugged a USB device (Baochip Baosec-lite, `1d50:6198`) into the
  RJ45 + USB3 board. This session re-checked enumeration (01:40 UTC). It follows up the unverified
  QinHeng hub from the NVMe entry below.
- **Result (PASS):** The device appeared at `1-1.4.1`, meaning port 1 of the QinHeng `1a86:8091`
  hub, which is itself on port 4 of the Genesys `05e3:0608` hub. It negotiated **480M (USB 2.0
  high-speed)**, the most a CM4 can do. `usbhid` bound its two HID interfaces and `cdc_acm` its
  serial interface (`/dev/ttyACM1`, with a `/dev/serial/by-id/` link). It asks for 100 mA and
  logged no over-current. **The QinHeng hub is the RJ45 + USB3 board's hub.** It is powered
  independently of the AIO V2 `USB` rail, which was off (GPIO23) throughout. The first two
  full-speed enumeration attempts failed with `device descriptor read/64, error -32` before the
  third came up at high speed. That reads as contact bounce during insertion, not a fault, but
  watch for it on other devices.
- **Photos:** none this session.
- **Next:** Remaining follow-ups: NVMe-only boot with the card removed, `JP1`/pack, the CR1220,
  and the reverse-polarity LED.

## 2026-09-23 — Ethernet links at 1 Gbps; charging confirmed

- **What:** The device owner plugged in a live Ethernet cable, then the charger, and this session
  re-ran checklist 2.2 (01:35 UTC) and the charge half of 1.7 (01:37 UTC).
- **Result — Ethernet (PASS):** `bcmgenet ... eth0: Link is Up - 1Gbps/Full - flow control
  rx/tx`. `ethtool` reports `Speed: 1000Mb/s`, `Duplex: Full`, `Link detected: yes`, and
  `mii-tool` reports `negotiated 1000baseT-FD flow-control, link ok`. NetworkManager brought up
  `Wired connection 1` with DHCP `192.168.x.y/24`, and `eth0` took the default route (metric
  100) ahead of `wlan0` (600). `ping` over `eth0`: 5/5 to the gateway (avg 1.4 ms) and 3/3 to
  `1.1.1.1` (avg 13.6 ms). Downloading 100 MB over `eth0` gave 10.3 MB/s from Hetzner, 6.0 MB/s
  from OVH, and a partial 0.5 MB/s from Tele2. That points to the internet connection or the
  remote server as the limit, not the link. **The LAN rate was not measured**, because no
  `iperf3` peer was available. Counters after ~240 MB: 0 RX errors, 11 TX drops.
  `mdf_err_cnt` counts frames the MAC filter rejected (multicast and the like) and is not an
  error. This confirms the 2026-09-22 working theory that the interim adapter was the cause.
  *(Corrected 2026-09-25: the AIO V2's Ethernet ribbon had no port on the kit's adapter; see the
  2026-09-25 correction entry.)*
- **Result — charging (PASS, one sub-check left):** After re-plugging, `axp22x-ac online=1` and
  the battery went to `Charging`. The first sample read 4 mA, and it then held a steady **1.96 A**
  at 3.95–3.96 V, 65→66%. `aiov2_ctl --status`: `AC powering system + battery`, 7.78 W.
  `throttled=0x0`. The pack had discharged 73→65% during the ~30 min on battery before that. Still
  to check: the reverse-polarity LED, which needs someone at the board. ~2 A into the unverified
  `9900mAh` pair is ~1 A per cell, reasonable for genuine 18650s. Given the cells' provenance,
  check them for heat during the first full charge.
- **Photos:** none this session.
- **Next:** Look at the reverse-polarity LED. Measure the LAN rate with `iperf3` against another
  LAN host. Do the remaining follow-ups from the NVMe entry below: NVMe-only boot, `JP1`/pack, the
  RJ45+USB3 hub, and the CR1220.

## 2026-09-23 — HackerGadgets kit installed, boot migrated to NVMe; storage/NIC/USB/power tests

- **What:** The device owner fitted three boards from HackerGadgets #11953: the **CM4/CM5 adapter**
  (with the port for the AIO V2's Ethernet ribbon — *corrected 2026-09-25*), the **NVMe battery board**, and the **RJ45 + USB 3.0 board**.
  They also migrated root to NVMe. The SSD is the **WD PC SN730 256 GB** (SN `<ssd-serial-redacted>`), the
  first of the four candidates in [`../records/order-and-warranty.md`](../records/order-and-warranty.md).
  The Meshnology LiPo pack was **not** fitted this session. This session, from software on the
  booted system (uptime ~5 min at start, 01:10 UTC 2026-09-23), ran checklist tests 1.5–1.7, 2.2,
  2.3, 3.5 and section 4 of [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md).
  Installed `nvme-cli`, `smartmontools` and `fio` for the tests.
- **Result — boot:** Root is `/dev/nvme0n1p2` and `/boot/firmware` is `/dev/nvme0n1p1`.
  `cmdline.txt` and `/etc/fstab` both reference the NVMe PARTUUID `e10af45d-0{1,2}`, not the
  card's `21965b0c`. The microSD is **still inserted** as a fallback. Its `bootfs` gets
  auto-mounted under `/media/`, but nothing runs from it. EEPROM `2026/05/17 20:13:18`
  (`224877da`), `BOOT_ORDER=0xf416` (NVMe, then SD, then USB). `systemd-analyze`: **20.7 s** to
  `graphical.target` (1.1 s kernel + 19.6 s userspace). The slowest unit is
  `aiov2-rails-boot.service` at 9.9 s, not storage.
- **Result — storage (PASS):** PCIe link `LnkSta 5GT/s ×1`. The drive is capable of 8GT/s ×4,
  so that is the CM4's Gen2 ×1 ceiling, as expected. SMART `PASSED`, `critical_warning 0`,
  `media_errors 0`, and the one error-log entry is empty (status `0`). No NVMe/AER errors in `dmesg`. **The drive is
  second-hand and heavily used**, which the owner confirmed is expected: 25,560 power-on hours,
  47.48 TB written, `percentage_used 21%`, 55 unsafe shutdowns. That is the baseline to compare
  against later. `fio` on the NVMe root (2 GiB file, `direct=1`, 20 s each):

  | Test | Result |
  |---|---|
  | Seq read 1 MiB QD8 | 398 MiB/s (at the Gen2 ×1 ceiling) |
  | Seq write 1 MiB QD8 | 365 MiB/s |
  | Rand read 4 KiB QD32 | 55.1k IOPS |
  | Rand write 4 KiB QD32 | 36.1k IOPS |
  | Rand read 4 KiB QD1 | 11.0k IOPS, 76 µs avg latency |

  SSD temperature was 40 °C idle and 49 °C right after the run, with no thermal-management
  transitions. **Gotcha:** the first `fio` pass accidentally ran in `/tmp`, which is **tmpfs on
  trixie**, and reported 1.1 GiB/s. That is impossible over this link. Benchmark under
  `/var/tmp` or `$HOME`. This is noted in [`../runbooks/nvme-boot.md`](../runbooks/nvme-boot.md).
- **Result — NIC (partial):** `eth0` (`bcmgenet`) is up and `mii-tool -v` reads the PHY over MDIO
  (1000baseT capable). There is **no carrier because no cable was plugged in**, per the owner. So
  Ethernet through the new adapter is **installed but not yet link-tested**, and checklist 2.2 stays
  open. No USB Ethernet device enumerated. `wlan0` is associated and carries the default route.
- **Result — USB (PASS):** The Genesys `05e3:0608` 4-port hub, the keyboard (`1eaf:0024`) and a
  **QinHeng `1a86:8091` hub** enumerate, all at 480M on `dwc2`. The QinHeng hub is not in any
  earlier record, so it is presumably the RJ45 + USB3 board's hub. That is *unverified*: nothing
  was plugged into its ports. With `aiov2_ctl SDR on`, the RTL2838 enumerates on hub port 3.
  `rtl_test -s 2400000` for ~25 s lost **0 samples/million** (24 bytes total), which re-passes
  3.5. `usb_claim_interface error -6` appeared first, but that was **`readsb` holding the
  dongle**, not a USB fault. `readsb` was stopped for the test and left inactive afterwards
  (it is still `enabled` and returns on the next boot). No over-current or USB error messages in
  `dmesg`.
- **Result — power:** On battery the whole time. `axp22x-ac online=0` shows no charger was
  connected. Pack at 71–73 %, 3.63–3.68 V. The system drew **~5.3 W (1.44–1.46 A at the cell)**
  with the screen on, GPS + LoRa rails on and SDR/USB off. `aiov2_ctl --measure` rail deltas
  were: SDR +0.64 W, GPS +0.29 W, LoRa about 0, USB about 0 (nothing attached). Brief peak 7.3 W /
  2.01 A while SDR + USB were on and `rtl_test` was starting. `throttled=0x0`, SoC 63.7 °C. The
  interim 18650 pair is presumably now in the NVMe battery board's holder, but *unverified*: the
  owner did not say, and `JP1` must be **open** for 18650s. **Charging was not tested** because
  no charger was connected.
- **Result — RTC:** At boot `rtc-pcf85063` logged `POR issue detected` / `Power loss detected,
  invalid time`, so the RTC lost its time across the hardware swap. NTP resynced it and it now
  reads correctly. That suggests the CR1220 is flat, missing or not making contact. Logged in
  [`known-issues.md`](known-issues.md).
- **Photos:** none this session.
- **Next:** Plug in a live Ethernet cable and re-run 2.2. Plug a USB device into the RJ45 + USB3
  board's ports to confirm the QinHeng hub belongs to it. Connect a charger to confirm charging
  (1.7). Check `JP1` is open for the 18650s. Check the CR1220. Power-cycle with the microSD
  removed to prove NVMe-only boot.

## 2026-09-22 — `webdash`: sub-pages embedded as frames, gated by the radios

- **What:** Added inline `<iframe>` embeds for the three sub-pages `webdash` already links to
  (ADS-B map, Kismet, Meshtastic UI), each shown/hidden by the radio that backs it: ADS-B by the
  SDR rail, Meshtastic UI by the LoRa rail. Kismet isn't tied to any aiov2 rail on this build (its
  capture adapter is a plain USB dongle), so its frame is gated on its own running/locked state
  instead — called out explicitly in the docs so it doesn't look like an oversight later. GPS was
  left without a frame — gpsd has no web UI in this stack. Frames tear down to `about:blank` when
  hidden (not just `display:none`) so a flipped-off radio doesn't leave a session
  polling/rendering in the background; a frame only reloads on an actual on/off transition, not
  every ~3s status tick, so it doesn't get yanked out from under active use. The existing
  "Open ↗" links stay as a fallback in case either cross-origin target (Kismet/Meshtastic, on
  their own `tailscale serve` ports) ever blocks being framed.
- **Result:** Rebuilt and restarted the container (`docker compose up -d --build`); starts clean,
  `/api/health` OK, served static files confirmed to carry the new markup/CSS/JS. **Not
  click-tested in an actual browser** — this session has no browser attached to the device's
  display, so the frames' visual behavior (appearing/disappearing as rails toggle, actually
  rendering Kismet/Meshtastic content) is unverified; ask the device owner to confirm in person.
  Incidentally found and cleaned up a Kismet crash-loop triggered while checking whether its HTTP
  response sets framing-blocking headers (couldn't get an answer either way — see
  [`known-issues.md`](known-issues.md)); Kismet was left back in its normal stopped/disabled state.
- **Photos:** none this session.
- **Next:** confirm in a real browser that all three frames render and toggle correctly. The
  Meshtastic frame will show a connection error regardless, until the known `meshtasticd`
  webserver bug is fixed upstream.

## 2026-09-22 — Reinstalling meshtasticd did not fix the web UI failure

- **What:** Tried `sudo apt install --reinstall meshtasticd` as the next step on the web-server
  startup failure diagnosed earlier today. Backed up `/etc/meshtasticd/{config.yaml,config.d,ssl}`
  to the scratchpad first; confirmed `/var/lib/meshtasticd/.portduino` (the real node/channel
  database, holding the joined NCMesh/SCMesh state) is outside the package and untouched by any
  dpkg operation.
- **Result:** Reinstall completed cleanly; `config.yaml`'s checksum is unchanged (dpkg correctly
  left the locally-modified conffile alone). Restarted the service — **identical failure**,
  `Error starting Web Server framework, error number: 4`, same as before. Rules out a corrupted
  local install as the cause. Updated [`known-issues.md`](known-issues.md) with this negative
  result.
- **Photos:** none this session.
- **Next:** no local fix left to try short of a different `meshtasticd` build/version. Web UI
  stays down; use the CLI/GTK client/mobile app instead, as already documented.

## 2026-09-22 — Meshtastic web UI unreachable from webdash: diagnosed as a meshtasticd regression

- **What:** Investigated the report "the Meshtastic UI isn't available from webdash." Checked
  `webdash`'s own config first (`tailscale serve status`, `/api/links`), then `meshtasticd` itself
  (`ss -tlnp`, `journalctl -u meshtasticd`, cert/key validity, dependency versions, IPv6/AppArmor/
  FD-limit/disk-space checks), then searched for the exact error message externally.
- **Result:** Not a `webdash` bug. `webdash`'s `tailscale serve` mapping (`:9443 → localhost:9443`)
  and its Meshtastic data panel (via the TCP API on `4403`) both work correctly. The actual fault:
  `meshtasticd`'s own embedded HTTPS webserver (Ulfius + `libmicrohttpd12t64` + `libgnutls30t64`)
  fails to start every time — `Error starting Web Server framework, error number: 4` — reproduced
  across the current boot and three manual restarts. Ruled out cert/key mismatch, missing web
  root, port conflict, IPv6 dual-stack, AppArmor, FD limits, disk space, and dependency-version
  drift (nothing in that chain has changed since the 2026-09-16 install). This is a **regression**:
  [`../../software/meshtastic.md`](../../software/meshtastic.md) recorded the same webserver
  working on 2026-09-18 with these same certs. `journalctl` doesn't retain logs from before the
  current boot, so the exact point/cause of the regression couldn't be pinned down. A Meshtastic
  Discourse thread reports the identical error message on a different Pi, suggesting an upstream
  bug in this beta build rather than something specific to this device. Updated
  [`known-issues.md`](known-issues.md), `software/meshtastic.md`, `software/webdash.md`, and
  `docs/reference/webdash-architecture.md` to record this and stop pointing people at a working
  web UI that no longer exists.
- **Photos:** none this session.
- **Next:** no fix found. The mesh itself, TCP API, CLI, GTK client, and mobile app (Network mode)
  all still work — only the browser UI is down. If pursued further: file/search a
  `meshtastic/firmware` GitHub issue with the exact error text, or try a clean
  reinstall/downgrade of `meshtasticd`.

## 2026-09-22 — Keyboard checklist item (1.2) partially verified from software

- **What:** Ran the next checklist item, 1.2 Keyboard. Checked what a shell-only session can
  confirm: HID device enumeration and handler binding.
- **Result:** `ClockworkPI uConsole Keyboard` (event6, `sysrq`/`kbd`/`leds` handlers) and the
  separate `Consumer Control` interface (event5, carries the `Fn` media/brightness layer) are both
  present and bound, with stable `/dev/input/by-id/` symlinks; `showkey`/`dumpkeys` are installed.
  Per-key and `Fn`-layer registration is a physical test (someone at the keyboard running
  `showkey -a` and watching every key/combo register) that this session has no way to perform, so
  item 1.2 stays unchecked pending that observation.
- **Photos:** none this session.
- **Next:** confirm every key + the `Fn` layer registers in person, then check off 1.2.

## 2026-09-22 — Display checklist item (1.1) closed: Fn brightness keys confirmed

- **What:** Device owner confirmed in person that the `Fn` brightness-key combo changes the
  display's brightness level, closing the one piece the earlier software-only check couldn't see.
- **Result:** Checklist item 1.1 (Display) now passes in full.
- **Photos:** none this session.
- **Next:** move on to checklist 1.2 (Keyboard).

## 2026-09-22 — Display checklist item (1.1) partially verified from software

- **What:** Ran the next unchecked bring-up item in sequence, 1.1 Display. Checked what a
  shell-only session can confirm: `/sys/class/backlight/backlight@0` state and the DSI panel's DRM
  connector status.
- **Result:** `brightness=3` (of `max_brightness=9`), `bl_power=0` (unblanked, i.e. on);
  `card1-DSI-1` reports `status=connected`; framebuffer is `720×1280`, matching the panel spec.
  Backlight-on-at-boot is confirmed. The other half of the pass criterion — `Fn` brightness keys
  visibly changing the level — needs a person at the keyboard watching the screen, which this
  session has no way to do, so item 1.1 stays unchecked pending that observation.
- **Photos:** none this session.
- **Next:** confirm the `Fn` brightness-key behavior in person, then check off 1.1.

## 2026-09-22 — Onboard Ethernet failure re-diagnosed: interim adapter, not a mainboard fault

- **What:** Revisited the 2026-09-20 "Onboard Ethernet never links" diagnosis after the device
  owner identified the likely cause: the CM4-to-CPI adapter currently fitted is the uConsole kit's
  own basic adapter — an older model supporting CM4 only, not CM5 — which has no port for the
  AIO V2's Ethernet ribbon. The upgraded HackerGadgets adapter, part of order #11953, has one.
  *(Corrected 2026-09-25: first written as a ribbon missing from the adapter, leading to the
  mainboard's jack.)*
- **Result:** This lines up exactly with the 2026-09-20 findings (MDIO management works, RGMII
  data path doesn't) without needing to assume damage. Downgraded the standing conclusion in
  [`known-issues.md`](known-issues.md) from "probable hardware fault, may need RMA" to "expected
  behavior of the interim adapter, no RMA needed." Updated
  [`decisions.md`](decisions.md)'s CM4-adapter open question,
  [`../../hardware/specs/mainboard-v3.14.md`](../../hardware/specs/mainboard-v3.14.md), and
  [`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md) to
  match; checklist item 2.2 note revised accordingly.
- **Photos:** none this session.
- **Next:** still unverified on hardware — #11953 hasn't arrived. Re-test checklist 2.2 once the
  HackerGadgets adapter is installed; if Ethernet still fails at that point, the hardware-fault
  hypothesis is back in play.

## 2026-09-22 — Thermals recheck (checklist 1.4)

- **What:** Re-ran `sudo vcgencmd measure_temp`/`get_throttled` per the outstanding "re-check after
  longer settle" note from 2026-09-16.
- **Result:** 62.8 °C, `throttled=0x0` — statistically the same as the 2026-09-16 reading
  (62–63 °C), still above the checklist's < 60 °C idle bar, never throttled. Uptime was 1 h 04 m
  (well past "just booted"), but not a clean idle: GPS + LoRa rails are on by design now (the
  2026-09-22 standing boot config) and this checking session was itself running, so the number
  includes real background load, not a true floor.
- **Photos:** none this session.
- **Next:** still open — a deliberate 10-minute load run (to see the delta from this reading) has
  not been done. Whether 62–63 °C idle is itself a problem worth chasing (better airflow/thermal
  pad, etc.) is also still undecided — two data points 6 days apart agreeing is at least evidence
  it's a stable operating point, not a fluke or a regression.

## 2026-09-22 — Spotty Wi-Fi traced to antenna connector, fixed

- **What:** Moved the CM4's external Wi-Fi u.FL antenna lead from the connector on the mainboard
  (`CPI 3.14`) to the u.FL connector on the CM4 module itself.
- **Result:** Wi-Fi network connectivity works as expected — the general networking "spotty"
  symptom (which persisted even after the 2026-09-20 `/etc/hosts` fix) is resolved. Checklist item
  2.1 now passes. See the 2026-09-22 update to the "Networking 'spotty'"
  [known-issues.md](known-issues.md) entry.
- **Photos:** none this session.
- **Next:** none open from this fix. The mechanism (why the mainboard connector was bad) was not
  diagnosed, only the fix was verified.

## 2026-09-22 — Ran bring-up checklist's baseline-state test, found the cold-boot rail default had drifted

- **What:** Ran [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md)
  test 0 (`uname -a`, `/etc/os-release`, `aiov2_ctl --status`, `aiov2_ctl --boot-rails-status`) on
  the live device (`fancy`, Debian 13 trixie, kernel `6.12.62-v8+`, uptime since 2026-09-21 22:38).
- **Result:** `--status` and `--boot-rails-status` both report GPS and LoRa **on**, SDR and USB
  off — contradicting the "all four rails off at cold boot" answer settled 2026-09-16. Traced it
  to `/usr/local/share/aiov2_ctl/config.json`, which now holds a `rails_on_boot` block (mtime
  2026-09-17 23:42, the day after the settled note) setting GPS/LoRa to boot on. That key is only
  ever written by the `aiov2_ctl` GUI tray app's per-rail "start on boot" checkbox — no CLI flag
  touches it — so someone toggled it manually, plausibly to keep `meshtasticd`/`gpsd` alive across
  reboots, and it was never logged. Updated the stale "settled" notes in
  [`module-bringup-tests.md`](../checklists/module-bringup-tests.md),
  [`decisions.md`](decisions.md), and [`known-issues.md`](known-issues.md) to record the actual
  current state and the undocumented change. Confirmed with the device owner same-day:
  GPS/LoRa-on-boot is intentional (keeps `meshtasticd`/`gpsd` alive across reboots without a
  manual `aiov2_ctl GPS on`/`LORA on` every time) — closed as the new standing cold-boot baseline
  rather than reverted.
- **Photos:** none this session.
- **Next:** still open — re-verify against an actual power cycle rather than an already-up
  system; this run only read `--boot-rails-status`'s prediction and the config file, not a fresh
  boot.

## 2026-09-21 — CM4 antenna A/B test reverted to external u.FL

- **What:** Compared the CM4's onboard PCB antenna against its module-level u.FL connector.
  `/boot/firmware/config.txt`'s `dtparam=ant2` was commented out (`#dtparam=ant2 # ant2-ab-test`,
  backed up as `config.txt.ant2-test-backup`/`.ant2-test-preRevert`) for the onboard side of the
  test, ~16:28. The antenna lead was then moved back onto the CM4's own u.FL pad and
  `dtparam=ant2` restored, ~16:38.
- **Result:** `/boot/firmware/config.txt` carries `dtparam=ant2` (external u.FL selected). The
  edit (mtime 16:38:04) predates the current boot (`uptime -s` 16:44:21), so the running kernel
  already has it applied — no reboot needed. No signal-quality numbers from the comparison were
  recorded, so the open question in [`decisions.md`](decisions.md) (which antenna performs
  better in the shell) stays open even though the selection itself is settled back to external.
  The leftover test-backup files (`config.txt.ant2-test-backup`, `.ant2-test-preRevert`) were
  removed from `/boot/firmware/` after confirming they matched the restored and superseded
  states respectively; the dated rollback copies (`config.txt.bak*`) were left alone.
- **Photos:** none this session.
- **Next:** if link-quality numbers from the A/B test exist, record them in `decisions.md` to
  close the performance question, not just the selection.
## 2026-09-21 — `aircrack-ng` installed for authorized WPA/WPA2 auditing

- **What:** Installed `aircrack-ng` (Debian trixie's own repos, no third-party apt repo needed —
  `aircrack-ng` 1.7, package `1:1.7+git20230807.4bf83f1a-2`), the first tool on this build capable
  of active Wi-Fi actions (deauth, handshake capture, cracking) rather than passive observation.
  Made the boundary explicit rather than relying on implication: updated `CLAUDE.md` and
  `knowledge/README.md`'s responsible-use section to spell out the carve-out — own network or
  documented written authorization, nothing else — and added the same note to
  `knowledge/wardriving/README.md`. Added `*.cap`/`*.pcap`/`*.pcapng`/`*.hccapx`/`*.hc22000` to
  `.gitignore` as a backstop (captures and cracked output are secrets).
- **Result:** `airmon-ng` correctly enumerates both radios (`wlan0` onboard brcmfmac, no monitor
  mode; `wlan1` the RT5370 Kismet already uses, monitor-capable). Verified `airmon-ng start
  wlan1` / `airmon-ng stop wlan1mon` toggles monitor mode cleanly and restores the interface —
  one cosmetic quirk noted (MAC address changed by one digit across the cycle, not investigated
  further, doesn't affect function). Did not run `airmon-ng check kill` during verification,
  since this build also runs Kismet, `aiov2_ctl`, and Tailscale that `check kill` would disrupt;
  noted in `software/aircrack-ng.md` for whoever runs a real capture session later.
- **Photos:** none this session.
- **Next:** none open from this batch — actual authorized-target usage is out of scope for a
  bring-up session.

## 2026-09-21 — `webdash` redesigned: grouped panels, rail control, app proxying/links

- **What:** Reworked the dashboard on request: grouped panels by use case (Platform: System +
  aiov2_ctl rails; Services: Kismet, GPS, ADS-B, Meshtastic) instead of one flat grid, and
  loosened panel spacing/typography that had been reading as crowded. Added real control: the
  aiov2_ctl rails panel is now toggle switches (`POST /api/aiov2/rail` → the aiov2-bridge → the
  same `aiov2_ctl <FEATURE> on|off` command by hand), deliberately superseding the original v1
  read-only-only scope now that the read path was proven. Answered "can other apps be proxied
  through the dashboard": tar1090's ADS-B map now is, at `/apps/tar1090/` (it turned out to
  already use paths relative to whatever prefix it's served under, so a straight passthrough
  proxy needed no HTML rewriting); Kismet and meshtasticd's web UI are linked instead, each via
  its own new `tailscale serve` mapping (`:2501`, `:9443`), since both assume they own the URL
  root.
- **Result:** All verified against real services on this hardware, using an in-process
  `TestClient` with the auth dependency overridden rather than the device owner's real
  session/credentials (which this session never touched) — `/api/links`, the tar1090 proxy
  (200, correct bytes, redirect from `/apps/tar1090` to the trailing-slash form), and the rail
  endpoint (toggled USB on/off through the full stack, plus confirmed `422` on invalid
  feature/state via `Literal` types rather than a generic `502`). **Found and fixed a real bug
  while testing**: the mesh collector reconnected every ~15s (its cache TTL), which raced the
  `meshtastic` library's own teardown — closing right after the handshake collides with its
  background reader thread's immediate post-handshake heartbeat send, `BrokenPipeError`,
  logged (not raised) every cycle. Fixed by holding one persistent `TCPInterface` for the app's
  lifetime instead of reconnecting per poll; confirmed clean logs across repeated calls
  afterward. Also caught mid-session: attempting to back up/restore the real auth store as part
  of a test plan was correctly blocked by the harness's own credential-leakage guard — tested
  via dependency override instead, which needed no access to real credentials at all.
- **Photos:** none this session.
- **Next:** none open from this batch.

## 2026-09-21 — `webdash` first-run QR code was broken; fixed

- **What:** Caught live: once `webdash` was reachable over the tailnet, a real setup attempt
  (`/setup`, username `wickedsmile`, 2026-09-21 15:10) showed a broken image where the TOTP QR
  code should be. Root cause: `segno`'s `svg_data_uri()` — despite the name — returns a
  **percent-encoded** data URI (`data:image/svg+xml;charset=utf-8,...`) by default, not base64;
  `auth.py`'s `setup_qr_svg()` assumed base64 and stripped a `;base64,` prefix that was never
  there, then `setup_done.html` wrapped the (untouched) full data URI in a second, invalid
  `data:image/svg+xml;base64,` wrapper. Fixed by rendering the SVG to raw bytes
  (`segno...save(buf, kind="svg")`) and base64-encoding it directly, rather than trusting
  `svg_data_uri()`'s implied format.
- **Result:** Confirmed fixed — decoded the returned base64 payload and verified real `<svg>`
  content, then ran a full setup → login → `/api/status` cycle successfully. The broken-QR account
  (`wickedsmile`) was deleted rather than reused, since its TOTP secret was never actually
  confirmed scannable — whoever sets up next (the device owner) gets a clean `/setup` now that the
  fix is in the running container.
- **Photos:** none this session.
- **Next:** none.

## 2026-09-21 — `webdash` exposed tailnet-wide via `tailscale serve`

- **What:** Widened `webdash` access (previous entry) from "this device only" to the whole
  tailnet, via `sudo tailscale serve --bg --https=443 localhost:8090` rather than handing Uvicorn
  a cert file directly (the approach CyberDeck's own `webdash` uses) — `tailscale serve` gets the
  same TLS-terminated result without this app having to track cert renewal itself. The app's own
  Uvicorn bind stayed at `127.0.0.1`, unchanged; `tailscale serve` is what does the proxying.
- **Result:** Reachable at `https://fancy.example-tailnet.ts.net/`, confirmed with a real
  Let's Encrypt cert issued through Tailscale (`openssl s_client` against the endpoint). Confirmed
  `tailscale serve status` reports "(tailnet only)" — deliberately did **not** run `tailscale
  funnel`, which would expose it to the public internet instead. `tailscale serve`'s config lives
  in `tailscaled`'s own state and is re-applied automatically on `tailscaled` restart/reboot — no
  extra systemd unit needed.
- **Photos:** none this session.
- **Next:** none — this closes the "decide on wider access" item from the previous entry.

## 2026-09-21 — `webdash` operator dashboard: planned, built, verified end-to-end

- **What:** Planned then built a Docker-based operator dashboard aggregating this build's
  software stack (`aiov2_ctl`, Kismet, gpsd, meshtasticd, readsb/tar1090) behind one TOTP-gated
  page — modeled on the proven architecture of a sibling build's dashboard
  ([`w1cked5mile/CyberDeck`](https://github.com/w1cked5mile/CyberDeck)'s `webdash`, Pi 5), scoped
  down for this hardware since every peripheral here already runs as its own service (that deck
  owns hardware directly; this one aggregates). Installed Docker (`docker.io`/`docker-compose`
  from Debian trixie's own repos — no third-party apt repo needed, unlike Kismet). Full plan:
  [`../reference/webdash-architecture.md`](../reference/webdash-architecture.md).
- **Result:** Working end-to-end, verified on this hardware. Image builds to 205 MB. Three things
  changed from the original plan during the build, all documented in the architecture doc's
  "Resolved" section: (1) `aiov2_ctl --status` needs `pinctrl`/GPIO device access that's fragile
  to bind-mount, so it's a tiny host-side systemd bridge (`uconsole-aiov2-bridge.service`,
  `127.0.0.1:8765`) instead; (2) the container runs as uid/gid 1000, not root — root left the
  bind-mounted auth store root-owned on the host; (3) found and fixed a real bug where closing an
  unauthenticated WebSocket before `accept()` silently swallows the intended close code (client
  saw a bare HTTP 403, never the "session expired" path). Confirmed the `meshtastic` Python
  library's `TCPInterface` talks to `meshtasticd`'s TCP API cleanly — no serial port involved.
  Tested every collector against this build's actual resting state: Kismet `stopped`, gpsd
  `running`/no fix, `readsb` `stopped` (SDR rail off, its normal state), `aiov2_ctl` rails
  matching a direct host `--status` call, meshtasticd `running` with real node/channel data.
  Bound Uvicorn to `127.0.0.1` only (not `0.0.0.0`) — deliberately not exposed past this device
  yet, since v1's login has no rate limiting and the panels include live GPS position. The
  first-run test account was deleted afterward so whoever runs `/setup` next sets real
  credentials, not a leftover test password.
- **Photos:** none this session.
- **Next:** Decide on wider access (Tailscale, TLS) before relying on this away from the device
  itself. `docs/reference/webdash-architecture.md`'s build-order section 2–4 (only 1 of those,
  `system.py`, was meant to ship before the others — all shipped together instead once the
  aiov2_ctl bridge pattern was settled).

## 2026-09-21 — `gpsd` re-enabled (swapped back from meshtasticd), no fix yet

- **What:** Re-enabled `gpsd` on `/dev/serial0` so Kismet and other tools can share the GPS
  receiver, reversing the 2026-09-18 swap that gave `meshtasticd` exclusive raw-serial ownership.
  Renamed `/etc/meshtasticd/config.d/gps-aio-v2.yaml` to `.disabled` (kept, not deleted) and
  restarted `meshtasticd` — confirmed via `lsof /dev/serial0` that it released the port before
  starting `gpsd`. Applied the already-staged [`../../configs/gpsd/gpsd.default`](../../configs/gpsd/gpsd.default)
  (diffed identical to what was deployed 2026-09-16) and ran `sudo systemctl enable --now gpsd`.
- **Result:** `gpsd` opens `/dev/serial0` cleanly (`NMEA0183` driver, 9600 8N1) and both
  `gpspipe -r` (raw `$GNGGA`/`$GNRMC`) and `gpspipe -w` (JSON `TPV`/`SKY`) confirm it's reading the
  receiver correctly. **No satellite fix after ~5 minutes of polling** — `TPV mode` stayed at `1`
  (no fix) and every `SKY` report showed zero tracked satellites throughout. The antenna/module
  itself was already confirmed healthy 2026-09-16 (`$GPTXT,...,ANTENNA OK`, see
  [`decisions.md`](decisions.md)), so this reads as no sky view (indoors) rather than a fault —
  matches the fix-expectations table in [`../../software/gps.md`](../../software/gps.md): "cold
  start, indoors: may never fix." `meshtasticd` itself is unaffected (LoRa mesh, channels) — only
  its GPS-sourced position stopped, since it no longer has a serial port to read.
- **Photos:** none this session.
- **Next:** Re-test `cgps -s`/`gpspipe -w` outdoors or near a window for an actual fix. If
  Meshtastic needs position again before then, the revert steps are in
  [`../../software/gps.md`](../../software/gps.md).

## 2026-09-21 — Kismet installed, and a monitor-capable adapter found already attached

- **What:** Installed Kismet for passive Wi-Fi/BT survey (not part of `aiov2_ctl --add-apps`;
  Debian's own repos don't carry it). Added Kismet's official apt repo
  (`https://www.kismetwireless.net/repos/apt/release/trixie`), preseeded the
  `kismet-common/install-setuid` debconf question (its whiptail prompt otherwise hangs a
  non-interactive install), and installed `kismet-core` plus the full `kismet-capture-*` helper
  set — package `2025-09-R1`, `Kismet 2025.09.0-b5d5a2d04`. Added the working user to the `kismet`
  group, applied the staged [`../../configs/kismet/kismet_site.conf`](../../configs/kismet/kismet_site.conf)
  (correcting its `log_prefix`, which was still written for a `pi` user that doesn't exist on this
  build), and ran a short group-capture (no `sudo`) test.
- **Result:** `iw dev` turned up a **Ralink RT5370 USB dongle** (`rt2800usb`, `lsusb` `148f:5370`)
  already attached as `wlan1`, monitor mode confirmed via `iw list` — this is not the AC1200
  (`#12253`, still on pre-order) but stands in for it. The onboard CM4 Wi-Fi (`brcmfmac`, `wlan0`)
  confirmed **no** monitor mode. `kismet_site.conf` was repointed at the RT5370
  (`source=wlan1:name=rt5370`) with a note to re-check `iw dev` once the AC1200 lands. Verification
  run: group-based capture started cleanly, `wlan1` → `wlan1mon`, logged real APs/devices, GPS
  connection to `gpsd` failed non-fatally (gpsd is installed but not yet enabled — tracked
  separately), and the interface reverted to managed mode on exit. The test capture (real
  neighboring SSIDs/MACs) was deleted immediately; `*.kismet`/`*.kismetdb`/`*.wiglecsv` are now in
  [`../../.gitignore`](../../.gitignore) as a backstop.
- **Photos:** none this session.
- **Next:** Enable `gpsd` for GPS-tagged captures (`software/gps.md`), then run a real survey
  session per [`../../knowledge/wardriving/runbooks/passive-survey-session.md`](../../knowledge/wardriving/runbooks/passive-survey-session.md).
  When the AC1200 arrives, re-run `iw dev` and update `kismet_site.conf`'s `name=` (and interface
  letter, if the RT5370 is still attached too). Full notes:
  [`../../software/kismet.md`](../../software/kismet.md).

## 2026-09-20 — Onboard Ethernet diagnosed as a hardware fault

- **What:** first attempt at checklist 2.2 (Ethernet). Plugged a cable into the mainboard v3.14's
  RJ45 jack — this build has no separate HackerGadgets upgrade-kit RJ45+USB3 board installed, so
  this is the CM4's own native `bcmgenet` gigabit controller. `eth0` never showed carrier.
- **Diagnostic chain, each step ruling out one layer:**
  1. `ip -d link show eth0` / `ethtool eth0`: interface up, driver loaded, `Link detected: no`.
  2. `/proc/device-tree/scb/ethernet@7d580000`: `status=okay`, `phy-mode=rgmii-rxid`, `phy-handle`
     correctly pointing at `mdio@e14/ethernet-phy@0` — the `clockworkpi-uconsole` overlay is
     configuring this correctly.
  3. `mii-tool -v eth0`: successfully read the PHY's vendor OUI, model/rev, and full capability
     list over MDIO — the SoC↔PHY management/control path works.
  4. `ethtool -s eth0 speed 100 duplex full autoneg off`: forced a fixed-speed link (bypasses
     autonegotiation entirely, needs only a raw electrical link pulse) — still no link, from the
     PHY's own status register.
  5. Confirmed the cable and far-end port are good by testing them on a different machine.
  6. Jack LEDs (solid green + solid amber with a cable inserted) initially looked like a real link
     the driver wasn't reporting, but the same LEDs are solid with the cable **fully unplugged** —
     not wired to real link state on this board, so not usable as a diagnostic here.
- **Conclusion:** every software-checkable layer (overlay/device-tree config, MDIO management,
  forced-mode negotiation) works correctly, and the cable/port are confirmed good. That isolates
  the fault to the mainboard's own Ethernet hardware — most likely the RJ45 jack's solder/magnetics
  or the PHY chip's analog transceiver section, not something an OS-side fix can address.
- **Also corrected:** `hardware/specs/mainboard-v3.14.md`'s spec table had no Ethernet row at all
  (an omission from when it was compiled from the BOM), and
  `docs/checklists/module-bringup-tests.md` labelled this test "(RJ45 board)" with a "USB
  2.0-bottleneck" note that actually describes the separate, uninstalled upgrade-kit board — both
  corrected to reflect that this is the CM4's native onboard gigabit path.
- **Photos:** none this session.
- **Next:** physical inspection of the jack/solder joints under the shell, or file an RMA against
  the base kit mainboard. See [`known-issues.md`](known-issues.md) and
  [`../records/order-and-warranty.md`](../records/order-and-warranty.md).

## 2026-09-20 — Linux hostname change (`clockworkpi` → `fancy`) fixed a stale `/etc/hosts` entry

- **Observed:** networking described as "spotty" on this device. System hostname is `fancy`
  (renamed at some earlier point), Tailscale already reflects that (`tailscale status` shows this
  node as `fancy`, matching the naming convention of the other tailnet devices), but
  `/etc/hosts` still carried the old `127.0.1.1 clockworkpi` line.
- **Why that causes flakiness:** anything that calls `hostname` and then resolves it locally
  (`sudo`, some daemons) does so via `/etc/hosts` first; a stale entry there makes that resolution
  fail and fall through to a slower path instead of hitting `127.0.1.1` immediately.
- **Fix:** updated `/etc/hosts` line 6 to `127.0.1.1		fancy`. Confirmed with
  `getent hosts $(hostname)` → `127.0.1.1 fancy`.
- **Also:** this session's shell has no TTY, so `sudo` couldn't prompt for a password to make the
  fix directly. Granted the `wicked5mile` user a blanket `NOPASSWD` sudo rule
  (`/etc/sudoers.d/010-wicked5mile-nopasswd`, `ALL=(ALL) NOPASSWD: ALL`), applied by the user from
  a real terminal via `~/setup-nopasswd-sudo.sh`. This is broader than the scoped, single-command
  `NOPASSWD` rules already in place for `meshtasticd`/`readsb` — an explicit choice to allow
  future agent sessions to make system-level fixes like this one without a TTY available.
- **Photos:** none this session.
- **Next:** none.

## 2026-09-18 — ADS-B tracking installed; airband listening confirmed; SDR docs corrected

- **SDR rail checked:** was off (matches documented default). Turned on live
  (`aiov2_ctl SDR on`) — not persisted to boot. With the rail on, the RTL2838 (RTL2832U) enumerates
  on USB and `rtl_test -t` finds it: `HackerGadgets, AIO_V2 Ext, SN: 25120901`, tuner reported as
  `Rafael Micro R820T` (same already-documented benign tuner-ID quirk, not `R860` as the datasheet
  names it). The `[R82XX] PLL not locked!` / `No E4000 tuner found, aborting` lines from
  `rtl_test -t` are also already-documented benign (`known-issues.md`) — plain `rtl_sdr`/`rtl_fm`
  stream fine.
- **`readsb` + `tar1090` installed** for ADS-B tracking (the gap `known-issues.md` flagged
  2026-09-16 when the `hackergadgets-uconsole-aio-board` meta-package that would have bundled this
  turned out to be unpublished). Installed directly from wiedehopf's own upstream installer
  scripts instead — both scripts read in full before running (readsb builds from source + a
  systemd service reading the RTL-SDR directly; tar1090 is a lighttpd-served map on top). Confirmed
  working: `readsb` claims the same device `rtl_test` found, `tar1090` map serves at
  `http://<device-IP>/tar1090`. Both `systemctl enable`d, active on boot.
- **Single-tuner conflict, same shape as the GPS/gpsd one:** `readsb` holds the RTL-SDR
  continuously once running, so `rtl_fm`/`gqrx`/`sdrpp` fail with `failed to open rtlsdr device #0`
  while it's up — confirmed by `lsof` showing `readsb`'s PID holding `/dev/bus/usb/.../007`. Unlike
  the GPS case this isn't just a software policy choice: a single-tuner SDR can only listen to one
  frequency at a time regardless, so ADS-B (1090MHz) and airband (118-137MHz) can never run
  simultaneously on this hardware no matter how the software is configured.
- **Built `configs/sdr/sdr-swap.sh`** to toggle between the two modes (`toggle`/`adsb`/`free`/
  `status` — stops/starts `readsb`). Added a scoped sudoers rule
  (`/etc/sudoers.d/020-readsb-wicked5mile`, `systemctl start/stop/status readsb` only) so it runs
  passwordless, matching the same pattern already used for `meshtasticd` rather than a blanket
  sudo grant.
- **Airband voice (118–137MHz AM) confirmed working** via `rtl_fm -f <freq> -M am -s 12k -g 40 - |
  aplay -r 12000 -f S16_LE -`, using the board's dedicated bulkhead-SMA SDR antenna (telescopic
  whip, fitted since 2026-09-15) — separate from the LoRa antenna on `ANT1`.
  **Bug hit and fixed:** the first attempt used `aplay -r 12k` (copying `rtl_fm`'s `-s 12k`
  shorthand), but `aplay` doesn't accept unit suffixes on `-r` — it failed immediately with
  `invalid rate argument '12k'`, which closed the pipe under `rtl_fm` and produced `Signal caught,
  exiting! / User cancel, exiting...`. That message is `rtl_fm`'s normal clean-shutdown log line
  for *any* terminating signal (confirmed by reproducing it via a `timeout`-sent SIGTERM too) —
  it was never a real "cancel," just a confusing symptom of the `aplay` flag typo. Fix: `-r 12000`.
- **Docs corrected to match reality** — `software/sdr-stack.md`, `software/adsb-tar1090.md`,
  `software/gps.md`, `configs/sdrpp/README.md`, and `software/README.md` all still assumed
  `aiov2_ctl --add-apps` would work and/or that `gpsd` stayed the GPS owner; both assumptions are
  wrong as of the 2026-09-16/18 entries in this file. Corrected in place rather than left to rot,
  each edit citing the entry here it's based on.
- **Photos:** none this session.
- **Next:** log a first-light ADS-B finding under `knowledge/aerospace/findings/` once there's
  been a real observation session (not done yet — today's aircraft count was 0, no traffic in
  range at the time, not itself a finding). Confirm what `sdrpp` actually is (fork/version/source)
  if it's going to be relied on — currently unconfirmed provenance.

## 2026-09-18 — Node renamed to uWicked

- **What:** `meshtastic --set-owner "uWicked" --set-owner-short "uWIC"` — confirmed via
  `meshtastic --info`: `Owner: uWicked (uWIC)`. Short name capped at 4 chars, matching the
  `uConsole`→`uCON` convention this build started with.
- **Also updated `configs/meshtastic/us915.yaml`** (`owner`/`owner_short`) to match, so a future
  `meshtastic --configure us915.yaml` re-apply doesn't silently revert the name back to
  `uConsole`/`uCON`. The 2026-09-17 build-log entry describing that original `--configure` run is
  left as-is — it's an accurate record of what was applied that day, not a live config reference.
- **Photos:** none this session.
- **Next:** none.

## 2026-09-18 — GPS got a real fix; native GUI installed; web server enabled

- **GPS fix confirmed:** `meshtastic --nodes` now shows real lat/lon/altitude for this node (was
  `0/0/0` right after the GPS bring-up earlier today), confirming the antenna has usable sky view.
  Not recording the actual coordinates here per this repo's no-precise-locations convention —
  "fix acquired" is the fact worth keeping.
- **`gtk-meshtastic-client` installed** (`sudo apt install gtk-meshtastic-client`, v1.2-1, an
  unofficial GTK4/Libadwaita client from Debian's own repos — not the `hackergadgets`
  meta-package, which still doesn't work per the 2026-09-16 entry). Confirmed connects over
  TCP/IP to `localhost` and shows the node/channels correctly. No CLI flag or `gsettings` key to
  pre-seed the TCP host — has to be entered in its connection screen each time (checked its
  `--help` and `org.kop316.meshtastic.gschema.xml`; neither exposes one).
- **meshtasticd's Webserver module enabled:** uncommented `Port: 9443` and
  `RootPath: /usr/share/meshtasticd/web` in `/etc/meshtasticd/config.yaml` (`RootPath` already
  pointed at real files — the web assets ship with the `meshtasticd` package). On restart it
  auto-generated a self-signed cert/key under `/etc/meshtasticd/ssl/` (no error, expected
  first-run behavior per the config's own comment) and came up listening on `0.0.0.0:9443` — LAN-
  and Tailscale-reachable, not just localhost. Confirmed with `ss -tlnp`. Gives browser access
  (local page or `client.meshtastic.org` pointed at the device) without installing anything
  further, and the official mobile app can also reach this node over its **Network** (TCP)
  connection type independent of this module, since `hasBluetooth: false` on this hardware.
- **Photos:** none this session.
- **Next:** none blocking. `software/meshtastic.md` updated to describe all current interaction
  paths (CLI, native GUI, mobile app, browser) as the reference.

## 2026-09-18 — GPS wired into meshtasticd (gpsd handed off the serial port)

- **What:** Turned on the GPS rail (`aiov2_ctl GPS on`, persisted with `--boot-rail GPS on`).
  `gpsd` (installed 2026-09-16, running since) was already successfully talking to the GNSS module
  on `/dev/serial0` — confirmed via `gpspipe`: `{"class":"DEVICE",...,"driver":"NMEA0183",...}`,
  `{"class":"TPV",...,"mode":1}` (mode 1 = no fix yet, not a fault; see below).
- **Conflict found:** `meshtasticd`'s GPS support (confirmed by grepping strings in the binary —
  only `SerialPath` exists, no gpsd/network client) only knows how to open a raw serial device
  directly, and `gpsd` was holding `/dev/serial0` exclusively (`cat`/`stty` against the port both
  failed with `Device or resource busy` while gpsd was up). Only one of them can own the port.
  **Decision:** stopped and disabled `gpsd.service`/`gpsd.socket` in favor of meshtasticd owning
  GPS directly — this repo's GPS bring-up (checklist 3.2/3.3, `gpsd`-based) is now superseded by
  meshtastic's own GPS handling; if a future tool needs raw NMEA independent of meshtastic (e.g.
  `pygpsclient`), `gpsd` would need to be re-enabled and meshtasticd's GPS config removed/disabled
  first — they cannot run together as configured.
- **Config:** added `/etc/meshtasticd/config.d/gps-aio-v2.yaml` (`GPS: SerialPath: /dev/serial0`).
  This alone did nothing until `position.gps_mode` (protocol-level device config, separate from the
  daemon's own serial config) was also set to `ENABLED` via
  `meshtastic --set position.gps_mode ENABLED` — the `SerialPath` setting only says *where* to
  look; `gps_mode` is the actual on/off switch, and needs a `meshtasticd` restart to take effect
  (didn't apply live to an already-running process in testing).
- **Result:** `[GPS] L76K detected` in the log on restart — chip identified correctly — followed by
  `[GPS] updatePosition LOCAL pos@0 ... lat=0 lon=0 alt=0` (actively polling, no fix yet). Confirmed
  via `meshtastic --info`: `"gpsMode": "ENABLED"`. No fix is expected/normal until the antenna has
  clear sky (matches gpsd's own pre-handoff HDOP 25.50/mode-1 reading — this is an antenna/sky-view
  condition, not a wiring or config problem).
- **Photos:** none this session.
- **Next:** get the antenna clear sky and confirm an actual fix (`lat`/`lon` non-zero, `gpsMode`
  aside, watch for `mode: 3` equivalent / a position broadcast on the mesh). Checklist items 3.2/3.3
  are effectively superseded by this meshtasticd-direct approach rather than completed as originally
  written (those assumed gpsd stayed the GPS owner) — worth a pass to reconcile the checklist text.

## 2026-09-17 — Full `us915.yaml` applied; joined NCMesh and SCMesh channels

- **What:** Applied the full staged config: `meshtastic --configure configs/meshtastic/us915.yaml`.
  Landed cleanly in one shot — `lora.region=US`, `lora.modem_preset=LONG_FAST`, `lora.hop_limit=3`,
  `lora.tx_enabled=True`, `device.role=CLIENT`, `position.gps_enabled=False`,
  `position.position_broadcast_smart_enabled=True`, `display.screen_on_secs=60`, owner set to
  `uConsole`/`uCON`. `meshtasticd` stayed up through it (same PID as before, no restart).
- **Joined two regional community meshes** — your location is near the NC/SC border, so both are
  plausibly in RF range: added `SCMesh` (index 1) and `NCMesh` (index 2) as SECONDARY channels,
  each with `psk=default` (Meshtastic's public built-in key, base64 `AQ==` — the same key every
  stock LongFast channel ships with, not a real secret). Sourced from each community's own site:
  [ncmesh.net/join](https://ncmesh.net/join/) and [scmesh.us](https://www.scmesh.us/). Confirmed via
  `meshtastic --info`:
  ```
  Index 0: PRIMARY psk=default   name=""       (LongFast, region US)
  Index 1: SECONDARY psk=default name="SCMesh"
  Index 2: SECONDARY psk=default name="NCMesh"
  ```
  First `--ch-add NCMesh` attempt hit a transient `Broken pipe`/connection-reset right after the
  `--configure` run (likely the daemon still settling from the config write); retried immediately
  and it went through clean. `meshtasticd` never restarted or crashed through any of this.
- **MQTT internet-bridging deliberately NOT configured for either network**, on request — the
  Linux-native MQTT module only holds one broker connection at a time, so bridging to
  `mqtt.ncmesh.net` and `mqtt.scmesh.us` simultaneously isn't possible without picking one (or
  running some kind of relay, not attempted). Both channels still work for local LoRa
  hear/relay regardless — MQTT only affects whether that traffic also crosses the internet to
  each community's wider network. `uplinkEnabled`/`downlinkEnabled` are `false` on both channels
  as a result. Revisit and pick one broker if internet-bridging is wanted later; each community's
  MQTT username/password (public, meant for anyone joining) are on their own sites linked above —
  intentionally not copied into this repo per the no-secrets convention, even though they're not
  truly private.
- **Photos:** none this session.
- **Next:** none blocking — node is fully configured and on both community channels. Optional:
  pick a single MQTT broker (NC or SC) if internet-bridging is wanted, or revisit the still-broken
  `--export-config` hang noted in the entry below.

## 2026-09-17 — LoRa region set to US

- **What:** With `meshtasticd` finally initializing (see entry below), set the node's region so TX
  is no longer blocked: `meshtastic --host localhost --set lora.region US`. Confirmed applied with
  `meshtastic --host localhost --get lora.region` → `lora.region: 1` (US). `meshtasticd` stayed up
  through the change (same PID, no restart).
- **Not yet done:** this only sets `lora.region`. The rest of the staged
  [`configs/meshtastic/us915.yaml`](../../configs/meshtastic/us915.yaml) (`modem_preset:
  LONG_FAST`, `hop_limit: 3`, `tx_enabled: true`, device role, position/display settings) has
  **not** been applied — that needs `meshtastic --configure configs/meshtastic/us915.yaml`, not
  done this session. Don't assume the rest of that file reflects the device's actual state yet.
- **`--export-config` hangs:** tried to capture the real device state as
  `configs/meshtastic/as-applied.yaml` per this file's own header instructions. Both
  `meshtastic --export-config` (piped to a file) and `meshtastic --export-config FILE` hang
  indefinitely with **zero output**, not even the usual "Connected to radio" line — a different
  failure signature than the original CLI-hang bug (which was `meshtasticd` not running at all;
  this is `meshtasticd` healthy and responding fine to plain `--get`/`--set` in the same session,
  just not to `--export-config` specifically). Not investigated further this session. No
  `as-applied.yaml` exists yet as a result.
- **Photos:** none this session.
- **Next:** decide whether to run the full `--configure us915.yaml` now or leave `modem_preset`/etc.
  at device defaults for now; separately, `--export-config`'s hang is worth a fresh look (or an
  upstream check) before relying on it for future config snapshots.

## 2026-09-17 — `meshtasticd` installed and run against real hardware for the first time

- **What:** `meshtasticd` (previously only planned, see 2026-09-16 entry below) is now installed
  and enabled as a systemd service, with `/etc/meshtasticd/config.d/lora-aio-v2.yaml` pointing it
  at the AIO V2's SX1262. This is the first session that actually exercised the SPI link against
  the chip, not just checked that a `spidev` node exists.
- **Bug 1 — wrong `spidev` bus, `Failed to open posix file /dev/spidev1.0, errno=2`:** the config
  (and `hardware/specs/aio-v2.md`/`software/meshtastic.md`) assumed `/dev/spidev1.0`, but that node
  did not exist. **Root cause:** `config.txt` had `dtoverlay=spi1-0cs` (see Bug 2), and a `-0cs`
  overlay registers zero chip-select lines, so the kernel never creates a spidev child device for
  SPI1 at all — by design, not a fluke. Traced via `/sys/bus/spi/devices/`: the only spidev present
  (`/dev/spidev4.0`) was bound to devicetree node `spi@7e204800`, an unrelated alternate-function
  SPI controller (BCM2711's "SPI4"), not SPI1 (`spi@7e215080`). Pointing meshtasticd at
  `spidev4.0` was a **wrong intermediate fix** — it opened without error but talked to a bus with
  no SX1262 on it.
- **Bug 2 — `config.txt` overlay didn't match this repo's own documented convention:**
  `docs/reference/pinout-gpio.md` and the vendor setup guide both specify `dtoverlay=spi1-1cs` for
  CM4, but the live `config.txt` had `dtoverlay=spi1-0cs`. Changed to `spi1-1cs` and rebooted.
  After reboot, `/dev/spidev1.0` correctly appears, bound to `spi@7e215080` (the real SPI1/AUX
  controller), and `/sys/kernel/debug/gpio` now labels GPIO18 `spi1 CS0 ... ACTIVE LOW` — this
  matches the empirical CS confirmation noted in the yaml's header comment from 2026-09-16, so
  `spi1-1cs` is very likely what was in effect when that note was written, and `spi1-0cs` was a
  later, undocumented regression.
- **Bug 3 — `CS: 18` in the yaml now conflicts with hardware CS:** with `spi1-1cs` the kernel owns
  GPIO18 as hardware CS0. meshtasticd's Portduino layer manually claiming the same line via
  libgpiod (as `CS: 18` requests) fails with `gpiod_line_request_reconfigure_lines: Assertion
  'request' failed` and the process aborts. **Fix:** removed the `CS:` line from the yaml — with
  `spi1-1cs`, chip select is hardware-managed per SPI transfer and needs no manual GPIO.
- **Bug 4 — LoRa rail was off:** `aiov2_ctl --boot-rails-status` showed `LORA: OFF` (matches the
  documented all-off boot default). Chip can't respond to anything, powered or not, without this.
  Fixed with `aiov2_ctl LORA on` (live) and `aiov2_ctl --boot-rail LORA on` (persisted).
- **Separate meshtasticd software bug:** whenever `SX126x init` fails for *any* reason, the
  process hits `free(): invalid pointer` in its own error-handling path and aborts (glibc abort,
  not a clean error return) — turning a "radio not found" condition into a crash-loop under
  systemd rather than a graceful degraded/no-radio state. Not something fixable from this repo's
  side; worth an upstream meshtasticd issue if it keeps mattering.
- **Where it stands after all four fixes:** `SX126x init result -2` ("chip not found", no SPI
  response at all) changed to **`SX126x init result -707`** (RadioLib `SPI_CMD_INVALID`), and the
  failure now happens immediately instead of after a ~10s delay. This reads as real, live SPI
  traffic reaching an actual chip that's rejecting the command — a materially different signature
  from "nothing's there," but still failing before the node comes up on the local API
  (`meshtastic --host localhost --info` gets connection-refused on 4403, since meshtasticd never
  gets that far). Busy (BCM 24), Reset (BCM 25), and IRQ (BCM 26) are sourced only from the vendor
  spec sheet (`hardware/specs/aio-v2.md`) and, unlike CS, have **never been electrically verified**
  against this board the way CS was (`/sys/kernel/debug/gpio` labeling). That's the leading
  suspect. Reseating the AIO V2 on the mainboard connector is also untried and appears in this
  file's own watch-list as a forum-reported fix for "AIO V2 not responding."
- **Resolved, same session, after a reseat + one more config fix:** reseating the AIO V2 on the
  mainboard connector made no difference (identical `-707`, ruling out a loose connector). The
  actual cause was a **TCXO/XTAL mismatch**: RadioLib's SX126x driver defaults to assuming a plain
  crystal unless told otherwise, but `hardware/specs/aio-v2.md` already documents this module as
  TCXO-equipped, and the yaml never set `DIO3_TCXO_VOLTAGE`. This exact failure mode (`-706`/`-707`)
  is a known, documented RadioLib signature for a TCXO/XTAL mismatch (see
  [RadioLib#689](https://github.com/jgromes/RadioLib/issues/689),
  [meshtastic/firmware#2208](https://github.com/meshtastic/firmware/issues/2208)). Added
  `DIO3_TCXO_VOLTAGE: 1.8` (a common value for SX1262 breakout boards; not vendor-confirmed for
  this specific module, just the first value tried) below `DIO2_AS_RF_SWITCH` in the yaml — worked
  on the first try: `SX126x init result 0`, `sx1262 init success`, API server up on TCP 4403.
  `meshtastic --host localhost --info` now connects immediately and returns real node info
  (`!dddf317f`). Checklist item 3.9 now passes.
- **Photos:** none this session.
- **Next:** set the LoRa region (currently `UNSET`, so TX is disabled — `[NodeInfo] send - lora tx
  disabled: Region unset` in the log, expected and not a bug) via `meshtastic --configure
  ../configs/meshtastic/us915.yaml` or `meshtastic --set lora.region US`. Then checklist 3.10 (a
  second node for the round-trip test). The unrelated `free(): invalid pointer` crash-on-failure
  bug in meshtasticd's error path (noted above) is dormant now that init succeeds, but would
  resurface as a crash-loop instead of a clean error if the radio ever fails to init again (e.g.
  after a config mistake) — worth keeping in mind when editing `lora-aio-v2.yaml` further.

## 2026-09-16 — `meshtastic` CLI installed, found it needs `meshtasticd` to do anything

- **What:** Installed the `meshtastic` Python CLI without `sudo` (Debian Trixie blocks a bare
  `pip install` as an externally-managed environment) via a venv:
  `python3 -m venv ~/.venvs/meshtastic && ~/.venvs/meshtastic/bin/pip install meshtastic`,
  symlinked to `~/.local/bin/meshtastic` (already on `PATH`). Installed clean, `v2.7.11`. Then ran
  `aiov2_ctl LORA on` and `meshtastic --info` per the checklist.
- **Result:** `meshtastic --info` hung indefinitely with no output, even with `--debug`. Traced
  this to a wrong assumption in [`software/meshtastic.md`](../../software/meshtastic.md): the
  `meshtastic` package is a *client* that talks to a running Meshtastic node over
  serial/TCP/BLE — it does not drive the SX1262's SPI bus directly. This board's SX1262 has no
  onboard microcontroller running Meshtastic firmware, so `--info` sits waiting for a node that
  doesn't exist. The missing piece is **`meshtasticd`**, the native Linux build of the Meshtastic
  firmware itself, which would actually drive the SPI radio. Confirmed via `apt-cache search
  meshtastic` that this image's configured apt sources have no `meshtasticd` package (only client
  packages `python3-meshtastic`/`gtk-meshtastic-client`) — it ships from Meshtastic's own apt
  repo, not configured here, and adding a repo plus installing needs `sudo`. Corrected
  `software/meshtastic.md`, `docs/checklists/module-bringup-tests.md`, and `known-issues.md`.
  The SX1262 control-pin map `meshtasticd` will need (IRQ/DIO1 = BCM 26, Busy = BCM 24, Reset =
  BCM 25, CS on `spidev1.0`) was already documented in `hardware/specs/aio-v2.md`, so the next
  `sudo` session just needs to add the repo, install, and write the config.
- **Photos:** none this session.
- **Next:** Add Meshtastic's apt repo and install `meshtasticd`, configure it for the AIO V2's
  SX1262 pins, then retry `meshtastic --info` (checklist 3.9). All `sudo`-gated.

## 2026-09-16 — Bluetooth mouse recovered, onboard speaker verified

- **What:** Two ad hoc checks with a person at the device: (1) the paired Bluetooth mouse had
  stopped responding, (2) ran the module bring-up checklist's audio test (item 1.3) with someone
  present to actually hear it.
- **Result:**
  - **Bluetooth mouse (M720 Triathlon)**: was stuck in a connect/abort loop —
    `bluetoothd[664]: profiles/input/hog-lib.c:set_report_cb() Error setting Report value:
    Request attribute has encountered an unlikely error`, repeating every 10–60 s. This is a known
    upstream BlueZ bug ([bluez/bluez#1911](https://github.com/bluez/bluez/issues/1911), ATT error
    0x0E): when a BLE HID peripheral wakes from its own sleep, its GATT server needs a moment to
    become ready, and BlueZ's `hog-lib` treats a read/write that lands in that window as permanent
    failure instead of retrying — no accepted fix is merged yet. Not caused by, or related to,
    this session's GPIO/overlay work — separate subsystem entirely. Re-paired the mouse
    (`bluetoothctl remove` + re-pair while the mouse was in pairing mode, new random address
    `aa:bb:cc:dd:ee:05`) and reconnected once it was actively moving; held stable afterward.
    **If it recurs**: nudge the mouse and let BlueZ's automatic reconnect retry — there's no
    permanent fix available without a BlueZ patch or a wired/Unifying-receiver alternative.
  - **Audio (checklist 1.3, pass)**: `speaker-test -D plughw:0,0 -c2 -twav -l1` on the
    `bcm2835 Headphones` ALSA card — front-L/R tones confirmed audible. **Default `PCM` volume
    (80%, -17.41 dB) was inaudible; had to raise it to 100% (+4.00 dB, the top of this control's
    range) to hear anything** — worth knowing so a quiet speaker isn't mistaken for a hardware
    fault. `clockworkpi-audio-patch.service` (amp enable / headphone jack-sense) and
    `clockworkpi-audio-shutdown.service` were both already active since boot — no manual GPIO
    workaround needed on this image. Headphone-jack auto-switch not yet tried.
- **Photos:** none this session.
- **Next:** Headphone-jack auto-switch test; display (1.1) and keyboard (1.2) checklist items
  still need a person at the device.

## 2026-09-16 — Post-reboot: RTC/GPS/LoRa overlays verified, boot-rail default settled

- **What:** Picked up after the RTC/GPS/LoRa overlays and `cmdline.txt` fix from the prior session
  ([`docs/runbooks/software-install.md`](../runbooks/software-install.md) step 3) were applied and
  the device rebooted. Ran the reboot-dependent rows of
  [`docs/checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md): baseline
  rail state, RTC, GPS rail, LoRa rail, and a re-check of the SDR rail.
- **Result:**
  - **Baseline rail state settled**: post-reboot `aiov2_ctl --status`/`--boot-rails-status` shows
    GPS/LoRa/SDR/USB all off after a cold boot — closes the "near-settled" item in
    [`decisions.md`](decisions.md) and checklist item 0.
  - **RTC (3.1, partial pass)**: `pcf85063a` enumerates on `i2c-1` at `0x51`; `/dev/rtc0` exists;
    `timedatectl` shows RTC time within 1 s of system time. Full power-off/no-network cycle test
    not run — needs `sudo`, which needed an interactive password not available this session.
  - **GPS rail (3.2, pass)**: `aiov2_ctl GPS on` then reading the UART produced a full NMEA set
    (`$GNGGA`, `$GNGLL`, `$GNGSA`, `$GPGSV`, `$GLGSV`, `$GNRMC`, `$GNVTG`, `$GNZDA`) plus
    `$GPTXT,01,01,01,ANTENNA OK` — which also answers the open TODO item on `ANT7` centre-pin
    continuity. **Found the device is `/dev/serial0` (`ttyS0`), not `/dev/ttyAMA0`** as every doc
    in this repo assumed: the CM4's onboard Bluetooth holds the full PL011, which registers as
    `ttyAMA1`. Corrected across `pinout-gpio.md`, `software/gps.md`, `software/aiov2_ctl.md`,
    `hardware/specs/aio-v2.md`, `first-rf-checkout.md`, the checklist, `drivers/README.md`, the
    presentation deck, and the `configs/boot`/`configs/systemd` runbook notes —
    `configs/gpsd/gpsd.default`'s `DEVICES=` line would have pointed gpsd at a device that doesn't
    exist, now fixed to the stable `/dev/serial0` symlink. Full detail in
    [`decisions.md`](decisions.md). No fix yet (0 satellites, indoors) — expected.
  - **LoRa rail (3.8, pass)**: `spidev1.0` present after `aiov2_ctl LORA on`; no `devterm-printer`
    conflict on this image. `meshtastic --info` (3.9) still blocked — the CLI isn't installed and
    installing it needs `sudo`, unavailable this session (see `known-issues.md`).
  - **SDR rail re-checked (3.4/3.5)**: still passes after the overlay reboot, with GPS/LoRa on or
    off making no difference. Noted a new cosmetic warning, `[R82XX] PLL not locked!`, printed by
    `rtl_test -t` on every run — benign, plain `rtl_test` streams normally afterward (~52 bytes
    lost in an 8 s run). Logged in `known-issues.md` so it isn't mistaken for a regression later.
  - Turned GPS/LoRa/SDR rails back off at the end of the session (was on AC power throughout, no
    battery-draw concern, but leaving rails in a known-off state matches the checklist baseline).
- **Photos:** none this session.
- **Next:** `sudo`-gated work is the remaining blocker — installing `gpsd`/`meshtastic` (needs
  `apt`/`pip`), `sudo hwclock -r` (RTC read confirmation), and the full RTC power-cycle test all
  need an interactive session with the account password. Once installed: GPS fix test (3.3) under
  open sky, `meshtastic --info` (3.9), and a second Meshtastic node for the link test (3.10).

## 2026-09-16 — Software bring-up: `aiov2_ctl` installed, SDR rail verified end-to-end

- **What:** Started [`docs/runbooks/software-install.md`](../runbooks/software-install.md) and
  [`docs/checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md) on the same
  boot session as "First boot" above (device has been up since `2026-09-16 10:48:36`, no reboot
  during this session). Installed `aiov2_ctl` per the runbook, then exercised every non-reboot-
  dependent test in the bring-up checklist.
- **Result:**
  - **Fixed a pre-existing, unrelated `apt` breakage first** — `initramfs-tools`/`rpd-plym-splash`
    were stuck half-configured (`mkinitramfs: failed to determine device for /`), triggered by
    installing the runbook's `python3-pyqt6` dependency. Not a boot risk (this image has no
    `initrd` reference in `config.txt`/`cmdline.txt`, so it doesn't boot through one), but it would
    have blocked every later `apt install`. Fixed with the workaround the error itself names
    (`MODULES=most` in `/etc/initramfs-tools/initramfs.conf`, `.bak` kept) and
    `apt --fix-broken install`.
  - **`aiov2_ctl` installed clean** from `hackergadgets/aiov2_ctl` (git HEAD at install time) via
    `sudo python3 ./aiov2_ctl.py --install`. Reviewed `install_self()` before running it: copies
    the script to `/usr/local/bin`, writes bash completion + a desktop entry, installs and enables
    `aiov2-rails-boot.service`. No GPIO is touched at install time.
  - **RTC (PCF85063A) confirmed physically present** — answers at I2C address `0x51` on bus 1 —
    before any overlay was applied. `/dev/rtc0` doesn't exist yet because the `i2c-rtc,pcf85063a`
    overlay from [`configs/boot/config-cm4.txt`](../../configs/boot/config-cm4.txt) hasn't been
    applied (that step needs a reboot — deferred, see Next).
  - **SDR rail verified end-to-end, checklist 3.4 and 3.5 both pass:** `aiov2_ctl SDR on` →
    dongle enumerates (`HackerGadgets, AIO_V2 Ext, SN: 25120901`) → `rtl_test -t` finds it with no
    `usb_claim_interface error -6` → `rtl_test -s 2400000 -d0` over ~20 s lost only ~132 bytes
    (~1 sample per million) — well inside "near-zero." Installed the *plain Debian* `rtl-sdr`
    package for this (`sdrpp-brown` isn't available — see known-issues) and pre-staged
    [`configs/modprobe.d/blacklist-rtl-dvb.conf`](../../configs/modprobe.d/blacklist-rtl-dvb.conf);
    the kernel DVB driver was already loaded but `rtl_test` detached it live without incident.
    Rail returned to **off** afterward (its default).
  - **Tuner identifies as "R820T"**, not "R860" as named in the BOM/specs. Likely just how this
    `librtlsdr` build's tuner-ID table labels an R860 (same R82xx family/register set) — not
    treated as a hardware discrepancy, but worth a source-checked footnote if anyone chases it.
  - **Settled (pending one empirical check) — SDR is *not* on by default at boot on this build.**
    This repo's docs (`pinout-gpio.md`, `software/aiov2_ctl.md`, `hardware/specs/aio-v2.md`) cited
    `BOOT_DEFAULTS = {7: True, ...}` in `aiov2_ctl.py` as the boot-time default. Reading the
    current source: that dict is only used as a *state-inference fallback* for `--status`
    reporting when `pinctrl get` returns an undriven level (`_gpio_state_for_pin`, ~line 750) — the
    systemd boot service actually calls `apply_rails_on_boot()`, which reads
    `_rails_on_boot_from_config()` (~line 109): every rail defaults to **False** when no
    `rails_on_boot` config exists, which is the case here (no config file at all yet). Live
    `aiov2_ctl --boot-rails-status` right now reports all four rails off, and HackerGadgets' own
    setup guide states "the SDR, GPS and LoRa modules are off by default — this is intentional to
    save battery." *Verify marker: this session did not reboot to confirm empirically* — the
    Claude Code session driving this work runs directly on the uConsole itself, and a reboot would
    drop it. **Next person with hands on the device: reboot once, then `aiov2_ctl --status`, and
    close [`decisions.md`](decisions.md)'s open item for real.** See `decisions.md` for the full
    citation.
  - **`vcgencmd` needs `sudo`** — `/dev/vcio` is `root:root 0600`, so the unprivileged runbook
    command fails silently (`Can't open device file`). Works fine with `sudo`, and
    `/sys/class/thermal/thermal_zone0/temp` cross-checks it. Not a hardware issue, just a
    permissions note for the checklist.
  - **Idle CPU temp borderline-high: 62–63 °C** against the checklist's "< 60 °C" pass bar,
    `throttled=0x0` (never throttled). Measured with the shell closed, shortly after a burst of
    package-install CPU load; not re-checked after a longer settle or with everything (SDR, etc.)
    off for a while. Not marked pass/fail in the checklist — flagged in known-issues instead.
  - **The `--add-apps` companion packages (`hackergadgets-uconsole-aio-board`, `meshtastic-mui`,
    `sdrpp-brown`, `tar1090`, `pygpsclient`) are not installable on this image as documented.**
    Confirmed by direct inspection, not just a failed `apt install`: none of those package names
    exist in the configured `clockworkpi/apt` repo (`bookworm`, `arm64` — the only component that
    repo has), and there is no separate `hackergadgets` apt repo (`hackergadgets`'s GitHub org has
    exactly three repos, none of them a package repo). A ClockworkPi forum thread shows other users
    hitting the identical "can't find package" error with no working fix posted; the maintainer's
    only reply says "it's in the repo, did you run apt update" — which does not match what's
    actually published. Corrected known-issues' prior entry, which had guessed "dpkg errors."
    Worked around it for SDR only, today, with the plain Debian `rtl-sdr` package; GPS/LoRa
    equivalents (`gpsd`, `meshtastic` CLI) are also available from stock Debian/pip and are the
    likely path once the overlay/reboot step happens — not yet done.
  - Also ran, cleanly, with no findings worth a separate note: `aiov2_ctl --status`/`--power`
    (AC-charging, 100%, ~0.3 W — on the interim 18650 pack, AC connected throughout, so this is
    *not* a battery-discharge reading), `aiov2_ctl USB on` + `lsusb -t` (hub and RTL-SDR enumerate
    correctly), `tailscale status` (this node shows online in the tailnet).
- **Photos:** none this session.
- **Next:**
  - Reboot once to empirically confirm the all-rails-off boot behavior above, then close the
    `decisions.md` item.
  - Apply the RTC (`i2c-rtc,pcf85063a`) and LoRa (`spi1-1cs`) overlays from
    `configs/boot/config-cm4.txt`, and the `cmdline.txt` console removal from
    `configs/boot/cmdline-notes.md`, together with that same reboot — back up both files first.
  - After that reboot: RTC test 3.1, GPS tests 3.2/3.3, LoRa tests 3.8/3.9 (needs a second
    Meshtastic node for 3.10).
  - Re-check idle temp after a longer settle with all rails off; run the 10-minute PPM test
    (3.6) and the full power-characterization table (section 4) as a dedicated session — both are
    too long to fold into this one.
  - Find a real substitute path for `sdrpp-brown`/`tar1090`/`meshtastic-mui`/`pygpsclient` since
    the meta-package route is a dead end on this image.

## 2026-09-16 — First boot: hardware identifiers captured

- **What:** Kit confirmed assembled — CM4 seated on the mainboard, booted to a desktop session on
  the uConsole shell/screen/keyboard. Pulled every serial/identifier the running system exposes:
  `/proc/cpuinfo`, device tree, `lsusb -v`, `lsblk`, `ip -br link`, `/sys/class/power_supply/`,
  and `/boot/firmware/config.txt`.
- **Result:**
  - CM4 serial `<cm4-serial-redacted>`, board revision `Rev 1.1` — closes the "read at first boot"
    placeholder in [`../../hardware/specs/cm4-lite-8gb.md`](../../hardware/specs/cm4-lite-8gb.md),
    [`../records/order-and-warranty.md`](../records/order-and-warranty.md), and this checklist.
  - CM4 wireless/Ethernet MACs recorded (`aa:bb:cc:dd:ee:7e` / `...7d`).
  - Mainboard's USB input controller identifies as `ClockworkPI uConsole`, `iSerial=20230713` — a
    firmware build-date marker, not a per-unit serial; recorded in
    [`../../hardware/specs/mainboard-v3.14.md`](../../hardware/specs/mainboard-v3.14.md).
  - microSD in use: `mmcblk0`, CID `0x3832c348`, 29.5 GB — this card was tracked as "not ordered";
    that status is now stale across `TODO.md` and `docs/accessories.md` (updated).
  - **Two previously-*unverified* claims confirmed on real hardware:** `axp20x-battery` read
    3.886 V, consistent with the 1S LiPo topology decided in `decisions.md` (not a 2S pack); and
    `dtparam=ant2` is set, so the CM4's external u.FL antenna is selected, not the onboard PCB one.
  - **Not detected:** no `/dev/nvme*` device at this boot — system is running from microSD, not the
    NVMe board. Physical seating of the NVMe/adapter board is unconfirmed.
- **Photos:** none this session — this was a software-only pull, no case opened.
- **Next:** Visually inspect and photograph the mainboard/shell/kit (never done — only confirmed
  powered), confirm the NVMe board is actually seated, and record its form factor once found.
  *(Corrected on merge: this was the interim 18650 pack, not the NVMe board or the Meshnology LiPo
  — see the assembly entries below. The 3.886 V PMIC reading is consistent with either 1S source.)*

## 2026-09-15 — Shell closed, keyboard and display in, all 8 antennas fitted

- **What:** Completed mechanical assembly. Front shell, keyboard and display installed, shell
  closed, and all eight antennas fitted: seven on the top-edge `ANT1`–`ANT7` strip and the
  telescopic whip on the left-hand SDR bulkhead. **Still nothing powered on.**
- **The antenna breakout strip is now installed.** The earlier assembly frame had only the single
  SDR bulkhead; the 7-way strip is in and populated.
- **Mapping corroborated by the build.** The two `Bluetooth`-marked stubs sit on `ANT2`/`ANT3` and
  the GNSS puck on `ANT7` — exactly what
  [`../reference/antennas-and-rf-connectors.md`](../reference/antennas-and-rf-connectors.md)
  specifies. Good independent evidence the mapping was applied as written.
- **Every stub is vendor-marked, and the set matches the mapping row for row.** An edge-on frame
  reads them in fitted order: `LoRa`, `Bluetooth`, `Bluetooth`, `Wi-Fi`, `Wi-Fi`, `Wi-Fi`, then
  the GNSS puck. `ANT1` carries a `LoRa` antenna, supplied with the kit.
- **Correction, same day.** An earlier entry in this log and a `known-issues.md` entry claimed
  `ANT1` had an unmarked, wrong-band stub. Both were wrong and are retracted. The claim came from
  an inventory close-up that showed only three of six markings — the rest faced away — and that
  partial count was written up as complete, overturning a correct earlier reading in the process.
  The supporting length argument was also unsound: "shorter than an 82 mm ¼-wave" only implies a
  band for a straight radiator, and these are loaded stubs, which are routinely half that length
  at their design frequency. No mismatch is suspected. See
  [`known-issues.md`](known-issues.md) for the withdrawn entry.
- **Four antennas have no radio behind them.** `ANT2`/`ANT3`/`ANT5`/`ANT6` are fed by the AC1200,
  which is still on pre-order (#12253). An antenna fitted is not a radio connected.
- **Shell closed before first boot**, which the assembly runbook advises against
  ([`../runbooks/assembly.md`](../runbooks/assembly.md)). Mitigating: `TF` and `ON/OFF` are on the
  top edge and externally accessible, so inserting a microSD does not need the shell opened.
  Re-flashing via `rpiboot` on the adapter's USB-C port would.
- **Labelling is better than assumed.** Each stub carries its function in text, so the fitted
  device is self-documenting. The **jacks** are still bare — pull a stub and the port is
  identifiable only from the mapping table.
- **Photo:** [`../../images/inventory/20260916-assembled-antennas-fitted.jpg`](../../images/inventory/README.md)
- **Photo (markings):** [`../../images/inventory/20260916-antenna-markings-fitted.jpg`](../../images/inventory/README.md)
- **Next:** cells still unweighed. *(Corrected on merge: the microSD was bought and flashed
  2026-09-15 — this session was written without that knowledge.)*

## 2026-09-23 — HackerGadgets kit delivered; NVMe fitted; owner reports install and test

- **What:** HackerGadgets order #11953 arrived — CM4/5 Adapter Pro, NVMe battery board, RJ45+USB3
  board. The on-hand M.2 NVMe was pulled from stock, identified, and fitted. Owner reports the
  boards were **installed and tested**.
- **NVMe identified:** **WD PC SN730, 256 GB, M.2 2280, OPAL** self-encrypting. `SDBQNTY-256G-1001`,
  Lenovo channel part (LEN P/N `SSS0L24774`, FRU `5SS0V26411`), FW `11130101`, HW `0A`, 3.3 V 2.8 A,
  manufactured 19DEC2019, **SN `<ssd-serial-redacted>`**. 2280 seats on the board's outermost standoff, so
  the form-factor question that has been open since the BOM was written is closed.
- **OPAL is a live question, not a footnote.** A previously-deployed enterprise drive can come back
  locked. If it was ever paired to another host it may refuse to take an image until it is unlocked
  or reverted. *Unverified either way* — nothing in the report says whether the drive was blank.
- **Board names and revisions recorded:** `Raspberry Pi CM4/5 Adapter Pro for uConsole` and
  `uConsole NVMe Battery Board`. Neither carries a unit serial.
- **Four silkscreen findings new to this repo**, all in
  [`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md):
  the adapter's **RTC-battery JST is CM5-only** ("Don't connect when using CM4"); its DIP switch is
  **`1:nRPIBOOT` / `2:EEPROM_nWP`**; **`GPIO4` is routed to an IPEX `RPITX` connector** rather than
  to the mainboard, with a 0Ω link position to restore normal routing; and the battery board has an
  optional **`R14`/`J6`** manual battery on/off modification.
- **`JP1` is still not legible** in any frame. The battery-mode jumper the assembly runbook turns on
  has never been seen directly — a solder-jumper footprint beside `BAT2` is consistent with it, but
  its as-shipped state is unrecorded and the board is now installed.
- **Photos:** [`../../images/inventory/`](../../images/inventory/README.md) — five `20260923-*`
  frames. The SSD label frame carries the drive's factory revert code; it is **not transcribed
  anywhere** and the frame is marked sensitive in that README.
- **What "tested" covered is not recorded**, because no command output was supplied. The
  bring-up rows in [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md)
  therefore stay open, and the build state still says no device behaviour has been *documented*.
  Whatever was run — `lsblk`, `nvme list`, `lspci`, a boot — pasting it closes several rows at once,
  including the CM4 serial capture that has been owed since 2026-09-06.

## 2026-09-16 — Mailbox sweep: AC1200 order found, and #11953 has shipped

- **What:** Searched both mailboxes for the AC1200 purchase. No hardware was touched.
- **AC1200 is a real order:** HackerGadgets **#12253**, placed 2026-09-15, 【Pre-Order】AC1200 USB-C
  WiFi Card (supports monitor mode) × 1, $45.00 + $18.00 EURPOST = **$63.00**. It landed in the
  **Gmail** mailbox, not the `example.com` one that holds #11953 — the same
  split that hid the AliExpress order earlier. BOM item 7 is promoted from optional to specified;
  the BOM/mapping disagreement is closed.
- **But it has not arrived.** #12253 is a pre-order with no ship notice, so the four antenna
  positions it feeds (`ANT2`/`ANT3` BT, `ANT5`/`ANT6` Wi-Fi) are **reserved, not populated**. The
  port mapping describes the finished state; today only `ANT1`, `ANT4`, `ANT7` and the SDR bulkhead
  have a radio behind them.
- **Unrelated finding in the same sweep: order #11953 shipped on 2026-09-14**, PFC tracking
  `SPXCLT003022609140031768`. The repo had carried "not yet shipped" since 2026-09-05. That is the
  NVMe battery board, adapter and RJ45 board — the parts the interim 18650 pack is standing in for.
- **Product-name trap worth recording:** #11953's title reads "…/AC1200 WiFi(with monitor mode
  supported)…" but its variant line ends in `NONE`, which is the card option. No card ships with
  the kit. Two separate orders.
- **Next:** track `SPXCLT003022609140031768`; when it lands, the adapter, battery-board and `JP1`
  decisions all re-open.

## 2026-09-15 — First assembly: mainboard, CM4, AIO V2, interim 18650 pack

- **What:** Fitted the mainboard into the rear shell and populated it — CM4 on its adapter, AIO V2
  in the mini-PCIe expansion slot, ClockworkPi's **stock battery board** with the 2-bay holder and
  two 18650 cells, `SCREEN` FPC landed in `J302`, and one SMA bulkhead through the shell. **Nothing
  was powered.**
- **Interim by design:** the 18650 pack stands in until the HackerGadgets NVMe battery board
  arrives (order #11953, still unshipped). That also means the **stock battery board is installed,
  not the NVMe one**, so the `JP1` jumper question does not apply yet — `JP1` lives on the NVMe
  board, and the stock board is 18650-only with no such jumper.
- **Adapter in use is the kit's `RPI CM4 to CPI V3.14 Adapter`** — by elimination, since the
  HackerGadgets adapter has not shipped. *Inferred from the shipping state, not read off the
  silkscreen: the adapter is underneath the CM4 in this frame.* This is an interim answer to the
  adapter question in [`decisions.md`](decisions.md), not a resolution of it — the HackerGadgets
  board is still the one that carries PCIe for NVMe boot.
- **Result — the cells are the problem.** Both are wrapped **`9900mAh 3.7V`**,
  `18650 LI-ION RECHARGEABLE BATTERY`, with **no brand, model or batch code**. No 18650 holds
  9900 mAh; mass-production parts top out near 3500 mAh, so the label overstates by roughly 2.8×.
  Since the two holder positions are in **parallel**, fitting two cells of unknown capacity and
  internal resistance is exactly what the matched-pair rule exists to prevent. Full entry with the
  weigh / voltage / capacity checks that settle it: [`known-issues.md`](known-issues.md).
- **`power-budget.md` is now stale in both columns:** its ≈22 Wh two-18650 figure assumed
  ≈3000 mAh cells, and the 37 Wh LiPo column describes a pack that is not installed. Pack energy is
  **unmeasured**. Left as written rather than rewritten against a number nobody has measured.
- **Also read off this frame:** GNSS module is `GP-02` `BDS+GPS`; `LoRa` and `GPS` u.FL positions
  are present on the AIO V2; mainboard confirms `clockwork` / `CPI 3.14` / `V5`. The 7-way
  `ANT1`–`ANT7` breakout strip is **not** installed in this configuration — a single SMA bulkhead is.
- **Photo:** [`../../images/inventory/20260916-assembly-trial-fit-18650.jpg`](../../images/inventory/README.md)
- **Not established from the frame:** whether a microSD is fitted, whether the `SCREEN` FPC latch is
  closed, which u.FL leads are landed, and whether the display or keyboard are attached. **Nothing
  has been powered on**, so no device behaviour is confirmed by this session either.
- **Antenna port mapping fixed** (same date, recorded after the fact): SDR on the bulkhead SMA,
  LoRa `ANT1`, BT1/BT2 `ANT2`/`ANT3`, Wi-Fi 1 (CM4 onboard) `ANT4`, Wi-Fi 2/3 `ANT5`/`ANT6`, GPS
  `ANT7`. Table, rationale and the three things it implies are in
  [`../reference/antennas-and-rf-connectors.md`](../reference/antennas-and-rf-connectors.md); the
  assembly runbook's one-line u.FL step is now a full routing procedure.
- **Next:** weigh and capacity-test the cells before any power-up. Set `dtparam=ant2` or `ANT4` is
  inert. Source a 915 MHz antenna before enabling the LoRa rail. *(Corrected on merge: the microSD
  was bought and flashed 2026-09-15, so it is no longer a blocker.)*

## 2026-09-15 — uConsole kit + AIO V2 unboxed and photographed

- **What:** Opened the AliExpress/OpenSourceSDRLab parcel (order 8214326520279843), photographed
  the outer carton and both retail-box faces, then both trays as opened, then laid out the full
  contents and photographed that twice. Ten frames total. Nothing was powered, measured, or
  inspected under magnification — this was an arrival record only.
- **Result:** Kit and AIO V2 both present. Retail box label reads `uConsole Kit` / `NC-D` / `NONE`
  with `FCC ID:2A2YT-UC-CM4B` — the kit's own FCC grant, distinct from the CM4's `2ABCB-RPICM4`.
  `NC-D` / `NONE` are recorded verbatim and **not decoded**; the label QR or the vendor listing
  settles what they mean. Mainboard silkscreen reads `CPI 3.14` / `V5`. The kit
  supplied more than the BOM anticipated: its own battery board with a 2-bay 18650 holder, an
  EXT board with a SIM slot, a **CM4→CPI3.14 adapter**, a copper-foil thermal pad, speakers and
  a power button. Three items in the layout are unaccounted for by any order record — two 18650
  cells and a `Meshnology 10000mAh 3.7V 37Wh` LiPo pack — all logged under Discrepancies in
  [`../checklists/inventory-and-inspection.md`](../checklists/inventory-and-inspection.md).
  Two install decisions now have to be made that did not exist before: kit adapter vs HackerGadgets
  adapter (the latter is what carries PCIe for NVMe boot), and EXT board vs AIO V2 for the single
  mini-PCIe slot.
- **Photos:** [`../../images/inventory/`](../../images/inventory/README.md) — thirteen `20260916-*`
  frames, downscaled to 1600 px. None carries a `DateTimeOriginal`, a camera make/model, or a GPS
  block, so the date above is the session date, not a camera timestamp.
- **Close-up frames (AIO V2 group, LiPo label) settled four open items:** the AIO V2 revision is
  `uConsole AIO extension board V2`; the antenna breakout is 7 u.FL→SMA positions `ANT1`–`ANT7`
  with on-board u.FL connectors labelled `SDR` / `LoRa` / `GPS` and a `GP-02 BDS+GPS` GNSS module;
  the antenna count is 8 (6 stubs, 1 telescopic, 1 puck) with 7 pigtails; and the pack label reads
  `Meshnology` / `10000mAh` / `3.7V` / `37Wh` with no model number.
- **Breakout jack gender settled: standard SMA female.** An edge-on frame of the antenna breakout
  held in hand puts all 7 jack faces square to the camera — external threads, recessed centre
  socket, no metal proud of the PTFE. RP-SMA female would show a centre pin. This reverses an
  earlier entry that called polarity unresolvable by photography: it was unresolvable in the
  frames available then, not in principle. The **antenna-side** connectors are still unread, so
  whether the set mates is open — SMA female jacks need SMA male antennas.
- **One earlier reading corrected:** the dim layout frame appeared to show a stub marked `LoRa`.
  The close-up shows only `Wi-Fi` ×2 and `Bluetooth` ×1 — **no LoRa-marked antenna is present**,
  and the stubs are far shorter than a 915 MHz ¼-wave. Nothing gets connected to the SX1262 and
  keyed until a LoRa-band antenna is identified or bought.
- **Not done — and blocking assembly:** per-board inspection. FPC contacts, u.FL connectors,
  board-to-board pins and the AIO V2's RF cans are all unchecked, and no serials have been
  transcribed. The `Bias-T` marking on the rear I/O plate locates the function but does not say
  whether the rail is switched in software or by a jumper. The AliExpress dispute window makes
  the inspection pass time-boxed.
- **Next:** per-board inspection pass with serials; identify the cells and the LiPo pack; measure
  the pack and the rear cavity. *(Corrected on merge: the microSD was bought and flashed
  2026-09-15; #11953 shipped 2026-09-14.)* The NVMe battery board, RJ45 board and `JP1` rows stay
  open until #11953 arrives.

## 2026-09-15 — microSD flashed with uConsole CM4 v3.1, read-back verified

- **What:** Fetched and validated the uConsole CM4 OS image ahead of flashing the build's microSD.
  Card identified as Windows Disk 2 (29.5 GB, Realtek PCIE card reader, mounted `E:`). The card was
  **not** blank — it held an ESP32 scanner's filesystem (`SCANS/` with 3 BLE captures and a
  wardrive CSV, plus `config/`, `fonts/`, and BLE/GATT/IoT/Theengs/UPC databases, 65 MB total).
  Confirmed with the user that this data was expendable before going further.
- **Result:** `uConsole_CM4_v3.1_64bit.img.bz2` downloaded from `dl.clockworkpi.com`
  (2,212,739,229 bytes), extracted to a 7,407,140,864-byte image with the bzip2 CRC passing.
  Structure verified before flashing: MBR `55aa`, partition 1 type `0c` FAT32 `bootfs` (512 MB at
  LBA 8192), partition 2 type `83` Linux (6.87 GB). Both SHA-256 sums recorded in
  [`firmware-versions.md`](firmware-versions.md) — note that ClockworkPi publishes **no** upstream
  checksum, so these are provenance for our copy only, not an authenticity check.
- **Flashed:** written to the card from an elevated Windows shell with the raw writer at
  `D:\Source\uConsole\flash-sd.ps1`, then verified by reading the card back and comparing SHA-256
  against the image — **match**. The resulting partition layout on the card agrees with the image:
  `bootfs` FAT32 512 MB at byte offset 4,194,304 (LBA 8192), Linux partition 6,548 MB at
  541,065,216 (LBA 1,056,768).
- **Still unverified:** nothing has been *booted*. The card is known-good as a byte-for-byte copy of
  the image, which says nothing about whether the uConsole comes up — first boot waits on the
  mainboard, still in transit.
- **Windows flashing traps hit** (both now in [`known-issues.md`](known-issues.md)): raw
  `\\.\PhysicalDriveN` access requires Administrator, and `Set-Disk -IsOffline` does not work on
  removable media — the card's volumes must be locked and dismounted with
  `FSCTL_LOCK_VOLUME`/`FSCTL_DISMOUNT_VOLUME` and the handles held for the whole write.
- **Corrected along the way:** the image is distributed as `.img.bz2`, not the `.img.7z` this repo
  had recorded in two places — `.7z` applies only to the 2023 `v0.1b` xfce image. `.gitignore` also
  had no `*.bz2` rule, so the real image format was not actually excluded from commits.
- **Next:** on mainboard arrival, insert the card and work the first-boot checklist in
  [`../runbooks/imaging-and-first-boot.md`](../runbooks/imaging-and-first-boot.md) — the display
  should light immediately (the image pulls up GPIO9 at boot). Then fill the remaining as-flashed
  rows (EEPROM, kernel, keyboard firmware) in [`firmware-versions.md`](firmware-versions.md).

## 2026-09-14 — LiPo pack swapped to Meshnology (confirmed deliberate)

- **What:** Identified a physical LiPo pack from a photo of its label, flagged it as a mismatch
  against the decided spec, then confirmed with the user it was an intentional substitution.
- **Result:** Label reads "Meshnology, 10000 mAh, 3.7 V, 37 Wh, Lithium Rechargeable Battery."
  This replaces the pack decided 2026-09-07 (UDIY-0001L, 15000 mAh, 55.5 Wh) — swapped due to that
  pack's long shipping time; the Meshnology pack was already on hand. Updated
  [`decisions.md`](decisions.md), [`../accessories.md`](../accessories.md), and
  [`../reference/power-budget.md`](../reference/power-budget.md) (runtime estimates recalculated
  at ~31 Wh usable instead of ~47 Wh).
- **Photos:** [`20260914-lipo-meshnology-10000mah.jpg`](../../images/inventory/20260914-lipo-meshnology-10000mah.jpg).
- **Next:** JST pitch/polarity and protection-circuit checks (still open, see
  [`decisions.md`](decisions.md)) apply to this pack now. Measure rear-cavity fit against it.

## 2026-09-14 — AIO V2 parcel unboxed, contents identified from photo

- **What:** Counted and identified contents of the received AIO V2 parcel, first from a manual
  list, then corrected/detailed against a photo of the unboxed layout. Not yet fitted; board not
  yet inspected under magnification for shipping damage.
- **Result:** GPS antenna ×1 (cylindrical puck-style), WiFi antenna ×3, Bluetooth antenna ×2,
  LoRa antenna ×1 (all rubber-duck, SMA), SDR whip ×1, u.FL-to-u.FL cables ×8 (various lengths),
  u.FL-to-SMA ×1, bagged spare SMA bulkhead hardware. The photo corrected two items misidentified
  from the initial list: "antenna board" is a **7-position SMA bulkhead breakout** silkscreened
  `ANT1`–`ANT7`, wired to the AIO board via FPC ribbon; "USB extension board" is actually **the
  AIO V2 board itself** — its own silkscreen reads "uConsole AIO extension board V2, Designed by
  HackerGadgets.com" (HackerGadgets-branded PCB despite the OpenSourceSDRLab AliExpress listing).
  Also newly observed: the GNSS chip is marked **GP-02, BDS+GPS**; the board's u.FL pads are
  silkscreen-labeled SDR/LoRa/GPS; a separate small **"Bias-T" panel bracket** shipped with the
  kit (purpose/wiring not yet confirmed). Full detail recorded in
  [`../../hardware/specs/aio-v2.md`](../../hardware/specs/aio-v2.md). This resolves the
  antenna-count open item in [`../accessories.md`](../accessories.md).
- **Photos:** [`20260914-aiov2-parcel-contents.jpg`](../../images/inventory/20260914-aiov2-parcel-contents.jpg).
- **Next:** Inspect the AIO V2 board itself, sort the 8 u.FL-to-u.FL cables by length, trace which
  of ANT1–7 maps to which radio, confirm the Bias-T bracket's function. Still waiting on the
  uConsole mainboard (departed GOFO regional hub) and the HackerGadgets kit before assembly.

## 2026-09-14 — Shipment status check, AliExpress order split into two parcels

- **What:** Queried the shipment tracker (`http://homeserver.example-tailnet.ts.net:8090/api/shipments`)
  for current status on the two outstanding packages, then corrected against what actually showed
  up: the AliExpress order (`8214326520279843`) shipped as **two separate physical parcels**
  despite one YunExpress tracking number on file.
- **Result:** The **AIO V2 board has arrived** (not yet unboxed/inspected). The **uConsole v3.14
  mainboard is still in transit** — last scan shows it departed the GOFO regional hub. The
  tracker's earlier "delivered" status only reflected the AIO V2 parcel; don't assume one tracking
  number means one shipment for this order going forward. The HackerGadgets kit (`#11953`,
  NVMe/adapter/RJ45 + battery holder) remains **in transit**: vendor marked it fulfilled 2026-09-11
  but issued no tracking number.
- **Photos:** none this session.
- **Next:** Can inventory/photograph the AIO V2 now per
  [`../checklists/inventory-and-inspection.md`](../checklists/inventory-and-inspection.md) — but
  full assembly still waits on the mainboard and the HackerGadgets kit. Independently, still need
  to buy the BLOCKER accessories in [`../accessories.md`](../accessories.md) (microSD, second
  UDIY-0001L pack) regardless of shipping status.

## 2026-09-06 — CM4 inventory and inspection

- **What:** Unboxed and photographed the Raspberry Pi CM4 delivered 2026-09-04 (Newark order
  10397194). Read the part code, regulatory markings, and silkscreen; checked the board-to-board
  connectors and the antenna provision. Nothing was powered — this was inspection only.
- **Result:** Variant confirmed as **CM4108000** (wireless, 8 GB, Lite) — matches the BOM. No
  visible damage. No printed serial, so serial capture moves to first boot
  (`cat /proc/cpuinfo | grep Serial`). Found a **u.FL external-antenna connector** on the module,
  which introduces an antenna-selection decision (`dtparam=ant2`) recorded in
  [`../../hardware/specs/cm4-lite-8gb.md`](../../hardware/specs/cm4-lite-8gb.md).
- **Photos:** [`../../images/inventory/`](../../images/inventory/README.md) — downscaled copies,
  originals held off-repo with checksums recorded.
- **Next:** Remaining two packages (AliExpress kit + AIO V2, HackerGadgets upgrade kit) are still
  in transit or unshipped. Inventory rows for those stay open.

## YYYY-MM-DD — <title>

- What:
- Result:
- Photos:
- Next:

---

_Template above; copy it for each session._
