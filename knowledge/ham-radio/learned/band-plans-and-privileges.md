# Band plans — what is where

Reference for interpreting what the receiver hears. **Verify against the current ARRL band chart
and FCC Part 97 before transmitting** — segment boundaries and privileges change.

## VHF/UHF bands this build can receive well

### 2 m (144–148 MHz)

| Segment | Use |
|---|---|
| 144.000–144.100 | CW / EME |
| 144.100–144.275 | SSB weak signal (144.200 is the calling frequency) |
| 144.390 | **APRS** (North America) |
| 144.900–145.100 | Digital, packet |
| 145.100–145.500 | FM repeaters |
| 145.800–146.000 | **Satellite / ISS** |
| 146.400–147.600 | FM repeaters and simplex (146.520 is the national simplex calling frequency) |

### 70 cm (420–450 MHz)

| Segment | Use |
|---|---|
| 432.000–432.100 | CW / EME |
| 432.100 | SSB calling |
| 435.000–438.000 | **Satellite** |
| 440.000–450.000 | FM repeaters and simplex |

## Other bands within reach of the RTL-SDR

| Band | Range | Notes |
|---|---|---|
| 6 m | 50–54 MHz | Sporadic-E openings make it unpredictable and interesting |
| 1.25 m | 222–225 MHz | Regionally active |
| 23 cm | 1240–1300 MHz | Within the tuner's range; sparse activity |

## HF — out of scope on this hardware

The R860 tuner starts around 24 MHz, so 160 m through 12 m are unreachable without an upconverter
or a direct-sampling receiver. 10 m (28–29.7 MHz) is marginally within range.

## Repeaters

A repeater listens on one frequency and retransmits on another, separated by a standard offset:

| Band | Standard offset |
|---|---|
| 2 m | ±600 kHz |
| 70 cm | ±5 MHz |

Most require a CTCSS/PL tone on input; the **output** is what you listen to. Find local machines
and their offsets at https://www.repeaterbook.com/.

## Digital modes on VHF/UHF

| Mode | Where | Receivable here |
|---|---|---|
| APRS | 144.390 MHz | Yes — decode with `direwolf` or `multimon-ng` |
| FT8 | 50.313 / 144.174 MHz | Yes, with WSJT-X and accurate time |
| Packet | 145.010–145.090 | Yes |
| DMR / D-STAR / Fusion | repeater outputs | Yes, unencrypted amateur traffic |

## Rule of thumb

Receiving anywhere is fine. Transmitting requires a license, the correct band segment for your
class, and the mode permitted in that segment. The only transmitter on this build is the LoRa
radio in 902–928 MHz ISM, which is a Part 15 device, not an amateur one.
