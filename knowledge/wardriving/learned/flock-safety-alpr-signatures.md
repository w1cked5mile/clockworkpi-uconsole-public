---
title: Flock Safety ALPR — RF/wireless signatures
discipline: wardriving
date: 2026-09-06        # UTC
---

# Flock Safety ALPR — RF/wireless signatures

Durable target profile for identifying Flock Safety automated license-plate-reader (ALPR) cameras and associated nodes by their WiFi, BLE, and physical signatures. Companion runbook: [`../runbooks/flock-camera-wardriving-detection.md`](../runbooks/flock-camera-wardriving-detection.md).

## Detectability status (2025–2026)

Passive RF wardriving of Flock hardware has degraded sharply. Current-firmware Falcon/Condor units backhaul over **cellular LTE**, WiFi is enabled mainly during install/troubleshooting, and BLE beacons are disabled on a growing share of units. What remains on newer units is **intermittent WiFi probe requests for a hidden network** — a faint signal easily missed from a moving vehicle. Treat RF as a supplement to visual ID and public-records requests, not a standalone census.

Falsifier on record: DeFlockILM drove an OUI-SPY (flock-you firmware) past **4 confirmed** cameras and detected **0**.

## Product families

- **Falcon / Falcon Flex** — fixed pole-mounted ALPR (the common target)
- **Condor** — PTZ camera
- **Raven** — acoustic gunshot-detection node (BLE service UUIDs below)

## Hardware (Falcon V2)

| Element | Detail |
|---|---|
| Compute | Lantronix Open-Q 624A SoM · Qualcomm Snapdragon 624 · Android 8.1 |
| Cellular | LTE Cat-4 (Sierra Wireless RC76B) — primary backhaul; uploads stills + vehicle-fingerprint metadata, not live video |
| WiFi | Lite-On 802.11 a/b/g/n/ac; used mainly at install (web positioning UI) |
| Bluetooth | External battery pack ↔ camera link |
| Power | Solar panel + battery; no hardwired connection required |
| Marking | QR sticker encodes part number, IMEI, MAC, serial |

## WiFi signatures

SSID substrings (case-insensitive on newer firmware): `Flock-[partial-MAC]` (camera AP, install/troubleshoot only), `FS Ext Battery`, `Penguin`, `Pigvision`, generic `flock`/`Flock`/`FLOCK`.

MAC OUI prefixes — community fingerprinting (@NitekryDPaul + DeFlockJoplin) catalogs **31 Flock WiFi OUIs**, ~19/31 with data in WiGLE. Representative:

- WiFi variants: `70:C9:4E`, `3C:91:80`, `D8:F3:BC`, `80:30:49`
- Battery units: `58:8E:81`, `EC:1B:BD`, `90:35:EA`
- `CC:CC:CC` — generic/test default; matches non-Flock devices too (false-positive source)
- Full list: `data/flock_ouis.csv` in simeononsecurity/flock-finder (range ~`70:C9:4E`…`82:6B:F2`)
- `82:6B:F2` has the **locally administered bit** set (`0x82 & 0x02 ≠ 0`), so it is not an IEEE
  OUI: any randomised phone or laptop address can start with it. A match on that prefix alone is
  no evidence of a Flock device — see
  [`80211-identifiers-and-regdom.md`](80211-identifiers-and-regdom.md#oui-false-positives)

Probe-request/IE fingerprint (current-firmware method) keys on the combination: 802.11 management frame type=0 subtype=4 (probe request) + SSID IE length 0 (wildcard/hidden) + transmitter OUI in the known list + IE field pattern match. Detector rule value: `wifi_wildcard_probe_ie_sig`. Cameras sleep most of the duty cycle and wake briefly to upload, so WiFi is only observable in short windows.

## BLE signatures

- Advertised names: `FS Ext Battery`, `Penguin` (updated to numeric-only `Penguin-NNNNNNNNNN`), `Flock`, `Pigvision`
- Manufacturer data from **XUNTONG (company ID `0x09C8`)** carrying serials on external batteries
- Raven service UUIDs: `0000180a-0000-1000-8000-00805f9b34fb` (Device Info), `00003100-0000-1000-8000-00805f9b34fb` (GPS)
- Caveat: BLE beacons disabled on many deployed units; absence of BLE ≠ absence of camera

## Physical / visual ID

Small enclosure on a pole, frequently with a solar panel and external battery box. Falcon = fixed ALPR, Condor = PTZ, Raven = acoustic node. Visual ID + the DeFlock app is currently the most reliable field method; the on-unit QR sticker (IMEI/MAC/serial) confirms.

## References

- flock-you — https://github.com/colonelpanichacks/flock-you · architecture: https://virtuallyscott.github.io/flock-you/architecture/
- flock-back — https://github.com/NSM-Barii/flock-back
- flock-finder (31 OUIs, WiGLE) — https://github.com/simeononsecurity/flock-finder
- Ryan O'Horo, "Spotting Flock Safety's Falcon Cameras" — https://www.ryanohoro.com/post/spotting-flock-safety-s-falcon-cameras
- DeFlockILM field test — https://deflockilm.org/flock-detector-field-test/
- Hackaday, "Detecting Surveillance Cameras With The ESP32" — https://hackaday.com/2025/09/26/detecting-surveillance-cameras-with-the-esp32/
- DeFlock map — https://deflock.org/ (formerly deflock.me)
