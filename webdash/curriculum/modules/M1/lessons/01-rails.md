---
id: M1.rails
title: Rails — a switch per radio
est_minutes: 15
glossary: [rail]
---

Think of a house with a light switch per room. Each radio on the AIO V2 board has its own power
switch — a **rail** — and the Raspberry Pi flips it with a **GPIO** pin: a pin that software can
set high (on) or low (off). webdash's rail switches send that command through a small helper on
the host (the "bridge").

@ref docs/reference/platform-basics/buses-and-rails.md#what-a-rail-is

Right now: GPS {live:aiov2.rails.GPS.on}, LORA {live:aiov2.rails.LORA.on}, SDR
{live:aiov2.rails.SDR.on}, USB {live:aiov2.rails.USB.on}.
