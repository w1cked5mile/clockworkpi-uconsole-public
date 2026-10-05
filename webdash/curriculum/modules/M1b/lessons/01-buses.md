---
id: M1b.buses
title: Four buses, four chips
est_minutes: 20
---

A **bus** is the wiring and the set of rules the Pi uses to talk to a chip. The AIO V2's four
chips each use a different one — the GPS receiver, the LoRa radio, the SDR, and the **RTC**
(real-time clock, which keeps time while the Pi is off). Each bus is switched on at boot by an
**overlay**: a line in the boot settings file, `config.txt`.

@ref docs/reference/platform-basics/buses-and-rails.md#four-ways-to-talk-to-a-chip

Where each chip sits, and the device file Linux gives it (a **device node**, under `/dev`):

@ref docs/reference/platform-basics/buses-and-rails.md#where-each-aio-v2-device-sits

Which boot lines switch each bus on:

@ref docs/reference/platform-basics/device-tree.md#this-builds-lines
