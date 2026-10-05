---
title: "First ADS-B aircraft — 40+ km"
discipline: aerospace
date: 2026-09-28T00:25Z
location: EM95ma
---

# Finding: First ADS-B aircraft — 40+ km

- **Frequency / band:** 1090 MHz (L-band)
- **Mode / modulation:** Mode S / ADS-B (PPM)
- **Equipment:** Fancy (uConsole CM4, AIO V2), RTL-SDR on the SDR rail
- **Software:** readsb + tar1090

## Observation

First ADS-B reception on Fancy. With the SDR rail on and readsb decoding, tar1090 tracked
multiple aircraft, the farthest at **40+ km**.

Key readings at the time of capture:

- Aircraft tracked: **9** (8 with position)
- Message rate: **66.1 messages/s**
- Farthest range shown by tar1090: **40+ km**

Reading pinned in webdash (SDR rail on, decoding):

- `adsb.aircraft_count`: 9
- `adsb.messages_per_s`: 66.1
- `adsb.state`: running
- `adsb.with_position`: 8
- `aiov2.power.source`: AC
- `aiov2.power_num.power_w`: 4.37
- `aiov2.power_num.voltage_v`: 4.27
- `aiov2.rails.GPS.on`: true
- `aiov2.rails.LORA.on`: true
- `aiov2.rails.SDR.on`: true
- `aiov2.rails.USB.on`: false
- `gps.fix`: 3D
- `gps.grid`: EM95ma
- `gps.hdop`: 0.9
- `gps.satellites_used`: 11
- `gps.satellites_visible`: 15
- `mesh.nodes_seen`: 3
- `mesh.rx_packets`: 0
- `mesh.state`: running
- `system.cpu_percent`: 16.4
- `system.temp_c`: 58.9

## Identification

- Candidate signal(s): ADS-B / Mode S Extended Squitter on 1090 MHz
- Confidence: High — decoded and mapped by readsb/tar1090 with position on 8 of 9 aircraft

## Conclusion / next steps

- SDR rail switched off after the capture (idle SDR rail costs ~0.64 W, more while decoding).
  Restore confirmed: `adsb.state` back to stopped, `aiov2.rails.SDR.on` false, power draw down
  to ~2.33 W.
- Next: log the antenna, gain, and sample rate used; retry to push maximum range beyond 40 km.
