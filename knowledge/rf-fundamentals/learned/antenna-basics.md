# Antenna basics

The antenna is the single largest determinant of what this build can hear. Everything downstream
— gain, decoder, software — can only work with what the antenna delivers.

## Resonance and length

An antenna is resonant when its electrical length matches a fraction of the wavelength:

```
λ (m) = 300 / f (MHz)
quarter wave (mm) ≈ 75000 / f (MHz)   then trim ~5% for end effect
```

| Band | Frequency | ¼-wave |
|---|---|---|
| Broadcast FM | 100 MHz | 750 mm |
| 2 m amateur / VHF | 145 MHz | 517 mm |
| NOAA APT satellites | 137 MHz | 547 mm |
| LoRa US915 | 915 MHz | 82 mm |
| ADS-B | 1090 MHz | 69 mm |
| GPS L1 | 1575 MHz | 48 mm |

A ¼-wave whip needs a **ground plane** (radials, a metal surface, or the device chassis). Without
one, the feedline coax becomes the missing half of the antenna and the pattern goes unpredictable.

## SWR and matching

Standing Wave Ratio measures how much power reflects back from a mismatch.

| SWR | Reflected power | Verdict |
|---|---|---|
| 1.0:1 | 0 % | perfect |
| 1.5:1 | 4 % | fine |
| 2.0:1 | 11 % | acceptable |
| 3.0:1+ | 25 %+ | fix it before transmitting |

For **receive only**, moderate mismatch costs a little sensitivity and is rarely fatal. For
**transmit** (LoRa), reflected power goes back into the PA — this is why transmitting with no
antenna can destroy the SX1262.

## Gain and pattern

Gain is not amplification; it is redirection. A 6 dBi antenna concentrates energy in some
directions by stealing it from others.

| Type | Gain | Pattern | Use here |
|---|---|---|---|
| ¼-wave whip | ~2 dBi | omni, doughnut | general portable use |
| Dipole (V-dipole) | ~2 dBi | omni-ish, broadside | NOAA APT satellites |
| Collinear | 5–8 dBi | omni, flattened | ADS-B fixed station |
| Yagi | 7–15 dBi | directional | chasing one signal/satellite |
| Patch (GPS) | ~3 dBic | hemispherical, RHCP | GNSS — needs sky view |

Higher gain on a handheld device is usually the wrong trade: a flattened pattern means aircraft
overhead or satellites near zenith fall into the null.

## Polarization

Mismatched polarization costs 20+ dB — more than any gain figure you would gain back.

| Signal | Polarization |
|---|---|
| Terrestrial FM/VHF/UHF voice | vertical (mobile) or horizontal (broadcast) |
| ADS-B | vertical |
| LoRa | vertical |
| GPS / weather satellites | circular (RHCP) — a linear antenna loses ~3 dB, unavoidable |

## Feedline

Loss rises with frequency and length. Thin 1.13 mm u.FL pigtails are acceptable at 10–15 cm and
wasteful at a metre. Every connector adds a few tenths of a dB; adapters stack up.

## Practical rules for this build

1. Correct band beats expensive.
2. Height and clear view beat gain — especially for ADS-B and GNSS.
3. Never transmit without an antenna attached.
4. Watch the AIO V2's 5 V bias tee: DC-shorted antennas short the supply
   ([`../../../docs/reference/antennas-and-rf-connectors.md`](../../../docs/reference/antennas-and-rf-connectors.md)).
