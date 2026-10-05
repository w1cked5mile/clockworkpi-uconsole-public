---
id: M9.targets
title: What is up there, and the antenna problem
est_minutes: 30
---

A handful of things in low orbit are receivable with this build and a modest antenna: the ISS (its
packet digipeater and periodic SSTV image events), single-channel FM amateur satellites around
436–437 MHz, and the polar weather satellites on 137 MHz. The first and hardest lesson is to **check
status before planning**, because satellites are decommissioned and replaced and frequencies go quiet:

@ref knowledge/aerospace/learned/weather-satellites.md#what-is-up-there

Note what that table says plainly: the NOAA APT weather satellites are **off air** (decommissioned in
2025), and the remaining 137 MHz imagery is Meteor LRPT, which needs SatDump and a 137 MHz antenna
this build does not have. So weather imaging is theory here; the live target is the ISS packet
digipeater — which itself has run on 145.825 MHz and on 437.825 MHz and been off entirely, so you
verify its current frequency and status first, every time.

Each signal has a recognisable character — APT is ~34 kHz wide FM with a 2400 Hz subcarrier, LRPT is
~120 kHz digital QPSK, and passes last 10–15 minutes with a few kHz of Doppler:

@ref knowledge/aerospace/learned/weather-satellites.md#signal-characteristics

The antenna is the deciding factor, and the reason is polarisation. These satellites transmit
**right-hand circular polarisation** from a moving point in the sky. A linear antenna (an ordinary
whip) into a circular signal loses a fixed ~3 dB you cannot recover — and a *wrong-pattern* antenna
loses far more at the low elevations where a pass starts and ends:

@ref knowledge/aerospace/learned/weather-satellites.md#antenna-is-the-deciding-factor

For the ISS packet pass in this module's lab a whip still works (packets are robust and you only need a
few), but understanding the ~3 dB floor and the low-elevation penalty is what lets you grade a weak or
partial result honestly instead of blaming the hardware.
