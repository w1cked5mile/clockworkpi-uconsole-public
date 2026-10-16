---
id: M1.jp1
title: JP1 and the cells
est_minutes: 15
---

The NVMe battery board takes either two 18650 cells or a flat LiPo pack, and one solder jumper,
JP1, decides which current path is used.

@ref docs/reference/power-budget.md#two-supported-battery-options

> **Today on Fancy:** the Meshnology 1S LiPo pair is fitted with JP1 soldered **closed**
> (2026-10-11); don't refit 18650s with JP1 closed. Measuring or swapping cells is hands-on work with
> a meter — not something the dashboard or a lab does.

@ref docs/reference/power-budget.md#battery-safety

The interim 18650s that first powered Fancy failed the first two rules — unbranded, unknown capacity —
and have been retired. The fitted Meshnology pair is a known 1S pack, but it has its own hazard: the
device cuts power with no warning at ≈3.53 V under load, so M1's lab stays short and stops itself well
above that (3.6 V).
