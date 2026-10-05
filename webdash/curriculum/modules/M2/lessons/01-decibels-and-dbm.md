---
id: M2.decibels
title: The dB and the dBm
est_minutes: 15
---

Every RF number you will meet — antenna gain, path loss, receiver sensitivity, noise — is quoted in
decibels. The trick that makes it easy: because decibels are logarithms, **gains and losses add**
instead of multiplying. Learn a handful of values and you can do most link math in your head.

@ref knowledge/rf-fundamentals/learned/db-and-link-budget.md#the-two-units-that-matter

Keep the two apart: **dB** is a *ratio* — how much bigger or smaller — while **dBm** is an actual
*power* referenced to 1 mW. "+3 dB" doubles a power; "−100 dBm" names a specific, tiny one. The whole
link budget in the next lesson is just this addition, one term at a time.
