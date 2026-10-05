---
id: M11.session
title: Designing and running the field session
est_minutes: 35
---

With a budget composed, the session designs itself around two limits: the pack's predicted runtime and
the **3.5 V abort line**. The plan is a ~2 h battery session with all four stations live at once — GPS
tracking, the mesh node receiving, ADS-B decoding, and a Wi-Fi survey on the AC1200 — everything you
brought up individually in M3, M4, M6 and M7, now running together and drawing from one cell.

The system is **1S** (a single cell in series terms), which is what makes the voltage line meaningful:
there is no higher-cell headroom to hide a sagging cell, so the cell voltage is the real fuel gauge, and
3.5 V is where you stop:

@ref docs/reference/power-budget.md#battery-the-system-is-1s

That is also why this module is gated. A sustained 2 h high-draw session is exactly the condition that
exposes an unverified pack, so the safety rules are not optional:

@ref docs/reference/power-budget.md#battery-safety

Running the session is then a measurement, not a demo. You unplug from AC so the whole session runs on
battery, confirm all four stations are actually live (a fix, mesh RX, readsb decoding, the survey
adapter in monitor mode), and let the dashboard record the mean draw over the two hours. The number you
want is the **measured mean power**, because the whole point is to set it beside your composed estimate:

- If measured and composed agree within a watt or so, your budget method is sound.
- If they diverge, account for it — screen brightness, whether readsb was really decoding traffic, how
  busy the survey band was, CPU load from the session shells. Each is a line you either measured or
  estimated, and the gap tells you which estimates were off.

Finish with a written reflection against the rubric: what the budget predicted, what the session
measured, where they differed and why, and what you would change next time. That reflection — not a
single pass/fail reading — is the capstone, because budgeting and honestly reconciling a field session is
the system-level skill the whole track builds toward.
