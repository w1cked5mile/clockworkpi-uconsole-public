# First RF checkout

First light for each radio, in an order where every step proves one thing. Run after
[`software-install.md`](software-install.md) and alongside
[`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md) section 3.

Rules for the session: **antenna attached before any rail is enabled**, one radio at a time
(they contend for USB and SPI), and every result written down — a first-light session that
produces no notes has to be repeated.

## 0. Preflight

- [ ] Antennas connected: SDR, LoRa (915 MHz), GPS
- [ ] Outdoors or by a window for GPS/ADS-B
- [ ] `aiov2_ctl --status` — record starting rail state
- [ ] Battery charged, or on external power (RF work is the heaviest draw in the budget)

## 1. SDR — is the receiver alive?

```bash
aiov2_ctl SDR on
rtl_test -t                    # device + tuner
rtl_test -s 2048000 -d 0       # 30 s, watch for dropped samples
```

Pass: `Found 1 device(s)`, tuner `R860`, no `usb_claim_interface error -6`, no sample loss.
Fail on `-6` → apply the DVB blacklist ([`../../configs/modprobe.d/blacklist-rtl-dvb.conf`](../../configs/modprobe.d/blacklist-rtl-dvb.conf)) and replug the rail.

## 2. SDR — is the antenna path real?

Tune broadcast FM in SDR++ (88–108 MHz, WFM, manual gain). A local station should be obvious.

Then NOAA weather radio (162.400–162.550 MHz, NFM) — an always-on transmitter is a better antenna
test than FM because it is weaker and narrower.

- [ ] Note the strongest station and its S-level/noise floor as a baseline to compare against
      after antenna changes.

## 3. SDR — calibration

```bash
rtl_test -p                    # 10+ minutes, warm
```

- [ ] Record PPM in `knowledge/sdr/configs/`. Every later frequency measurement inherits it.

## 4. ADS-B — first decode

Swap to the 1090 MHz antenna, start the decoder, open tar1090.

- [ ] Aircraft visible within a few minutes → the receive chain works end to end.
- [ ] Log message rate and max range as a finding in `knowledge/aerospace/findings/`.

Detail: [`../../software/adsb-tar1090.md`](../../software/adsb-tar1090.md).

## 5. GPS — fix

```bash
aiov2_ctl GPS on
stty -F /dev/serial0 9600; timeout 10 cat /dev/serial0      # raw NMEA (not /dev/ttyAMA0 -- see software/gps.md)
cgps -s                                                      # via gpsd
```

- [ ] 3D fix with ≥4 satellites. Cold start under clear sky: seconds to minutes.
- [ ] Then `aiov2_ctl --sync-rtc` once system time is correct.

Silence → rail off, `console=serial0` still in `cmdline.txt`, or wrong baud.
Detail: [`../../software/gps.md`](../../software/gps.md).

## 6. LoRa — node up

```bash
aiov2_ctl LORA on
ls /dev/spidev1.*              # spidev1.0 must exist
meshtastic --info              # SX1262 detected, region US
```

- [ ] Message round trip with a second node (required — a single node proves nothing).

Detail: [`../../software/meshtastic.md`](../../software/meshtastic.md).

## 7. Power characterization

With each radio in turn, record `aiov2_ctl --power`:

- [ ] Idle · SDR streaming · GPS acquiring · LoRa listening · all on
- [ ] Write the measured figures into [`../reference/power-budget.md`](../reference/power-budget.md)
      and delete the estimates they replace.

## 8. Close out

- [ ] Bring-up checklist rows marked pass/fail
- [ ] Failures in [`../logs/known-issues.md`](../logs/known-issues.md) with symptom, command, output
- [ ] Session notes in [`../logs/build-log.md`](../logs/build-log.md), captures as findings under
      `knowledge/<discipline>/findings/` using [`../../knowledge/_templates/signal-id.md`](../../knowledge/_templates/signal-id.md)
- [ ] Baseline image taken once everything passes ([`backup-and-restore.md`](backup-and-restore.md))

## Legal note

Everything above is **receive-only** except the Meshtastic step, which transmits in the license-free
US 902–928 MHz ISM band within Part 15 limits. Amateur-band transmission requires a license. See
[`../../knowledge/README.md`](../../knowledge/README.md).
