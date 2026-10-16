# webdash Detect: passive offensive-device detection

Status: **paused, 2026-10-16. The backend is built; the tab, the BLE listener and the learning
section are not.** Work stopped on a platform-level blocker (below). It resumes only once a reply
to the feedback sent about that blocker indicates the remaining work is in bounds — tracked in
[`../../TODO.md`](../../TODO.md).

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

**Unverified on this build:** the Kismet `/devices/last-time/<ts>/devices.json` and
`/alerts/last-time/<ts>/alerts.json` endpoints and the `kismet.alert.*` field names. They come
from Kismet's REST documentation, not from a run against Kismet 2025.09 on Fancy. The backend has
also not yet run in the container. Settle with the USB rail on and Kismet running:

```bash
curl -s -u "$KUSER:$KPASS" "http://127.0.0.1:2501/alerts/last-time/0/alerts.json" | head -c 400
curl -s -u "$KUSER:$KPASS" -X POST "http://127.0.0.1:2501/devices/last-time/0/devices.json" \
  -d 'json={"fields":[["kismet.device.base.macaddr","mac"]]}' | head -c 400
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
