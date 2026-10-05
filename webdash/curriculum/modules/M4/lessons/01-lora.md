---
id: M4.lora
title: Chirps below the noise
est_minutes: 35
---

**LoRa** ("long range") is the radio method Meshtastic uses. Two units first, because everything
after uses them:

@ref knowledge/rf-fundamentals/learned/db-and-link-budget.md#the-two-units-that-matter

@ref knowledge/mesh-networks/learned/lora-modulation-and-airtime.md#chirp-spread-spectrum

@ref knowledge/mesh-networks/learned/lora-modulation-and-airtime.md#the-three-parameters

@ref knowledge/mesh-networks/learned/lora-modulation-and-airtime.md#meshtastic-presets-us915

Fancy runs the **LONG_FAST** preset: spreading factor 11 at 250 kHz. Don't confuse the *preset*
LONG_FAST with the *channel name* LongFast in the next lesson — one sets how the radio
modulates, the other is just a name that happens to match.
