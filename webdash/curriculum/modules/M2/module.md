---
id: M2
title: dB, antennas, link budget
themed_title: Passage 2 · Dead reckoning
discipline: rf-fundamentals
prerequisites:
  - {id: M0, soft: false}
sources:
  - knowledge/rf-fundamentals/learned/db-and-link-budget.md
  - knowledge/rf-fundamentals/learned/antenna-basics.md
  - docs/reference/antennas-and-rf-connectors.md
objectives:
  - "**Calculate** free-space path loss (FSPL, within +/-1 dB) and a quarter-wave (lambda/4) whip length for a given frequency."
  - "**Compute** the received power in dBm and the link margin for a real link, and read it against receiver sensitivity."
  - "**Justify** why height beats gain for most of Fancy's links."
  - "**Locate** ANT1 and the bias-tee port on the AIO V2, and state the port-safety rule before any transmit."
est_minutes: 120
today:
  state: ready
  reason: "Calculation and board inspection - needs no radios beyond the dashboard. Prerequisite: M0."
---

Radio work lives or dies on a few numbers you can do on paper before you ever key up or tune in: how
much a signal spreads out over distance (path loss), how many dB an antenna buys you, and whether
what is left clears the receiver's noise floor (the link margin). This module is the *dead reckoning*
of the spectrum - estimating reach from known quantities - and it underpins everything that follows:
you cannot judge an SDR capture, a mesh link or a satellite pass without it.

It draws on the repo's `db-and-link-budget.md`, `antenna-basics.md` and the antenna/connector
reference, and ends (LAB-16) with a worked link budget for a real Fancy link - the 5 km LongFast
case: received about -80.7 dBm against a sensitivity of about -131.5 dBm, a margin of about 51 dB.
