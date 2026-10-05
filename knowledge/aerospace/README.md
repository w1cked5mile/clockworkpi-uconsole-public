# Aerospace — reference index

Aircraft and satellite signal reception. Mostly receive-only and broadly legal. On this build: RTL-SDR for 1090 MHz ADS-B and sat downlinks (external antenna recommended), AIO GPS/RTC for timestamping.

## Aircraft — ADS-B (1090 MHz) & UAT (978 MHz US)

| Tool | Role | Link |
|---|---|---|
| readsb | Mode S / ADS-B decoder (actively maintained) | https://github.com/wiedehopf/readsb |
| dump1090 (FlightAware) | Classic 1090 MHz decoder | https://github.com/flightaware/dump1090 |
| tar1090 | Improved web map for readsb/dump1090 (installed via AIO apps) | https://github.com/wiedehopf/tar1090 |
| dump978 | UAT 978 MHz decoder (US GA) | https://github.com/flightaware/dump978 |
| Awesome ADS-B | Curated list of decoders/feeders/tools | https://adsb.cool/ |

Feeder networks / maps: [adsb.lol](https://adsb.lol/) · [adsb.fi](https://adsb.fi/) · [ADSBexchange](https://www.adsbexchange.com/) · [FlightAware](https://flightaware.com/).

## Aircraft — other data links

| Signal | Tool | Link |
|---|---|---|
| ACARS (VHF) | acarsdec | https://github.com/TLeconte/acarsdec |
| VDL Mode 2 | dumpvdl2 | https://github.com/szpajder/dumpvdl2 |
| HFDL (HF) | dumphfdl | https://github.com/szpajder/dumphfdl |
| SATCOM (Inmarsat) | JAERO | https://github.com/jontio/JAERO |
| Multi-mode client / aggregation | airframes.io xng | https://github.com/airframesio/xng |

## Satellites & weather

| Target | Tool | Link |
|---|---|---|
| Pass prediction | Gpredict | https://github.com/csete/gpredict |
| NOAA APT / Meteor LRPT / many sats | SatDump | https://www.satdump.org/ |
| Global ground-station network | SatNOGS | https://satnogs.org/ |
| Orbital elements (TLE) | CelesTrak | https://celestrak.org/ |
| Amateur satellites | AMSAT | https://www.amsat.org/ |

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| Junzi Sun — The 1090 MHz Riddle | Mode S downlink formats, ICAO address, decoding DF17 by hand (B6) | https://mode-s.org/decode/ | 200 on 2026-09-24 |
| FAA — ADS-B program | 1090ES vs UAT; US mandate context (B6) | https://www.faa.gov/air_traffic/technology/adsb | 200 on 2026-09-24 |
| ICAO Annex 10 Vol IV — Surveillance | Normative Mode S definitions (B6) | — | paywalled; cite by title |
| CelesTrak — TLE format FAQ | TLE fields, epoch and staleness (B7) | https://celestrak.org/columns/v04n03/ | 200 on 2026-09-24 |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/adsb-basics.md`](learned/adsb-basics.md) | 1090ES, DF17/CPR, range horizon, what improves results |
| [`learned/weather-satellites.md`](learned/weather-satellites.md) | APT/LRPT, antennas, pass planning |
| [`configs/adsb-and-pass-prediction.md`](configs/adsb-and-pass-prediction.md) | Decoder settings, baseline metrics, gpredict setup |
| [`runbooks/adsb-receive-tar1090.md`](runbooks/adsb-receive-tar1090.md) | Decoder → map → gain sweep → recorded baseline |
| [`runbooks/noaa-apt-reception.md`](runbooks/noaa-apt-reception.md) | Predict, record, decode a weather-satellite pass |

## Capture here

`learned/` Mode S/ADS-B + sat-pass concepts, `configs/` decoder/antenna/gain configs, `runbooks/` "stand up an ADS-B receiver", "capture a NOAA/Meteor pass", `findings/` reception ranges, logged frames, decoded images.
