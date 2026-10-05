---
id: M9.planning
title: Planning a pass — AOS, LOS, elevation and Doppler
est_minutes: 35
---

Unlike every signal so far, a pass cannot be tuned at will — it has to be planned. A predictor gives
you the three things a session needs: **AOS** (acquisition of signal, when the bird rises above the
horizon), **LOS** (loss of signal, when it sets), the **maximum elevation** it reaches, and the
direction it travels. The rule of thumb: a pass above ~30° is worth recording; below ~20°, expect
noise, because the low-elevation geometry is where the polarisation and path losses bite hardest:

@ref knowledge/aerospace/learned/weather-satellites.md#pass-prediction

gpredict is not installed on this build, so use n2yo.com (or a phone app) for prediction. One
discipline point that catches everyone: **TLE freshness.** Predictions are computed from orbital
elements (TLEs) that go stale within days. "Nothing at the predicted time" is, more often than not, a
stale TLE rather than a dead satellite or broken hardware — refresh the elements and re-predict before
suspecting anything else. (That is the runbook's "stale TLE" troubleshooting row, and it is the single
most common first-pass mistake.)

The other number you plan around is **Doppler**. Because the satellite is moving toward you then away,
its received frequency is shifted high on approach and low on departure. The size scales with
frequency:

- **2 m (145.8 MHz):** about ±3.4 kHz across the pass — small enough that FM reception tolerates it
  without retuning.
- **70 cm (436 MHz):** about ±10 kHz — large enough that you either widen the capture (`rtl_fm -s 48k`)
  or retune during the pass. This is why the ISS packet frequency matters: at 437.825 MHz you must plan
  for the wider Doppler; at 145.825 MHz you largely do not.

Plan the capture to start about a minute *before* AOS and run through LOS, with gain fixed for the whole
pass — you decode afterwards, not live, so the job during the pass is simply to record cleanly.
