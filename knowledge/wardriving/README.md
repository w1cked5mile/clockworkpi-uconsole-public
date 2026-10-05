# Wardriving — reference index

Passive survey and geolocation of broadcast Wi-Fi and Bluetooth beacons. On this build: the AC1200 (MediaTek MT7921AUN, `wlan1`, `mt7921u`) is the survey adapter — arrived and installed 2026-09-30, with monitor mode verified on-device across 2.4/5/6 GHz; its own controller `hci1` (USB) is the passive-BLE controller. (The RT5370 was the 2.4 GHz-only stand-in before it arrived, now removed.) The onboard Wi-Fi (`wlan0`) has no monitor mode and is the network link; `hci0` is Fancy's own paired-device controller. AIO V2 GPS (`aiov2_ctl GPS on`) for geotagging.

> **Scope and ethics.** Wardriving here is **observation only** — logging SSIDs/BSSIDs/signal/position that devices broadcast openly. Do **not** associate with, deauthenticate, capture handshakes from, or attempt to crack networks you do not own or have written authorization to test. Laws vary; passive observation and active intrusion are treated very differently. Respect privacy; don't target individuals. **`aircrack-ng` is the one exception to observation-only** — see [`../../software/aircrack-ng.md`](../../software/aircrack-ng.md) and the [WPA2 handshake capture & audit runbook](../../docs/runbooks/wifi-wpa2-handshake-audit.md): own network or documented written authorization, nothing else.

## Tools

| Tool | Role | Link |
|---|---|---|
| Kismet | Wireless detector/logger (Wi-Fi, BT, more); GPS-aware. Wi-Fi only here — its Bluetooth source scans actively | https://www.kismetwireless.net/ |
| WiGLE | Global wardriving DB + Android app + APIs | https://wigle.net/ |
| gpsd | GPS daemon feeding position to Kismet/tools | https://gpsd.gitlab.io/gpsd/ |
| aircrack-ng suite | Installed 2026-09-21 for authorized WPA/WPA2 auditing only (own network or written authorization); the suite includes injection and deauth tools (`aireplay-ng`) — see [`../../software/aircrack-ng.md`](../../software/aircrack-ng.md) | https://www.aircrack-ng.org/ |
| Sniffle | BLE sniffing (with compatible radio) | https://github.com/nccgroup/Sniffle |

## Knowledge bases

| Resource | Link |
|---|---|
| Ringmast4r wardriving knowledge base | https://ringmast4r.org/ |
| Kismet documentation | https://www.kismetwireless.net/docs/ |

## Workflow

1. Plug in the monitor-capable adapter (Kismet sets monitor mode itself); confirm the AIO GPS has a fix (`cgps`/`gpsd`).
2. Run Kismet with GPS; export to Wiglecsv for WiGLE upload.
3. Geotag/map findings; keep locations general in committed notes.

## ALPR / Flock Safety camera detection

Detecting and mapping Flock Safety ALPR cameras. Current Flock firmware backhauls over cellular LTE with BLE beacons and WiFi SSIDs largely disabled, so passive RF wardriving now misses most units — weight WiGLE desk-mapping and visual/DeFlock confirmation accordingly. See [`learned/flock-safety-alpr-signatures.md`](learned/flock-safety-alpr-signatures.md) (signatures, OUIs, hardware) and [`runbooks/flock-camera-wardriving-detection.md`](runbooks/flock-camera-wardriving-detection.md) (ESP32 / laptop / desk-mapping procedure).

| Resource | Role | Link |
|---|---|---|
| flock-you | ESP32-S3 passive detector (WiFi probe/IE + BLE); buzzer/LED + Flask dashboard | https://github.com/colonelpanichacks/flock-you |
| flock-you docs | Architecture: signatures, channel hopping, JSON schema | https://virtuallyscott.github.io/flock-you/architecture/ |
| flock-back | Python wardriving tool (monitor-mode WiFi + BLE), Kismet integration | https://github.com/NSM-Barii/flock-back |
| flock-finder | Maps Flock cameras from WiGLE using 31 OUI prefixes; GeoJSON/CSV, daily CI | https://github.com/simeononsecurity/flock-finder |
| DeFlock | Crowdsourced OSM-based ALPR map + mobile app | https://deflock.org/ |
| DeFlockILM field test | Reliability of ESP32 detectors on current firmware | https://deflockilm.org/flock-detector-field-test/ |
| Spotting Falcon cameras | Hardware teardown / visual + RF ID | https://www.ryanohoro.com/post/spotting-flock-safety-s-falcon-cameras |

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| Bluetooth SIG — Core Specification | Advertising channels 37/38/39, PDU types, address randomisation (B10) | https://www.bluetooth.com/specifications/specs/core-specification/ | 200 on 2026-09-24 |
| IEEE Registration Authority | What an OUI is; the authoritative lookup source (B11) | https://standards.ieee.org/products-programs/regauth/ | 200 on 2026-09-24 |
| FCC OET KDB 905462 — U-NII DFS | Why DFS channels are quiet; US regulatory domain (B11) | https://apps.fcc.gov/oetcf/kdb/ | blocks scripted checks; confirm in a browser |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/wifi-capture-fundamentals.md`](learned/wifi-capture-fundamentals.md) | Monitor mode, what broadcast frames reveal, MAC randomization |
| [`learned/ble-passive-observation.md`](learned/ble-passive-observation.md) | BLE advertising channels, passive vs active scanning, address types, the verified passive method on this build |
| [`learned/80211-identifiers-and-regdom.md`](learned/80211-identifiers-and-regdom.md) | OUI/BSSID/SSID, the locally administered bit, reading `iw reg get`, DFS, OUI false positives |
| [`learned/flock-safety-alpr-signatures.md`](learned/flock-safety-alpr-signatures.md) | ALPR camera Wi-Fi/BLE signatures and their limits |
| [`configs/kismet-passive-survey.md`](configs/kismet-passive-survey.md) | Rationale and checks around the staged Kismet config |
| [`runbooks/passive-survey-session.md`](runbooks/passive-survey-session.md) | Pre-flight, survey, close-out, privacy-safe finding |

## Capture here

`learned/` 802.11/BT + monitor-mode notes, `configs/` Kismet/gpsd configs, `runbooks/` survey procedure, `findings/` coverage maps and summaries (aggregate, not raw personal data).
