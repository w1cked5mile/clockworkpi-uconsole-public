---
id: M7.ble
title: "Bluetooth LE: three channels, no connection"
est_minutes: 15
glossary: [ble-advertisement, mac-randomization]
---

A Bluetooth LE device that wants to be found **advertises**: it sends a short packet on three
fixed channels, again and again, without waiting for anyone.

@ref knowledge/wardriving/learned/ble-passive-observation.md#advertising-and-channels

Fancy has two Bluetooth radios, with separate jobs. The onboard one (`hci0`, a Cypress chip on
the CM4, Bluetooth 5.0, on a serial link) is for Fancy's own use: its paired keyboard, mouse and
other devices. Recon uses the AC1200's own Bluetooth controller (on USB), which arrived and is
installed — it comes up as `hci1`, verified 2026-09-30 (its Bluetooth 5.2 version is still a vendor
claim). Both run under BlueZ 5.82. A controller listens on one
advertising channel at a time, and hears only legacy advertisements with the commands used here.

## Whose address is it?

Every advertisement carries the sender's address. Most phones never advertise their real one:

@ref knowledge/wardriving/learned/ble-passive-observation.md#address-types-and-randomisation

So a count of Bluetooth addresses is a count of addresses. A phone that stays nearby for an hour
can appear as four; a device busy in a connection may stop advertising and not appear at all. The
next lesson counts them on Fancy, and the finding says the count overstates devices.
