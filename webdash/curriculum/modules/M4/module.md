---
id: M4
title: LoRa and Meshtastic
themed_title: Passage 4 · Listening watch
discipline: mesh-networks
station: mesh
prerequisites:
  - {id: M1b, soft: false}
sources:
  - knowledge/rf-fundamentals/learned/db-and-link-budget.md
  - knowledge/mesh-networks/learned/lora-modulation-and-airtime.md
  - knowledge/mesh-networks/learned/meshtastic-architecture.md
  - knowledge/mesh-networks/learned/reading-packets.md
  - software/meshtastic.md
  - configs/meshtastic/us915.yaml
objectives:
  - "**Explain** why LoRa decodes below the noise floor, and what raising the spreading factor trades."
  - "**Verify** from the journal which frequency slot the node is on, and why the channel name decides it."
  - "**Interpret** RSSI and SNR on a received packet, and tell a slot or preset mismatch from a key mismatch."
  - "**State** who can read a message on the default channel, and what you must never change to get more range."
est_minutes: 140
today:
  state: ready
  reason: "The node is on SCMesh (924.125 MHz) and linked to the owner's Heltec V3 on 2026-09-23. The local mesh has been quiet, so the first-packet step waits for the world. Over-the-air send from webdash: not yet verified on Fancy."
---

The only radio the dashboard can make transmit. The labs here send nothing themselves — but
while the LORA rail is on, the mesh software beacons and relays on its own (CLIENT role). You
can see how often in `journalctl -u meshtasticd` (`num_packets_tx`).
