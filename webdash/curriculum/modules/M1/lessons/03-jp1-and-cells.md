---
id: M1.jp1
title: JP1 and the cells
est_minutes: 15
---

The NVMe battery board takes either two 18650 cells or a flat LiPo pack, and one solder jumper,
JP1, decides which current path is used.

@ref docs/reference/power-budget.md#two-supported-battery-options

> **Today on Fancy:** JP1 is open and two unverified 18650 cells are fitted. JP1 must be soldered
> closed *before* the Meshnology LiPo goes on. Measuring or swapping cells is hands-on work with a
> meter — not something the dashboard or a lab does.

@ref docs/reference/power-budget.md#battery-safety

The cells fitted today don't meet the first two rules — they are unbranded and their capacity is
unknown — which is why M1's lab stays short and stops itself at 3.5 V.
