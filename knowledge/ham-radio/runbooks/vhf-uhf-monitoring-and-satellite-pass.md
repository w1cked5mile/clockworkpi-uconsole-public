# Runbook — VHF/UHF monitoring and a satellite pass

Two sessions that exercise the amateur bands receive-only: local repeaters and APRS first, then a
satellite pass once the ground-based path is proven.

## Session A — local repeaters and APRS

### Preconditions

- [ ] `aiov2_ctl SDR on`; `rtl_test -t` passes
- [ ] 2 m antenna (¼-wave ≈ 519 mm at 144.39 MHz, ~490–500 mm trimmed). On Fancy this is the
      telescopic whip, **maximum length unmeasured** and with **no ground plane** — expect several dB
      below a proper ¼-wave
- [ ] PPM known: **≈ +1 ppm**, measured 2026-09-24 — see below
- [ ] Local repeater list from https://www.repeaterbook.com/
- [ ] `readsb` stopped; it holds the SDR (`usb_claim_interface error -6` otherwise)

### Two terms before you start

**PPM (parts per million)** is how far off frequency the SDR's clock crystal runs. At 20 ppm, a
dongle tuned to 146.520 MHz actually listens about 2.9 kHz away (20 × 146.52 = 2,930 Hz). `-p`
tells `rtl_fm` how much to correct. A 2 m FM voice channel is 12.5–25 kHz wide, so small errors
mostly degrade audio; tens of ppm can push you partly off channel, and data modes like APRS suffer
first. This dongle measured **≈ +1 ppm** (checklist 3.6, 2026-09-24; see
[`../../sdr/configs/gain-and-sample-rate-profiles.md`](../../sdr/configs/gain-and-sample-rate-profiles.md)).
That's small: about 146 Hz at 146 MHz, so `PPM=1` and `PPM=0` both work.

**"Access" on RepeaterBook** is normally the repeater's **access tone**: a sub-audible CTCSS/PL
tone (e.g. `100.0`) or DCS code (e.g. `D023`) a radio must *transmit* to open the repeater. `CSQ`
means no tone is needed. It only matters for transmitting. Receive-only listening hears the
repeater's **output** frequency whether or not a tone is present, so set `REPEATER=` to the listed
output frequency, not the offset/input. (If the field shows words like "Open" or "Closed" instead
of a tone, it describes who may use the repeater.)

### Steps

```bash
PPM=1                        # dongle frequency error, measured ≈ +1 ppm 2026-09-24 (checklist 3.6)
sudo systemctl stop readsb   # readsb holds the SDR; run `sudo systemctl start readsb` when done
REPEATER=146.940M            # example only: a local repeater OUTPUT frequency from repeaterbook
# uses: multimon-ng (installed 2026-09-24 via apt)

# 1. National simplex calling frequency — usually quiet, confirms tuning
rtl_fm -f 146.520M -M fm -s 24k -g 35 -p "$PPM" - | aplay -t raw -r 24000 -f S16_LE -c 1

# 2. A local repeater OUTPUT frequency from repeaterbook
rtl_fm -f "$REPEATER" -M fm -s 24k -g 35 -p "$PPM" - | aplay -t raw -r 24000 -f S16_LE -c 1

# 3. APRS
rtl_fm -f 144.390M -M fm -s 22050 -g 35 -p "$PPM" - | multimon-ng -t raw -a AFSK1200 -A -
```

- [ ] At least one repeater heard (evenings and commute hours are most active)
- [ ] At least one APRS packet decoded — proves the full chain end to end

## Session B — satellite pass

### Preconditions

- [ ] Session A passed
- [ ] Pass predicted with `gpredict` or n2yo.com: AOS/LOS in UTC, maximum elevation, direction
- [ ] **Elevation ≥ 30°** for a first attempt
- [ ] Outdoors, clear sky, antenna free of obstructions
- [ ] Targets: ISS APRS 145.825 MHz, ISS SSTV 145.800 MHz, or an FM satellite downlink at 436–437 MHz.
      **Check the ISS packet frequency first:** it has run on 437.825 MHz and been off
      ([ARRL](https://www.arrl.org/news/iss-packet-digipeater-is-now-on-70-centimeters)). At 437.825
      MHz expect ±10 kHz Doppler — widen with `-s 48k` or retune

### Method

1. Start recording ~1 minute before AOS and run through LOS — decode afterwards.
2. Compensate Doppler: on 2 m it is small (~±3 kHz); on 70 cm it is several kHz and needs
   retuning during the pass or tracking software.
3. Do not change gain mid-pass.

```bash
PPM=${PPM:-1}; sudo systemctl stop readsb   # same setup as Session A, in case this is a new shell
timeout 900 rtl_fm -f 145.825M -M fm -s 22050 -g 35 -p "$PPM" - \
  | tee $(date -u +%Y%m%dT%H%MZ)_iss-aprs.raw \
  | multimon-ng -t raw -a AFSK1200 -A -
```

### Record

In `../findings/` (template: [`../../_templates/finding.md`](../../_templates/finding.md)):

- [ ] Target, frequency, UTC AOS/LOS, maximum elevation
- [ ] Antenna, gain, PPM, position (general location only)
- [ ] Result: packets decoded / audio heard / nothing, and at what point in the pass

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| Repeaters silent | Genuinely idle — verify with a known-busy machine at peak time before suspecting hardware |
| APRS audio but no decodes | Deviation/gain wrong, or PPM error; try 22050 Hz sample rate exactly |
| Satellite heard only at peak elevation | Antenna pattern or obstruction — normal at poor sites |
| Nothing at the predicted time | Stale TLE — refresh orbital elements |

## Legal

Everything here is **receive only**. Transmitting on amateur frequencies requires a license, and
this build has no amateur transmitter. See [`../learned/licensing-path-us.md`](../learned/licensing-path-us.md).
