---
id: M5
title: SDR foundations and capture discipline
themed_title: Passage 5 · Keeping the log
discipline: sdr
station: sdr
prerequisites:
  - {id: M1b, soft: false}
  - {id: M2, soft: false}
sources:
  - knowledge/rf-fundamentals/learned/sampling-and-bandwidth.md
  - knowledge/rf-fundamentals/learned/receiver-performance.md
  - knowledge/sdr/runbooks/first-capture-and-calibration.md
  - knowledge/rf-fundamentals/configs/capture-metadata-conventions.md
  - knowledge/sdr/learned/rtl-sdr-limits.md
  - software/sdr-stack.md
objectives:
  - "**Explain** IQ sampling, bandwidth and data rate, and predict a capture's size (e.g. 2.048 MS/s is about 4 MB/s)."
  - "**Execute** `rtl_test`, and read PPM error as a frequency offset (e.g. +1 ppm is about 146 Hz at 146 MHz)."
  - "**Find** the gain knee - the point past which more gain adds noise, not signal."
  - "**Produce** a named, checksummed IQ capture and write a finding, following the capture-metadata convention."
est_minutes: 180
today:
  state: ready
  reason: "Needs the SDR rail (aiov2_ctl SDR on) and readsb stopped so the dongle is free; inspectrum is not installed (not required by these labs). Prerequisites: M1b, M2."
---

The SDR is Fancy's widest window on the spectrum, but a receiver is only as good as the discipline
behind it. This module builds the mental model - IQ samples, sample rate versus bandwidth, and the
data rate that follows - then the habits: run `rtl_test`, find the gain knee, and take a capture that
is named, checksummed and documented so it still means something a week later. *Keeping the log* is
the point: a capture nobody can reproduce is a story, not evidence.

It draws on `sampling-and-bandwidth.md`, `receiver-performance.md`, the capture-metadata convention,
`rtl-sdr-limits.md` and the `first-capture-and-calibration.md` runbook, and ends (LAB-09/10/11) with a
real, checksummed capture and a finding. Worked figures it leans on: 2.048 MS/s is about 4 MB/s of raw
IQ; +1 ppm is about 146 Hz of offset at 146 MHz.
