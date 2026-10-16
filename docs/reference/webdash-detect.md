# webdash Spotter: passive offensive-device detection

Status: **paused, 2026-10-16. The backend is built; the tab, the BLE listener and the learning
section are not.** Work stopped on a platform-level blocker (below). It resumes only once a reply
to the feedback sent about that blocker indicates the remaining work is in bounds — tracked in
[`../../TODO.md`](../../TODO.md).

**Name (owner, 2026-10-16):** the tab is **Spotter** (plain label), replacing the design team's
"Detect" / "Kraken watch". Code paths (`app/detect/`, `/api/detect/*`) keep the `detect` name.

## Sighting names

Agreed by the owner on 2026-10-16. Each name is a themed subtitle shown after the plain class name,
never in place of it (Q8). The keys are `CLASSES` in `webdash/app/detect/rules.py`.

| Class key | Sighting name |
|---|---|
| `flipper` | Dolphin |
| `pwnagotchi` | Remora |
| `marauder` | Kraken |
| `bruce` | Shark |
| `pineapple` | Siren |
| `deauther` | Cutter |
| `implant` | Submarine |
| `deauth_flood` | Squall |
| `beacon_flood` | Ghost fleet |
| `ble_spam` | Flotsam |
| `other` | Unknown contact |

## The concept

The owner asked for a fifth Wi-Fi tab. It watches for the radio signatures of pentest and prank
hardware nearby (Flipper Zero, Pwnagotchi, ESP32 Marauder, Bruce, WiFi Pineapple and similar
devices) and keeps a durable log of contacts. Each contact records UTC time and date, location, device
name, every identifier the radio actually heard, and an icon per device class so record types read
at a glance.

It is a **defensive lookout**, inside this repo's legal posture
([`../../CLAUDE.md`](../../CLAUDE.md), [`../../knowledge/README.md`](../../knowledge/README.md)):

| Does | Never does |
|---|---|
| Reads what Kismet has already heard on `wlan1` (monitor mode, receive-only) | Transmit, deauth, jam, or spam back |
| Logs matches to an owner-supplied rules file, and Kismet's own alerts | Connect to, pair with, or "neutralize" a detected device |
| Records location as a 6-character Maidenhead grid plus an optional place label | Record or export lat/lon |
| Keeps the log on the device, outside git | Upload the log to WiGLE or any map |
| States the rule that fired and its confidence | Claim a match is proof: SSIDs and frame addresses can be spoofed |
| (Planned) passive BLE on the AC1200's `hci1` | Active scanning, Kismet's Bluetooth source, or anything on `hci0` |

The design team ran stages 0–3 of the [pipeline](webdash-design-team.md#the-pipeline) on
2026-10-16:

| Stage | Agent | Outcome |
|---|---|---|
| 0 Brief | main session | Station, user moment, bar rows, out-of-scope list |
| 1 Evidence | `webdash-qa` | Baseline read from the code (screenshots blocked at the time, see below). Found: "Hunt" already names an SDR tab; a fifth tab overflows the tab strip at 390 px; no icon set exists; `.pill` fails contrast in the vintage skin |
| 2 Concept | `creative-director` | Tab **Detect** (`#/wifi/detect`), subtitle **"Kraken watch"**, framed as passive sonar: it listens, classifies, logs, never answers. Owner motifs kept: kraken, siren/mermaid, submarine. Dropped: "booty" (next to the banned "loot") and "hunt" as UI text (collides with `#/sdr/hunt`, implies pursuit). One glyph per class, always beside its plain name, in the text colour |
| 3 Structure | `design-planner` | A watch line (Wi-Fi / BLE / position, each with its off state and control); a "heard in the last 5 min" band; filters and export; a log table grouped by UTC date with expandable detail rows. The USB rail switch moves into the view head |
| 5 Technical review | `senior-rf-engineer` | Legal posture confirmed for detection-only. The signature catalogue was not delivered (see below) |

Owner defaults taken from the stage 3 open decisions: the "seen" marker is stored server-side,
the "now" window is 5 minutes, there is no sound, and the log is kept until cleared (capped at
5,000 contacts).

## What is built (commit `4c7f3e5`, branch `feat/webdash-hunt`)

| Path | What |
|---|---|
| [`../../webdash/app/detect/rules.py`](../../webdash/app/detect/rules.py) | Loads and validates the owner's rules file; matching (exact / prefix / contains / regex) |
| [`../../webdash/app/detect/observe.py`](../../webdash/app/detect/observe.py) | Kismet device or alert → log observation; folds a poll into the store |
| [`../../webdash/app/detect/store.py`](../../webdash/app/detect/store.py) | Contact log, seen marker, watch on/off, per-source coverage intervals |
| [`../../webdash/app/detect/engine.py`](../../webdash/app/detect/engine.py) | Polls Kismet every 10 s, only while the watch is on |
| [`../../webdash/app/detect/export.py`](../../webdash/app/detect/export.py) | CSV (formula-neutralised), JSON and Markdown export |
| [`../../webdash/tests/test_detect.py`](../../webdash/tests/test_detect.py) | 22 unit tests, all passing on the host |

Routes (session-gated like every other write path): `GET /api/detect/records`,
`GET /api/detect/rules`, `POST /api/detect/watch`, `POST /api/detect/seen`,
`POST /api/detect/record/<id>/place`, `DELETE /api/detect/record/<id>`, `POST /api/detect/clear`,
`GET /api/detect/export?fmt=csv|json|md`. The 3 s status snapshot gains a counts-only
`data.detect` block, with no names, SSIDs or addresses.

The rules file is `~/.local/share/uconsole-webdash/data/detect-rules.json`. It is absent by
default, so only Kismet's own alerts are logged until the owner adds rules from sources they've
checked. To prove the log works end to end, match your own hotspot:

```json
{"rules": [{"id": "own-hotspot", "class": "other", "radio": "wifi", "field": "ssid",
            "match": "exact", "pattern": "<your hotspot SSID>", "confidence": "low"}]}
```

Valid `class` values are listed in `CLASSES` in `rules.py`.

**Checked against live Kismet 2025.09, 2026-10-16** (USB rail on, AC1200 on `wlan1`):

| Endpoint | Result | Backend fit |
|---|---|---|
| `POST /devices/last-time/<ts>/devices.json` with field simplification | **200**; a list of records keyed by the requested aliases, 21 devices in a 60 s window; `last_time` an integer, SSID a string or integer `0` when absent | Matches `engine._fetch` and `snapshot._reduce` (0 already reads as "no SSID") |
| `GET /alerts/last-time/<ts>/alerts.json` | **200**; a bare list (not a `kismet.alert.list` wrapper), empty in the window | `engine._fetch` accepts both shapes |

**Ran in the rebuilt container, 2026-10-16.** `test_detect` (22) and `test_survey` (28) pass in the
container. The real status snapshot carries `data.detect` (watch off, `kismet_stopped`,
`not_built`, 0 rules). A live poll ran in a separate process with a throwaway data dir, so the
dashboard's own log stayed untouched, using a temporary catch-all SSID rule. Two polls ran with no
errors in about 110–150 ms each; 5 contacts were logged with their sightings counted, and the
summary carried no addresses. GPS had no fix indoors, so those records had no grid.

Still *unverified*: the `kismet.alert.*` field names, which need a real alert to read, and a
watch switched on from a logged-in session through `POST /api/detect/watch`. Re-check the alert
fields when Kismet next raises one, without printing addresses:

```bash
curl -s -u "$KUSER:$KPASS" "http://127.0.0.1:2501/alerts/last-time/0/alerts.json" \
  | python3 -c 'import json,sys; a=json.load(sys.stdin); print(len(a), sorted(a[0]) if a else "no alerts")'
```

## Not built

- The Detect tab itself (`index.html`, `js/detect.js`, styles, the tab-strip overflow fix, the
  USB-rail move, the overview fact and strip item).
- The passive BLE listener on `hci1`: a localhost host bridge, proved passive-only with `btmon`
  (`Type: Passive (0x00)` present; no `Type: Active`, no `SCAN_RSP`). It must not disturb
  `bluetoothd` or `hci0`. CPython has no `HCI_CHANNEL_USER` constant, so a user-channel bind would
  need `ctypes`.
- The learning section on the devices themselves, the detection-signature catalogue, and the
  starter rules.
- The living-doc updates that land with a working feature (architecture, design, software notes).

## Blockers

| # | Blocker | State |
|---|---|---|
| B1 | The session started in a "don't ask" permission mode that denied Bash, WebSearch and WebFetch. It blocked the QA renders, the tests, git and the RF research | **Resolved** the same day: switched to auto mode |
| B2 | **An automated safety classifier at the platform level stopped responses four times**: while briefing the device researcher for the learning section, during the detection-signature research, and while writing the tab's front-end file. Each stop instructs the assistant not to produce that content again in any form. The classifier's reasons are not visible to the assistant, and no repo setting affects it | **Open.** Feedback has been sent to Anthropic, and a second note points to this repo as evidence of the defensive intent |

B2 is not this repo's legal posture. The posture allows passive detection, and both the design team
and the assistant read it that way.
