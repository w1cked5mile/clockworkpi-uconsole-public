---
id: LAB-04
title: From NMEA to a 3D fix
themed_title: Sea trial · Take a fix
mode: guided
est_minutes: 25
requires: {rails: [GPS], services: [gpsd]}
transmits: false
world: "A view of the sky. Indoors away from windows the receiver may never fix; that's normal."
steps:
  - id: rail
    text: "The GPS rail is on (it boots on; switch it on here if not)."
    check: {type: status, path: aiov2.rails.GPS.on, op: eq, value: true}
  - id: gpsd
    text: "gpsd is running and reporting — not just accepting connections."
    check: {type: status, path: gps.fix, op: ne, value: unknown}
  - id: nmea
    text: "Run gpspipe -r -n 20 and paste the output. Only the sentence types are checked; nothing you paste is stored."
    check: {type: paste, parser: regex, pattern: '^\$G(N|P|L|B)(RMC|GGA),', min_matches: 1}
  - id: visible
    text: "At least one satellite is visible."
    check: {type: status, path: gps.satellites_visible, op: gte, value: 1}
    world_wait: true
  - id: rail-off
    text: "Now time a first fix. Switch the GPS rail off (on this page) and leave it off: this step passes after about 30 s. Wait for it before switching back on."
    check: {type: status, path: aiov2.rails.GPS.on, op: eq, value: false}
    hold_ticks: 8
  - id: rail-on
    text: "Switch it back on. The clock starts now."
    check: {type: status, path: aiov2.rails.GPS.on, op: eq, value: true}
    hold_ticks: 1
  - id: fix3d
    text: "A 3D fix."
    check: {type: status, path: gps.fix, op: eq, value: 3D}
    world_wait: true
  - id: ttff
    text: "Time to first fix, from switching the rail on to the first 3D reading."
    check: {type: computed, fn: first_true_elapsed, step: fix3d, from_step: rail-on, save_as: ttff_s}
  - id: used
    text: "At least four satellites used — enough to solve position and the clock."
    check: {type: status, path: gps.satellites_used, op: gte, value: 4}
    world_wait: true
  - id: finding
    text: "File a finding: on this page save a note with what you saw, use Copy as finding, and save it in the repo on Fancy as knowledge/rf-fundamentals/findings/<date>-first-fix.md (date as YYYY-MM-DD, UTC). Record satellites used, HDOP and the time to first fix. Grid square only, never coordinates."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/rf-fundamentals/findings/*.md", pattern: '^# Finding:', min: 1, fresh: true}
restore:
  - {type: status, path: aiov2.rails.GPS.on, op: eq, value: true}
evidence: [gps.satellites_used, gps.satellites_visible, gps.hdop, gps.grid]
---

Evidence records the grid square, never coordinates, and the time to first fix (`ttff_s`).
Whether that counts as a warm or a cold start is *unverified*: the rail cut removes power, but
whether the GP-02 keeps its stored orbits on a backup supply isn't known. Measured to within
about 5 s (one dashboard reading at each end). Six or more satellites used is a strong fix; four is enough
to pass.
