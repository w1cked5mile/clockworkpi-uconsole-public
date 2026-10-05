---
id: M2.linkbudget
title: Path loss and the link margin
est_minutes: 25
glossary: [snr]
---

Radio spreads out as it travels; the further it goes, the weaker it arrives. Free-space path loss
(FSPL) puts a number on that spreading, and it depends only on distance and frequency.

@ref knowledge/rf-fundamentals/learned/db-and-link-budget.md#free-space-path-loss

Assemble the whole budget by adding every gain and subtracting every loss, then compare the result to
the receiver's sensitivity. The difference is your **link margin** — how much signal you have to
spare:

@ref knowledge/rf-fundamentals/learned/db-and-link-budget.md#worked-example-meshtastic-at-5-km

The floor you compare against is not zero — it is thermal noise, and it rises with bandwidth, which
is why a wider receiver is a noisier one. A signal has to clear that floor by its mode's required
signal-to-noise ratio (SNR) to decode:

@ref knowledge/rf-fundamentals/learned/db-and-link-budget.md#noise-floor-and-snr

A positive margin means the link should close in free space; real terrain, walls and foliage eat into
it. In LAB-16 you compute this whole budget yourself for the 5 km LoRa link.
