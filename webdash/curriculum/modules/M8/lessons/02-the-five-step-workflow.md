---
id: M8.workflow
title: The five-step identification workflow
est_minutes: 25
---

Identifying a signal is a discipline, not a guess. The workflow keeps you honest: you describe what
you actually see before you theorize about what it is, then narrow it down. Start by recording the
observables - frequency, bandwidth, timing, shape - before naming anything:

@ref knowledge/rf-fundamentals/learned/signal-identification-workflow.md#1-record-the-observables-before-theorizing

The band allocation narrows the field faster than any other single clue - what is *legal* and
expected on that frequency:

@ref knowledge/rf-fundamentals/learned/signal-identification-workflow.md#2-check-the-allocation

Then compare against a known reference (the sigidwiki catalogue, or a signal you already trust like
NOAA Weather Radio):

@ref knowledge/rf-fundamentals/learned/signal-identification-workflow.md#3-compare-against-a-reference

Step 4 is to confirm with a decoder *within limits*: for an open standard (ADS-B, AIS, APRS, a
weather satellite) a decode that locks is strong evidence, though a decode that fails does not
disprove your guess. **If the candidate is encrypted or a protected private communication, stop at
classification** — decoding or divulging its contents is off-limits under the ECPA. Finally, log it,
using the signal-ID worksheet:

@ref knowledge/rf-fundamentals/learned/signal-identification-workflow.md#5-log-it
