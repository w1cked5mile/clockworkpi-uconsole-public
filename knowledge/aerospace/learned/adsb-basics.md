# ADS-B basics

The easiest high-value decode on this platform: aircraft broadcast their own position, in the
clear, on a single frequency.

## The signal

| Property | Value |
|---|---|
| Frequency | 1090 MHz (1090ES — Extended Squitter) |
| Modulation | Pulse position modulation, 1 Mbit/s |
| Frame length | 56 or 112 bits (~64 or ~120 µs) |
| Polarization | Vertical |
| Rate | Position roughly twice per second per aircraft |

A parallel 978 MHz UAT link carries general aviation traffic in US airspace — receivable with the
same hardware, different decoder settings.

## Message types worth knowing

| Downlink Format | Contents |
|---|---|
| DF17 | ADS-B from a Mode S transponder — identity, position, velocity |
| DF18 | ADS-B from non-transponder sources (TIS-B/ADS-R relays) |
| DF11 | All-call reply — acquisition |
| DF4 / DF5 / DF20 / DF21 | Mode S surveillance replies (altitude/identity), interrogation-driven |

Within DF17, the *type code* selects the payload: identification (callsign), airborne position,
surface position, velocity.

## CPR — why position takes two messages

Positions use Compact Position Reporting, which sends latitude/longitude in alternating **even**
and **odd** encodings. A decoder needs one of each within a short window to resolve an
unambiguous global position; afterwards it can track locally from single messages. This is why a
new aircraft appears as "seen" before it appears "positioned", and why message counts always
exceed position counts.

## Range and the horizon

Reception is line-of-sight limited:

```
radio horizon (km) ≈ 4.12 × (√h_receiver_m + √h_aircraft_m)
```

An aircraft at 10 km altitude with a receiver at 10 m: ≈ 425 km theoretical. Real results are
lower — terrain, buildings, antenna pattern, and the 8-bit dynamic-range limit of the RTL-SDR.
150–250 km with a good outdoor antenna is a solid result; 30–80 km indoors is typical.

## What improves results, in order

1. **Antenna** — a purpose-built 1090 MHz collinear or ¼-wave with radials, correctly polarized.
2. **Height and clear view** — more than any electronic change.
3. **Short, low-loss feedline** — loss at 1 GHz is real.
4. **Gain tuning** — too much gain overloads and *reduces* message rate; sweep it and keep the best.
5. **A 1090 MHz filter or LNA** — only if strong out-of-band transmitters are present.

## MLAT

Multilateration derives positions for aircraft that transmit Mode S but not ADS-B position, by
comparing arrival times across several receivers. It requires feeding a network and an accurate
clock; it is a network capability, not a local decode.

## Legality

ADS-B is an unencrypted broadcast intended for public reception — receiving, decoding, and
displaying it is standard practice. Feeding aggregators is optional and shares your receiver's
location.

Runbook: [`../runbooks/adsb-receive-tar1090.md`](../runbooks/adsb-receive-tar1090.md).
