# Local monitoring frequency list

Working list of what is active in this area, built from survey rather than copied from the
internet. Fill it in from the sweeps in
[`../runbooks/scanner-monitoring-session.md`](../runbooks/scanner-monitoring-session.md).

## Confirmed active (fill in from survey)

| Frequency | Mode / bandwidth | Identified as | Signal strength | First heard (UTC) | Notes |
|---|---|---|---|---|---|
| 162.550 MHz | NFM 12.5 kHz | NOAA weather radio | | | Reference transmitter — always on |
| | | | | | |

## Known reference frequencies (nationwide)

| Service | Frequency | Notes |
|---|---|---|
| NOAA weather radio | 162.400 / 162.425 / 162.450 / 162.475 / 162.500 / 162.525 / 162.550 MHz | One of these is active in any US area |
| Marine VHF Ch 16 | 156.800 MHz | Distress/calling — monitor only |
| AIS | 161.975 / 162.025 MHz | Coastal only; inland sites hear nothing |
| FRS/GMRS | 462.5625–462.7250, 467.5625–467.7125 MHz | License-free (FRS) and licensed (GMRS) |
| MURS | 151.820–154.600 MHz (5 channels) | License-free |
| Railroad AAR | 160.215–161.565 MHz | Where track is nearby |
| POCSAG/FLEX paging | 929–932 MHz | Often carries personal data — classify only |

## Survey settings used

| Setting | Value |
|---|---|
| Antenna | |
| Gain | |
| PPM | |
| Sweep bins / integration | |
| Date, general location | |

## Discipline

- Record **classification**, not message content.
- Note when a channel is digital and encrypted; that observation is the endpoint, not a starting
  point for decryption.
- Verify state-level rules before recording or sharing unencrypted public-safety audio.

Legal framing: [`../../rf-fundamentals/learned/us-spectrum-and-legal.md`](../../rf-fundamentals/learned/us-spectrum-and-legal.md).
