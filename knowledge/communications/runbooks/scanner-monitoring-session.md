# Runbook — VHF/UHF monitoring session

Survey a local land-mobile band, identify what is there, and log it without capturing content.

## Preconditions

- [ ] `aiov2_ctl SDR on`; `rtl_test -t` passes
- [ ] Antenna appropriate to the band (VHF ~150 MHz: ¼-wave ≈ 500 mm; UHF ~460 MHz: ≈ 163 mm)
- [ ] PPM correction known
- [ ] Baseline noise floor recorded ([`../../rf-fundamentals/runbooks/noise-floor-baseline.md`](../../rf-fundamentals/runbooks/noise-floor-baseline.md))

## 1. Confirm the receiver with a known transmitter

NOAA weather radio is continuous and unmistakable:

```bash
PPM=1                        # dongle frequency error, measured ≈ +1 ppm 2026-09-24 (checklist 3.6)
sudo systemctl stop readsb   # readsb holds the SDR; run `sudo systemctl start readsb` when done

rtl_fm -f 162.550M -M fm -s 24k -g 30 -p "$PPM" - | aplay -t raw -r 24000 -f S16_LE -c 1
```

Audio present → antenna, gain, and tuning all work. No audio → fix that before surveying.

## 2. Sweep the band for activity

```bash
rtl_power -f 150M:165M:12.5k -i 10 -e 30m -g 30 vhf-survey.csv
rtl_power -f 450M:470M:12.5k -i 10 -e 30m -g 30 uhf-survey.csv
```

Longer integration finds intermittent users that a short sweep misses. Plot or sort the CSV to
rank occupied channels.

## 3. Classify each active channel

For each hit, record:

| Field | How |
|---|---|
| Frequency | corrected by PPM |
| Bandwidth | measured on the waterfall |
| Mode | analog NFM vs digital — see [`../learned/digital-voice-and-trunking.md`](../learned/digital-voice-and-trunking.md) |
| Pattern | continuous data (control channel), bursty voice, periodic telemetry |
| Strength | relative to the noise floor |

Cross-reference against https://www.sigidwiki.com/ and the FCC ULS for licensed users in the area.

## 4. Log the finding

In `../findings/` (template: [`../../_templates/finding.md`](../../_templates/finding.md)):

- [ ] Band swept, date/time UTC, general location, equipment and settings
- [ ] Table of active frequencies with bandwidth, mode, and classification
- [ ] Which are digital, and whether encrypted (an encrypted stream is identifiable as such
      without decoding it)

**Log the technical characterization, not message contents.**

## Boundaries

- Encrypted traffic: identify that it is encrypted, then stop.
- Paging: frequently carries personal and medical information — classify, do not store or divulge.
- Unencrypted public-safety audio: legality of listening varies by state; recording and divulging
  are separate questions. Verify before doing either.
- This build cannot transmit on any of these services and must not attempt to.

Framing: [`../../rf-fundamentals/learned/us-spectrum-and-legal.md`](../../rf-fundamentals/learned/us-spectrum-and-legal.md).
