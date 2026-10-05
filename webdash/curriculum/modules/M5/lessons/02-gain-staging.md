---
id: M5.gain
title: Gain staging and the 8-bit ceiling
est_minutes: 20
---

The RTL-SDR digitises with only 8 bits (in its ADC, the analog-to-digital converter), so it can span about 48 dB between the noise floor and
clipping — a narrow window. Too little gain buries weak signals in quantisation noise; too much
gain overloads the front end and manufactures false signals. The skill is finding the **knee**:
enough gain to lift the signal off the floor, not so much that the receiver folds.

@ref knowledge/rf-fundamentals/learned/receiver-performance.md#gain-staging

Overload does not look like "loud" — it looks like spurs, images and a noise floor that rises
everywhere at once. Learn the symptoms so you back the gain off instead of chasing them:

@ref knowledge/rf-fundamentals/learned/receiver-performance.md#overload-symptoms

Use **manual** gain, not AGC (automatic gain control), and set it to the knee for the band you are on. You will do exactly
this when you pick the gain for the noise-floor sweep (LAB-10) and the IQ capture (LAB-11).
