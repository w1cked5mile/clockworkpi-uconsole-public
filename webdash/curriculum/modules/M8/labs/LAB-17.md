---
id: LAB-17
title: Three signal IDs
themed_title: Sea trial · Name three lights
mode: guided
est_minutes: 50
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Receive only, in a waterfall app (gqrx or SDR++). You classify three real signals - NOAA Weather Radio (a known reference), broadcast FM, and one 902-928 MHz ISM burst from ANOTHER source. The ISM burst depends on an external emitter turning up, so it may take patience or a second session. Never key Fancy's own LoRa node: it transmits, and being right next to the SDR it would overload the front end anyway."
steps:
  - id: sdr-on
    text: "Switch the SDR rail on (on this page, or aiov2_ctl SDR on)."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to take the dongle (it starts when the SDR rail comes on). If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: stop-readsb
    text: "Now free the dongle from readsb: sudo systemctl stop readsb"
    check: {type: status, path: services.readsb.active, op: ne, value: active}
  - id: id-noaa
    text: "Open a waterfall app (gqrx or SDR++; see software/sdr-stack.md) and tune NOAA Weather Radio (162.475 MHz here). Record its observables and classify it: a steady, continuous carrier about 12.5-16 kHz wide with a centre carrier - narrowband FM voice. This is your trusted reference. Attest you observed and classified it."
    check: {type: attest, prompt: "I observed NOAA WX at 162.475 MHz and classified it as narrowband FM voice by its width and continuous shape."}
  - id: id-fm
    text: "Tune broadcast FM (88-108 MHz) and pick a strong station. Classify it: very wide (about 150-200 kHz), continuous, no single centre carrier - wideband FM. Note how its width alone separates it from the NOAA NFM signal."
    check: {type: attest, prompt: "I observed a broadcast FM station and classified it as wideband FM, distinguishing it from NFM by its ~150-200 kHz width."}
  - id: id-ism
    text: "Look for a burst in the 902-928 MHz ISM band from ANOTHER device - a mesh neighbour's Heltec, an ISM meter, a doorbell. The receiver only shows ~2 MHz at once, so tune your window to a likely spot (a neighbour's Meshtastic US915 channel) or first sweep 902-928 with rtl_power to find activity, then tune there. Classify what you see: a LoRa CSS chirp sweeping diagonally, or a brief FSK (frequency-shift keying) / OOK (on-off keying) packet. DO NOT key Fancy's own LoRa node. Attest you observed and classified a burst from a source that is not Fancy."
    check: {type: attest, prompt: "I observed a 902-928 MHz burst from a source other than Fancy and classified it (LoRa chirp or FSK/OOK), without keying Fancy's own node."}
  - id: log
    text: "Log all three using the signal-ID worksheet (knowledge/_templates/signal-id.md): for each, the centre frequency, bandwidth, modulation guess, waterfall description, allocation, reference/decoder, a confidence grade AND what would raise that grade. Save all three worksheets in a SINGLE file in the repo, knowledge/rf-fundamentals/findings/<date>-signal-ids.md (date YYYY-MM-DD, UTC) - separate files per signal will not pass; the check needs three Center-frequency lines in one file. Do not log any artefact (image, DC spike, harmonic) as one of the three."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/rf-fundamentals/findings/*-signal-ids.md", pattern: '(?i)cent(?:er|re) frequency', min: 3, fresh: true}
  - id: restart-readsb
    text: "Give the dongle back: sudo systemctl start readsb"
    check: {type: status, path: services.readsb.active, op: eq, value: active}
  - id: sdr-off
    text: "Switch the SDR rail off."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
restore:
  - {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - {type: status, path: services.readsb.active, op: ne, value: inactive}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: []
---

Three signals, three honest classifications, three logged worksheets. The check counts three
"center frequency" fields in your findings; the grading that matters - correct modulation, correct
confidence, no artefact mistaken for a signal - is yours to hold. NOAA WX is the anchor you already
trust from M5; FM shows how width alone separates modes; and the ISM burst is a real-world unknown
you classify from another source, never by transmitting. All receive-only.
