---
id: M6
title: ADS-B — the sky overhead
themed_title: Passage 6 · Lookout
discipline: aerospace
station: sdr
prerequisites:
  - {id: M1b, soft: false}
sources:
  - knowledge/aerospace/learned/adsb-basics.md
  - knowledge/aerospace/runbooks/adsb-receive-tar1090.md
  - software/adsb-tar1090.md
  - webdash/app/collectors/adsb.py
objectives:
  - "**Explain** why an aircraft can appear in the table before it appears on the map (CPR even/odd)."
  - "**Estimate** the radio horizon for a receiver and aircraft height."
  - "**Calculate** a quarter-wave antenna length for an ADS-B frequency."
  - "**Operate** readsb and tar1090 from the SDR rail, and **restore** the rail afterwards."
est_minutes: 100
today:
  state: ready
  reason: "Verified 2026-09-24: with the SDR rail on, `readsb` decoded about 9 messages/s on the telescopic whip indoors — the live message rate it reports, also shown in tar1090; re-read it there rather than treating 9/s as fixed."
---

Airliners broadcast their identity, position and altitude on 1090 MHz several times a second.
Fancy's SDR can decode them with nothing more than the whip. This module is also the first time
you switch a rail on, watch a service come up, and put the device back the way you found it.
