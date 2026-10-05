---
id: M10.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: aprs-freq
    concept_tags: [C37]
    type: single
    prompt: "What is the APRS channel in North America?"
    choices:
      - "144.390 MHz"
      - "162.550 MHz"
      - "446.000 MHz"
    answer: 0
    explanation: "APRS lives on 144.390 MHz in North America; 162.550 is NOAA Weather Radio and 446.000 is a UHF simplex frequency."
  - id: aprs-chain
    concept_tags: [C37]
    type: single
    prompt: "APRS packets reach structured data through which chain?"
    choices:
      - "antenna → FM demod → AFSK1200 → AX.25 → structured data"
      - "antenna → SSB demod → CW → structured data"
      - "antenna → GMSK → TDMA → structured data"
    answer: 0
    explanation: "APRS is 1200-baud AFSK over FM carrying AX.25 packets; you FM-demod, decode AFSK1200, then parse AX.25 - the chain multimon-ng runs."
  - id: aprs-baud
    concept_tags: [C37]
    type: single
    prompt: "APRS on 2 m is sent as..."
    choices:
      - "1200-baud AFSK over FM"
      - "9600-baud GMSK"
      - "single-sideband voice"
    answer: 0
    explanation: "North American 2 m APRS is 1200-baud AFSK over FM - which is why an ordinary FM demod plus multimon-ng decodes it."
  - id: ft8-timing
    concept_tags: [C37]
    type: single
    prompt: "Why does FT8 need the system clock accurate to within about a second?"
    choices:
      - "it uses rigid 15-second slots, so a drifting clock produces zero decodes and no error"
      - "it transmits a timestamp that must match the FCC's"
      - "it does not - timing is irrelevant to FT8"
    answer: 0
    explanation: "FT8's 15-second slots require the clock within ~1 s; a drifting clock silently yields no decodes, which is why NTP and the RTC matter (and M3 is recommended)."
  - id: offset-2m
    concept_tags: [C36]
    type: single
    prompt: "A 2 m repeater uses which standard offset between its input and output?"
    choices:
      - "±600 kHz"
      - "±5 MHz"
      - "±12.5 kHz"
    answer: 0
    explanation: "2 m repeaters use a ±600 kHz offset; 70 cm uses ±5 MHz. The 12.5 kHz figure is the narrowband land-mobile channel spacing, not a repeater offset."
  - id: ctcss-receive
    concept_tags: [C36]
    type: single
    prompt: "You are only LISTENING to a repeater's output. Does its input CTCSS/PL tone matter?"
    choices:
      - "no - the input tone gates transmitting, not receiving; you just tune the output"
      - "yes - you must set the tone to hear the output"
      - "yes - without the tone the output is encrypted"
    answer: 0
    explanation: "CTCSS on the input gates who can key the repeater; it has nothing to do with receiving. To listen you simply tune the output frequency."
  - id: hf-range
    concept_tags: [C36]
    type: single
    prompt: "Why are the HF bands (160 m–12 m) out of scope on this build?"
    choices:
      - "the R860 tuner starts around 24 MHz, so HF is unreachable without an upconverter"
      - "HF is illegal to receive"
      - "HF needs a licence to receive"
    answer: 0
    explanation: "The RTL-SDR's R860 tuner starts near 24 MHz, so 160 m through 12 m need an upconverter or direct-sampling receiver; only 10 m is marginally in range. Receiving HF is legal and needs no licence."
  - id: classes-vec
    concept_tags: [C38]
    type: single
    prompt: "Which is true of the US amateur licence path?"
    choices:
      - "three classes (Technician, General, Extra), written VEC exams, no Morse code at any class"
      - "a Morse-code test is required for General and Extra"
      - "the FCC administers the exams directly, in person only"
    answer: 0
    explanation: "Technician, General and Extra are earned by written exams through a Volunteer Examiner Coordinator; there is no Morse requirement at any class, and sessions run in person and online."
  - id: licence-no-tx
    concept_tags: [C38]
    type: single
    prompt: "If you earn a Technician licence, what does it change for Fancy specifically?"
    choices:
      - "nothing about Fancy's hardware - the SDR is receive-only; a licence makes acquiring a separate transmitter useful, it adds no transmit capability here"
      - "it lets the RTL-SDR transmit on 2 m and 70 cm"
      - "it legalises the SX1262's ISM transmissions"
    answer: 0
    explanation: "A licence adds capability, not hardware: the SDR stays receive-only and would need a separate radio to transmit. The SX1262 already operates legally under Part 15 in ISM, so a licence legalises nothing in current use."
  - id: receive-no-licence
    concept_tags: [C38]
    type: single
    prompt: "Which of these receive-only activities needs an amateur licence?"
    choices:
      - "none of them - monitoring repeaters, decoding APRS, and receiving satellite downlinks all need no licence"
      - "decoding APRS needs a Technician licence"
      - "receiving the ISS needs a General licence"
    answer: 0
    explanation: "Receiving anywhere on the amateur bands needs no licence; only transmitting does. The whole receive-only workflow - repeaters, APRS, satellite downlinks, FT8/WSPR spotting - is open to anyone."
---

Eight of ten to pass, Technician-style. The items cover the band plans (C36: 2 m repeater offset,
why input CTCSS is irrelevant when listening, and why HF is out of reach here), APRS and digital modes
(C37: the APRS frequency and decode chain, its 1200-baud AFSK, and FT8's timing requirement), and
licensing (C38: the three VEC classes with no Morse, that a licence adds no transmitter to Fancy, and
that all receiving is licence-free). The licensing items are the ones Track C turns on - finishing the
track prepares you for the exam and is not itself a licence.
