---
id: M2.antennas
title: Antennas, and why height beats gain
est_minutes: 25
---

The antenna decides what Fancy can hear before any software runs. Two ideas carry most of the weight.
First, an antenna is *resonant* at a length tied to the wavelength — the quarter-wave formula you will
use in the lab:

@ref knowledge/rf-fundamentals/learned/antenna-basics.md#resonance-and-length

Second, antenna "gain" — measured in **dBi**, decibels relative to an isotropic (point-source)
radiator — is not amplification but redirection: a high-gain antenna concentrates energy in some
directions by stealing it from others:

@ref knowledge/rf-fundamentals/learned/antenna-basics.md#gain-and-pattern

On a handheld that flattened pattern is usually the wrong trade: it pushes aircraft overhead and
satellites near the zenith into the null. So **height and a clear view beat gain** for most of Fancy's
links. The build's practical rules:

@ref knowledge/rf-fundamentals/learned/antenna-basics.md#practical-rules-for-this-build

One more antenna property decides what Fancy hears: **polarization**, the orientation of the wave. An
antenna aligned to the wrong orientation throws signal away — and for the circularly polarized
sources (GPS, weather satellites) a plain linear whip pays an unavoidable price:

@ref knowledge/rf-fundamentals/learned/antenna-basics.md#polarization

You will use the quarter-wave formula (λ/4 ≈ 75000 / f_MHz, then trim ~5% for a real whip) on three
bands in LAB-16.
