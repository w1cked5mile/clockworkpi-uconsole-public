---
id: M10
title: Ham bands, APRS and licensing
themed_title: Passage 10 · The amateur bands
discipline: ham-radio
station: sdr
prerequisites:
  - {id: M2, soft: false}
  - {id: M5, soft: false}
  - {id: M3, soft: true}
sources:
  - knowledge/ham-radio/learned/band-plans-and-privileges.md
  - knowledge/ham-radio/learned/digital-modes-and-aprs.md
  - knowledge/ham-radio/learned/licensing-path-us.md
  - knowledge/ham-radio/runbooks/vhf-uhf-monitoring-and-satellite-pass.md
objectives:
  - "**Locate** the 2 m and 70 cm band segments and repeater offsets, and **state** why a repeater's input CTCSS tone does not matter when you are only listening to its output."
  - "**Explain** the APRS decode chain (FM → AFSK1200 → AX.25) and why FT8 needs the system clock within about a second."
  - "**Decode** live APRS packets receive-only with `multimon-ng`, and read position and path from them."
  - "**Describe** the US licence path (Technician / General / Extra via a VEC exam) and state precisely what a licence does and does not change for Fancy."
est_minutes: 120
today:
  state: ready
  reason: "Receive-only throughout: the SDR is receive-only and the only transmitter on this build (the SX1262) is a Part 15 ISM device, not an amateur one, so nothing here transmits on amateur spectrum. Needs the SDR rail and readsb stopped; multimon-ng is installed (2026-09-24). HF is theory only (the R860 tuner starts ~24 MHz). FT8 is covered as theory - it needs WSJT-X and an audio loopback, which are not installed. Prerequisites: M2, M5; M3 recommended for the GNSS/timing grounding."
---

This module is the ham-radio counterpart to M12's land-mobile survey: the same receive-and-classify
discipline, aimed at the amateur VHF/UHF bands. You learn where things live on 2 m and 70 cm —
repeaters and their offsets, the SSB and satellite segments, the APRS channel — then decode APRS for
real, and finish with the licence path and an honest account of what a licence would and would not
give this build.

The thread that runs through it, and the one Track C's page states plainly, is that **finishing this
module is not a licence, and a licence does not give Fancy a transmitter.** Receiving anywhere on
these bands is fine and needs nothing; transmitting needs a licence *and* a radio this build does not
have. The SDR is receive-only, and the SX1262 only ever transmits in the 902–928 MHz ISM band under
Part 15. So everything here is a receive-only workflow — a genuine way to learn the bands before
sitting the exam, not a substitute for it.

It draws on `band-plans-and-privileges.md`, `digital-modes-and-aprs.md` and `licensing-path-us.md`,
with the monitoring runbook behind the lab, and ends (LAB-13) with a live APRS decode on 144.390 MHz
— receive only, waiting on a digipeater or iGate being in range.
