---
id: M9.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: aos-los
    concept_tags: [C30]
    type: single
    prompt: "In pass planning, what do AOS and LOS mean?"
    choices:
      - "acquisition of signal (the satellite rises above the horizon) and loss of signal (it sets)"
      - "automatic orbit sync and lock-onstop"
      - "antenna orientation setting and line-of-sight"
    answer: 0
    explanation: "AOS is when the bird rises into view and LOS when it sets; you record from about a minute before AOS through LOS."
  - id: elevation
    concept_tags: [C30]
    type: single
    prompt: "What maximum elevation makes a pass worth recording for a first attempt?"
    choices:
      - "above ~30 degrees; below ~20 degrees expect mostly noise"
      - "any elevation works equally well"
      - "below 10 degrees is best, to catch it on the horizon"
    answer: 0
    explanation: "A pass above ~30 deg is worth recording; low-elevation passes suffer most from polarisation and path loss, so below ~20 deg is mostly noise."
  - id: doppler-band
    concept_tags: [C30]
    type: single
    prompt: "Roughly how large is the Doppler shift across a pass, and where is it worse?"
    choices:
      - "about ±3.4 kHz at 145.8 MHz and ±10 kHz at 436 MHz - worse on 70 cm"
      - "the same on every band, about ±1 kHz"
      - "about ±10 kHz on 2 m and ±3 kHz on 70 cm - worse on 2 m"
    answer: 0
    explanation: "Doppler scales with frequency: ~±3.4 kHz at 145.8 MHz (tolerable on FM) and ~±10 kHz at 436 MHz, which needs a wider capture or retuning."
  - id: doppler-70cm
    concept_tags: [C30]
    type: single
    prompt: "Capturing the ISS packet digipeater at 437.825 MHz, what do you do about Doppler?"
    choices:
      - "widen the capture (e.g. rtl_fm -s 48k) or retune during the pass"
      - "nothing - Doppler is negligible at 70 cm"
      - "change gain continuously to follow it"
    answer: 0
    explanation: "At 70 cm the ~±10 kHz shift is large, so widen the sample rate (-s 48k) or retune. At 145.825 MHz the shift is small enough to ignore on FM."
  - id: polarization
    concept_tags: [C30]
    type: single
    prompt: "These satellites transmit circular polarisation. What does a linear whip cost you?"
    choices:
      - "a fixed ~3 dB loss you cannot recover, and more at low elevation"
      - "nothing - polarisation does not affect reception"
      - "it gains ~3 dB over a circular antenna"
    answer: 0
    explanation: "A linear antenna into a circular signal loses ~3 dB unavoidably; a wrong-pattern antenna loses far more at the low elevations where passes begin and end."
  - id: tle-fresh
    concept_tags: [C30]
    type: single
    prompt: "You hear nothing at the predicted time. What is the most common cause?"
    choices:
      - "a stale TLE - refresh the orbital elements and re-predict before suspecting hardware"
      - "the dongle is broken"
      - "the satellite has been destroyed"
    answer: 0
    explanation: "Predictions come from TLEs that go stale within days; 'nothing at the predicted time' is usually a stale TLE, not dead hardware or a dead satellite."
  - id: record-then-decode
    concept_tags: [C30]
    type: single
    prompt: "What is the capture discipline for a pass?"
    choices:
      - "record the whole pass first, then decode afterwards; a pass cannot be re-run"
      - "decode live and discard the recording"
      - "record only the peak-elevation minute"
    answer: 0
    explanation: "You record from before AOS through LOS and decode from the recording afterwards, because the pass is over in minutes and cannot be repeated."
  - id: fixed-gain
    concept_tags: [C30]
    type: single
    prompt: "During the pass, your gain should be..."
    choices:
      - "fixed for the whole pass - changing it mid-pass ruins the recording"
      - "raised steadily as the satellite climbs"
      - "set to maximum at AOS and dropped at LOS"
    answer: 0
    explanation: "Keep gain fixed through the pass; adjusting it mid-pass corrupts the recording you will decode later."
  - id: check-status
    concept_tags: [C30]
    type: single
    prompt: "Before planning an ISS packet pass, what must you check?"
    choices:
      - "its current frequency and status - it has run on 145.825 and 437.825 MHz and been off entirely"
      - "nothing - it is always on 145.825 MHz"
      - "the weather forecast only"
    answer: 0
    explanation: "The ISS packet digipeater's frequency and on/off status change; verify it is active and on which frequency before building the plan around it."
  - id: apt-off
    concept_tags: [C30]
    type: single
    prompt: "What is the status of NOAA APT weather-image reception on this build?"
    choices:
      - "theory only - NOAA APT was decommissioned in 2025, and Meteor LRPT needs SatDump and a 137 MHz antenna not on hand"
      - "the primary live target of this module"
      - "available on the standard whip with no extra software"
    answer: 0
    explanation: "NOAA APT went off air in 2025; the remaining 137 MHz imagery (Meteor LRPT) needs SatDump and a 137 MHz circular/V-dipole antenna, so imaging is kept as theory and the live target is the ISS packet pass."
---

Eight of ten to pass - this is the planning exercise the module is graded on. The items cover pass
geometry (C30: AOS/LOS, the ≥30° elevation rule), the physics you plan around (Doppler sizes and the
70 cm widening, the ~3 dB circular-polarisation loss), the disciplines that decide success (TLE
freshness, record-then-decode, fixed gain), and the honest status of the targets (check the ISS station
first; NOAA APT imaging is theory here). Planning is the skill; the capture waits on a good pass.
