---
id: M7.counts
title: Counts, not people
est_minutes: 20
glossary: [mac-randomization, oui]
---

A survey produces a list of addresses. It is tempting to read it as a list of devices, or of
people. It is neither.

@ref knowledge/wardriving/learned/wifi-capture-fundamentals.md#mac-randomization

How can you tell a made-up address from a real one? One bit:

@ref knowledge/wardriving/learned/80211-identifiers-and-regdom.md#reading-the-bit

Bluetooth LE has its own address scheme, covered in lesson 5 once advertising is introduced.

## A worked example

Kismet lists 40 client MAC addresses that sent probe requests during a 10-minute survey. How
many phones is that? **You can't tell.** One phone that rotates its probe address every few
minutes, or every scan, can appear as a dozen. Two of those "clients" might be the same laptop
before and after it joined its own network. The honest finding says "40 client addresses
observed, most locally administered (randomised); device count unknown".

## What an OUI match proves

The first three bytes of a real (globally administered) address are the maker's **OUI**. A
lookup tells you who registered those bytes — often a chip maker, not the brand on the box — not
what the device is, who owns it, or that it is the thing you think it is. Never look up a random
or locally administered address: its first bytes are noise.

## What goes in a finding

@ref knowledge/wardriving/learned/wifi-capture-fundamentals.md#privacy-and-handling

| In a finding | Never in a finding |
|---|---|
| UTC start and end times | SSIDs or network names |
| Grid square (or city), e.g. {live:gps.grid} | MAC or Bluetooth addresses, BSSIDs |
| Counts: networks, clients, advertisers | Any list of devices |
| Security mix as counts (WPA3 / WPA2 / WEP / open) | Anything about one household or person |
| Channel use on 1 / 6 / 11 | Coordinates, street names, addresses |
| Adapter, software, channels, hop rate | Screenshots of device lists |

The labs name the files plainly: `knowledge/wardriving/findings/<date>-wifi-survey.md` and
`<date>-ble-count.md`, dated in UTC. Once the Wi-Fi finding is written, the `.kismet` log is
deleted — it holds every address, and coordinates too.
