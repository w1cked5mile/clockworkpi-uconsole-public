---
id: M2.ports
title: Fancy's antenna ports, and transmit safety
est_minutes: 15
---

Knowing the math is not enough if you plug the wrong thing into the wrong port. On the AIO V2 the
**SDR bulkhead is receive-only**, and the port you manually key up for RF work is **ANT1**, the
SX1262's port (the SX1262 is Fancy's LoRa transceiver). The onboard Wi-Fi and Bluetooth radios
transmit too, but under their own stacks — the two rules below are about the ports you handle, and
both are hardware safety, not preference.

**Never key the SX1262 into an empty or badly matched port.** Reflected power goes straight back into
the power amplifier and can destroy it. Keep the LoRa antenna fitted on ANT1 whenever the LoRa rail
is enabled.

**The SDR bulkhead SMA carries a 5 V bias tee** — DC fed onto the coax to power an active antenna or
LNA (low-noise amplifier). A DC-shorted antenna on that port shorts the supply, so know which port it
is before you connect anything:

@ref docs/reference/antennas-and-rf-connectors.md#the-bias-tee

Being physically off the antenna strip, the SDR bulkhead is hard to confuse with the others by feel —
useful, because the transmit-port and bias-tee rules are the two ways to damage this hardware from the
antenna side.
