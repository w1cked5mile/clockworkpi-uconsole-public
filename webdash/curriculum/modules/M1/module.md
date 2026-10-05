---
id: M1
title: Power and rails
themed_title: Passage 1 · Know the load
discipline: platform
station: power
prerequisites:
  - {id: M0, soft: false}
sources:
  - docs/reference/power-budget.md
  - docs/reference/platform-basics/buses-and-rails.md
  - software/aiov2_ctl.md
objectives:
  - "**Identify** the rail and GPIO pin behind each radio."
  - "**Measure** what the SDR rail plus readsb decoding costs, on battery."
  - "**Calculate** runtime from watt-hours and watts."
  - "**Explain** what JP1 selects, and why it matters before changing batteries."
est_minutes: 60
today:
  state: degraded
  reason: "The fitted 18650 cells are unverified (labelled 9900 mAh, no brand). The lab runs on battery for about 3 minutes and stops itself at 3.5 V or 30%."
---

Everything on Fancy runs from one lithium cell's worth of energy. Knowing what each radio costs
is how you decide what to leave on.
