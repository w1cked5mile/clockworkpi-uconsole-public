# RF fundamentals — reference index

Cross-cutting theory and reference that underpins every other discipline: DSP, modulation, antennas, propagation, signal identification, safety, and spectrum regulation.

## Core concepts to master

- Decibels: dB, dBm, dBi, dBd; link budget; path loss (free-space, Fresnel zones)
- IQ sampling, complex signals, Nyquist, sample rate vs. bandwidth, aliasing, decimation
- Modulation: AM/FM/PM; digital ASK/FSK/PSK/QAM; OFDM; symbol rate vs. baud
- Filters, FFT/waterfall interpretation, SNR, noise floor, gain staging
- Antennas: dipole/monopole, gain/pattern, polarization, SWR, matching, coax loss, grounding

## Learning resources

| Resource | What it covers | Link |
|---|---|---|
| PySDR | SDR + DSP from scratch in Python (best free primer) | https://pysdr.org/ |
| Great Scott Gadgets — SDR with HackRF | Free video course on SDR fundamentals | https://greatscottgadgets.com/sdr/ |
| RTL-SDR Blog | News, tutorials, project ideas | https://www.rtl-sdr.com/ |
| Signal Identification Wiki (sigidwiki) | Identify signals from their waterfall/audio | https://www.sigidwiki.com/ |
| Awesome-SDR | Curated SDR resource list | https://github.com/CanYoleri/awesome-SDR |
| Awesome-RF | Curated RF/SDR/security list | https://github.com/Quetzal-coalt/Awesome-RF |
| ARRL Technical / Antenna info | Antenna theory, practical RF | https://www.arrl.org/antennas |

## Reference data

| Resource | Use | Link |
|---|---|---|
| RadioReference | Frequency + trunked-system database | https://www.radioreference.com/ |
| US Frequency Allocation Chart (NTIA) | Who uses what spectrum (US) | https://www.ntia.gov/page/2011/united-states-frequency-allocation-chart |
| ITU / national regulators | Allocations by region | https://www.itu.int/ |

## Safety & regulation

- RF exposure: FCC OET Bulletin 65 (US) — https://www.fcc.gov/general/oet-bulletins-line — mind power/duty cycle when transmitting.
- Never transmit without the required license/authorization for the band.

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| GPS.gov — performance standards and specifications | GPS accuracy definitions behind DOP and error claims (gap B1) | https://www.gps.gov/performance-standards-specifications | 200 on 2026-09-24 |
| gpsd — JSON protocol | TPV `mode`, SKY `hdop`/`uSat`, `eph`: the fields webdash's GPS collector reads (B1) | https://gpsd.gitlab.io/gpsd/gpsd_json.html | 200 on 2026-09-24 |
| gpsd — NMEA 0183 revealed | GGA/RMC/GSV field layouts; the NMEA standard itself is paywalled at nmea.org (B1) | https://gpsd.gitlab.io/gpsd/NMEA.html | 200 on 2026-09-24 |
| PySDR — Noise and dB | dB vs dBm vs relative power in SDR software; dBFS (B2) | https://pysdr.org/content/noise.html | 200 on 2026-09-24 |
| ITU-R P.526 — propagation by diffraction | Fresnel-zone clearance and obstacle loss (B3) | https://www.itu.int/rec/R-REC-P.526 | 200 on 2026-09-24 |
| ARRL — propagation | Plain-language VHF propagation, Sporadic-E, ducting (B3) | https://www.arrl.org/propagation | 200 on 2026-09-24 |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/db-and-link-budget.md`](learned/db-and-link-budget.md) | dB arithmetic, path loss, worked link budgets, noise floor |
| [`learned/antenna-basics.md`](learned/antenna-basics.md) | Resonance, SWR, gain/pattern, polarization, feedline |
| [`learned/sampling-and-bandwidth.md`](learned/sampling-and-bandwidth.md) | Nyquist, IQ, decimation, aliasing, sustainable rates here |
| [`learned/modulation-basics.md`](learned/modulation-basics.md) | Field guide: what each mode looks like on a waterfall |
| [`learned/receiver-performance.md`](learned/receiver-performance.md) | Gain staging, dynamic range, overload, the 8-bit ceiling |
| [`learned/signal-identification-workflow.md`](learned/signal-identification-workflow.md) | Observation → allocation → reference → decode → log |
| [`learned/us-spectrum-and-legal.md`](learned/us-spectrum-and-legal.md) | Receiving vs decoding vs transmitting in the US |
| [`configs/capture-metadata-conventions.md`](configs/capture-metadata-conventions.md) | Filenames, required metadata, file formats, storage |
| [`runbooks/noise-floor-baseline.md`](runbooks/noise-floor-baseline.md) | One-time RF-environment baseline and gain ceiling |

## Capture here

Put derived understanding in `learned/`, reusable procedures in `runbooks/`, and observations in `findings/`.
