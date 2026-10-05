# GNSS basics — fixes, DOP, NMEA and time

What the GPS station's numbers mean, and why the clock matters. Sources: gpsd's JSON protocol
and NMEA pages (linked in [`../README.md`](../README.md) §Learning-platform references) and this
build's own readings. Written 2026-09-24 for the learning platform (gap B1).

## Why four satellites

Each satellite broadcasts its position and the exact time it sent the signal. The receiver
measures how long each signal took to arrive, which gives a distance. Three distances would pin
down a position if the receiver's clock were perfect — but it's a cheap crystal, off by far more
than the nanoseconds that matter (1 µs of clock error is 300 m of range error). So the receiver
treats its own clock error as a fourth unknown, and four unknowns need four satellites.

| Satellites used | What the receiver can solve | gpsd `mode` | webdash shows |
|---|---|---|---|
| 0–2 | nothing useful | 1 | `none` |
| 3 | latitude and longitude, assuming an altitude | 2 | `2D` |
| 4 or more | latitude, longitude, altitude, and its own clock error | 3 | `3D` |

## Used versus visible

The receiver *sees* every satellite whose signal it can detect, and *uses* only those it has
locked and decoded well enough to trust. Visible is always ≥ used. Indoors, a receiver can see a
handful of satellites and use none.

## DOP: geometry, not signal strength

Dilution of precision says how badly the satellites' layout magnifies ranging errors into
position error. Satellites spread across the whole sky give a low DOP; satellites bunched in one
patch of sky give a high DOP, however many there are.

The working bands used in this repo (common references are a little more lenient):

| HDOP | Reading |
|---|---|
| < 1 | excellent |
| 1–2 | good |
| 2–5 | fair |
| > 5 | poor — treat the position with suspicion |

HDOP is horizontal, VDOP vertical, PDOP both. They are unitless multipliers. gpsd's `eph`
(webdash `eph_m`) is different: gpsd's *estimate* of horizontal error in metres. It combines
geometry with the receiver's own error model, so it is not a measured error.

## Signal strength: C/N0

DOP ignores signal strength. Strength is a separate number: carrier-to-noise density, **C/N0
in dB-Hz** — gpsd's `ss` field. The "carrier" is the satellite's signal, and dB-Hz means the
ratio is taken against the noise in 1 Hz of bandwidth, so it is not comparable to the SNR you'll
meet in M4. Rough guide: above 40 dB-Hz strong, 30–40 good, 20–30 weak but trackable, below about
20 hard to acquire. This build has fixed with satellites at 15–33 dB-Hz.

## Time to first fix (TTFF)

Two kinds of orbit data matter. The **almanac** is a rough description of every satellite's
orbit, valid for weeks; the **ephemeris** is the precise orbit of one satellite, valid for a few
hours. A receiver that already holds them knows where to look.

| Start | What the receiver already knows | Typical TTFF |
|---|---|---|
| Cold | nothing: no time, no position, no almanac | 30 s to several minutes with clear sky; may never fix indoors |
| Warm | rough time and position, valid almanac | tens of seconds |
| Hot | recent ephemeris for the satellites in view | seconds |

On Fancy, gpsd runs with `-n` ([`../../../configs/gpsd/gpsd.default`](../../../configs/gpsd/gpsd.default)),
so the receiver stays powered and polled even with no client. A fix measured without switching
the GPS rail off first is therefore a **warm or hot** start, not a cold one.

## NMEA versus gpsd JSON

The receiver speaks NMEA 0183: comma-separated sentences over the UART. gpsd reads them and
serves JSON to clients. Two sentences carry the fix. This is the well-known textbook example
(Munich), not a reading from this device:

```text
$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47
```

| Field | Value | Meaning |
|---|---|---|
| time | `123519` | 12:35:19 UTC |
| latitude | `4807.038,N` | 48° 07.038′ N (degrees and decimal minutes, not decimal degrees) |
| longitude | `01131.000,E` | 11° 31.000′ E |
| fix quality | `1` | GPS fix (0 = none) |
| satellites | `08` | used in the fix |
| HDOP | `0.9` | |
| altitude | `545.4,M` | above mean sea level |
| geoid separation | `46.9,M` | height of the geoid above the WGS84 ellipsoid |
| DGPS age, station | (empty) | only filled when differential corrections are used |
| checksum | `*47` | XOR of the characters between `$` and `*`, to catch corruption |

`$GNRMC` carries time, date, status (`A` valid / `V` void), position, speed and course. The
talker prefix says which system: `GP` GPS, `GB` or `BD` BeiDou, `GN` a combined multi-system
fix. Fancy's receiver (the AIO V2's GP-02) is GPS plus BeiDou; `GL` (GLONASS) appears on other
receivers.

gpsd turns these into JSON classes. **TPV** (time-position-velocity) carries the fix (`mode`,
`time`, `lat`, `lon`, `eph`); **SKY** carries the satellites — each with `PRN` (its ID), `el` and
`az` (elevation and azimuth in degrees), `ss` (C/N0) and `used` — and the DOPs.
webdash's GPS collector reads exactly these two.

## GNSS time, the RTC and NTP

A 3D fix also gives UTC to well within a microsecond — inside the receiver. Delivered to Fancy
as NMEA text over a 9600-baud serial line with no PPS (pulse-per-second) wire, the system only
gets it to tens of milliseconds (*unverified*; settle with `chronyc sourcestats`). Fancy has
three clocks:

| Clock | Source | Survives power loss? |
|---|---|---|
| System clock | NTP when online; otherwise whatever it booted with | no |
| RTC (real-time clock chip, PCF85063A) | set from the system clock by `aiov2_ctl --sync-rtc` | **only with a backup cell — none is fitted** (a known gap on this build) |
| GNSS | the satellites | n/a — needs a fix |

NTP (network time protocol) sets the system clock from the internet when Fancy is online.
Without the RTC cell, an offline cold boot starts with a wrong system clock. That breaks TOTP
logins (the six-digit codes depend on the time) and mislabels timestamps. It does **not** slow
the GPS fix: gpsd doesn't pass the system time to the receiver. A slow first fix after full power
removal comes from the receiver losing its own stored ephemeris (whether the GP-02 has its own
backup supply is *unverified*). Whether GNSS time is fed into the system clock (chrony's shared
memory source) on this build is *unverified* — check with `chronyc sources`.

## On this build

| Reading | Value | When |
|---|---|---|
| Fix | 3D, 9 of 12 satellites used, HDOP 0.9, grid EM95 | 2026-09-23, checklist 3.3 |
| Fix | 3D, 12 of 17 used, HDOP 1.1, PDOP 1.9, `eph` ≈ 21 m | 2026-09-24, webdash S2 test |
| C/N0 | 15–33 dB-Hz | 2026-09-23 build log |
| TTFF | not measured | — |
