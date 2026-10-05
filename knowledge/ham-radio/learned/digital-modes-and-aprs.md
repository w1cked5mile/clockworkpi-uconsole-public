# APRS, FT8, and receive-only digital participation

Digital modes that this build can decode today, without a license and without a transmitter.

## APRS (144.390 MHz in North America)

Automatic Packet Reporting System: AX.25 packets carrying position, weather, telemetry, and short
messages, sent as 1200 baud AFSK over FM.

Decode chain:

```bash
PPM=1                        # dongle frequency error, measured ≈ +1 ppm 2026-09-24 (checklist 3.6)
sudo systemctl stop readsb   # readsb holds the SDR; run `sudo systemctl start readsb` when done
# uses: multimon-ng direwolf (installed 2026-09-24 via apt)

# via multimon-ng
rtl_fm -f 144.390M -M fm -s 22050 -g 35 -p "$PPM" - \
  | multimon-ng -t raw -a AFSK1200 -A -

# or direwolf, which also handles igating and beaconing (beaconing needs a license + transmitter)
direwolf -c direwolf.conf
```

What you will see: position beacons from mobiles and fixed stations, weather station reports,
digipeater paths, and occasional messages. Packets are unencrypted by design and already
aggregated publicly at aprs.fi — decoding them locally is an exercise, not surveillance.

Useful because it exercises the whole chain: antenna → FM demod → AFSK → AX.25 → structured data.

## FT8 and WSPR

Weak-signal modes designed to work below the noise floor with rigid timing.

| Mode | Purpose | Timing requirement |
|---|---|---|
| FT8 | Structured contacts | 15-second slots — system clock must be within ~1 second |
| WSPR | Propagation beacons | 2-minute slots |

On VHF, 144.174 MHz is the FT8 frequency; 6 m uses 50.313 MHz. Decode with WSJT-X. Accurate time
is mandatory, which is where NTP plus the AIO V2's RTC earns its place — a drifting clock produces
zero decodes and no error message.

Receive-only operators can report decodes to PSKReporter and WSPRnet, which is a genuine
contribution to propagation data and needs no license.

## Satellites and the ISS

| Target | Downlink | Notes |
|---|---|---|
| ISS APRS digipeater | 145.825 MHz | Packets relayed through the station |
| ISS SSTV events | 145.800 MHz | Periodic image transmissions — check schedules |
| SO-50 and similar FM birds | 436–437 MHz downlink | Single-channel FM; audible with a modest antenna |

Passes are short (5–10 minutes) and Doppler-shifted by several kHz on 70 cm — retune during the
pass or use tracking software. Predict with `gpredict` or n2yo.com.

## Practical starting order

1. APRS on 144.390 — always active, easy decode, immediate feedback.
2. Local repeater outputs — confirms the antenna and band.
3. FT8 on 144.174 — validates timing and weak-signal handling.
4. An ISS or FM satellite pass — hardest, most rewarding.

Each of these is receive-only. Transmitting on any of them requires a license
([`licensing-path-us.md`](licensing-path-us.md)) and hardware this build does not have.
