---
id: M0.quiz
kind: quiz
pass_threshold: 1.0
items:
  - id: tx-control
    concept_tags: [C01, C27]
    type: single
    required: true
    prompt: The LORA rail is on and nobody touches the dashboard. Does Fancy transmit?
    choices:
      - "No — only the Send button transmits"
      - "Yes — the mesh software announces the node and relays other nodes' packets on its own"
      - "Only if the SDR rail is also on"
    answer: 1
    explanation: A mesh node in the CLIENT role beacons and relays. Send adds your own messages on top.
  - id: hardware
    concept_tags: [C05]
    type: multi
    required: true
    prompt: Which dashboard controls change the device's hardware state?
    choices:
      - "The rail switches"
      - "Show coordinates"
      - "Log out"
    answer: [0]
    explanation: Rail switches power radios on and off. Show coordinates only changes what this page displays.
  - id: questions
    concept_tags: [C01]
    type: multi
    required: true
    prompt: Which of these are the repo's three questions for when you're unsure?
    choices:
      - "Is it intended for the general public?"
      - "Is the signal strong enough to decode?"
      - "Am I decoding or just observing?"
      - "Am I transmitting under a licence or exemption I actually hold?"
      - "Has anyone else decoded it before?"
    answer: [0, 2, 3]
    explanation: If any of the three is unclear, log the observation without content and move on.
  - id: default-key
    concept_tags: [C26, C02]
    type: single
    required: true
    prompt: A message sent on the SCMesh primary channel with the default key AQ== can be read by…
    choices:
      - "Only your own nodes"
      - "Anyone in range who sets up SCMesh with the public default key — which anyone can"
      - "Nobody — Meshtastic encrypts every message with your private key"
    answer: 1
    explanation: The default key is published, so the default channel is effectively public.
  - id: commit
    concept_tags: [C02]
    type: multi
    required: true
    prompt: Which of these may be committed to the repo?
    choices:
      - "The grid square EM95"
      - "Your home's decimal latitude and longitude"
      - "A Meshtastic channel PSK"
      - "A UTC timestamp"
    answer: [0, 3]
    explanation: Location is grid-square only, and keys never go in git.
  - id: grid
    concept_tags: [C02]
    type: single
    required: true
    prompt: "A textbook position, 48.1° N 11.5° E (Munich), is in which 4-character grid square?"
    choices: ["JN58", "NJ58", "JN85", "JO58"]
    answer: 0
    explanation: "Longitude first: 191.5 / 20 → J; latitude 138.1 / 10 → N; then 11.5 / 2 → 5 and 8.1 → 8."
---

Every question must be right. Retry as often as you like.
