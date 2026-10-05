# Runbook — NOAA APT weather-satellite reception

Record a satellite pass and decode it into an image. Plan around the pass; everything else is
preparation.

> **Status 2026-09-24: not runnable as written.** NOAA-15, -18 and -19 were decommissioned
> June–August 2025, so there is no APT signal to receive (see
> [`../learned/weather-satellites.md`](../learned/weather-satellites.md)). The planning steps still
> apply to Meteor-M LRPT, which needs SatDump and a 137 MHz V-dipole or QFH antenna — neither is on
> hand.

## Preconditions

- [ ] Satellite status verified as active ([`../learned/weather-satellites.md`](../learned/weather-satellites.md))
- [ ] Pass predicted: AOS/LOS times (UTC), maximum elevation, direction — use `gpredict` or n2yo.com
- [ ] **Pass elevation ≥ 30°** for a first attempt
- [ ] V-dipole, QFH, or turnstile antenna, outdoors with clear sky
- [ ] `aiov2_ctl SDR on`; PPM correction known
- [ ] Decoder available: `noaa-apt` or SatDump

## Frequencies

| Satellite | Frequency |
|---|---|
| NOAA 15 | 137.6200 MHz |
| NOAA 18 | 137.9125 MHz |
| NOAA 19 | 137.1000 MHz |

## 1. Set up before AOS

- [ ] Antenna outdoors, oriented per its type (V-dipole: elements horizontal, opening toward the
      pass direction)
- [ ] Gain ~30–40 dB, sample rate 250 kS/s, WFM with ~40 kHz bandwidth
- [ ] Confirm the receiver hears *something* at 137 MHz (noise floor looks normal, no local carrier)

## 2. Record the whole pass

Record audio for APT rather than decoding live — a recording can be re-decoded with different
settings.

```bash
PPM=1                        # dongle frequency error, measured ≈ +1 ppm 2026-09-24 (checklist 3.6)
sudo systemctl stop readsb   # readsb holds the SDR; run `sudo systemctl start readsb` when done
# uses: sox (installed 2026-09-24 via apt)

# start ~1 minute before AOS, stop ~1 minute after LOS
timeout 900 rtl_fm -f 137.9125M -M fm -s 60k -r 11025 -g 35 -p "$PPM" -E deemp - \
  | sox -t raw -r 11025 -es -b16 -c1 -V1 - $(date -u +%Y%m%dT%H%MZ)_noaa18.wav rate 11025
```

Do not retune or change gain mid-pass — it corrupts the image.

## 3. Decode

```bash
noaa-apt <recording>.wav -o pass.png
# or use SatDump for APT/LRPT with more processing options
```

## 4. Record the result

In `../findings/` (template: [`../../_templates/finding.md`](../../_templates/finding.md)):

- [ ] Satellite, frequency, UTC AOS/LOS, maximum elevation, direction
- [ ] Antenna type, orientation, height, surroundings
- [ ] Gain, sample rate, PPM
- [ ] Result: full image / partial / noise, with the image file referenced (images live in the repo
      only if small; raw audio and IQ are gitignored)

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Noise for the whole pass | Wrong antenna type or polarization; satellite inactive; wrong frequency |
| Signal only near maximum elevation | Antenna pattern or obstruction at low angles — normal for poor sites |
| Image bands but heavy noise | Gain too high or too low; local 137 MHz interference |
| Skewed or torn image | Sample-rate/timing error, or the receiver was retuned mid-pass |
| Nothing at the predicted time | Prediction used a stale TLE — refresh the elements |

## Expectations

Partial images are a normal first result. Improve in this order: antenna type → siting and
elevation → gain → decoder settings.
