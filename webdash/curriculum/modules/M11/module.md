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
  - "**Design** a ~2 h battery session running GPS, mesh, ADS-B and a Wi-Fi survey together, within the pack's real runtime and the 3.5 V abort line."
  - "**Compare** the measured mean draw against your composed estimate, and **account** for the difference."
  - "**Reflect** against a rubric: what the budget predicted, what the session measured, and what you would change."
est_minutes: 180
today:
  state: blocked
  reason: "POWER-GATED on real hardware. The capstone runs ~2 h on battery with everything live, so it must not run until the battery path is verified: the interim 18650 pair in service is unverified (wrapped 9900mAh, no provenance, not capacity-tested), JP1 is open, and the Meshnology LiPo is not fitted. Per the build state, the lab stays gated until EITHER the fitted pack is capacity-tested OR the Meshnology pack is fitted with JP1 soldered closed. The lessons (composing a power budget, designing the session) can be read and worked now; LAB-20's battery run waits on that gate. Prerequisites: M3, M4, M6, M7."
---

The capstone pulls the whole platform together: GPS, the mesh, ADS-B and a Wi-Fi survey all running at
once, on battery, for a couple of hours — a shakedown cruise. The skill it certifies is not operating
any one radio (you learned those in M3, M4, M6 and M7) but **budgeting and running the system as a
whole**: composing a power budget from the measured idle floor and per-rail deltas, predicting how long
the pack will last, then running the session and comparing what you measured against what you predicted.

A word on why this module is gated. It is the one exercise that deliberately runs Fancy hard on battery
for a sustained period, so it carries a power-safety gate: it does not run until the battery path is
verified — the fitted pack capacity-tested, or the Meshnology LiPo fitted with JP1 soldered closed. As
of the current build state the interim 18650 pair is unverified and JP1 is open, so **the lab is blocked
on purpose.** The planning half — composing the budget and designing the session — you can do now; the
battery run waits on that hardware work, which is the honest state of the device, not a limitation of
the lesson.

It draws on `docs/reference/power-budget.md`, the build's measured power numbers, and ends (LAB-20)
with the shakedown itself: a ~2 h battery session with all four stations live, mean draw recorded and
compared to the estimate, aborting at 3.5 V.
