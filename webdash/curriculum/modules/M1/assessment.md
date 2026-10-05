---
id: M1.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: runtime
    concept_tags: [C06]
    type: numeric
    prompt: "About how many hours does a 37 Wh pack last at a steady 5 W (all of it usable)?"
    answer: 7.4
    tolerance: 0.7
    unit: h
    explanation: 37 Wh ÷ 5 W = 7.4 h. Real runtime is lower until the usable fraction is measured.
  - id: jp1
    concept_tags: [C06]
    type: single
    required: true
    prompt: The Meshnology LiPo pack is about to replace the 18650s. What has to happen to JP1 first?
    choices:
      - "Nothing — JP1 only matters for 18650s"
      - "It must be soldered closed"
      - "It must be cut open"
    answer: 1
    explanation: JP1 open is for 18650s; the JST LiPo needs it closed. It sets the current path.
  - id: parallel
    concept_tags: [C06]
    type: single
    prompt: Two 18650 cells on this board are wired…
    choices:
      - "In series, for 7.4 V"
      - "In parallel, for 3.7 V with the capacities added"
    answer: 1
    explanation: The AXP228 is a single-cell charger, so the cells sit in parallel.
  - id: on-battery
    concept_tags: [C06]
    type: single
    prompt: Why measure a rail's cost on battery rather than on AC?
    choices:
      - "On AC the charger feeds the system, so the reading at the cell isn't what the device draws"
      - "The rails only work on battery"
      - "AC makes the SDR noisier"
    answer: 0
    explanation: On AC, power at the cell is mostly charging current.
  - id: gpio
    concept_tags: [C05]
    type: single
    prompt: Which GPIO pin switches the SDR rail?
    choices: ["27", "16", "7", "23"]
    answer: 2
    explanation: GPS 27, LORA 16, SDR 7, USB 23.
---

Four of five, and the JP1 question must be right.
