# webdash redesign: components you can read, and a device that teaches

Status: **proposed design, 2026-09-23. Phases 1–3 built the same day; phases 4–8 not built.** Merged from six agent reviews of webdash as it
stood on branch `claude/mesh-messaging-20260923`: design-planner, creative-director,
web-ui-engineer, syllabus-designer, tutor and guided-learning (definitions in
[`../../.claude/agents/`](../../.claude/agents/)). Screenshots reviewed were taken on the device at
1440 px, 1280×480 and 390 px.

Companion documents: [`webdash-architecture.md`](webdash-architecture.md) (what exists and why) and
[`../../software/webdash.md`](../../software/webdash.md) (how to run it).

**2026-09-24:** the learning layer (§Learning layer, §Syllabus, §Missions, build phases 7–8) is
expanded and partly revised in [`learning-platform-plan.md`](learning-platform-plan.md): content
moves out of `/static`, progress moves server-side, the syllabus gains M1b and M12, and the missions
are reconciled with 21 labs. Where the two disagree, the plan is newer.

## Goals

1. Each of Fancy's components (system, power rails, GPS, LoRa mesh, SDR/ADS-B, Kismet) answers one
   question at a glance and tells you what to do when it's off.
2. The dashboard teaches: every reading can be explained using the device's own live numbers, and
   every component leads to a module in `knowledge/` and a hands-on mission checked by live data.
3. It fits the uConsole's screen first, stays usable by keyboard, and works offline.
4. It never makes transmitting or changing hardware feel casual, and it keeps the repo's legal
   posture: receive, learn, licensed transmit.

## What the review found in the current UI

| # | Problem | Evidence | Status |
|---|---|---|---|
| F1 | The broken Meshtastic iframe takes about half the page | 440 px blank frame in all three screenshots; [`../logs/known-issues.md`](../logs/known-issues.md) | **fixed 2026-09-23** |
| F2 | On the uConsole, only System and Rails are above the fold; every radio is below it | 1280×480 screenshot | **fixed 2026-09-23** |
| F3 | Nothing shows which rail powers which service | rail grid is separate from service panels | **fixed 2026-09-23** |
| F4 | Status is colour-only, and misleading: mesh stays green with the LORA rail off; GPS "no fix" is the same amber as Kismet "locked" | `setDot` in `app.js` | **fixed 2026-09-23** |
| F5 | Off-state messages say "start it" with no control and no command | Kismet and ADS-B panels | open (phase 4) |
| F6 | Raw values with no meaning, e.g. "Battery 101%", "Satellites 0/0", no units on SNR | screenshots | partly fixed (below) |
| F7 | The Send box doesn't say it transmits, or on what | mesh form | open (phase 4) |
| F8 | No focus styles; rail switches have no accessible name; inline `onchange` | `styles.css`, `app.js` | **fixed 2026-09-23** |
| F9 | `build_status()` runs once per WebSocket client, so two tabs double the gpsd sessions | `main.py` | **fixed 2026-09-23** |
| F10 | `cpu_percent` reads 0% on the first call | `system.py` | **fixed 2026-09-23** |
| F11 | No place for learning content; `knowledge/` isn't linked from anywhere | — | open (phases 6–8) |

**Fixed during this review (2026-09-23), in the mesh-messaging branch:**

- The message log froze once it held 200 messages. The UI keyed on the count, which stops changing
  when the buffer is full. Messages now carry a monotonic `id`.
- The 200 limit was checked in UTF-16 units in the browser but UTF-8 bytes on the server. The
  browser now checks bytes.
- With no channel list loaded, Send fell back to channel 0 (LongFast). Send is now disabled until
  channels are known.
- The mesh panel's node name, state and channel names went through `innerHTML` unescaped. They are
  now escaped. Received messages were already `textContent` only.
- Meshtastic battery 101 now shows as "external power". SNR shows units, and RSSI is shown.

## Concept and voice

**Concept: "the chart room".** Fancy's instruments are laid out as a navigator's station, drawing on
seamanship and navigation only: position, lookout, hailing, logbook. The name comes from Henry
Every's frigate, but **the theme never uses piracy**: no Jolly Roger, skulls, "plunder", "raid",
"boarding" or "loot". Kismet in particular is a *harbour survey*, passive by definition. Keep the
theme typographic (no parchment, wood or brass gradients).

**Exception for authorized-active content (Track D, added 2026-09-26).** The offensive-but-authorized
track is themed on the *letter of marque* — a privateer's **written authorization** — because that is
the one thing the track is about: own gear or a documented engagement. The framing must foreground
authorization, never aggression: it may use "commission", "sounding", "sea trial", "sanctioned"; it
still may **not** use "raid", "plunder", "boarding" or "loot", and must never glamorize testing
anyone else's network. A privateer without papers is just a pirate — the papers are the whole point.

**Voice rules:**

- The plain technical name comes first; a thematic name is at most a small subtitle. A learner
  must still learn "ADS-B", not only "Lookout".
- Errors are never themed.
- Empty and off states always say why, and what to do next.
- Numbers carry meaning: `SNR −6 dB · marginal`, not `SNR -6`.
- Anything that transmits says where it goes and who can read it.

| Plain name | Subtitle | Primary question it answers |
|---|---|---|
| Radio power (AIO V2 rails) | *Switchboard* | What is powered, and what depends on it? |
| GPS (gpsd) | *Sextant* | Where and when am I, and how sure? |
| Meshtastic (LoRa) | *Hailing* | Who's out there, and can I talk to them? |
| ADS-B (SDR) | *Lookout* | What's overhead? |
| Kismet (Wi-Fi/BT) | *Harbour survey* | What's broadcasting around me? (passive) |
| System | *Hull & engine* | Is the device healthy? |
| Learn | *Chart table* | What can I learn next? |

GPS was *Position & time* until 2026-09-25. It became *Sextant*: a sextant is how a navigator took
a fix from the sky, which is what GNSS does, and it matches module M3's "Shoot the sun". *Compass*
was rejected because GPS gives position and time, not heading, so the name would teach a wrong idea.
*Charts* was rejected because it collides with the Chart Table, and Fancy shows position as a grid
square, never on a map.
| Event log | *Ship's log* | What changed, and when? |

Sample rewrites, taken from the creative-director review:

| Current | Proposed |
|---|---|
| `aiov2_ctl rails` | `Radio power (AIO V2 rails)`, with a note: each switch powers one radio; off means no power draw |
| `Battery 101%` (mesh) | `Power: external` (done) |
| `Fix none` / `Satellites 0/0` | `Searching: 0 satellites heard. Indoors this is normal; outdoors a first fix takes 1–15 min.` |
| `Kismet is stopped — start it to view its UI here.` | `Harbour survey (Kismet) is not running. It only listens. Start: sg kismet -c 'kismet --no-ncurses-wrapper'` (the verified foreground path; the service crash-looped until 2026-09-25 and a start is not yet re-tested) |
| `No messages yet.` | `No messages heard yet. Messages from any node in range appear here.` |
| `Message the mesh…` | `Message everyone on LongFast (public: anyone in range can read it)…` |
| `disconnected — retrying…` | `Connection lost, retrying. Readings below are stale.` (and dim them) |

## Information architecture

The organising idea is **rail → radio → service → action → learn**. Each radio is a *station* that
owns its rail switch, so the dependency is visible where you look.

| Station | Rail (GPIO) | Service / source | Learn module |
|---|---|---|---|
| Mesh (LoRa) | LORA (16) | meshtasticd `:4403` | M4 |
| GPS | GPS (27) | gpsd `:2947` | M3 |
| SDR / ADS-B | SDR (7) | readsb + tar1090 | M5, M6 |
| Wi-Fi survey | USB (23), internal USB-C port | Kismet `:2501` | M7 |
| Power | — (PMIC) | aiov2 bridge `:8765` | M1 |
| System | — | psutil, thermal | M1 |

The USB rail (23) powers the AIO V2's internal USB-C port, meant for an AC1200 or other accessory
radio, so its switch sits on the Wi-Fi survey station, and that station reads *rail off* when USB
is off.

**Derived status.** A station's state combines its rail and its service. For example, Mesh with
LORA off is *off* even though the TCP API still answers.

**Routes** (hash-routed, one page, no framework):

| Route | View |
|---|---|
| `#/` | Overview: status strip and one tile per station |
| `#/mesh`, `#/gps`, `#/sdr`, `#/wifi`, `#/power`, `#/system` | Station detail |
| `#/learn`, `#/learn/<module>` | Syllabus and module pages |
| `#/mission/<id>` | A mission, docked beside its station |
| `#/glossary` | All explainers |
| `#/log` | Ship's log: state changes and milestones |

## Layout

| Target | Viewport | Structure | Visible without scrolling |
|---|---|---|---|
| **uConsole (design first)** | 1280 wide, ~480 usable (*assumed from the screenshot; the panel is 1280×720 before browser chrome*) | 40 px status strip, then a 3×2 tile grid; detail views are 60/40 (primary / facts, actions, learn); the mission pane docks 300–360 px on the right | All six tiles, no scrolling |
| Desktop | ≥1280, >700 tall | Same grid, max width 1400 px; learn drawer and mission pane dock | Everything |
| Phone | <640 | Status strip becomes a scrollable chip row; single column ordered Mesh, GPS, SDR, Wi-Fi, Power, System; the mission becomes a bottom sheet of at most 45% height | Strip plus two tiles |

Rules:

- No fixed-height blank regions. A detail view's primary area is sized from the viewport.
- Iframes appear only in detail views, only when the target is confirmed up (a `web_ui` probe),
  collapsed by default behind "Show embedded map". The Meshtastic frame is removed and replaced by
  a known-issue note. Keep only the tar1090 frame (same-origin, proxied).
- Container queries on cards, so a card behaves the same in a view or beside a mission.

**Status strip** (always visible): device name · power source and voltage · CPU temp · four rail
chips (`GPS ● LORA ● SDR ○ USB ○`) · connection state · Learn · log out.

**Tile anatomy:** header (icon, plain name, status word) → one hero figure → up to two facts →
footer (rail switch or primary action, then ⓘ). The tile opens the detail view; the switch and ⓘ
are separate targets.

## Visual system

Keep the existing dark phosphor-green palette. Additions:

| Token | Value | Use |
|---|---|---|
| `--learn` | dim brass, about `#c9a45c` (*check AA contrast on `--panel`*) | Learning affordances only: Learn links, ⓘ, milestones, the chart table. Green means live data; brass means something to learn. |
| `--idle` | cyan | Up but waiting (no fix, no aircraft yet) |
| `--tx` | orange | Controls that transmit |
| `--focus` | `#facc15`, 2 px outline | `:focus-visible` everywhere |
| `--panel-2` | `#0e130e` | Replaces four hard-coded uses |

**Status never relies on colour alone:**

| State | Colour | Glyph | Word |
|---|---|---|---|
| running | `--ok` | ● | live |
| idle | `--idle` | ◐ | waiting |
| off (deliberate, normal here) | `--off` | ○, dashed border | off |
| needs action | `--warn` | ▲ | action |
| error | `--err` | ✕ | error |
| stale (no update for >10 s) | dimmed | — | "last update 14 s ago" |
| transmit control | `--tx` | antenna glyph | TX |

**Type scale** (monospace for values, tabular numerals): 12 / 14 / 16 / 20 / 28 px. The 28 px size
is for the single hero figure per tile. **Spacing:** 4 / 8 / 12 / 16 / 24 / 32. Targets are at
least 36 px (44 px on phone).

**Icons:** single-weight inline SVG line icons in the style of nautical chart symbols: compass rose
(GPS), signal flags (mesh), radar arc (ADS-B), buoy (Kismet), lever (rails), thermometer, battery,
book (learn), TX.

**Signature elements:**

- **Bearing ring.** One reusable circular gauge for "what's around me and how well do I hear it":
  GPS satellites by azimuth, the last mesh message's SNR, and aircraft by bearing. Each needs the
  collector fields listed under [Data gaps](#data-gaps).
- **Ship's log strip.** A one-line UTC-stamped ticker of real state changes under the header
  (`14:02Z GPS 3D fix, 7 sats`). Expands to `#/log`. Built from real transitions only.

## Stations

| Station | Tile | Detail view | Primary action | Off / idle state (teaches) |
|---|---|---|---|---|
| **Mesh** | nodes heard (hero, excluding self), unread count, last message | Message log as the main area; channel tabs; node list; radio config (region, preset, hop limit, channel utilisation) | **Transmit on ⟨channel⟩** in `--tx`, with a byte counter and a "public" badge; disabled with a reason when LORA is off | "LoRa rail off: the SX1262 is unpowered. Messages sent to you now are missed and not replayed." |
| **GPS** | fix in words (hero), satellites used/visible, time since fix | Bearing-ring sky plot, fix type, HDOP, time to first fix; position as **Maidenhead grid by default**, precise coordinates behind a reveal press | GPS rail | "Searching: needs a sky view" as *idle*, not a warning |
| **SDR / ADS-B** | aircraft (hero), with position, message rate | tar1090 frame sized to the viewport; aircraft table (callsigns as text only) | SDR rail; open map (hidden until readsb runs) | "SDR rail off (the default). readsb restarts in a loop without a dongle; that's expected." |
| **Wi-Fi survey** | devices (hero), state | Counts by type only, never SSIDs or MACs on the dashboard face; adapter status | The verified start command to copy (no new write path) | "Passive survey only: listens, never connects." Links to the responsible-use section |
| **Power** | source, voltage, watts | Charge-flow diagram (AC → system and pack), V / A / W, mode sentence, runtime *estimate* with an "untested pack" badge | Rail switches with their consequences as descriptions ("Turning SDR off stops ADS-B") | n/a |
| **System** | CPU temp (hero), CPU and memory bars | Sparklines (2 h), throttle state | none | n/a |

**Transmit and hardware controls.**

- The first time a person uses Send or a rail switch, it shows one line saying what it does, e.g.
  "Transmits on 902–928 MHz, public channel, readable by anyone. Legal under FCC Part 15; don't
  include location or personal details."
- The mesh channel select has no silent default.
- Rail switches become `button[role=switch]` with `aria-checked`, a busy state and an inline error
  on failure.

## Learning layer

| Entry point | Where | Content | Behaviour |
|---|---|---|---|
| ⓘ on every glossary term | next to labels | tutor explainers | Native `popover`: tooltip line, "right now on Fancy" filled from live status, Learn more → module |
| Off / idle card | inside each off tile | tutor copy | The most-read teaching surface |
| State-triggered hints | panel footers | syllabus hints | e.g. GPS 0/0 → "No sky view. Normal indoors"; first mesh message → "What does −6 dB SNR mean?" |
| Missions | docked beside the station | guided-learning | Steps tick from live data |
| Syllabus | `#/learn` | 12 modules, 3 tracks | Module page: concepts, live readout, hands-on mission |
| Ask the tutor | explainer drawer | tutor agent | Phase 1: copies a prompt (field, explainer, status with lat/lon removed) for `claude --agent tutor`. Phase 2 is an [open decision](#open-decisions) |
| Milestones | ship's log and tile mark | creative director | Real-data triggers only; once each; no scores or streaks; each offers "Copy as finding" |

### Content format

- All learning content ships as static JSON in `webdash/app/static/learn/`, so it works offline.
- Files: `modules.json`, one file per module, `glossary.json`, `missions.json`.
- Blocks are typed (`p`, `list`, `code`). A tiny inline renderer supports only `**b**`, `` `code` ``
  and internal `[text](#/route)` links.
- `{live:mesh.last_snr}` tokens resolve against the status store and are inserted as text.
- Nothing device-specific goes in `/static`, because it is served without auth.

### Explainers

The tutor review supplied full text for ten: CPU temp, load, rails, power, GPS fix, satellites,
ADS-B, Kismet, channels and SNR. It also supplied one-liners for every other field, and the next
concepts: RSSI, noise floor, channel utilisation, airtime, LongFast, the US 902–928 MHz region, hop
limit, 1090 MHz/CPR, radio horizon, monitor mode, SDR gain and HDOP. They become
`glossary.json` in phase 6.

### Syllabus

| # | Module | Needs | Lab on Fancy (success visible) | Today |
|---|---|---|---|---|
| M0 | Orientation and the rules | — | Panel census: which control transmits | ready |
| M1 | Platform and power | M0 | SDR rail cost from `aiov2_ctl --watch` | ready (watts not yet on the dashboard) |
| M2 | dB, antennas, link budget | M0 | FSPL for 5 km at 915 MHz by hand | ready |
| M3 | GNSS and time | M1 | 3D fix with ≥6 satellites used; TTFF logged | needs outdoors |
| M4 | LoRa and Meshtastic | M1 | 24 h passive soak; then one legal Part 15 message | waiting on first packet |
| M5 | SDR foundations | M1, M2 | `rtl_test`, PPM, `rtl_power` noise baseline | ready |
| M6 | ADS-B | M1 | Aircraft with position on the map; max range logged | ready (SDR rail) |
| M7 | Passive Wi-Fi survey | M0, M3 | 10-minute survey; no monitor interface left after | Kismet service crash-looped until 2026-09-25; the foreground run is still what the lab uses |
| M8 | Identifying signals | M5 | Three signal-ID entries | ready |
| M9 | Weather satellites | M5, M8 | One recorded pass | check the NOAA constellation first |
| M10 | Ham bands and licensing | M2, M5 | Hear a repeater or APRS on 144.390 (receive only) | ready |
| M11 | Capstone field session | M3, M4, M6, M7 | 2 h on battery with all four services | wait for the Meshnology pack |

Tracks:

| Track | Modules | Time |
|---|---|---|
| **A, just got Fancy** | M0, M1, M3, M4, M6 | ~6 h |
| **B, RF curious** | A plus M2, M5, M7, M8, M9, M11 | ~20 h |
| **C, ham-bound** | M0, M2, M5, M8, M10 | ~14 h |

Every lab shows its "Today" status in the UI, so a learner never mistakes a known fault for their
own mistake.

### Missions

Missions are step lists whose checks are **declarative predicates** in `missions.json`, e.g.
`{"path": "aiov2.rails.SDR.on", "op": "eq", "value": true}`.

- Supported operators: `eq`, `ne`, `gte`, `lte`, `in`, `exists`.
- Computed checks (a 30 s mean, time since step start) are a small named registry in JS. Nothing is
  `eval`'d.
- A check passes only after it holds on two ticks in a row.
- Steps that depend on the world (sky view, another node in range) are "waiting on the world". They
  don't block the mission, and they complete in the background.
- Missions never flip rails or start services themselves. Transmitting is optional and confirmed,
  and never required to finish a mission.

| Mission | Steps (checks) | Module |
|---|---|---|
| **Walk the deck** (onboarding, 10 min) | live connection; find CPU temp; find the power source; open each rail card; read the status legend; pick a first mission (suggested from live state) | M0 |
| **Know your power** | unplug (`power.source != AC`); 60 s idle draw; SDR on and measure the difference; SDR off; plug back in. Stop if the pack is below 3.5 V (unverified 18650s) | M1 |
| **Shoot the sun** (GPS) | rail on; gpsd reporting; satellites visible ≥1 (waiting); 2D then 3D fix with TTFF timed; switch display to grid square | M3 |
| **Hail the fleet** (mesh) | meet your node; read channels; why "nodes seen" includes you; keep watch for any received packet (waiting); *optional* first message; read a signal report | M4 |
| **Watch the skies** (ADS-B) | SDR on; readsb running within 90 s; messages per second > 0; plane with position and open the map; SDR off | M6 |
| **Harbour survey** (Kismet, passive) | acknowledge the passive-only rules; start with the verified foreground command; set the Kismet admin login; devices ≥1; stop and confirm `wlan1` is managed | M7 |

**Progress** is stored per browser, in `localStorage` under a `fancy.v1.` prefix. Every access is
wrapped in try/catch, and the UI works without it. Evidence snapshots (e.g. TTFF 94 s, SDR +0.9 W,
first packet SNR −6) never include coordinates or message text. A "Copy as finding" button fills
[`../../knowledge/_templates/`](../../knowledge/_templates/) fields, so results flow back into
`knowledge/*/findings/`.

## Data gaps

All new routes are read-only, session-gated, time out within 2 s and fail into a `state` value.
The table is ordered by how many features need each field.

| Field | Source | Needed by |
|---|---|---|
| `aiov2.power` as numbers (W, V, A, %) plus `mode`/`direction` passthrough | bridge (strings already sent) — **done 2026-09-24** as `aiov2.power_num` | Power view, M1, Know your power |
| `mesh.nodes_heard` (excluding self), `last_rx_ts`, `rx_packets`, `channel_util`, `air_util_tx`; radio config | `iface.nodes`, localStats/deviceMetrics (*verify availability on meshtasticd 2.7.26 portduino*) | Mesh tile, M4, Hail the fleet |
| `GET /api/mesh/nodes` (names, last heard, SNR, hops; **no positions**) | `iface.nodes` | Mesh detail |
| `gps.hdop`, `tpv_age_s`, `sky[]` (PRN, az, el, ss, used), `grid` (Maidenhead, server-side) | gpsd TPV/SKY | GPS detail, bearing ring, M3 |
| `adsb.messages_per_s`, top-25 aircraft (hex, flight, alt, rssi) | readsb `stats.json`, `aircraft.json` | SDR detail, M6 |
| `services.*.{active, n_restarts}` | new read-only bridge endpoint (systemd) — **done 2026-09-24** (`GET /services`) | tells "stopped" from "crash-looping" |
| `web_ui` up/down for meshtasticd `:9443` and Kismet | TCP probe | frame gating (F1) |
| `system.throttled` | `get_throttled` via bridge | System, M1 |
| `GET /api/history` (2 h ring buffer at 30 s: CPU, temp, V, W, satellites, nodes) | in-app | sparklines |
| Kismet read-only API token | stored server-side, never committed | Kismet device counts past `locked` |

## Build plan

Each phase ships on its own. Verify each on the device: `sg docker -c 'docker compose up -d
--build'`, then Chromium at `127.0.0.1:8090`, then a phone over Tailscale.

| Phase | Scope | Verify |
|---|---|---|
| 1. Fixes | F1 (remove the mesh frame, add `web_ui` gating), F4 derived status and glyphs, F8 focus and `role=switch`, F10, unclosed `<span>`s in `index.html`, escaping of every remaining `innerHTML` template | Keyboard-only pass with visible focus; no blank frame with LORA on; mesh dot goes off with LORA off |
| 2. One collection loop | A single background task builds status every 3 s and every WebSocket gets the cached copy (F9); `/api/history` | Two tabs, one gpsd session in `ss -tn \| grep 2947` |
| 3. Skeleton | ES modules, router, status strip, overview tiles in the new order; existing panels move into detail views unchanged | Every route loads; back/forward work; overview fits 1280×480 with no scroll |
| 4. Components | Status card, service card with teaching off-state, rail switch, message-log rewrite (append-only, byte counter, TX caption, disabled with reason) | Emoji counted in bytes; form disables when LORA goes off |
| 5. Collectors and detail views | Fields from [Data gaps](#data-gaps); sky plot, node table, aircraft table, power flow | GPS against `cgps`; nodes against `meshtastic --nodes`; aircraft against tar1090 |
| 6. Explainers | `glossary.json` from the tutor review, popovers, the "right now on Fancy" readout | Tab to ⓘ, Enter opens, Esc closes; `<script>` in a glossary entry renders as text |
| 7. Learn | Syllabus pages, `{live:}` tokens, the ship's log strip, milestones | Renders offline; progress survives reload and degrades in a private window |
| 8. Missions | Predicate evaluator, docked pane, the six missions | "Watch the skies" end to end, each step ticking from live data |

Phases 1–2 were built and verified on the device on 2026-09-23, except that the ADS-B frame is
still gated on the SDR rail, not collapsed behind "Show embedded map" (phase 4). Phase 1's
Kismet frame is gated on Kismet's own state, which already implies its web UI is answering. Phases 3 onward can start once the open decisions below are
settled.

## Open decisions

The owner asked for phase 3 without choosing, so phase 3 (2026-09-23) went with the
recommendation on the first four rows below: tutor copy-prompt only (nothing built yet),
`localStorage` for progress (nothing built yet), only the tar1090 frame kept, and GPS as a grid
square by default. Themed subtitles are on. Any of these can be reversed; see
[`../logs/decisions.md`](../logs/decisions.md).

| Decision | Options | Recommendation |
|---|---|---|
| Ask-the-tutor in the dashboard | (a) copy a prompt for `claude --agent tutor`; (b) a server `/api/tutor` route calling the Claude API | (a) now. (b) needs an API key kept out of the repo, internet access, and a rule that the route can only read status |
| Progress storage | per-browser `localStorage`, or a server file | `localStorage`: a server file would add a third write path for little gain on a single-operator device |
| Embedded frames | keep all, or only tar1090 | Only tar1090, collapsed; link out to the rest |
| Precise GPS position on the dashboard | shown, or grid by default with a reveal | Grid by default, matching the repo's location rule |
| Themed subtitles | on, or off | On, as subtitles only; easy to drop |

## Skins (added 2026-10-04)

The visual look is a **skin**, selectable and independent of the theme/voice layer (which stays the
same across skins — subtitles, naming, the legal posture are unchanged). Two ship:

| Skin | `data-skin` | Look |
|---|---|---|
| Chart room (default) | *(attribute absent)* | Dark green-phosphor instrument panel; Courier mono; the original design. |
| Vintage | `vintage` | Mid-century Simpson Electric panel meter: aged-ivory faceplate tiles in dark bakelite bezels, sepia ink, oxblood needle-red accents. Italic GFS Didot Classic wordmark/titles, C059 (Century Schoolbook) body, monospace only for live readings. |

**How it works.** A skin re-points the existing `:root` CSS variables under
`:root[data-skin="<name>"]` in `styles.css`, plus a few font/texture rules; markup never changes, so
a third skin is just another token block. The default skin leaves the attribute unset. The **Skin**
toggle in the Learn head cycles skins and persists the choice in `localStorage` (`fancy.v1.skin`);
an inline loader in `index.html` sets the attribute before first paint so reloads don't flash.

**Constraints a new skin must keep:** offline only — use fonts already on the device (`fc-match`
to confirm) or a self-hosted face, never a CDN; keep the status-level contrast ≥ 4.5:1 on its panel
colour; and don't restyle anything outside the token block and a handful of scoped rules, so the
other skins stay intact.

## Content gaps in `knowledge/`

These came from the syllabus review:

1. No GNSS `learned/` doc: fix types, DOP, TTFF, NMEA, time vs RTC. Suggested path:
   `rf-fundamentals/learned/gnss-basics.md`.
2. Platform and power as a learning topic: 1S Li-ion, PMIC readings, rail economics.
3. Reading received Meshtastic packets: SNR/RSSI, hops, NodeDB, why a new node hears nothing, what
   public channels expose.
4. Bluetooth/BLE passive survey fundamentals.
5. Every `findings/` folder is empty. The labs should seed the first entries.
6. A dashboard-literacy doc: each field, its source and its units.
7. [`../../knowledge/README.md`](../../knowledge/README.md) still says findings wait until the
   hardware is in hand.
