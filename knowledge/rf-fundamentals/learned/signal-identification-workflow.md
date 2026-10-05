# Signal identification workflow

A repeatable path from "what is that?" to a logged identification, or an honest "unknown".

## 1. Record the observables before theorizing

| Observable | How to get it | Why it matters |
|---|---|---|
| Centre frequency | Reading, corrected by your PPM figure | Band allocation narrows candidates fastest |
| Bandwidth | Measure against the span, edge to edge | Eliminates whole classes of mode |
| Timing | Continuous / periodic / bursty; measure the period | Strong fingerprint for digital systems |
| Shape | Carrier present? Symmetric? Sharp edges? | Separates analog from digital families |
| Strength & variability | Steady, fading, mobile? | Distinguishes local infrastructure from distant/mobile |
| Time and date | UTC | Many systems are schedule-driven |

## 2. Check the allocation

Frequency alone resolves most cases. US allocations worth memorizing for this platform:

| Range | Typical occupants |
|---|---|
| 88–108 MHz | Broadcast FM |
| 118–137 MHz | Airband AM voice |
| 137–138 MHz | Weather satellites (APT/LRPT) |
| 144–148 / 420–450 MHz | Amateur 2 m / 70 cm |
| 154–162 MHz | Public service, marine, NOAA weather radio |
| 162.025 / 161.975 MHz | AIS |
| 902–928 MHz | ISM — LoRa, telemetry, sensors |
| 1090 MHz | ADS-B |
| 1575.42 MHz | GPS L1 |

## 3. Compare against a reference

https://www.sigidwiki.com/ is the standard catalogue: search by frequency and bandwidth, then
compare the waterfall image. Match on **shape plus bandwidth plus timing**, not shape alone.

## 4. Confirm with a decoder — within limits

If the candidate is an open standard (ADS-B, AIS, APRS, ACARS, weather satellite, Meshtastic),
run the matching decoder; a successful decode is the confirmation. If the candidate is encrypted
or a protected private communication, **stop at classification** — see the legal note in
[`us-spectrum-and-legal.md`](us-spectrum-and-legal.md).

## 5. Log it

Copy [`../../_templates/signal-id.md`](../../_templates/signal-id.md) into the relevant
discipline's `findings/`. A finding with no gain setting, sample rate, antenna, or timestamp
cannot be reproduced — record them even when the identification fails.

State confidence honestly: **confirmed** (decoded), **probable** (matches a reference on multiple
observables), **unknown** (logged for later). These map to the signal-ID worksheet's `status` field —
confirmed = `identified`, probable = `candidate`, unknown = `unidentified` — the same three-level
scale under two names. Unknowns are useful; guesses recorded as facts are not.

## Common false positives

- **Images and aliases** — move with retuning; not real signals.
- **DC spike** at the centre of the capture — an artifact of the receiver.
- **Harmonics** of a strong local transmitter at exact integer multiples.
- **Device self-noise** — switching supplies, HDMI, USB 3.0 hash. Test by powering the suspect off.
