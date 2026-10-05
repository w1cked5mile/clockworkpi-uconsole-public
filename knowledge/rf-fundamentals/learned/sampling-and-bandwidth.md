# Sampling, bandwidth, and IQ

What the numbers in an SDR interface actually mean, and why 2.048 MS/s is the practical ceiling on
this build.

## Nyquist, and why complex sampling changes it

Real sampling captures a bandwidth of **half** the sample rate. SDRs sample **complex (IQ)** —
two streams, in-phase and quadrature — which recovers the full rate as usable bandwidth:

```
usable bandwidth ≈ sample rate        (complex/IQ sampling)
```

At 2.048 MS/s the receiver sees roughly 2 MHz of spectrum at once, centred on the tuned
frequency. The centre itself often carries a DC spike — an artifact, not a signal; offset-tune to
move signals off it.

## Why IQ

A real-valued sample cannot distinguish a signal 10 kHz above the tuned frequency from one 10 kHz
below. The quadrature channel carries the phase information that resolves the ambiguity, which is
what allows one waterfall to show both sides of centre.

Data rate: **sample rate × 2 channels × bytes per sample**. At 2.048 MS/s with 8-bit IQ, that is
~4 MB/s — 240 MB per minute of raw capture. This is why `.iq`/`.cu8` files are gitignored.

## Decimation and filtering

Demodulators do not need the full capture bandwidth. The chain is:

```
tune → capture at S MS/s → filter to the signal's bandwidth → decimate → demodulate
```

Decimating by N reduces rate by N and improves SNR by roughly 10·log10(N) dB within the retained
bandwidth — narrower is more sensitive, which is why a 12.5 kHz NFM filter hears things a 200 kHz
WFM filter does not.

## Aliasing

Energy outside the captured bandwidth folds back in as false signals if the front-end filtering is
poor. Symptoms: a "signal" that moves when you retune, or an image mirrored about centre. The
RTL-SDR's front end is modest, so strong nearby transmitters (broadcast FM, pagers, LTE) can
produce images across the band — attenuate or filter rather than chase them.

## What this build can sustain

| Sample rate | Notes |
|---|---|
| 2.4 MS/s | RTL-SDR maximum; frequently lossy on CM4's shared USB 2.0 |
| **2.048 MS/s** | Practical working rate — verify with `rtl_test -s 2048000` |
| 1.024 MS/s | Comfortable for narrowband work, half the data |
| 250 kS/s | Fine for a single NFM/AM channel |

Dropped samples corrupt decoders silently — a decoder that "sometimes works" is often a sample-loss
problem, not a signal problem. Measure before blaming the antenna.

See also: [`receiver-performance.md`](receiver-performance.md),
[`../../sdr/configs/gain-and-sample-rate-profiles.md`](../../sdr/configs/gain-and-sample-rate-profiles.md).
