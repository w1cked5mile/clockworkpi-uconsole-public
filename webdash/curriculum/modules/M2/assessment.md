---
id: M2.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: fspl-calc
    concept_tags: [C13]
    type: numeric
    prompt: "Free-space path loss for a 5 km link at 915 MHz, using FSPL = 20 log10(d_km) + 20 log10(f_MHz) + 32.45. Answer in dB."
    answer: 105.7
    tolerance: 1.0
    explanation: "20*log10(5)=14.0, 20*log10(915)=59.2, +32.45 gives 105.7 dB."
  - id: quarter-wave
    concept_tags: [C15]
    type: numeric
    prompt: "Quarter-wave whip length for LoRa at 915 MHz, lambda/4 = 75000 / f_MHz. Answer in mm."
    answer: 82
    tolerance: 3
    explanation: "75000 / 915 = 82 mm (trim ~5% for end effect on a real whip)."
  - id: margin
    concept_tags: [C13]
    type: numeric
    prompt: "Received power on the 5 km LoRa link is about -80.7 dBm and LongFast sensitivity is about -131.5 dBm. What is the link margin, in dB?"
    answer: 51
    tolerance: 1.5
    explanation: "-80.7 - (-131.5) = 50.8, about 51 dB of margin."
  - id: db-ratio
    concept_tags: [C13]
    type: single
    prompt: "+10 dB corresponds to what change in power?"
    choices: ["2x", "10x", "100x", "1000x"]
    answer: 1
    explanation: "dB is logarithmic: +10 dB = 10x power, +20 dB = 100x, +3 dB is about 2x."
  - id: gains-add
    concept_tags: [C13]
    type: single
    prompt: "In a link budget, an antenna gain and a path loss combine by..."
    choices: ["multiplying the ratios", "adding and subtracting in dB", "taking the larger of the two"]
    answer: 1
    explanation: "Because dB are logarithms, gains add and losses subtract - the budget is one long sum."
  - id: noise-floor
    concept_tags: [C14]
    type: single
    prompt: "The thermal noise floor is -174 dBm/Hz. Widening the receiver bandwidth..."
    choices:
      - "lowers the noise floor (less noise)"
      - "raises the noise floor by 10 log10(BW) (more total noise)"
      - "has no effect on the noise floor"
    answer: 1
    explanation: "noise floor dBm = -174 + 10 log10(BW_Hz) + noise figure; more bandwidth admits more total noise, so the floor rises."
  - id: height-beats-gain
    concept_tags: [C15]
    type: single
    prompt: "Why do height and a clear view usually beat higher antenna gain on a handheld like Fancy?"
    choices:
      - "Higher gain amplifies the signal, which overloads the receiver"
      - "Gain is redirection, not amplification; a flattened high-gain pattern pushes overhead signals into the null"
      - "Taller antennas always have more gain"
    answer: 1
    explanation: "Gain concentrates energy in some directions by stealing it from others; on a portable that flattened pattern nulls out aircraft overhead and satellites near the zenith."
  - id: polarization
    concept_tags: [C15]
    type: single
    prompt: "A linear antenna receiving a circularly polarized GPS or weather-satellite signal loses about..."
    choices: ["0 dB", "3 dB (unavoidable)", "20+ dB"]
    answer: 1
    explanation: "Linear-to-circular costs about 3 dB and is unavoidable; a full polarization mismatch (e.g. vertical vs horizontal) is the 20+ dB case."
  - id: port-safety
    concept_tags: [C16]
    type: single
    required: true
    prompt: "On the AIO V2, which is true about transmitting?"
    choices:
      - "Any SMA port can transmit if an antenna is fitted"
      - "ANT1 (LoRa) is the port you key up for RF work, and you must never key it into an empty or badly matched port"
      - "The SDR bulkhead is the transmit port"
    answer: 1
    explanation: "ANT1 is the SX1262's port; reflected power from an empty or mismatched port goes back into the power amplifier and can destroy it. The SDR bulkhead is receive-only (the onboard Wi-Fi/BT radios transmit under their own stacks, not a port you hand-key)."
  - id: bias-tee
    concept_tags: [C16]
    type: single
    prompt: "The AIO V2's SDR bulkhead SMA carries a 5 V bias tee. What must you avoid on that port?"
    choices:
      - "A DC-shorted antenna, which shorts the 5 V supply"
      - "Any antenna longer than 82 mm"
      - "Nothing - the bias tee is harmless"
    answer: 0
    explanation: "A DC path to ground on the bias-tee port shorts the 5 V supply; the SDR bulkhead is deliberately off the antenna strip so it can't be confused by feel."
---

Eight of ten to pass, and the port-safety item must be right — it is the one that protects the
hardware. The three calculations (FSPL, quarter-wave, margin) accept the ballpark within tolerance
(about a decibel, or ~5% on the whip length).
