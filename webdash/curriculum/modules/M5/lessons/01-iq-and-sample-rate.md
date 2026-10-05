---
id: M5.iq
title: IQ samples and the sample rate
est_minutes: 20
---

An SDR does not hand you a signal — it hands you *samples*: pairs of numbers, taken millions of times
a second, that describe the radio waveform. Each pair is one **IQ sample** (in-phase and quadrature),
and capturing both halves is what lets an SDR represent frequencies above *and* below the tuned
centre at once.

@ref knowledge/rf-fundamentals/learned/sampling-and-bandwidth.md#why-iq

The rule of thumb that shapes every capture: your usable bandwidth is roughly the **sample rate**, and
the sample rate sets the **data rate** you have to store and move. That is a real constraint on the
CM4's shared USB bus:

@ref knowledge/rf-fundamentals/learned/sampling-and-bandwidth.md#what-this-build-can-sustain

So "2.048 MS/s" (megasamples per second) is about 4 MB/s of raw IQ and about 2 MHz of usable window —
numbers you will predict in the assessment and hit for real in LAB-11.
