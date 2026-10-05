# Weather satellites — APT and LRPT

Polar-orbiting weather satellites transmit imagery continuously on VHF. With a correct antenna and
a pass prediction, this build can receive them.

## What is up there

| System | Frequency | Mode | Status |
|---|---|---|---|
| NOAA 15 | 137.6200 MHz | APT (analog) | **Decommissioned 2025-08-19** |
| NOAA 18 | 137.9125 MHz | APT | **Decommissioned 2025-06-06** |
| NOAA 19 | 137.1000 MHz | APT | **Decommissioned 2025-08-13** |
| Meteor-M N2-x | ~137.1 / 137.9 MHz | LRPT (digital, QPSK) | Series status changes — check before planning |

**NOAA APT is off air** (source: [NOAA OSPO, 2025-08-20](https://ospo.noaa.gov/data/messages/2025/08/MSG_20250820_1410.html)).
The remaining 137 MHz imagery is Meteor-M LRPT, which needs SatDump (not installed) and a 137 MHz
circular or V-dipole antenna (not on hand as of 2026-09-24). The APT content here is kept as theory.

**Verify the constellation before a session.** Satellites are decommissioned and replaced; a
frequency that worked last year may be silent. Sources: https://www.n2yo.com/, satellite status
pages, and the NOAA/NASA operational notices.

## Signal characteristics

- APT: ~34 kHz wide, FM, an audible 2400 Hz subcarrier tone. Decoders turn the audio into imagery.
- LRPT: ~120 kHz wide, digital QPSK. Better images, less tolerant of weak signal.
- Passes last 10–15 minutes from horizon to horizon.
- Doppler shift is a few kHz across a pass — APT tolerates it; LRPT decoders usually correct it.

## Antenna is the deciding factor

These satellites transmit **right-hand circular polarization** from a moving point in the sky.

| Antenna | Notes |
|---|---|
| V-dipole | Two ¼-wave elements at 120°, horizontal, ~547 mm each at 137 MHz. Cheapest thing that works. |
| QFH (quadrifilar helix) | Circularly polarized, near-hemispherical pattern. Best fixed option. |
| Turnstile | Circular, good compromise |
| Vertical whip | Poor — wrong polarization and pattern, expect fragments at best |

A linear antenna into a circular signal loses ~3 dB unavoidably; a *wrong-pattern* antenna loses far
more at the low elevations where passes begin and end.

## Pass prediction

A session must be planned around a pass. Use `gpredict`, https://www.n2yo.com/, or a phone app;
you need AOS/LOS times, maximum elevation, and direction. **Passes above ~30° elevation are worth
recording; below ~20°, expect noise.**

## Workflow

1. Predict a pass with good elevation.
2. Set up the antenna outdoors with a clear sky view.
3. Record the full pass as audio (APT) or IQ (LRPT) — decode afterwards, not live.
4. Decode with a tool such as `noaa-apt` or SatDump.
5. Log the pass, elevation, and result as a finding.

Runbook: [`../runbooks/noaa-apt-reception.md`](../runbooks/noaa-apt-reception.md).

## Expectations

First attempts commonly produce partial or noisy images. The usual causes, in order: wrong or
poorly sited antenna, low-elevation pass, gain set too high, and local 137 MHz interference.
