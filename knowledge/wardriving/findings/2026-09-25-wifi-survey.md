---
title: First passive Wi-Fi survey (LAB-15, RT5370)
discipline: wardriving
date: 2026-09-25T17:10Z
location: EM95 (grid from earlier GPS fixes at this location; the GPS rail was off, so this run had no fix)
---

# Finding: First passive Wi-Fi survey (LAB-15, RT5370)

- **Frequency / band:** 2.4 GHz, channels 1–11 (US), hopping at 5 channels/s
- **Mode / modulation:** 802.11b/g/n, receive only — the RT5370 in monitor mode (`wlan1mon`)
- **Equipment:** RT5370 USB adapter (`rt2800usb`) on an external USB port, its own stub antenna,
  indoors. NetworkManager leaves it unmanaged, so it sent no probe requests
- **Software:** Kismet 2025.09.0, foreground run, site config with `kis_log_data_packets=false`
  and `httpd_bind_address=127.0.0.1`

## Observation

Survey window 17:10:06–17:20:16 UTC (10 min 10 s); monitor mode held in all 58 ten-second samples.

| Device type (Kismet) | Count |
|---|---|
| Wi-Fi AP | 4 |
| Wi-Fi Client | 23 |
| Wi-Fi Bridged | 4 |

- **Security mix (access points):** 2 WPA2-PSK (AES-CCMP); 2 unknown — heard only through
  non-beacon frames during the window, so Kismet never read their capabilities. None seen open,
  WEP or WPA3.
- **Access-point channels:** 1, 3, 10 and 11, one each. Two of the four sit off the
  non-overlapping 1/6/11 plan.
- **Client channels:** 10 (12), 3 (3), 6 (2), 1 (1), none recorded (9).
- **Locally administered addresses:** 1 of 23 clients and 1 of 4 access points.
- **Packet log:** 1,400 packets — 651 management (598 probe requests, 24 beacons, 2 probe
  responses, 27 other) and 749 control. **No data frames and no EAPOL frames were logged.**

## Identification

- Candidate signal(s): ordinary home and neighbourhood 2.4 GHz Wi-Fi. No attempt to identify
  networks or devices, by design.
- Confidence: high for the counts; the client count overstates people and devices (address
  randomisation, and one device can appear on more than one channel).

## Conclusion / next steps

- The procedure works end to end on Fancy. Two problems found and fixed during the run:
  Kismet could not bind its web UI while `tailscale serve` held `:2501` (fixed with
  `httpd_bind_address=127.0.0.1`), and Kismet left `wlan1mon` up after a clean exit (removed with
  `sudo iw dev wlan1mon del`).
- With `kis_log_data_packets=false`, the packet log held management and control frames only.
  That settles the open question of whether data or EAPOL frames reach the log.
- 5 GHz and 6 GHz wait for the AC1200.
- The Kismet log was deleted after these counts were taken.
