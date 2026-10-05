---
id: M3.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: four
    concept_tags: [C24]
    type: single
    prompt: Why does a 3D fix need at least four satellites?
    choices:
      - "One per dimension plus a spare"
      - "Three for position, one to solve the receiver's own clock error"
      - "The standard requires it for redundancy"
    answer: 1
    explanation: The receiver's clock error is the fourth unknown.
  - id: indoors
    concept_tags: [C24]
    type: single
    prompt: Indoors the GPS station shows 5 visible, 0 used. That most likely means…
    choices:
      - "The receiver is broken"
      - "Signals are too weak to lock — normal indoors"
      - "gpsd has crashed"
    answer: 1
    explanation: Visible means detected; used means locked well enough to trust.
  - id: hdop
    concept_tags: [C24]
    type: single
    prompt: HDOP 1.1 with 12 satellites used describes…
    choices:
      - "Good satellite geometry"
      - "Poor geometry"
      - "Signal strength of 1.1 dB"
    answer: 0
    explanation: DOP is geometry, not strength.
  - id: gga-sats
    concept_tags: [C24]
    type: numeric
    prompt: "In $GPGGA,091500,3500.000,N,08100.000,W,1,05,2.4,210.0,M,-32.0,M,,*5C how many satellites are used?"
    answer: 5
    tolerance: 0
    explanation: The field after fix quality (1) is the satellite count, 05. The next field, 2.4, is HDOP.
  - id: gga-quality
    concept_tags: [C24]
    type: single
    prompt: "A GGA sentence has 0 in the fix-quality field. What does that mean?"
    choices:
      - "A perfect fix"
      - "No fix — the position fields can't be trusted"
      - "The receiver is using zero satellites for time only"
    answer: 1
    explanation: Fix quality 0 means no fix.
  - id: rtc
    concept_tags: [C24]
    type: single
    prompt: With no RTC backup cell, what goes wrong after an offline cold boot?
    choices:
      - "Nothing — the RTC keeps time on its own"
      - "The system clock is wrong: TOTP logins fail and timestamps are off"
      - "The GPS can't be used at all"
    answer: 1
    explanation: The RTC needs the cell to keep time without power. A slow first fix is a separate matter — the receiver losing its own stored orbits.
---

Five of six to pass.
