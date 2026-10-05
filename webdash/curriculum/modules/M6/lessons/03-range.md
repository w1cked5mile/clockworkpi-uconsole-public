---
id: M6.range
title: Range, the horizon and the whip
est_minutes: 25
---

@ref knowledge/aerospace/learned/adsb-basics.md#range-and-the-horizon

For Fancy held at about 1.5 m and an airliner at 10,000 m:

```text
d ≈ 4.12 × (√1.5 + √10000) ≈ 4.12 × (1.22 + 100) ≈ 417 km
```

That is almost the same as the textbook 425 km for a receiver on a 10 m mast, because the
aircraft's height dominates. What actually limits Fancy is the antenna: the telescopic whip
indoors typically reaches 30–80 km (*estimate*, not yet measured on Fancy — settle it with
tar1090's range outline).

How long should the whip be? A quarter of a wavelength:

@ref knowledge/rf-fundamentals/learned/antenna-basics.md#resonance-and-length

At 1090 MHz a quarter wave is 68.8 mm in free space, slightly shorter in practice. Set the whip
to about 65–69 mm, or as close as it goes — its length has not been recorded.

> **Before attaching any other antenna** to the SDR port: that port has a bias tee that can put
> 5 V on the antenna cable, and its state is unknown. A DC-grounded antenna would short that 5 V.
> Check with a meter first.
