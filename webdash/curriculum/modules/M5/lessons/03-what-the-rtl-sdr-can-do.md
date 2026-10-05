---
id: M5.limits
title: What the RTL-SDR can and cannot do
est_minutes: 20
---

Every capture you plan is bounded by the front end. This receiver is a **receive-only** RTL-SDR: it
tunes roughly 24 MHz to 1.766 GHz, samples up to about 2.4 MS/s (2.048 MS/s is the safe ceiling on
the CM4's USB), and never transmits. Knowing the hard edges keeps you from planning a capture the
hardware cannot make.

@ref knowledge/sdr/learned/rtl-sdr-limits.md#hard-limits

What that means task by task — where the RTL-SDR is enough, and where it is not:

@ref knowledge/sdr/learned/rtl-sdr-limits.md#realistic-expectations-by-task

When a signal is out of range (HF below the tuner, a mode too wide for 2 MHz), the limit is the
answer — you name it and move on rather than fighting the hardware.

You drive the receiver with a small **SDR toolchain**, each tool for one job: `rtl_test` checks the
device and its calibration, `rtl_power` sweeps power across a band, `rtl_fm` demodulates one channel
to audio, and `rtl_sdr` writes raw IQ to a file (see `software/sdr-stack.md`). The three labs use
each in turn — knowing which does what is half of using an SDR.
