---
id: M6.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: cpr
    concept_tags: [C29]
    type: single
    prompt: An aircraft appears in the table but not yet on the map. The most likely reason is…
    choices:
      - "Its transponder is faulty"
      - "readsb has not yet received both an even and an odd position message (CPR)"
      - "The map only updates once a minute"
    answer: 1
    explanation: A globally unambiguous position needs one even and one odd CPR frame, received close together.
  - id: horizon
    concept_tags: [C13, C29]
    type: numeric
    prompt: "Radio horizon in km for a receiver at 4 m and an aircraft at 6,000 m, using d ≈ 4.12 × (√h1 + √h2)?"
    answer: 327
    tolerance: 16
    unit: km
    explanation: 4.12 × (2.00 + 77.46) ≈ 327 km.
  - id: limit
    concept_tags: [C15, C29]
    type: single
    prompt: What limits Fancy's ADS-B range most?
    choices:
      - "The antenna and where it is"
      - "Holding Fancy at 1.5 m instead of 10 m"
      - "The ADC's bit depth"
    answer: 0
    explanation: Height barely changes the horizon here; the whip and its placement matter far more.
  - id: quarter-wave
    concept_tags: [C15]
    type: numeric
    prompt: A quarter wavelength at 978 MHz (UAT), in millimetres?
    answer: 76.7
    tolerance: 3.8
    unit: mm
    explanation: λ = 300 / 978 m ≈ 0.307 m; a quarter is about 76.7 mm.
  - id: restore
    concept_tags: [C29, C05]
    type: single
    prompt: You finish an ADS-B session. What should you do with the SDR rail?
    choices:
      - "Leave it on so readsb keeps running"
      - "Switch it off — it costs power, and readsb crash-looping is normal"
    answer: 1
    explanation: The rail costs about 0.64 W; readsb's crash loop with the rail off is the normal resting state.
---

Four of five to pass.
