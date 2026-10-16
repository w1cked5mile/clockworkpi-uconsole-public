---
id: M3.time
title: Time to first fix, and the RTC backup cell
est_minutes: 15
---

@ref knowledge/rf-fundamentals/learned/gnss-basics.md#time-to-first-fix-ttff

@ref knowledge/rf-fundamentals/learned/gnss-basics.md#gnss-time-the-rtc-and-ntp

The last fix arrived {live:gps.tpv_age_s} s ago by the system clock. If that number is large or
negative while GPS has a fix, the system clock is wrong. Since the RTC cell went in (2026-10-10)
that should be rare. If it does happen after an offline boot, suspect a flat cell first.
