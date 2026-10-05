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
    explanation: "Runtime is usable energy divided by average draw: ~31 Wh usable ÷ ~7 W ≈ 4.4 h, for example."
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
    explanation: "A 1S system runs from one cell (parallel cells still count as 1S), so its voltage directly reflects state of charge and sag; 3.5 V is the abort line."
  - id: abort-line
    concept_tags: [C06]
    type: single
    prompt: "At what cell voltage do you abort the session?"
    choices:
      - "3.5 V"
      - "5.0 V"
      - "2.5 V"
    answer: 0
    explanation: "3.5 V is the hard stop for the session; the safety-stop check watches for it and the lab aborts there to protect the cell."
  - id: usable-energy
    concept_tags: [C06]
    type: single
    prompt: "The budget uses ~31 Wh usable from the 37 Wh Meshnology pack. What is the catch?"
    choices:
      - "that ~85% figure is itself an estimate until the pack is discharge-tested, so the runtime prediction inherits the uncertainty"
      - "31 Wh is exact and measured"
      - "the pack holds far more than 37 Wh"
    answer: 0
    explanation: "Usable energy is taken as ~85% of 37 Wh but is unverified until a full discharge; any runtime built on it is an estimate, which is also why the whole module is gated on battery verification."
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
session, the 1S voltage gauge and 3.5 V abort, and the unverified usable-energy figure that gates the
module) and the reconciliation that closes it (C05: accounting for the gap between measured and composed
draw). The lab's battery run stays gated until the pack is verified; the budget and session design you
can work now.
