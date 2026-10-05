# ADS-B decoder settings and pass-prediction setup

Two configurations this discipline depends on. Fill in the measured column during bring-up.

## ADS-B decoder

`tar1090` is the map; `dump1090-fa` or `readsb` is the decoder. Settings that matter:

| Setting | Starting value | Notes | Measured |
|---|---|---|---|
| Gain | 40–49 dB, then swept | Highest **position** rate wins, not highest message count | |
| PPM correction | from `rtl_test -p` | The AIO's TCXO keeps this small but non-zero | |
| Device index | 0 | Only one dongle on this build | |
| Receiver location | set for range statistics | Stays local unless you feed an aggregator | |
| Sample rate | decoder-managed (2.4 MS/s typical) | Watch for USB sample loss on CM4 | |

Gain sweep procedure and the metrics table:
[`../runbooks/adsb-receive-tar1090.md`](../runbooks/adsb-receive-tar1090.md).

## Baseline to record once

| Metric | Value |
|---|---|
| Best gain | |
| Messages/sec at best gain | |
| Positions/sec | |
| Aircraft per 15 min | |
| Max range (km) | |
| Antenna and height | |

Every antenna change is measured against this row.

## Pass prediction (satellites)

`gpredict` is the standard local tool; https://www.n2yo.com/ works without installation.

```bash
sudo apt install -y gpredict
```

Configure once:

- [ ] Ground station: **general** location only (city or grid square), plus approximate altitude
- [ ] TLE sources: Celestrak (weather, amateur, ISS groups)
- [ ] Automatic TLE refresh enabled — stale elements are the usual cause of "nothing at the
      predicted time"
- [ ] Minimum elevation filter set to 20–30° so the pass list only shows workable passes

Record the ground-station settings used, since predicted vs actual AOS is only meaningful with
them.

## Frequencies kept here for convenience

| Target | Frequency |
|---|---|
| ADS-B | 1090 MHz |
| UAT (US general aviation) | 978 MHz |
| NOAA 15 / 18 / 19 APT | 137.6200 / 137.9125 / 137.1000 MHz |
| ISS APRS / SSTV | 145.825 / 145.800 MHz |

Verify satellite status before each session — see
[`../learned/weather-satellites.md`](../learned/weather-satellites.md).
