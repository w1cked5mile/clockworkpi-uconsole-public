---
id: M5.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: data-rate
    concept_tags: [C17]
    type: numeric
    prompt: "Raw IQ at 2.048 MS/s in cu8 format (2 bytes per sample). Roughly how many MB/s must you store and move?"
    answer: 4.1
    tolerance: 0.5
    explanation: "2.048 MS/s x 2 bytes = 4.096 MB/s, about 4 MB/s - a real load on the CM4's shared USB bus."
  - id: usable-bw
    concept_tags: [C17]
    type: single
    prompt: "The usable bandwidth of an IQ capture is roughly equal to..."
    choices: ["twice the sample rate", "the sample rate", "half the sample rate", "the tuner's whole range"]
    answer: 1
    explanation: "Complex (IQ) sampling gives usable bandwidth about equal to the sample rate, centred on the tuned frequency - so 2.048 MS/s is about a 2 MHz window."
  - id: gain-knee
    concept_tags: [C18]
    type: single
    prompt: "You keep raising the gain. Past the knee, what happens?"
    choices:
      - "signals just get louder and clearer"
      - "the front end overloads - spurs, images and a floor that rises everywhere at once"
      - "the sample rate drops"
    answer: 1
    explanation: "The 8-bit ADC spans only about 48 dB; too much gain overloads the front end and manufactures false signals rather than revealing real ones."
  - id: overload
    concept_tags: [C18]
    type: single
    prompt: "Which is a symptom of overload rather than a real signal?"
    choices:
      - "evenly spaced spurs and images that move when you change the gain"
      - "a single steady carrier at one frequency"
      - "a weak signal near the noise floor"
    answer: 0
    explanation: "Overload products (spurs, images, a rising floor) shift with gain; back the gain off toward the knee instead of chasing them."
  - id: rtl-cant
    concept_tags: [C21]
    type: multi
    prompt: "Which of these is the RTL-SDR front end UNABLE to do on this build?"
    choices:
      - "transmit"
      - "receive HF below ~24 MHz without extra hardware"
      - "sustain far more than ~2.4 MS/s over the CM4's USB"
      - "receive NOAA Weather Radio at 162 MHz"
    answer: [0, 1, 2]
    explanation: "It is receive-only, tunes ~24 MHz-1.766 GHz, and tops out near 2.4 MS/s (2.048 is the safe ceiling). 162 MHz is well within range."
  - id: ppm-what
    concept_tags: [C22]
    type: single
    prompt: "What does rtl_test -p measure, and what is the value on this build?"
    choices:
      - "sample loss; 0 lost"
      - "the crystal's frequency error in ppm; about +1 ppm here"
      - "the noise floor in dBm; about -100"
    answer: 1
    explanation: "-p measures the reference-crystal offset in parts per million; it settles near +1 ppm here, which is about 1 kHz of tuning error at 1 GHz."
  - id: rtl-test-s
    concept_tags: [C22]
    type: single
    prompt: "rtl_test -s 2048000 is run to check..."
    choices:
      - "that the tuner is an R820T"
      - "that the dongle can sustain that sample rate without dropping samples"
      - "the PPM offset"
    answer: 1
    explanation: "-s streams at the given rate and reports 'samples per million lost'; a few lost is normal on the shared USB bus, a flood means it can't keep up."
  - id: toolchain
    concept_tags: [C23]
    type: single
    prompt: "Which tool archives a RAW IQ file (not demodulated audio, not a power sweep)?"
    choices: ["rtl_fm", "rtl_power", "rtl_sdr", "rtl_test"]
    answer: 2
    explanation: "rtl_sdr writes raw IQ; rtl_fm demodulates to audio, rtl_power sweeps power vs frequency, rtl_test checks the device."
  - id: capture-name
    concept_tags: [C04]
    type: single
    prompt: "A good capture filename carries..."
    choices:
      - "just the date"
      - "its own parameters - UTC time, frequency, sample rate, gain and a label"
      - "the operator's name and location"
    answer: 1
    explanation: "A self-describing name (e.g. 20260924T1830Z_162475k_250k_g30_noaa-wx.cu8) means the file explains itself a month later without a separate note."
  - id: iq-storage
    concept_tags: [C04]
    type: single
    prompt: "Where do raw IQ captures belong?"
    choices:
      - "committed to the repo next to the finding"
      - "in ~/labs, referenced from a finding by sha256, never committed"
      - "uploaded to a public archive"
    answer: 1
    explanation: "Raw IQ is large and is gitignored; the finding pins the exact bytes with a sha256 so the capture is reproducible without storing it in git."
---

Eight of ten to pass. The one calculation (the ~4 MB/s data rate) accepts the ballpark; the rest are
single- or multiple-choice on IQ, gain staging, the RTL-SDR's limits, calibration, the toolchain, and
capture discipline.
