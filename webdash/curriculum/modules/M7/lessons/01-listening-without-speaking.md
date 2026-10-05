---
id: M7.passive
title: Listening without speaking
est_minutes: 20
glossary: [passive-scan, beacon, probe-request, ble-advertisement]
---

Two ways to find out what is nearby. **Passive** observation listens to what devices already
broadcast: a Wi-Fi router's **beacon**, a phone's **probe request**, a Bluetooth LE
**advertisement**. **Active** scanning asks — it sends a request and waits for replies. Asking
is transmitting, even when the request is tiny and the reply is automatic.

**If Fancy asks, Fancy transmits.** A passive scan only hears what devices already broadcast.

| Scan | What the scanner sends | What it hears |
|---|---|---|
| **Passive** | nothing | every advertisement or beacon on the channel it is tuned to |
| **Active** | a request to each device (Wi-Fi probe request, BLE scan request) | the broadcasts plus the replies |
| Classic Bluetooth (BR/EDR) inquiry | inquiry packets on hopping channels | classic devices that answer |

In this module the survey adapter sends nothing. Fancy's onboard radio is another matter: its
Wi-Fi (`wlan0`) is Fancy's network link and its Bluetooth (`hci0`) serves Fancy's paired devices.
Like any laptop, `wlan0` sends probe requests routinely to stay connected. That is Fancy using its
own radio, not surveying, and the survey never uses `wlan0` or `hci0`. Recon uses the AC1200's
Wi-Fi (`wlan1`) and its own Bluetooth controller (`hci1`), both verified on Fancy 2026-09-30.
(Before the card arrived, the RT5370 USB dongle stood in as the Wi-Fi test adapter.)

The repo's legal summary for Wi-Fi and Bluetooth:

@ref knowledge/rf-fundamentals/learned/us-spectrum-and-legal.md#wi-fi-and-bluetooth

## What this module never does

Every item here is a transmission, an intrusion, or a record of other people. Several of the
tools are installed on Fancy (`aircrack-ng` is one) — being installed is not permission.

| Never | Why |
|---|---|
| `bluetoothctl scan on` | Active LE scan plus a classic Bluetooth inquiry — both transmit |
| `btmgmt find`, `hcitool scan`, `hcitool inq` | Active discovery — transmits |
| `iw dev <if> scan`, `nmcli dev wifi list` / `rescan`, `wpa_cli scan` | Active scan — sends probe requests |
| Enabling a Bluetooth adapter (`hci0`, or the AC1200's) in Kismet (its `linuxbluetooth` source) | Kismet lists it as an available source; turning it on scans actively |
| Deauthentication (forged frames that kick a device off its network), `aireplay-ng`, anything from `aircrack-ng` | Transmits to disrupt other people's networks |
| Recording handshakes or PMKIDs (a key identifier an AP sends at connection) | Only useful for breaking a network's key |
| Joining any network you don't own — even an open one | Access without authorisation |
| Decrypting, or logging data frames and payloads | Content, not broadcast |
| Patching `wlan0`'s firmware with nexmon (third-party Broadcom firmware patches) to force monitor mode | Changes Fancy's own network link; out of scope |
| Publishing SSID or MAC lists | Records about other people |
| Uploading logs to WiGLE or any map | Publishes BSSIDs, SSIDs and coordinates |
| Following one device over time or place | Tracking a person |
| Precise coordinates | Grid square (or city) only |

## The law, in pointers

Not legal advice — these are where the rules come from, so you can read them yourself:

- **18 U.S.C. §2511(2)(g)(i)** allows receiving communications "readily accessible to the general
  public". Beacons and advertisements are built to be heard by anyone.
- **Joffe v. Google** (9th Cir. 2013) held that the *payloads* of unencrypted Wi-Fi traffic are
  **not** "readily accessible". It binds only in the 9th Circuit, and state wiretap and stalking
  laws may be stricter — Fancy's Kismet config turns data-frame logging off everywhere.
- **47 U.S.C. §333** forbids wilful interference. The FCC's 2014 Marriott consent decree
  (DA 14-1444) was about a hotel sending deauthentication frames at guests' hotspots.
- **18 U.S.C. §1030** (the CFAA) covers access to computers and networks without authorisation.

When unsure, go back to the three questions from M0: public? observing or decoding? transmitting?
