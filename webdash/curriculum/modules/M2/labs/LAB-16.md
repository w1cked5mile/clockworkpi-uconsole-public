---
id: LAB-16
title: Paper link budget
themed_title: Chart work · Dead reckoning
mode: offline
est_minutes: 40
transmits: false
requires: {rails: [], services: []}
world: "No radios needed — this is calculation and board inspection. Keep the M2 formulas to hand: FSPL = 20*log10(d_km) + 20*log10(f_MHz) + 32.45, and lambda/4 (mm) = 75000 / f_MHz."
steps:
  - id: fspl
    text: "Compute free-space path loss for the 5 km LoRa link at 915 MHz: FSPL = 20*log10(5) + 20*log10(915) + 32.45. Paste your answer in dB (it lands near 105-106)."
    check: {type: paste, parser: regex, pattern: '\b10[56]\b', min_matches: 1}
  - id: quarter-wave
    text: "Compute the RAW quarter-wave whip length lambda/4 = 75000 / f_MHz for ADS-B (1090 MHz), LoRa (915 MHz) and NOAA Weather Radio (which sits at 162 MHz). Paste all three in mm (near 68.8, 81.9 and 463.0). This check wants the untrimmed 75000/f figure - the ~5% real-whip trim is informational only."
    check: {type: paste, parser: regex, pattern: '(?s)(?=.*6[89])(?=.*8[12]).*46[0-9]', min_matches: 1}
  - id: received
    text: "Assemble the received power for the 5 km link: +22 dBm (TX) + 2 dBi (TX antenna) - 105.7 dB (FSPL) + 2 dBi (RX antenna) - 1 dB (feedline). Paste the received power in dBm, with its sign (near -80 to -81)."
    check: {type: paste, parser: regex, pattern: '-8[01]', min_matches: 1}
  - id: margin
    text: "The received power from the previous step is about -80.7 dBm, and LongFast (SF11/250 kHz) sensitivity is about -131.5 dBm. Compute the link margin (received minus sensitivity). Paste it in dB (near +50 to +51 - a positive margin means the link closes)."
    check: {type: paste, parser: regex, pattern: '5[01]', reject: '-\s?5[01]', min_matches: 1}
  - id: height-beats-gain
    text: "In one line, state why height and a clear view usually beat higher antenna gain on a handheld like Fancy."
    check: {type: attest, prompt: "I can explain that antenna gain is redirection, not amplification, and a higher-gain flattened pattern pushes overhead signals into the null - so height and a clear view beat gain on a portable."}
  - id: port-safety
    text: "On the AIO V2, ANT1 (LoRa) is the only transmit port and the SDR bulkhead carries a 5 V bias tee. Locate both and confirm the two rules."
    check: {type: attest, prompt: "I can locate ANT1 (the only TX port) and the SDR bias-tee bulkhead, and I will never transmit into an empty or mismatched port, nor put a DC-shorted antenna on the bias-tee port."}
---

This lab needs no radios — it is the paper the rest of the RF work rests on. You run the same numbers
M2 taught: free-space path loss, quarter-wave lengths, a received-power budget, and the margin that
says whether a link closes. The last two steps are the board-side habits — why height beats gain, and
the two antenna-port rules that keep you from damaging the SX1262 or the SDR bias tee.

Keep the formulas to hand: FSPL = 20*log10(d_km) + 20*log10(f_MHz) + 32.45, and lambda/4 (mm) =
75000 / f_MHz (trim ~5% for a real whip). Round to about a decibel or millimetre; the checks accept
the ballpark, not a to-the-digit match.
