---
id: M11
title: Capstone field session
themed_title: Passage 11 · The shakedown cruise
discipline: platform
station: power
prerequisites:
  - {id: M3, soft: false}
  - {id: M4, soft: false}
  - {id: M6, soft: false}
  - {id: M7, soft: false}
sources:
  - docs/reference/power-budget.md
objectives:
  - "**Compose** a power budget for a live field session from the measured idle floor plus per-rail deltas, and **predict** the runtime on the pack."
  - "**Design** a ~2 h battery session running GPS, mesh, ADS-B and a Wi-Fi survey together, within the pack's real runtime and the voltage floor (plug in by 3.60 V, shut down by 3.55 V)."
  - "**Compare** the measured mean draw against your composed estimate, and **account** for the difference."
  - "**Reflect** against a rubric: what the budget predicted, what the session measured, and what you would change."
est_minutes: 180
today:
  state: ready
  reason: "The power gate is met: the Meshnology LiPo pair is fitted with JP1 soldered closed (2026-10-11) and was discharge-tested on 2026-10-13 (52.2 Wh delivered before a hard cut at ≈3.53 V). Run the capstone on battery, but mind the measured floor — the device cuts power with no warning at ≈3.53 V under load, so plug in by 3.60 V and shut down by 3.55 V, not 3.5 V. Prerequisites: M3, M4, M6, M7."
---

The capstone pulls the whole platform together: GPS, the mesh, ADS-B and a Wi-Fi survey all running at
once, on battery, for a couple of hours — a shakedown cruise. The skill it certifies is not operating
any one radio (you learned those in M3, M4, M6 and M7) but **budgeting and running the system as a
whole**: composing a power budget from the measured idle floor and per-rail deltas, predicting how long
the pack will last, then running the session and comparing what you measured against what you predicted.

A word on this module's power-safety gate. It is the one exercise that deliberately runs Fancy hard on
battery for a sustained period, so it does not run until the battery path is verified — the fitted pack
capacity-tested, or the Meshnology LiPo fitted with JP1 soldered closed. **That gate is now met:** the
Meshnology pair was fitted with JP1 closed (2026-10-11) and discharge-tested (2026-10-13, 52.2 Wh to a
hard cut at ≈3.53 V). The one thing that test added to the safety picture: the device cuts power with no
warning at ≈3.53 V under load, and the fuel-gauge % is wrong on this pack — so run on **voltage**, plug
in by 3.60 V, and shut down by 3.55 V.

It draws on `docs/reference/power-budget.md`, the build's measured power numbers, and ends (LAB-20)
with the shakedown itself: a ~2 h battery session with all four stations live, mean draw recorded and
compared to the estimate, shutting down by 3.55 V (plug in by 3.60 V).
