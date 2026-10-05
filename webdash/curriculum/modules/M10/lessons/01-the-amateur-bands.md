---
id: M10.bands
title: Where things live on 2 m and 70 cm
est_minutes: 30
---

The amateur bands this build receives well are 2 m (144–148 MHz) and 70 cm (420–450 MHz) — the UHF/VHF
range a portable with a modest whip can actually work. Each band is divided into segments by use: CW
and weak-signal SSB at the bottom, the APRS channel, digital and packet, then the FM repeater and
simplex segments and a satellite window. Knowing the segment is the fastest classifier here, exactly
as the allocation was in M8 and M12:

@ref knowledge/ham-radio/learned/band-plans-and-privileges.md#2-m-144148-mhz

@ref knowledge/ham-radio/learned/band-plans-and-privileges.md#70-cm-420450-mhz

A **repeater** listens on one frequency and retransmits on another, separated by a standard offset
(±600 kHz on 2 m, ±5 MHz on 70 cm). The key point for a listener: you tune the **output**. Most
repeaters require a CTCSS/PL tone on their *input* to key them, but that tone gates transmitting, not
receiving — so when you are only listening, the input tone is irrelevant:

@ref knowledge/ham-radio/learned/band-plans-and-privileges.md#repeaters

HF is out of scope on this hardware — the R860 tuner starts around 24 MHz, so 160 m through 12 m are
unreachable without an upconverter, and only 10 m is marginally in range. Treat the HF band plan as
theory for the exam, not something you will hear on Fancy:

@ref knowledge/ham-radio/learned/band-plans-and-privileges.md#hf--out-of-scope-on-this-hardware

The rule of thumb to carry out of this lesson: receiving anywhere is fine; transmitting needs a
licence, the right segment for your class, and a permitted mode — none of which this receive-only
build does.

@ref knowledge/ham-radio/learned/band-plans-and-privileges.md#rule-of-thumb
