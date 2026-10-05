# software/

Application setup notes for this build. One file per app. Commands were first written from
upstream documentation on 2026-09-06, then run and corrected on this hardware during bring-up
(2026-09-16 onward; see [`../docs/logs/build-log.md`](../docs/logs/build-log.md)). Each file marks
anything still unverified.

| File | Covers |
|---|---|
| [`aiov2_ctl.md`](aiov2_ctl.md) | Rail control, power monitoring, boot rails, RTC sync |
| [`sdr-stack.md`](sdr-stack.md) | rtl-sdr tools, SDR++, calibration, airband listening |
| [`adsb-tar1090.md`](adsb-tar1090.md) | ADS-B decode + map |
| [`meshtastic.md`](meshtastic.md) | LoRa mesh node bring-up and region config |
| [`gps.md`](gps.md) | gpsd, PyGPSClient, NMEA verification |
| [`kismet.md`](kismet.md) | Passive Wi-Fi/BT survey — install, site config, capture-source notes |
| [`aircrack-ng.md`](aircrack-ng.md) | Authorized WPA/WPA2 auditing — install, monitor-mode verification, workflow |
| [`webdash.md`](webdash.md) | Operator dashboard — Docker install, aiov2_ctl bridge, first-run setup |

Install order: `aiov2_ctl` → companion apps → per-app config from [`../configs/`](../configs/).
The runbook that ties these together is
[`../docs/runbooks/software-install.md`](../docs/runbooks/software-install.md). `webdash` is a
later addition, not part of that base install order — it aggregates the others, so it comes last.
