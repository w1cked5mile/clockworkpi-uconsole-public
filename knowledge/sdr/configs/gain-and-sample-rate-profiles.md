# Gain and sample-rate profiles

Starting points per task, plus the per-device constants measured once. Fill the measured column
during bring-up; these values then become the reference for every later capture.

## Device constants (measure once)

| Constant | How | Value |
|---|---|---|
| PPM offset | `rtl_test -p` (10+ min, warm) | **≈ +1 ppm** (2026-09-24, owner: cumulative settled between 0 and +2 over 12.5 min warm; occasional single −5/−17 readings are USB timing jitter on the CM4's shared bus, not drift). Use `-p 1`; `-p 0` is also fine at this size |
| Max loss-free sample rate | `rtl_test -s <rate>` for 30 s | |
| Useful gain ceiling | gain sweep in [`../../rf-fundamentals/runbooks/noise-floor-baseline.md`](../../rf-fundamentals/runbooks/noise-floor-baseline.md) | |
| Noise floor (quiet band) | `rtl_power` baseline | |

## Task profiles

| Task | Frequency | Sample rate | Gain (start) | Bandwidth/mode | Notes |
|---|---|---|---|---|---|
| Broadcast FM check | 88–108 MHz | 1.024 MS/s | 15–20 dB | WFM 200 kHz | Sanity check only; strong signals overload easily |
| NOAA weather radio | 162.400–162.550 | 250 kS/s | 25–30 dB | NFM 12.5 kHz | Always-on reference transmitter — good antenna test |
| Airband voice | 118–137 MHz | 1.024 MS/s | 30–35 dB | AM 8 kHz | Quiet between transmissions is normal |
| NOAA APT satellites | 137.100 / 137.62 / 137.9125 | 250 kS/s | 30–40 dB | WFM 40 kHz | V-dipole or QFH; needs a pass prediction |
| ADS-B | 1090 MHz | decoder-managed | 40–49 dB | — | Use dump1090/readsb, not SDR++ |
| ISM survey | 902–928 MHz | 2.048 MS/s | 25–30 dB | wide | Observe only |
| Unknown-signal hunting | varies | 2.048 MS/s | start 20 dB, raise to the knee | wide → narrow | Manual gain, never AGC |

## Rules

- **Manual gain always.** AGC hides overload and makes sessions incomparable.
- Raise gain only until the noise floor starts to rise; stop there
  ([`../../rf-fundamentals/learned/receiver-performance.md`](../../rf-fundamentals/learned/receiver-performance.md)).
- Change one variable at a time between captures, and record every setting in the finding.
- Bias tee **off** unless a specific LNA needs it.

## Capture file naming

```
YYYYMMDDTHHMMZ_<centre-freq>_<sample-rate>_<gain>_<label>.cu8
20260915T2130Z_162550k_250k_g30_noaa-wx.cu8
```

Raw IQ is gitignored (`*.iq`, `*.cu8`, `*.cf32`, `*.sigmf-data`). Keep captures on external
storage and reference them by name and location from the finding that describes them.
