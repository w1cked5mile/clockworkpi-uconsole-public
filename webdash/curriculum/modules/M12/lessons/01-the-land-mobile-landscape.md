---
id: M12.landscape
title: What lives on the land-mobile bands
est_minutes: 30
---

The land-mobile spectrum is the VHF and UHF range where short-range two-way radio lives:
public-safety dispatch, business radios, GMRS and FRS family radios, railroad, paging and the
marine VHF band. Unlike broadcast FM, these are mostly **narrowband** channels (12.5 kHz is the
common grid), they are **bursty** — keyed only when someone talks — and they are a mix of analog and
digital. Before surveying, it helps to know what *should* be there, because the allocation narrows a
classification faster than anything else (the M8 workflow's step 2).

This build has one anchor you can always trust on the band: NOAA Weather Radio, a continuous NFM
voice carrier that is on 24/7. It is the best antenna-and-gain test the VHF band offers, and it is
the control signal LAB-18 starts from. The nationwide reference frequencies — NOAA, marine Ch 16,
FRS/GMRS, MURS, railroad and paging — are collected in the local list:

@ref knowledge/communications/configs/monitoring-frequency-list.md#known-reference-frequencies-nationwide

A caution that belongs up front, before you ever tune: some of this spectrum carries personal data
in the clear. POCSAG and FLEX paging around 929–932 MHz is unencrypted and routinely carries medical
and personal messages. The reference doc flags it, and the reason is legal as much as technical:

@ref knowledge/communications/learned/digital-voice-and-trunking.md#other-things-living-in-this-spectrum

The maritime side adds marine VHF voice (156–162 MHz, with Ch 16 as the distress/calling channel you
monitor but never key) and AIS, the ship-position broadcast you will meet in lesson 3. At an inland
site like your location these are mostly a travel capability — worth knowing, expected to be quiet here.
