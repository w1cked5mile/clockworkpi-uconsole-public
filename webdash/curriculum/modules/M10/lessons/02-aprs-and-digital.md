---
id: M10.aprs
title: APRS and receive-only digital modes
est_minutes: 35
---

APRS — the Automatic Packet Reporting System — is the easiest and most rewarding decode on these
bands, and it is always active on 144.390 MHz in North America. It is AX.25 packets carrying position,
weather, telemetry and short messages, sent as 1200-baud AFSK over FM. The decode chain is the whole
point: antenna → FM demod → AFSK1200 → AX.25 → structured data, and you run it with `rtl_fm` piped
into `multimon-ng` (installed on Fancy) — no licence, no transmitter:

@ref knowledge/ham-radio/learned/digital-modes-and-aprs.md#aprs-144390-mhz-in-north-america

APRS packets are unencrypted by design and already aggregated publicly at aprs.fi, so decoding them
locally is an exercise in the signal chain, not surveillance — the same framing as ADS-B and AIS.

The weak-signal digital modes FT8 and WSPR are built on rigid timing. FT8 uses 15-second slots and
needs the system clock within about a second; WSPR uses 2-minute slots. A drifting clock produces zero
decodes and no error message, which is exactly where NTP and the AIO V2's RTC earn their place — and
why M3 (GNSS and time) is a recommended prerequisite:

@ref knowledge/ham-radio/learned/digital-modes-and-aprs.md#ft8-and-wspr

On this build FT8 is theory only — it needs WSJT-X and an audio loopback, neither installed — but the
timing principle is exam material and matters the moment you add them.

Satellites and the ISS are the hardest, most rewarding targets: short passes (5–10 minutes), Doppler
shift of several kHz on 70 cm, and single-channel FM birds around 436–437 MHz. This is the ground
M9 (satellite passes) builds on:

@ref knowledge/ham-radio/learned/digital-modes-and-aprs.md#satellites-and-the-iss

A sensible order to learn them in — APRS first for immediate feedback, then repeater outputs, then
FT8, then a satellite pass:

@ref knowledge/ham-radio/learned/digital-modes-and-aprs.md#practical-starting-order
