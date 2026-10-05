---
id: rail
term: Rail
tooltip: A power line to one radio on the AIO V2 board, switched on or off by a Pi control pin (GPIO).
good_bad: "On means the radio has power. Here GPS and LORA are set to boot on; SDR and USB boot off."
try_this: Switch the SDR rail on, then pick an application (ADS-B, hunt, or listen) in the SDR view — the rail only powers the tuner, it no longer starts ADS-B for you — then switch it back off.
learn_more: "#/learn/m/M1"
---

The AIO V2 board has four rails — GPS, LORA, SDR and USB — each fed through a switch that a
Raspberry Pi GPIO pin controls. When a rail is off, the radio behind it has no power at all, so
the service that uses it (gpsd, meshtasticd, readsb) sees nothing. Turning a rail off is the
cheapest way to save battery.
