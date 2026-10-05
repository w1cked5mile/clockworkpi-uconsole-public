# RTL-SDR limits — what this front end can and cannot do

The AIO V2's receiver is an RTL2832U + R860 with a TCXO and a 5 V bias tee. Knowing its ceiling
prevents chasing hardware problems that are actually design limits.

## Hard limits

| Limit | Value | Consequence |
|---|---|---|
| Resolution | 8-bit ADC | ~48 dB instantaneous dynamic range; strong signals desensitize weak ones |
| Sample rate | 2.4 MS/s max; **2.048 MS/s practical** here | CM4's shared USB 2.0 bus drops samples above that |
| Tuning range | ~24 MHz – 1.766 GHz (R860) | The "100 kHz" figure requires direct sampling, which this board does not implement |
| Direction | Receive only | No transmit path — the only transmitter on this build is the SX1262 |
| Front-end filtering | Minimal | Images and intermodulation from strong local transmitters |

## What the TCXO buys

Base-model RTL-SDRs drift by tens of ppm as they warm up, which breaks narrowband digital
decoding. A TCXO holds within a few ppm, making ADS-B, AIS, and narrow FSK work reliably. Still
measure the residual offset once (`rtl_test -p`, 10+ minutes from warm) and record it in
[`../configs/gain-and-sample-rate-profiles.md`](../configs/gain-and-sample-rate-profiles.md).

## What the bias tee buys — and costs

5 V on the SMA centre conductor powers an external LNA or an active GPS/ADS-B preamp. It also
shorts through any DC-grounded antenna, so it must stay **off** by default. Enable it deliberately,
and note on the antenna itself that it expects bias.

## Realistic expectations by task

| Task | Verdict |
|---|---|
| Broadcast FM, NOAA weather radio, airband | Comfortable |
| ADS-B at 1090 MHz | Good — antenna and height dominate the result |
| AIS, APRS, POCSAG, narrow FSK telemetry | Works with adequate signal |
| Weather satellites (137 MHz APT/LRPT) | Works with the right antenna and a pass prediction |
| Wideband survey above 2 MHz at once | Not possible — sweep instead of capturing |
| HF (below 24 MHz) | Out of scope without an upconverter |
| Transmitting anything | Not possible |
| Simultaneous multi-band monitoring | Not possible — one tuner, one band at a time |

## When the limit is the answer

Symptoms that are the hardware, not a misconfiguration:

- Weak signals vanish when a strong one appears → 8-bit dynamic range.
- Decoders work intermittently at 2.4 MS/s → USB sample loss; drop to 2.048 MS/s.
- Signals appear at implausible frequencies → images from front-end overload; reduce gain or filter.

When a task genuinely exceeds these, the comparison of what a purpose-built radio adds is in
[`aio-v2-vs-hackrf.md`](aio-v2-vs-hackrf.md).
