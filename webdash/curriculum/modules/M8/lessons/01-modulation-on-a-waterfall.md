---
id: M8.modulation
title: What modulation looks like on a waterfall
est_minutes: 25
---

A **waterfall** is the scrolling frequency-versus-time display in a GUI SDR app such as gqrx or SDR++
(see `software/sdr-stack.md`) — where M5 drove the receiver from the command line, this module reads
that picture. A waterfall does not tell you what a signal *is*, but it shows you its shape - and
different modulations have different shapes. Analog modes carry a message by varying a carrier smoothly;
digital modes switch between states, which leaves sharper edges and often a repeating pattern.

@ref knowledge/rf-fundamentals/learned/modulation-basics.md#analog

@ref knowledge/rf-fundamentals/learned/modulation-basics.md#digital

Before you reach for any decoder, five features of the display already eliminate most candidates -
width, timing, shape, symmetry and frequency:

@ref knowledge/rf-fundamentals/learned/modulation-basics.md#what-the-waterfall-tells-you-before-any-decoder

One mode breaks the "fixed carrier" intuition: LoRa is a chirp that sweeps across its bandwidth, so
it looks like a diagonal streak, not a vertical line - worth knowing since it is where Fancy's own
LoRa lives, among the other ISM traffic (telemetry, meters, cordless devices) that shares 902-928 MHz:

@ref knowledge/rf-fundamentals/learned/modulation-basics.md#why-lora-is-different
