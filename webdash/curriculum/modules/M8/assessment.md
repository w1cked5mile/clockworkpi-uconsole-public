---
id: M8.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: bandwidth-first
    concept_tags: [C19]
    type: single
    prompt: "You have an unknown signal on the waterfall. Which measurement eliminates the most candidates fastest?"
    choices: ["its exact modulation", "its bandwidth (width against the span)", "its audio", "the operator's callsign"]
    answer: 1
    explanation: "Width against the span rules out most modes immediately, and the band allocation narrows it further - both before any decoder."
  - id: carrier-symmetry
    concept_tags: [C19]
    type: single
    prompt: "A signal shows a strong carrier line dead centre with sidebands around it. That points to..."
    choices: ["the AM family (a centre carrier)", "SSB (no carrier)", "PSK (no carrier)"]
    answer: 0
    explanation: "A visible centre carrier means an AM-family mode; FM, PSK and SSB have no such centre carrier."
  - id: digital-edges
    concept_tags: [C19]
    type: single
    prompt: "On the waterfall, sharp vertical edges and a repeating burst pattern suggest..."
    choices: ["a digital mode", "an analog voice mode", "receiver noise"]
    answer: 0
    explanation: "Sharp edges and periodic bursts are digital fingerprints; sloped skirts and continuous shapes lean analog."
  - id: wfm-vs-nfm
    concept_tags: [C19]
    type: single
    prompt: "Broadcast FM and NOAA Weather Radio are both FM. What tells them apart on the waterfall?"
    choices:
      - "colour"
      - "width - broadcast FM is ~150-200 kHz wide, NOAA is narrowband ~12.5-16 kHz"
      - "nothing, they look identical"
    answer: 1
    explanation: "Wideband FM broadcast is an order of magnitude wider than the narrowband FM used for NOAA voice; width alone separates them."
  - id: lora-chirp
    concept_tags: [C19]
    type: single
    prompt: "How does LoRa appear on a waterfall?"
    choices:
      - "a fixed vertical carrier line"
      - "a diagonal streak - a chirp sweeping across its bandwidth"
      - "three fixed tones"
    answer: 1
    explanation: "LoRa uses chirp spread spectrum (CSS): each symbol sweeps in frequency, drawing a diagonal, not a fixed carrier."
  - id: workflow-first
    concept_tags: [C20]
    type: single
    prompt: "What is the first step of the signal-ID workflow?"
    choices:
      - "guess the mode"
      - "record the observables (frequency, bandwidth, timing, shape) before theorizing"
      - "run a decoder"
    answer: 1
    explanation: "Describe what you actually see first; naming a mode before recording the observables biases everything after it."
  - id: allocation
    concept_tags: [C20]
    type: single
    prompt: "Why check the band allocation early?"
    choices:
      - "it is legally required before receiving"
      - "what is allocated and expected on that frequency narrows the candidates faster than almost anything"
      - "it tells you the exact modulation"
    answer: 1
    explanation: "The allocation says what should be there; it cuts the candidate list dramatically before you compare against a reference."
  - id: image-false-positive
    concept_tags: [C20]
    type: single
    prompt: "A 'signal' shifts across the display every time you retune the receiver. It is most likely..."
    choices:
      - "a real hopping transmitter"
      - "an image or alias - a receiver artefact, not a real signal"
      - "a harmonic"
    answer: 1
    explanation: "Images and aliases move with retuning; a real signal stays put in absolute frequency. Test by retuning."
  - id: dc-spike
    concept_tags: [C20]
    type: single
    prompt: "There is a persistent spike exactly at the centre of every capture, wherever you tune. That is..."
    choices: ["a strong local station", "the DC spike - a receiver artefact at the centre of the IQ", "a harmonic"]
    answer: 1
    explanation: "The DC spike is an artefact of direct-conversion/IQ receivers; it sits at the tuned centre regardless of frequency, so it is never a real signal."
  - id: confidence-grade
    concept_tags: [C20]
    type: single
    prompt: "An honest signal-ID entry includes..."
    choices:
      - "a definite name, always"
      - "a confidence grade (unidentified / candidate / identified) and what would raise it"
      - "only the frequency"
    answer: 1
    explanation: "The worksheet grades confidence and asks what would move it up; 'candidate: probably DMR (Digital Mobile Radio), would confirm with a decode' beats a confident wrong name. (The workflow's confirmed/probable/unknown map to the worksheet's identified/candidate/unidentified.)"
---

Eight of ten to pass. The items split between reading modulation off the waterfall (C19: width,
carrier symmetry, digital edges, WFM vs NFM, the LoRa chirp) and the workflow and its discipline
(C20: observe first, check allocation, reject images/DC-spike artefacts, grade confidence).
