---
id: M12
title: Land-mobile and maritime
themed_title: Passage 12 · Reading the traffic
discipline: communications
station: sdr
prerequisites:
  - {id: M8, soft: false}
sources:
  - knowledge/communications/learned/digital-voice-and-trunking.md
  - knowledge/communications/learned/ais-and-maritime.md
  - knowledge/communications/configs/monitoring-frequency-list.md
  - knowledge/communications/runbooks/scanner-monitoring-session.md
objectives:
  - "**Survey** a VHF/UHF land-mobile band with `rtl_power` and rank its occupied channels against the noise floor."
  - "**Classify** each active channel as analog FM, digital narrowband (probable DMR, P25 Phase 1 or NXDN by width and burst pattern) or unknown, with an honest confidence grade and no message content."
  - "**Explain** why encryption cannot be read off a waterfall — so \"encrypted\" is an observation, never a class to defeat — and why AIS is silent at an inland site."
  - "**Distinguish** what is lawful to log (the technical characterization) from what is not (contents of paging, private voice, or any encrypted traffic) under the ECPA and state public-safety rules."
est_minutes: 150
today:
  state: ready
  reason: "Needs the SDR rail (aiov2_ctl SDR on) and readsb stopped so the dongle is free. Uses NOAA Weather Radio (162.400-162.550 MHz, heard 2026-09-24) as the trusted reference. AIS is run for discipline but silence is expected inland (your location). No decoder for P25/DMR is installed, which is deliberate: classification stops at \"digital, probable type\". Prerequisite: M8."
---

M8 taught you to name a single signal from its shape. This module turns that skill on a whole band at
once: the land-mobile spectrum (VHF/UHF voice and data — public-safety, business, GMRS, paging) and
the maritime bands (marine VHF and AIS). You sweep for activity, rank what is occupied, and classify
each channel as analog, digital-of-a-probable-type, or honestly unknown — the same confidence
discipline as M8, scaled to a survey.

Two lines run through everything here. The first is that **encryption is not a waterfall feature**: a
digital channel looks the same whether its payload is plain or encrypted, so "encrypted" is a thing
you infer and then stop at — never a puzzle to solve. The second is the **legal line**. Receiving is
broad; recording and divulging are narrower, and paging in particular carries personal and medical
data in the clear. The rule is the same as every receive module on Fancy: classify and log the
*technical* characterization, never the content.

It draws on `digital-voice-and-trunking.md`, `ais-and-maritime.md`, the local
`monitoring-frequency-list.md` and the `scanner-monitoring-session.md` runbook, and ends (LAB-18)
with a real band survey: NOAA Weather Radio as the known-good control, at least five channels
classified by width and pattern, and a disciplined `rtl_ais` run that is expected to hear nothing
inland.
