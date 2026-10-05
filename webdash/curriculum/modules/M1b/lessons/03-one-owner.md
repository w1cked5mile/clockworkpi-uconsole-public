---
id: M1b.owners
title: One owner per device
est_minutes: 20
---

Only one program can use a device at a time. A few tools you'll meet: **rtl_test** is a test
program that opens the SDR; **DVB-T** is the Linux TV-tuner driver that would otherwise grab it;
TCP port 4403 is where meshtasticd talks to one client program.

@ref docs/reference/platform-basics/buses-and-rails.md#one-owner-per-device

@ref docs/reference/platform-basics/drivers-and-udev.md#why-the-dvb-t-driver-is-blacklisted

The SDR row is the one you'll hit first. Known fault, not your mistake — it's in the
known-issues log:

@ref docs/logs/known-issues.md#rtl_test-fails-with-usb_claim_interface-error--6-while-readsb-is-enabled
