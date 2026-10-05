---
id: M5.calibration
title: Calibration — is the receiver telling the truth?
est_minutes: 20
---

Before a capture means anything, you confirm the receiver is alive, keeping up, and tuned true. Three
`rtl_test` modes answer those: `-t` finds the device and tuner, `-s <rate>` checks it can sustain a
sample rate without dropping samples, and `-p` measures the crystal's frequency error in parts per
million (PPM).

@ref knowledge/sdr/runbooks/first-capture-and-calibration.md#2-ppm-offset

On this build the offset settles near **+1 ppm** once the dongle warms up — small, but 1 ppm is
146 Hz of error at 146 MHz, and a full kilohertz at 1 GHz, so it matters for narrowband work. You will measure it yourself
in LAB-09 and carry the figure (`PPM=1`) into later captures.
