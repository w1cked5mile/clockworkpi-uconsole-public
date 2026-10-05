---
id: M8
title: Identifying signals
themed_title: Passage 8 · Naming the lights
discipline: rf-fundamentals
station: sdr
prerequisites:
  - {id: M5, soft: false}
sources:
  - knowledge/rf-fundamentals/learned/modulation-basics.md
  - knowledge/rf-fundamentals/learned/signal-identification-workflow.md
objectives:
  - "**Classify** common modes (AM / FM / SSB, and digital versus analog) from a waterfall's shape and behaviour."
  - "**Apply** the five-step signal-identification workflow end to end on a live signal."
  - "**Grade** your confidence in an identification, and say what would raise it."
  - "**Reject** false positives - name why a feature is noise, an image or an artefact rather than a real signal."
est_minutes: 120
today:
  state: ready
  reason: "Needs the SDR rail (aiov2_ctl SDR on) and readsb stopped so the dongle is free; uses NOAA Weather Radio (162.475 MHz, heard 2026-09-24) as the trusted reference signal. Prerequisite: M5."
---

Once you can capture cleanly, the next skill is telling what you are looking at. A waterfall is full
of shapes - carriers, bursts, hops, images - and this module teaches you to name them: a repeatable
five-step workflow that moves from "what are its dimensions" (frequency, bandwidth, timing) to a
graded identification, with false positives (images, artefacts, noise) rejected along the way. Like
naming the lights on the water at night, the goal is a confident call from a known signature - and an
honest confidence grade when the call is not certain.

It draws on `modulation-basics.md` and `signal-identification-workflow.md`, and ends (LAB-17) with a
live identification: the NOAA Weather Radio voice on 162.475 MHz (narrowband FM), the build's
known-good reference transmitter.
