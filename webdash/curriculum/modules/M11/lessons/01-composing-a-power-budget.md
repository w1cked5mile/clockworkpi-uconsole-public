---
id: M11.budget
title: Composing a power budget
est_minutes: 35
---

A power budget is built the way you would compose any estimate from parts: start from a measured
baseline, add the cost of each thing you switch on, and divide the pack's usable energy by the total to
get runtime. The baseline here is the **measured ~5.0 W idle floor** (not the lower pre-measurement
estimate), and the key discipline is to prefer a measured delta over an estimated one wherever you have
it:

@ref docs/reference/power-budget.md#measured-supersedes-rows-below-where-they-overlap

Where a measurement does not exist yet, you fall back to the class-typical estimates, clearly marked as
estimates — the SDR rail, GPS rail, LoRa RX, Ethernet and the AC1200 card each have a line:

@ref docs/reference/power-budget.md#estimated-draw-by-state-5-v-system-side

Put together, a full field session composes roughly like this: the ~5.0 W floor, plus the measured
+0.64 W SDR rail and +0.29 W GPS rail, plus an estimated ~0.5–1 W for readsb actually decoding, plus
~1–1.8 W for the AC1200 in monitor mode for the survey. That lands near **7.4–8.7 W** — the exact figure
is what you compose and then test. The runtime scenarios table does this composition for several real
cases against the ~31 Wh usable estimate of the Meshnology pack:

@ref docs/reference/power-budget.md#runtime-scenarios-meshnology-37-wh-pack

Two honesty notes carry straight into your budget. First, usable energy (~31 Wh ≈ 85 % of 37 Wh) is
itself an estimate until the pack is discharge-tested — so your runtime prediction inherits that
uncertainty. Second, the readings that matter are taken at the cell, so they divide straight into pack
Wh with no converter-loss factor. Reading those numbers off the device is the next lesson's and the
lab's job:

@ref docs/reference/power-budget.md#reading-the-power-numbers
