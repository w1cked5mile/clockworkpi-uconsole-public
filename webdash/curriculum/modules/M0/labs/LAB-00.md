---
id: LAB-00
title: Deck census
themed_title: Sea trial · Walk the deck
mode: observe
est_minutes: 10
requires: {rails: [], services: []}
transmits: false
steps:
  - id: bridge
    text: "The dashboard can reach the AIO V2 bridge that reports and switches the rails."
    check: {type: status, path: aiov2.state, op: eq, value: ok}
  - id: services
    text: "The dashboard can read the state of the services it watches (readsb, gpsd, meshtasticd, Kismet)."
    check: {type: status, path: services.state, op: eq, value: ok}
  - id: tour
    text: "Open each station — Mesh, GPS, SDR, Wi-Fi, Power, System — and find its rail switch, if it has one. Note which stations have none."
    check: {type: attest, prompt: "I found the rail switch on each station that has one."}
  - id: rules
    text: "Pass the M0 check. Every question must be right: it covers what makes Fancy transmit."
    check: {type: quiz, assessment: M0.quiz}
restore: []
evidence: [aiov2.rails.GPS.on, aiov2.rails.LORA.on, aiov2.rails.SDR.on, aiov2.rails.USB.on]
---

A read-only tour. Nothing in this lab changes the device.
