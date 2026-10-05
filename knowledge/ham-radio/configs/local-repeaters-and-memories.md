# Local repeaters and receive memories

Working list for VHF/UHF monitoring. Populate from https://www.repeaterbook.com/ and confirm each
entry by actually hearing it — a directory listing is a claim, a decode is evidence.

## 2 m repeaters (144–148 MHz)

| Output freq | Offset | Tone (PL) | Call sign | Location | Heard? (UTC) | Notes |
|---|---|---|---|---|---|---|
| | −600 kHz | | | | | |

Listen on the **output** frequency. Input and tone matter only for transmitting, which requires a
license and hardware this build does not have.

## 70 cm repeaters (420–450 MHz)

| Output freq | Offset | Tone (PL) | Call sign | Location | Heard? (UTC) | Notes |
|---|---|---|---|---|---|---|
| | −5 MHz | | | | | |

## Fixed receive memories

| Frequency | Purpose |
|---|---|
| 146.520 MHz | 2 m national FM simplex calling |
| 446.000 MHz | 70 cm national FM simplex calling |
| 144.390 MHz | APRS (North America) |
| 144.174 MHz | FT8 (2 m) |
| 50.313 MHz | FT8 (6 m) |
| 145.825 MHz | ISS APRS digipeater |
| 145.800 MHz | ISS SSTV / voice downlink |
| 436–437 MHz | FM amateur satellite downlinks (Doppler — retune during the pass) |

## Receive settings that worked

| Band | Antenna | Gain | Sample rate | PPM | Notes |
|---|---|---|---|---|---|
| 2 m | | | 24 kS/s (rtl_fm) | | |
| 70 cm | | | | | |

## Notes

- Repeater silence at midday is normal; evenings and commute hours are the test.
- Doppler on 70 cm satellite passes is several kHz — a fixed tune loses the signal mid-pass.
- Everything here is receive-only. Transmitting requires a license
  ([`../learned/licensing-path-us.md`](../learned/licensing-path-us.md)) and a transmitter this
  build does not have.
