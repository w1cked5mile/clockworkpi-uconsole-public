# Runbook — first capture and calibration

Establish the device constants and produce one archived capture, so later work has a reference.

## Preconditions

- [ ] `aiov2_ctl SDR on`
- [ ] `rtl_test -t` reports the device and tuner `R860`
- [ ] DVB blacklist applied if `usb_claim_interface error -6` appeared
      ([`../../../configs/modprobe.d/blacklist-rtl-dvb.conf`](../../../configs/modprobe.d/blacklist-rtl-dvb.conf))
- [ ] Antenna appropriate to the target band, position photographed

## 1. Sample-rate ceiling

```bash
rtl_test -s 2400000 -d 0     # 30 s — note dropped samples
rtl_test -s 2048000 -d 0     # 30 s — expect zero or near-zero loss
```

Record the highest loss-free rate. Every later capture uses it or less.

## 2. PPM offset

```bash
rtl_test -p                  # let it run 10+ minutes from a warm start
```

Record the stabilized figure. Apply it in SDR++ and pass `-p "$PPM"` to command-line tools.

## 3. Confirm against a known transmitter

NOAA weather radio (162.400–162.550 MHz, NFM) is always on and narrow enough to expose frequency
error:

```bash
PPM=1                        # dongle frequency error, measured ≈ +1 ppm 2026-09-24 (checklist 3.6)
sudo systemctl stop readsb   # readsb holds the SDR; run `sudo systemctl start readsb` when done

rtl_fm -f 162.550M -M fm -s 24k -g 30 -p "$PPM" - | aplay -t raw -r 24000 -f S16_LE -c 1
```

Audio present and centred confirms tuning, gain, and the antenna path in one step.

## 4. Archive one raw capture

```bash
timeout 30 rtl_sdr -f 162550000 -s 250000 -g 30 -p "$PPM" \
  $(date -u +%Y%m%dT%H%MZ)_162550k_250k_g30_noaa-wx.cu8
ls -lh *.cu8      # ~15 MB for 30 s at 250 kS/s
```

Inspect it offline with `inspectrum` to confirm the file is real data and not a stream of noise.

## 5. Record

Copy [`../../_templates/finding.md`](../../_templates/finding.md) into `../findings/` with:

- [ ] Device constants from steps 1–2 (also into [`../configs/gain-and-sample-rate-profiles.md`](../configs/gain-and-sample-rate-profiles.md))
- [ ] Antenna, gain, sample rate, UTC time, general location
- [ ] Where the capture file is stored (it is gitignored — record the path and checksum)

## Notes

- Only one process can hold the dongle. Stop ADS-B decoders and SDR++ before running CLI tools.
- Data rate at 2.048 MS/s is ~4 MB/s — check free space before long captures.
- If results differ wildly between sessions, compare against
  [`../../rf-fundamentals/runbooks/noise-floor-baseline.md`](../../rf-fundamentals/runbooks/noise-floor-baseline.md)
  before changing settings.
