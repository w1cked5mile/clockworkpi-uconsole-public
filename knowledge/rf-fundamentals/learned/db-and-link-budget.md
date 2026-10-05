# Decibels and link budgets

Why: every RF spec — gain, loss, sensitivity, noise — is quoted in dB. Getting comfortable with
the arithmetic removes most of the mystery from "will this work at that range?".

## The two units that matter

| Unit | Meaning |
|---|---|
| dB | A **ratio**, not a quantity. +3 dB ≈ 2× power, +10 dB = 10× power, −3 dB ≈ half. |
| dBm | Power **referenced to 1 mW**. 0 dBm = 1 mW, +30 dBm = 1 W, −100 dBm = 0.1 pW. |

Because they are logarithms, gains and losses **add** instead of multiplying:

```
received dBm = TX dBm + TX antenna dBi − path loss dB + RX antenna dBi − feedline loss dB
```

Numbers worth memorizing: +3 dB = ×2, +6 dB = ×4, +10 dB = ×10, +20 dB = ×100.

## Free-space path loss

```
FSPL(dB) = 20·log10(d_km) + 20·log10(f_MHz) + 32.45
```

| Link | Distance | Frequency | FSPL |
|---|---|---|---|
| LoRa across town | 5 km | 915 MHz | ≈ 105 dB |
| ADS-B aircraft | 100 km | 1090 MHz | ≈ 133 dB |
| ISS voice downlink | 500 km | 145 MHz | ≈ 130 dB |

Free space is the optimistic case. Terrain, buildings, and foliage add loss; at UHF, a single
wall can cost 5–15 dB.

## Worked example: Meshtastic at 5 km

```
TX power           +22 dBm   (SX1262 max)
TX antenna          +2 dBi   (typical whip)
FSPL @5 km/915MHz  −105 dB
RX antenna          +2 dBi
feedline/connector   −1 dB
                   ────────
received            −80 dBm
```

LoRa LongFast (SF11/250 kHz, the preset this build runs) has a sensitivity near −131.5 dBm
(*datasheet-derived*: −137 dBm is the SF12/125 kHz figure; sensitivity worsens ~2.5 dB per SF step
down and ~3 dB per bandwidth doubling), so this closes with ~51 dB of margin —
which is why LoRa works through obstacles that would kill an FM link at the same power.

## Noise floor and SNR

Thermal noise floor: **−174 dBm/Hz** at room temperature. For a given bandwidth:

```
noise floor dBm = −174 + 10·log10(BW_Hz) + noise figure dB
```

At 125 kHz with a 5 dB noise figure: −174 + 51 + 5 = **−118 dBm**. A signal must exceed that by
the mode's required SNR to decode — LoRa uniquely decodes *below* the noise floor thanks to
processing gain.

## Practical implications for this build

- Antenna and height buy more than any software setting. +6 dBi of real antenna gain beats every
  gain-slider adjustment on the RTL-SDR.
- Feedline matters at 1 GHz: thin u.FL pigtails are fine at 10 cm, costly at 2 m.
- "Sensitivity" figures assume a matched antenna. An unmatched or missing antenna can cost
  20+ dB — more than any preamp will recover.

See also: [`antenna-basics.md`](antenna-basics.md), [`receiver-performance.md`](receiver-performance.md).
