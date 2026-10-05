---
id: M3.dop
title: Geometry — DOP
est_minutes: 15
glossary: [hdop]
---

@ref knowledge/rf-fundamentals/learned/gnss-basics.md#dop-geometry-not-signal-strength

Right now HDOP is **{live:gps.hdop}**, PDOP {live:gps.pdop}, and gpsd estimates the horizontal
error at {live:gps.eph_m} m.

These are live, not fixed: the DOP figures come from gpsd's `SKY` report and `eph_m` from its
`TPV` report — both printed by `gpspipe -w`. They tighten as more satellites come into view, so
re-read them rather than trusting one snapshot.

@ref knowledge/rf-fundamentals/learned/gnss-basics.md#signal-strength-cn0
