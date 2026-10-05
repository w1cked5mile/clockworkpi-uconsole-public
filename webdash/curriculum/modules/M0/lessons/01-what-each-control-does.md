---
id: M0.controls
title: What each control does
est_minutes: 10
glossary: [rail]
---

Fancy is a ClockworkPi uConsole with an **AIO V2** board — the add-on radio board — carrying four
radios: a GPS receiver, a **LoRa** radio (long-range, low-power, for the Meshtastic mesh), an
**SDR** (software-defined radio: a wideband receiver, used for aircraft) and a real-time clock.
The dashboard shows what they are doing.

Almost everything on the dashboard only reads. Three controls need care:

| Control | Where | What it does |
|---|---|---|
| Rail switch (GPS, LORA, SDR, USB) | Each station, and the Power view | Turns power to one radio on or off. Switching **LORA** on also starts the mesh radio transmitting on its own (see below). The other rails transmit nothing |
| **Send** (mesh messages) | Mesh station | **Transmits** a text message on 902–928 MHz (megahertz) |
| Show coordinates | GPS station | Read-only — it reveals your precise position on this page, once. Handle with care: coordinates never go in the repo |

Right now the rails read: GPS {live:aiov2.rails.GPS.on}, LORA {live:aiov2.rails.LORA.on},
SDR {live:aiov2.rails.SDR.on}, USB {live:aiov2.rails.USB.on}.

**While the LORA rail is on, Fancy transmits now and then even if you never press Send.** The
mesh software (meshtasticd, in the CLIENT role) announces the node, and relays packets it hears
from other nodes. That is normal for a mesh node, and it is licence-free under FCC Part 15.

The LoRa chip (an SX1262) is the only radio the dashboard can make transmit. Fancy's Wi-Fi and
Bluetooth transmit only as ordinary network links, and the Wi-Fi survey puts its adapter in
monitor mode, which only receives.

> **Rail off is not a fault.** With the SDR rail off, the aircraft decoder (readsb) has nothing to
> open and restarts in a loop. That is this build's normal resting state.
