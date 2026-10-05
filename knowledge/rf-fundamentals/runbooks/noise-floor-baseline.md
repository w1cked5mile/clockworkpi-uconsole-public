# Runbook — establish a noise-floor baseline

Purpose: one measurement session that produces a reference for the local RF environment, so later
"reception got worse" claims can be tested instead of guessed at.

Do this once after [`../../../docs/runbooks/first-rf-checkout.md`](../../../docs/runbooks/first-rf-checkout.md),
then repeat after any antenna change.

## Preconditions

- [ ] SDR rail on (`aiov2_ctl SDR on`), `rtl_test -t` passes
- [ ] PPM figure measured and recorded
- [ ] Antenna and its position documented (photograph it)
- [ ] Note the time (UTC) and general location — noise varies by hour and neighbourhood

## Procedure

### 1. Wideband sweep

```bash
# 24 MHz – 1.7 GHz in 1 MHz bins, ~10 s integration
rtl_power -f 24M:1700M:1M -i 10 -e 20m -g 20 baseline-wide-$(date -u +%Y%m%dT%H%MZ).csv
```

### 2. Per-band sweeps at working gain

```bash
rtl_power -f 88M:108M:25k  -i 10 -e 5m -g 20 baseline-fm.csv
rtl_power -f 130M:150M:25k -i 10 -e 5m -g 30 baseline-vhf.csv
rtl_power -f 900M:930M:25k -i 10 -e 5m -g 30 baseline-ism.csv
rtl_power -f 1085M:1095M:10k -i 10 -e 5m -g 40 baseline-adsb.csv
```

### 3. Gain sweep at one quiet frequency

Pick a frequency with no obvious occupant and step the gain, recording where the floor starts
rising without the signal following:

```bash
for g in 0 10 20 30 40 49; do
  rtl_power -f 250M:251M:10k -i 5 -e 10s -g $g gain-$g.csv
done
```

That knee is this environment's useful gain ceiling — see
[`../learned/receiver-performance.md`](../learned/receiver-performance.md).

### 4. Identify the local offenders

From the wideband sweep, list the strongest carriers. These are what will desensitize the
receiver and what a filter would target.

## Record

Write a finding in `findings/` (template: [`../../_templates/finding.md`](../../_templates/finding.md)) containing:

- [ ] Antenna type, position, height; gain and sample-rate settings; PPM
- [ ] Noise floor per band (dB, as reported)
- [ ] Useful gain ceiling from step 3
- [ ] Top five strongest signals and their frequencies
- [ ] UTC timestamp and general location

Keep the CSVs out of git if large; summarize in the finding and note where the raw files live.

## Interpretation

- A floor that rises uniformly with gain past the knee = you are amplifying your own noise.
- A floor much higher in one band = local interferer; consider filtering or repositioning.
- Later sessions that deviate from this baseline point at the antenna or environment, not the
  software.
