# AIO V2's built-in SDR vs. a purpose-built transceiver

The AIO V2's onboard SDR is an RTL-SDR (RTL2832U + R860 tuner) — a receive-only
front end, not a general-purpose SDR. Knowing exactly where that boundary
sits matters before assuming this build covers a given task.

## Capability comparison

| | AIO V2 (RTL2832U + R860) | HackRF One |
|---|---|---|
| Frequency range | 100 kHz – 1.74 GHz | 1 MHz – 6 GHz |
| Instantaneous bandwidth | ~2.4–3.2 MHz | up to 20 MHz |
| TX capability | **None — RX only** | Yes (half-duplex) |
| ADC resolution | 8-bit | 8-bit |
| Form factor | Built into the handheld; always on you | Bare board — needs a host, case, power |

## What the built-in RTL-SDR covers well

- Passive spectrum monitoring and wardriving up to 1.74 GHz.
- ADS-B, AIS, POCSAG/pagers, most sub-1 GHz ISM traffic, FM/NOAA/weather-sat APT.
- Anything where "receive and decode" is the whole task — no reason to reach for more hardware.

## Where it falls short (upgrade triggers)

- **Needs TX** — replay/injection testing, RF fuzzing, jamming for an authorized
  assessment. The RTL-SDR physically cannot transmit; no config change fixes this.
- **Needs > 1.74 GHz** — 2.4/5 GHz Wi-Fi, many satellite downlinks, parts of the
  microwave ham bands.
- **Needs wider instantaneous bandwidth** — capturing a full 20 MHz Wi-Fi channel,
  or a frequency-hopping signal that outruns ~3 MHz of visible spectrum.
- **Needs full duplex** — simultaneous TX+RX (e.g. a relay attack, or a fuzzer
  that needs to see a response while transmitting).
- **Needs better sensitivity/dynamic range at the same frequencies** — the RTL-SDR's
  8-bit ADC and consumer-grade front end are the weak link before frequency
  coverage is.

## Upgrade path (staged from the AIO V2 baseline)

1. **Antenna/filter first.** A better antenna, a band-pass filter, or a bias-tee
   LNA is usually the cheapest capability multiplier and often the actual
   bottleneck — try this before buying new SDR hardware.
2. **Second RTL-SDR dongle** over the AIO V2's external USB port for RX diversity
   or basic TDOA/direction-finding. Cheapest way to add a second receive channel.
3. **HackRF One** for TX capability and coverage to 6 GHz. This is the natural
   next step for this build: plug it into the AIO V2's USB hub and the uConsole
   becomes its Linux host/display/logger, running off the console's own battery.
4. **PlutoSDR or LimeSDR Mini** if the work needs true full-duplex (simultaneous
   TX+RX) or a cleaner 12-bit ADC — a step up from HackRF, not a replacement for it.
5. **Airspy R2/Mini** only if the limitation is RX sensitivity/dynamic range
   rather than needing TX — it doesn't transmit, so it's a lateral move from
   the built-in RTL-SDR, not an upgrade, unless noise floor is the actual problem.
6. **bladeRF 2.0 micro** for the widest instantaneous bandwidth (61.44 MHz) and
   highest performance in this list — reach for it only once HackRF's 20 MHz is
   the demonstrated bottleneck.

## Hardware alternatives (reference)

| Device | Freq range | Max BW | Duplex | ADC | Approx. price | Best fit |
|---|---|---|---|---|---|---|
| RTL-SDR (AIO V2 built-in) | 100 kHz – 1.74 GHz | ~3.2 MHz | RX only | 8-bit | included | Passive monitoring baseline |
| RTL-SDR Blog V4 (standalone) | 500 kHz – 1.7 GHz | ~3.2 MHz | RX only | 8-bit | ~$35 | Cheap 2nd receiver / diversity |
| HackRF One | 1 MHz – 6 GHz | 20 MHz | Half-duplex TX/RX | 8-bit | ~$300 | TX testing, wideband capture, portable pentesting |
| Airspy R2 / Mini | 24 MHz – 1.8 GHz | 10 MHz | RX only | 12-bit | ~$170 / $99 | High-sensitivity RX, low noise floor |
| PlutoSDR (ADALM-PLUTO) | 325 MHz – 3.8 GHz (hackable ~70 MHz–6 GHz) | 20 MHz (56 MHz w/ mods) | Full-duplex TX/RX | 12-bit | ~$150 | Full-duplex experimentation, GNU Radio learning |
| LimeSDR Mini 2.0 | 10 MHz – 3.5 GHz | 30.72 MHz | Full-duplex TX/RX | 12-bit | ~$170 | MIMO-capable full-duplex, cellular/LTE research |
| bladeRF 2.0 micro | 47 MHz – 6 GHz | 61.44 MHz | Full-duplex TX/RX | 12-bit | ~$480–720 | Highest-performance full-duplex, widest BW here |
| YARD Stick One (CC1111) | Sub-1 GHz only | narrow (dedicated radio IC) | Half-duplex TX/RX | n/a | ~$100 | Sub-GHz OOK/FSK replay (garage doors, fobs) — simpler than an SDR for this one niche |

## Integration notes specific to this build

- Any external SDR plugs into the AIO V2's internal/external USB hub. CM4 caps
  out at USB 2.0 (~480 Mbit/s shared, ~240–280 Mbit/s practical) — a HackRF
  streaming 20 MHz of 8-bit IQ (~320 Mbit/s raw) or a LimeSDR/bladeRF at their
  full bandwidth can bump into that ceiling. USB 3.0 requires CM5 (see
  `docs/logs/known-issues.md` in the repo root).
- The AIO V2's internal SDR rail and the internal USB hub share power
  management via `aiov2_ctl`/GPIO — running the built-in RTL-SDR and an
  external SDR at once means checking the power budget, not just plugging in.
