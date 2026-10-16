---
id: M11.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: runtime-formula
    concept_tags: [C06]
    type: single
    prompt: "How do you turn a power budget into a runtime estimate?"
    choices:
      - "runtime = usable energy (Wh) ÷ average draw (W)"
      - "runtime = average draw (W) × pack voltage (V)"
      - "runtime = cell voltage (V) ÷ current (A)"
    answer: 0
    explanation: "Runtime is usable energy divided by average draw: 52 Wh usable ÷ ~5.9 W (ADS-B + screen) ≈ 8.8 h, for example."
  - id: baseline
    concept_tags: [C06]
    type: single
    prompt: "What baseline should a field-session budget start from?"
    choices:
      - "the measured ~5.0 W idle floor, not the lower pre-measurement estimate"
      - "the 3.0 W bottom of the old estimate range"
      - "zero - add up only the radios"
    answer: 0
    explanation: "The 2026-09-23 measurement put idle at ~5.0 W, above the old 3.0-4.5 W estimate, so the runtime table is built on the measured floor; starting lower under-budgets every session."
  - id: measured-over-estimate
    concept_tags: [C06]
    type: single
    prompt: "You have both a measured delta and a class-typical estimate for the SDR rail. Which do you use, and how do you mark it?"
    choices:
      - "use the measured +0.64 W and mark the estimated lines as estimates"
      - "always use the estimate; measurements are unreliable"
      - "average the two together silently"
    answer: 0
    explanation: "Prefer the measured delta where you have it (SDR rail +0.64 W, GPS +0.29 W measured), and clearly label the lines that are still estimates - the budget's honesty depends on that distinction."
  - id: compose-session
    concept_tags: [C06]
    type: single
    prompt: "Composing the full field session (idle + SDR + GPS + readsb decoding + AC1200 survey), the average draw lands roughly where?"
    choices:
      - "~7-9 W"
      - "~2-3 W"
      - "~15-20 W"
    answer: 0
    explanation: "~5.0 idle + 0.64 SDR + 0.29 GPS + ~0.5-1 readsb + ~1-1.8 AC1200 composes to roughly 7.4-8.7 W - the figure you then measure against."
  - id: one-s
    concept_tags: [C06]
    type: single
    prompt: "Why is the cell voltage the meaningful fuel gauge on this build?"
    choices:
      - "the system is 1S - a single cell, so there is no higher-cell headroom to hide a sagging cell"
      - "because voltage never changes under load"
      - "it is not - only current matters"
    answer: 0
    explanation: "A 1S system runs from one cell (parallel cells still count as 1S), so its voltage directly reflects state of charge and sag; shut down by 3.55 V (plug in by 3.60 V)."
  - id: abort-line
    concept_tags: [C06]
    type: single
    prompt: "At what loaded cell voltage do you shut the session down?"
    choices:
      - "3.55 V (plug in by 3.60 V)"
      - "3.5 V"
      - "2.5 V"
    answer: 0
    explanation: "The device cuts power with no warning at ≈3.53 V under load, so 3.5 V is already too late. Plug in by 3.60 V and shut down by 3.55 V; a guard waiting for 3.45 V never fires. See the Low-battery table in power-budget.md."
  - id: usable-energy
    concept_tags: [C06]
    type: single
    prompt: "The budget uses 52 Wh usable from the ≈74 Wh Meshnology pair. What is the catch?"
    choices:
      - "52 Wh is what the device delivered before it cut out at ≈3.53 V; the pack probably held more, so usable energy depends on where the system shuts off"
      - "52 Wh is the pack's full capacity, measured to empty"
      - "usable energy does not depend on where the device shuts off"
    answer: 0
    explanation: "The 2026-10-12 discharge ended in a hard cut at ≥3.53 V with no knee in the curve, so 52 Wh is usable energy to that cut-off, not the cells' capacity. Move or explain the cut-off and every runtime built on it changes."
  - id: reconcile
    concept_tags: [C05]
    type: single
    prompt: "Your measured mean draw comes in a watt above your composed estimate. The right response is to..."
    choices:
      - "account for the gap - screen brightness, whether readsb was really decoding, survey band activity, CPU load - and note which estimated lines were off"
      - "ignore it; estimates are never exact"
      - "discard the measurement and trust the budget"
    answer: 0
    explanation: "The capstone is the reconciliation: each term was measured or estimated, and the gap between composed and measured tells you which estimates to revise. Explaining the difference is the point, not hiding it."
---

Eight of ten to pass. The items are the budgeting method the capstone certifies (C06: runtime = Wh ÷ W,
starting from the measured idle floor, preferring measured deltas over estimates, the ~7-9 W composed
session, the 1S voltage gauge and the 3.55 V shut-down (3.60 V plug-in), and the unverified usable-energy figure that gates the
module) and the reconciliation that closes it (C05: accounting for the gap between measured and composed
draw). The lab's battery run stays gated until the pack is verified; the budget and session design you
can work now.
