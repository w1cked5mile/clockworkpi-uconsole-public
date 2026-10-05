# SDR (software-defined radio) — reference index

General-purpose receive/transmit software and hardware, and the workflows that feed the other disciplines. On this build the RX front end is the AIO V2 RTL-SDR (RTL2832U + R860, 100 kHz–1.74 GHz); `aiov2_ctl SDR on`.

## Receiver / analysis software

| Tool | Role | Link |
|---|---|---|
| SDR++ (and sdrpp-brown fork) | Modern general-purpose receiver; fork preloaded on this build | https://github.com/AlexandreRouma/SDRPlusPlus |
| Gqrx | Lightweight receiver (Linux/Mac) | https://www.gqrx.dk/ |
| GNU Radio | DSP flowgraph framework (build your own) | https://www.gnuradio.org/ |
| SDRangel | Multi-mode RX/TX SDR application | https://github.com/f4exb/sdrangel |
| CubicSDR | Cross-platform receiver | https://cubicsdr.com/ |
| Universal Radio Hacker (URH) | Reverse-engineer unknown protocols | https://github.com/jopohl/urh |
| inspectrum | Offline capture/waterfall analysis | https://github.com/miek/inspectrum |
| SoapySDR | Vendor-neutral device abstraction | https://github.com/pothosware/SoapySDR |
| rtl-sdr (osmocom) | RTL2832U driver + `rtl_test`/`rtl_fm` | https://github.com/osmocom/rtl-sdr |

## Hardware families (reference)

| Device | Notes | Link |
|---|---|---|
| RTL-SDR (RTL2832U) | RX-only, cheap; this build's front end | https://www.rtl-sdr.com/ |
| HackRF One | 1 MHz–6 GHz half-duplex TX/RX | https://greatscottgadgets.com/hackrf/ |
| Airspy | High-performance RX | https://airspy.com/ |
| LimeSDR / PlutoSDR / bladeRF | Full-duplex TX/RX experimenter SDRs | https://wiki.myriadrf.org/LimeSDR |

## Workflow starting points

- Signal discovery → identify via [sigidwiki](https://www.sigidwiki.com/) → decode with a discipline-specific tool.
- Unknown/OOK protocol → capture → **URH** or **inspectrum**.
- Repeatable receive setups → `runbooks/`; device/gain configs → `configs/`.
- Wondering whether the built-in RTL-SDR is enough for a task, or when to reach
  for a HackRF/PlutoSDR/etc. → [`learned/aio-v2-vs-hackrf.md`](learned/aio-v2-vs-hackrf.md).

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| PySDR — Frequency Domain | FFT, bins, FFT size vs resolution bandwidth (B4) | https://pysdr.org/content/frequency_domain.html | 200 on 2026-09-24 |
| SDR++ (upstream) | FFT size, averaging and waterfall range controls in the installed app (B4) | https://www.sdrpp.org/ | 200 on 2026-09-24 |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/rtl-sdr-limits.md`](learned/rtl-sdr-limits.md) | Hard limits of this front end and what they explain |
| [`configs/gain-and-sample-rate-profiles.md`](configs/gain-and-sample-rate-profiles.md) | Per-task gain/rate starting points; device constants |
| [`runbooks/first-capture-and-calibration.md`](runbooks/first-capture-and-calibration.md) | PPM, sample-rate ceiling, first archived capture |

## Capture here

`learned/` DSP notes, `configs/` gain/sample-rate profiles per band, `runbooks/` receive procedures, `findings/` + `_templates/signal-id.md` for captures.
