---
id: M0.rules
title: The three questions
est_minutes: 10
---

Three words matter here. **Receiving** is picking up a signal. **Observing** is noting that it
exists — its frequency, strength and shape. **Decoding** is turning it into content. In the US,
receiving and observing are broadly legal; decoding and transmitting are where the rules bite.
The repo's legal summary ends with three questions to ask whenever you are unsure:

@ref knowledge/rf-fundamentals/learned/us-spectrum-and-legal.md#when-in-doubt

On Fancy, the answers usually look like this:

- **ADS-B (aircraft), weather radio, broadcast FM** — intended for the public, so decoding is fine.
- **Encrypted or private traffic** — observe that it exists; never try to decode it. (The US
  Electronic Communications Privacy Act, ECPA, is the law behind this.)
- **The mesh radio** — transmits under FCC Part 15, the rules for licence-free devices, in the
  902–928 MHz ISM (industrial, scientific and medical) band. Whether this single-channel radio
  meets Part 15's detailed rules is debated and its certification is *unverified*, so never raise
  its power or change its channel settings. Transmitting on any other band would need an amateur
  licence.

The repo's wider responsible-use rules:

@ref knowledge/README.md#responsible--legal-use
