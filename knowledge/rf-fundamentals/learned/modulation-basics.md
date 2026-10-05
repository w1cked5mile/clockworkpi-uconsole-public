# Modulation basics — and what each looks like on a waterfall

Identifying a signal starts with recognizing how it is modulated. This is the visual field guide.

## Analog

| Mode | Carries information in | Waterfall appearance | Typical bandwidth | Where |
|---|---|---|---|---|
| AM | Amplitude | Steady carrier line with symmetric sidebands | 6–10 kHz | Airband 118–137 MHz, shortwave |
| NFM | Frequency | Solid block, no centre carrier line, constant width | 12.5–25 kHz | VHF/UHF voice, NOAA weather radio |
| WFM | Frequency | Wide bright block, often with stereo/RDS subcarriers | 150–200 kHz | Broadcast FM 88–108 MHz |
| SSB | Frequency-shifted single sideband | Asymmetric smear on one side, no carrier | ~2.7 kHz | HF amateur (out of reach without an upconverter) |

## Digital

| Mode | Scheme | Appearance | Notes |
|---|---|---|---|
| OOK / ASK | Carrier on/off | Dashes at one frequency, gaps between | Remotes, sensors, 315/433/915 MHz ISM |
| FSK / GFSK | Two or more frequencies | Two parallel rails, or a fuzzy block | Telemetry, Bluetooth, many ISM devices |
| PSK | Phase | Flat block, indistinguishable from FSK by eye | Needs a decoder to tell apart |
| **LoRa (CSS)** | Chirp spread spectrum | Unmistakable diagonal sweeps repeating | 125/250/500 kHz, 902–928 MHz in US |
| ADS-B (PPM) | Pulse position | Very short bursts at 1090 MHz | 1 MHz wide, ~120 µs frames |

## What the waterfall tells you before any decoder

1. **Bandwidth** — measure it against the span; it eliminates most candidates immediately.
2. **Timing** — continuous, periodic bursts, or a single event? Periodicity is a strong fingerprint.
3. **Shape** — sharp edges suggest digital; sloped skirts suggest analog or poor filtering.
4. **Symmetry** — a centre carrier means AM-family; no carrier suggests FM/PSK/SSB.
5. **Frequency** — the band allocation narrows the field more than anything else.

Then compare against https://www.sigidwiki.com/ and log the result using
[`../../_templates/signal-id.md`](../../_templates/signal-id.md).

## Why LoRa is different

LoRa spreads each symbol across a wide chirp. Processing gain lets the receiver recover signals
**below** the noise floor, at the cost of throughput. Spreading factor trades range for airtime —
see [`../../mesh-networks/learned/lora-modulation-and-airtime.md`](../../mesh-networks/learned/lora-modulation-and-airtime.md).

## Legal boundary

Recognizing and classifying a signal is observation. **Decoding** protected, private, or encrypted
communications — and divulging their contents — is restricted in the US under the ECPA regardless
of whether the RF is receivable. Stick to open standards: ADS-B, AIS, APRS, broadcast, weather
satellites, and your own mesh traffic.
