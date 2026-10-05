---
id: M12.classify
title: Analog, digital, trunking — and the survey method
est_minutes: 40
---

The core skill of this module is telling analog from digital on a narrowband channel, and naming the
*probable* digital mode without a decoder. Analog NFM voice has sloped skirts and a continuous shape
while someone talks; digital modes have sharp edges and a repeating burst structure. Width and
pattern together point at a probable mode — DMR's two-slot TDMA alternation, P25 Phase 1's 12.5 kHz
C4FM, NXDN's 6.25 kHz narrow:

@ref knowledge/communications/learned/digital-voice-and-trunking.md#digital-voice-modes

Note the word **probable**. On this build there is no P25/DMR metadata decoder installed (op25,
sdrtrunk and DSD are all absent — a deliberate choice), so you classify from width and burst pattern
and stop at "digital, probably DMR". That is the honest endpoint, and it maps to the M8 worksheet's
*candidate* grade.

Some systems are **trunked**: instead of one frequency per channel, they pool frequencies and assign
them per call from a control channel — a continuous data stream that stands out on a waterfall. You
can recognise a trunked system from that control channel even when you cannot follow the voice:

@ref knowledge/communications/learned/digital-voice-and-trunking.md#trunking

The survey method itself is a sweep-then-classify loop. `rtl_power` sweeps a band over time and writes
power-versus-frequency rows to a CSV; occupied channels stand out as peaks above the floor. Longer
integration catches intermittent users a quick sweep misses:

@ref knowledge/communications/runbooks/scanner-monitoring-session.md#2-sweep-the-band-for-activity

Then, for each hit, you record a fixed set of observables — frequency, bandwidth, mode, pattern,
strength — exactly as the runbook lays out. This is the M8 workflow applied per channel:

@ref knowledge/communications/runbooks/scanner-monitoring-session.md#3-classify-each-active-channel

One thing the waterfall will never show you is whether a digital channel is encrypted. Encrypted and
plain digital traffic look identical; "encrypted" is something you infer from context (a public-safety
talkgroup that no open decoder locks) and then stop at. It is an observation to log, never a target.
