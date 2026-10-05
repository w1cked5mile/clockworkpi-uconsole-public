# LoRa modulation, spreading factors, and airtime

Why LoRa reaches further than its power suggests, and what the settings cost.

## Chirp spread spectrum

LoRa encodes symbols as linear frequency sweeps (chirps) across the channel bandwidth. The
receiver correlates against the expected chirp, which yields **processing gain** — the ability to
decode signals below the noise floor. That is the whole trick: range is bought with time, not power.

## The three parameters

| Parameter | Range | Effect |
|---|---|---|
| Spreading factor (SF) | 7–12 | Each step up roughly doubles airtime and adds ~2.5 dB of link budget |
| Bandwidth (BW) | 125 / 250 / 500 kHz | Wider = faster and less sensitive |
| Coding rate (CR) | 4/5 – 4/8 | More redundancy, more airtime, better error tolerance |

Symbol time = 2^SF / BW. Sensitivity at 125 kHz runs roughly −124 dBm at SF7 to −137 dBm at SF12 (SX1262 datasheet).

## Meshtastic presets (US915)

| Preset | SF / BW | Relative airtime | Practical use |
|---|---|---|---|
| SHORT_FAST | low SF, wide BW | shortest | Dense urban mesh, many nodes |
| **LONG_FAST** | middle | moderate | **Default; what most local meshes use** |
| LONG_SLOW | high SF, narrow BW | long | Maximum range, very low throughput |

**Every node in a mesh must use the same preset and channel settings.** A mismatched node is
invisible, not merely slower — this is the most common "my node can't see anyone" cause.

## Airtime and duty cycle

Airtime for one small packet ranges from tens of milliseconds (SF7) to several seconds (SF12).
Consequences:

- A slow preset with chatty nodes saturates the channel; the mesh gets *worse* as nodes are added.
- US 902–928 MHz under FCC Part 15 has no EU-style 1 % duty-cycle rule. Meshtastic does not
  frequency-hop, and whether single-channel 250 kHz LoRa at this power fits §15.247 cleanly is
  debated; the AIO V2's certification is *unverified* (no FCC ID on record). Keep the region
  setting and **do not raise power or change channel settings** to "improve" range — raise the
  antenna instead.
- Position beacons and telemetry are the usual airtime hogs. Increase their interval before
  reaching for a slower preset.

## Range expectations

| Environment | LONG_FAST, 22 dBm, whip antennas |
|---|---|
| Dense urban, ground level | 0.5–2 km |
| Suburban with some line of sight | 2–8 km |
| Hilltop to hilltop, clear path | 20 km+ |

Antenna height dominates everything else — see
[`../../rf-fundamentals/learned/db-and-link-budget.md`](../../rf-fundamentals/learned/db-and-link-budget.md).

## On this build

The AIO V2's SX1262 covers 860–960 MHz, so region is a **software setting**, not a hardware SKU
(closed as a decision in [`../../../docs/logs/decisions.md`](../../../docs/logs/decisions.md)).
Region for your location is **US** (902–928 MHz). Attach the antenna before enabling the rail.
