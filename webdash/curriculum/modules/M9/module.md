---
id: M9
title: Satellite passes
themed_title: Passage 9 · The sky overhead
discipline: aerospace
station: sdr
prerequisites:
  - {id: M5, soft: false}
  - {id: M8, soft: false}
sources:
  - knowledge/aerospace/learned/weather-satellites.md
  - knowledge/ham-radio/runbooks/vhf-uhf-monitoring-and-satellite-pass.md
objectives:
  - "**Plan** a pass: find AOS/LOS, maximum elevation (≥ 30° for a first attempt) and direction from a predictor, after checking the target's current frequency and status."
  - "**Explain** Doppler shift on a pass (about ±3.4 kHz at 145.8 MHz, ±10 kHz at 436 MHz) and polarisation mismatch (a fixed ~3 dB loss from linear into a circular signal, worse at low elevation, plus Faraday fading at VHF)."
  - "**Record** a full pass from before AOS through LOS, gain fixed, to decode afterwards rather than live."
  - "**Grade** a result honestly against the pass geometry — partial or noisy is the normal first outcome, and the usual causes are known."
est_minutes: 180
today:
  state: ready
  reason: "Receive-only. Needs the SDR rail and readsb stopped. The planning half (objectives, geometry, Doppler) always works; the live capture WAITS ON THE WORLD - it needs the ISS packet digipeater to be on (it has run on 145.825 and 437.825 MHz and been off entirely - check status first) and a predicted pass above ~30°. Imaging (NOAA APT) is theory only: NOAA APT was decommissioned in 2025 and Meteor LRPT needs SatDump and a 137 MHz circular/V-dipole antenna, neither on hand. gpredict is not installed; use n2yo.com for prediction. Prerequisites: M5, M8."
---

Everything so far has listened to signals that stay put. A satellite pass is different: the source is
moving fast across the sky for ten or fifteen minutes, so its frequency shifts as it goes (Doppler),
its signal is circularly polarised, and the whole session has to be *planned* around a predicted pass
rather than tuned at will. This module teaches that planning discipline and ends with a real capture —
the ISS packet digipeater, recorded from before it rises until it sets, and decoded afterwards.

Two numbers frame the physics. **Doppler**: a pass shifts the frequency by roughly ±3.4 kHz at
145.8 MHz and ±10 kHz at 436 MHz, high as the bird approaches and low as it recedes — small enough to
ignore on 2 m FM, big enough on 70 cm to need a wider capture or retuning. **Polarisation**: these are
circularly polarised downlinks, so a linear whip loses a fixed ~3 dB no matter what, and far more at
the low elevations where a pass begins and ends; VHF adds Faraday rotation fading on top. That is why a
pass above ~30° is worth recording and one below ~20° is mostly noise.

The honest framing, the same one the sources carry: NOAA APT weather imagery is **off air** (NOAA
decommissioned it in 2025), and the remaining 137 MHz imagery (Meteor LRPT) needs SatDump and a
137 MHz antenna this build does not have — so imaging is theory here. What *is* live is the ISS packet
pass, when the station is active. It draws on `weather-satellites.md` and the ham monitoring runbook's
satellite session, and ends (LAB-19) with a recorded ISS pass — a planning exercise you can always do,
and a capture that waits on a good pass and an active station.
