---
id: M3
title: GNSS and time
themed_title: Passage 3 · Shoot the sun
discipline: rf-fundamentals
station: gps
prerequisites:
  - {id: M1b, soft: false}
sources:
  - knowledge/rf-fundamentals/learned/gnss-basics.md
  - software/gps.md
  - configs/gpsd/gpsd.default
  - webdash/app/collectors/gps.py
objectives:
  - "**Interpret** fix mode, satellites used versus visible, and HDOP."
  - "**Read** a GGA sentence field by field."
  - "**Explain** why the missing RTC cell matters for time and logins, and what really slows a first fix."
est_minutes: 90
today:
  state: ready
  reason: "3D fix verified 2026-09-23 and 2026-09-24. The fix step needs a view of the sky — a window is usually enough."
---

Where you are and what time it is — the two things every other station leans on.
