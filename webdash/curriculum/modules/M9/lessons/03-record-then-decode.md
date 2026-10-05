---
id: M9.capture
title: Record then decode
est_minutes: 30
---

The capture discipline for a pass is different from a fixed signal: you **record the whole pass first
and decode afterwards**, because a pass is over in minutes and you cannot re-run it. The workflow is
short and strict — predict, set up outdoors with a clear sky, record from before AOS through LOS, then
decode from the recording:

@ref knowledge/aerospace/learned/weather-satellites.md#workflow

For the ISS packet target this means a single `rtl_fm` capture through the pass, teed to a raw file and
also piped live into `multimon-ng` so you can see packets arrive — but the file is the real product.
After checking the station's current frequency, a 2 m pass is captured with something like:

```bash
PPM=1; sudo systemctl stop readsb
timeout 900 rtl_fm -f 145.825M -M fm -s 22050 -g 35 -p "$PPM" - \
  | tee ~/labs/iss-pass-$(date -u +%Y%m%dT%H%MZ).raw \
  | multimon-ng -t raw -a AFSK1200 -A -
```

At 437.825 MHz instead, widen the sample rate to `-s 48k` for the ±10 kHz Doppler, and keep the gain
fixed for the whole pass — changing it mid-pass ruins the recording.

Grade the result against the geometry, not against a hope of perfection. Partial or noisy is the normal
first outcome, and the causes have a usual order:

@ref knowledge/aerospace/learned/weather-satellites.md#expectations

A pass where you recorded cleanly through AOS–LOS and decoded even a few packets is a success; a pass
with nothing is most often a stale TLE, a low elevation, or an inactive station — all of which you
diagnose from the plan, not by doubting the hardware. Record the pass, the elevation, and the honest
result as a finding, the same confirmed/partial/nothing grading you have used since M8.

An extension for later (not part of this lab, no track): once a 137 MHz circular or V-dipole antenna
and SatDump are on hand, the same record-then-decode workflow produces Meteor LRPT weather imagery —
that is LAB-14, kept as theory here because the antenna and decoder are not on hand and NOAA APT is off
air.
