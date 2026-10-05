---
title: Wardriving for Flock Safety ALPR cameras
discipline: wardriving
last_verified: 2026-09-06
---

# Runbook: Wardriving for Flock Safety ALPR cameras

**Goal:** Detect and geolocate Flock Safety ALPR cameras using passive RF wardriving plus desk-based data sources. Signature reference: [`../learned/flock-safety-alpr-signatures.md`](../learned/flock-safety-alpr-signatures.md).

> RF wardriving alone is unreliable on current firmware (LTE backhaul, BLE beacons off, WiFi names stripped). Combine methods; treat a single RF hit as a lead, not a confirmation.

## Prerequisites

- **Passive RX only.** Do not associate with, deauth, jam, or connect to any Flock device or network — see `knowledge/README.md` responsible-use/legal. Passive reception of open broadcasts and photographing devices in public rights-of-way is lawful; interference and unauthorized access are not.
- Hardware (pick a path):
  - ESP32 path: Seeed XIAO ESP32-S3 (or LilyGO T-Dongle S3, or Colonel Panic "Oui-Spy"). Passive 2.4 GHz.
  - Laptop/uConsole path: WiFi adapter with monitor mode — build's **AC1200 (MT7921AUN)** qualifies; BLE adapter (default `hci0`).
- Software + versions: flock-you firmware (ESP32); or flock-back (Python 3.10+, `BlueZ`, `tshark`); WiGLE API key for desk mapping.
- GPS: AIO V2 GNSS (`aiov2_ctl GPS on`) or phone GPS/gpsd for geotagging.

## Steps

### A — ESP32 detector (flock-you)

1. Flash flock-you to the ESP32-S3; confirm boot tones (200 Hz start, 800 Hz ready).
2. Signatures keyed: WiFi SSID substrings, 31 MAC OUIs, wildcard-probe+IE fingerprint, BLE names, Raven UUIDs (see signature reference).
3. Radio config: WiFi hop 11→6→1 (350 ms dwell) or all 13 ch (500 ms) — firmware default; US Wi-Fi uses channels 1–11, so 12–13 add dwell time and no US networks; BLE 5 s cycle / 1 s active window (`#define`-configurable).
4. Standalone: power from USB battery, drive the AO. Hit = three 1000 Hz pulses + LED (GPIO 21); logged as CRC-enveloped JSON to SPIFFS (~200-entry cap).
5. Mapped: pipe USB-CDC JSON (`{"event":"detection","detection_method":"wifi_wildcard_probe_ie_sig",...}`, 5 s per-MAC cooldown) into the flock-you Flask dashboard (`http://localhost:5000`); it correlates GPS (NMEA/gpsd/browser) and exports JSON/CSV/KML.

### B — Laptop / uConsole (flock-back)

1. Put the MT7921 adapter in monitor mode; confirm GPS fix (`cgps`).
2. Run flock-back: `-w` standalone wardrive, `-k` Kismet integration, band preset (2.4/5/combined), configurable hop delay.
3. Detection = WiFi probe requests (hidden SSID) + BLE ads (`FS Ext Battery`, XUNTONG mfr data). Logs to `database/flocks.json` (timestamp, type, RSSI, MAC, vendor, channel, frame metadata); packet mode adds `packets.json`.
4. GPS tagging is not yet built in — log position separately and correlate by timestamp.

### C — Desk mapping (WiGLE + flock-finder)

1. Obtain a WiGLE API key.
2. Run flock-finder `wigle_query.py` with OUIs from `data/flock_ouis.csv`, filtered by country or bounding box.
3. Output GeoJSON/CSV; render on Leaflet/GIS. flock-finder CI refreshes daily; self-host for a specific AO.
4. WiGLE data is historical/crowdsourced — use as leads to verify in person.

### D — Visual + DeFlock

1. Cross-check leads against the DeFlock map (https://deflock.org/; OSM tags `man_made=surveillance` + `surveillance:type`).
2. Confirm in person (pole unit + solar panel + external battery); submit via the DeFlock mobile app (FoggedLens/deflock-app).

## Verification

- Corroborate every RF hit with visual ID and/or the on-unit QR sticker (IMEI/MAC/serial).
- Absence of RF signal ≠ absence of camera (LTE backhaul, BLE off, WiFi idle).
- Flag `CC:CC:CC` and other generic-prefix matches as probable false positives.
- Pass criterion: a mapped point that matches a physically observed unit.

## Teardown

- Power down SDR/GPS/radio rails (`aiov2_ctl SDR off`, `GPS off`); return adapter from monitor to managed mode.
- Keep committed findings location-general (city/grid square); do not commit raw personal-device data or precise private locations.

## References

- flock-you — https://github.com/colonelpanichacks/flock-you · architecture (version-dependent signatures/schema): https://virtuallyscott.github.io/flock-you/architecture/
- flock-back — https://github.com/NSM-Barii/flock-back
- flock-finder — https://github.com/simeononsecurity/flock-finder
- DeFlock — https://deflock.org/ · app: https://github.com/FoggedLens/deflock-app
- Field reliability (mark methods version-dependent) — https://deflockilm.org/flock-detector-field-test/
- Hackaday ESP32 detection — https://hackaday.com/2025/09/26/detecting-surveillance-cameras-with-the-esp32/
