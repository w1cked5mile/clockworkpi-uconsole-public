---
id: M12.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: width-first
    concept_tags: [C34]
    type: single
    prompt: "On a narrowband land-mobile channel, which two observables let you classify it fastest, before any decoder?"
    choices:
      - "the operator's callsign and the time of day"
      - "its width against the 12.5 kHz grid and its burst pattern"
      - "its colour and its signal strength"
    answer: 1
    explanation: "Width (against the 12.5 kHz narrowband grid) plus pattern (continuous analog vs bursty digital) narrows the candidates before you reach for anything else - the M8 workflow, scaled to a survey channel."
  - id: analog-vs-digital
    concept_tags: [C34]
    type: single
    prompt: "A channel shows sharp vertical edges and a repeating burst structure rather than sloped skirts. That points to..."
    choices:
      - "an analog NFM voice channel"
      - "a digital mode"
      - "receiver noise"
    answer: 1
    explanation: "Sharp edges and periodic bursts are digital fingerprints; analog NFM voice has sloped skirts and a continuous shape while someone is keyed."
  - id: dmr-pattern
    concept_tags: [C34]
    type: single
    prompt: "Which waterfall signature suggests DMR specifically?"
    choices:
      - "a 150-200 kHz wide continuous carrier"
      - "a 12.5 kHz channel with a two-slot alternating (TDMA) pattern"
      - "a diagonal chirp sweeping across the band"
    answer: 1
    explanation: "DMR is 12.5 kHz with two TDMA time slots, which shows as a distinctive alternating pattern; the diagonal chirp is LoRa, and the wide continuous carrier is broadcast FM."
  - id: trunking-control
    concept_tags: [C34]
    type: single
    prompt: "What identifies a trunked system on the waterfall even when you cannot follow the voice?"
    choices:
      - "a continuous data stream on the control channel"
      - "the absence of any carrier"
      - "a single fixed analog voice frequency"
    answer: 0
    explanation: "Trunked systems pool frequencies and direct calls from a control channel - a continuous data stream that stands out, distinct from the conventional one-frequency-per-channel layout."
  - id: no-decoder-endpoint
    concept_tags: [C34]
    type: single
    prompt: "This build has no P25/DMR decoder installed. For a narrowband digital channel, what is the honest classification endpoint?"
    choices:
      - "wait until a decoder is installed, then report nothing until then"
      - "'digital, probably DMR (or P25 / NXDN)' graded as a candidate, from width and pattern"
      - "report it as confirmed DMR anyway"
    answer: 1
    explanation: "Without a decoder you classify from width and burst pattern and stop at a graded candidate - 'digital, probably DMR'. Claiming a confirmed decode you did not make is dishonest; refusing to classify at all wastes a valid observation."
  - id: encryption-not-visible
    concept_tags: [C01]
    type: single
    prompt: "Can you tell from the waterfall whether a digital channel's payload is encrypted?"
    choices:
      - "yes - encrypted traffic looks visibly scrambled"
      - "no - encrypted and plain digital traffic look identical, so 'encrypted' is inferred from context and is where you stop"
      - "yes - encrypted channels are always wider"
    answer: 1
    explanation: "Encryption is not a waterfall feature; plain and encrypted digital look the same. You infer 'encrypted' from context (no open decoder locks a protected talkgroup) and stop - it is an observation to log, never a target to defeat."
  - id: paging-privacy
    concept_tags: [C01]
    type: single
    prompt: "You find an unencrypted POCSAG paging channel around 929-932 MHz carrying what looks like medical messages. What is allowed?"
    choices:
      - "decode and save the messages since the channel is unencrypted"
      - "classify the signal as paging and move on - never store or divulge its contents"
      - "forward the messages to a friend in medicine"
    answer: 1
    explanation: "Paging is trivially receivable and frequently carries personal and medical data; the ECPA is exactly about storing or divulging it. Classify the signal, not the content."
  - id: public-safety-state
    concept_tags: [C01]
    type: single
    prompt: "You find an UNENCRYPTED public-safety voice channel. Before recording it, what must you check?"
    choices:
      - "nothing - unencrypted means unrestricted"
      - "your state's rules - listening is legal in most US states but not all, and recording or divulging can carry separate restrictions"
      - "only that your antenna is tuned"
    answer: 1
    explanation: "Legality of listening to unencrypted public-safety audio varies by state, and recording or divulging are separate questions. Verify your state's rules before doing either."
  - id: ais-frequencies
    concept_tags: [C35]
    type: single
    prompt: "AIS, the ship-position broadcast, lives on which VHF channels?"
    choices:
      - "156.800 MHz only (marine Ch 16)"
      - "161.975 and 162.025 MHz"
      - "929-932 MHz"
    answer: 1
    explanation: "AIS occupies 161.975 (AIS 1) and 162.025 MHz (AIS 2), both within a 50 kHz span so one capture covers them; 156.800 is marine Ch 16 voice and 929-932 is paging."
  - id: ais-inland
    concept_tags: [C35]
    type: single
    prompt: "You run rtl_ais at the your location (inland) site and decode zero messages. What does that mean?"
    choices:
      - "the receiver is broken"
      - "the expected result - AIS is line-of-sight VHF from vessels, so a landlocked site hears nothing"
      - "AIS is encrypted and needs a key"
    answer: 1
    explanation: "AIS is an unencrypted safety broadcast, but it is line-of-sight VHF from ships; inland sites hear nothing. Zero is the correct, honest result - NOAA Weather Radio is your proof the receiver works on the band."
---

Eight of ten to pass. The items split across reading the land-mobile bands (C34: width-and-pattern
classification, analog vs digital, DMR, trunking control channels, and the no-decoder honest
endpoint), the legal line that runs through all of it (C01: encryption is not visible, paging
privacy, state public-safety rules), and AIS (C35: its channels, and why inland silence is the
correct result). The legal items are not optional polish - they are the whole reason this module
classifies and stops.
