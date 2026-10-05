# Reading received Meshtastic packets — RSSI, SNR and the NodeDB

How to read the link-quality numbers on a received packet, and what the node list does and
doesn't tell you. Written 2026-09-24 for the learning platform (gap B5). Builds on
[`lora-modulation-and-airtime.md`](lora-modulation-and-airtime.md) and
[`../../rf-fundamentals/learned/db-and-link-budget.md`](../../rf-fundamentals/learned/db-and-link-budget.md).

## RSSI and SNR are different questions

| | RSSI | SNR |
|---|---|---|
| Stands for | Received signal strength indicator | Signal-to-noise ratio |
| Unit | dBm (absolute power) | dB (a ratio) |
| Measures | total power in the channel while the packet arrived — signal *plus* noise | how far the wanted signal sits above the noise |
| Answers | "how loud was it?" | "how cleanly could it be decoded?" |

RSSI is reported by the SX1262 against its own internal reference. It is useful for comparing
readings on the same node; as an absolute figure at the antenna connector it is uncalibrated
(*several dB either way, unverified on this build*).

## Why SNR can be negative and still decode

LoRa spreads each symbol over many chips (chirp spread spectrum), and the receiver's correlation
recovers a signal that sits *below* the noise floor. The deeper the spreading factor, the further
below: the SX1262 datasheet gives these demodulator limits.

| Spreading factor | Minimum SNR to decode (datasheet) |
|---|---|
| SF7 | −7.5 dB |
| SF8 | −10 dB |
| SF9 | −12.5 dB |
| SF10 | −15 dB |
| SF11 (LongFast) | −17.5 dB |
| SF12 | −20 dB |

So on this build's LongFast preset, a packet at −10 dB SNR is fine, and one near −17 dB is at
the edge. These are datasheet figures, *not measured on Fancy*.

## Diagnosing with the two numbers

Meshtastic only reports RSSI and SNR for packets it managed to demodulate, so "no numbers at
all" is a diagnosis too.

| What you see | Likely cause |
|---|---|
| strong RSSI, good SNR | healthy link |
| weak RSSI, poor SNR | range or obstruction — move higher, clear the path |
| strong RSSI, poor SNR | local interference raising the noise |
| **nothing at all** — no packets, no RSSI | **different frequency slot or preset**: the radio never demodulates the other node's packets |
| packets arrive with RSSI and SNR, but the content can't be read | **different channel key**: demodulated, but not decryptable |

The "nothing at all" row is what happened on this build on 2026-09-23: the node sat on
LongFast's 906.875 MHz slot while the owner's nodes were on SCMesh's 924.125 MHz, and LocalStats
showed `num_packets_rx=0` ([`../../../software/meshtastic.md`](../../../software/meshtastic.md)).

## Channel utilisation and airtime

Meshtastic reports two percentages:

- **Channel utilisation** — how much of the recent time the channel was busy with *anyone's*
  transmissions, as this node heard it.
- **Air util TX** — how much of the time *this node* was transmitting.

Firmware holds back its own non-essential traffic when channel utilisation is high. The exact
thresholds are *unverified here* — check the Meshtastic docs linked in [`../README.md`](../README.md).
On this build, `channel_utilization` read 0.0 during the quiet 2026-09-23 test, with the noise
floor at −93 dBm.

## Hops and the NodeDB

Every packet carries a hop limit (3 by default) that each rebroadcast decrements. "Hops away"
on a node entry is how many relays its last packet needed; 0 means heard directly.

The **NodeDB** is the node's list of every node it has ever learned about — including itself and
entries that haven't been heard for days. That is why webdash's `nodes_seen` includes Fancy
itself. For "what did I actually hear, and when", webdash has `mesh.rx_packets`, `rx_nodes` and
`last_rx_*`: counts and link quality of packets from other nodes since webdash started (no
payloads kept).

## On this build

| Reading | Value | Source |
|---|---|---|
| Traceroute SNR to the owner's Heltec V3 | 6.5 dB / 6.25 dB | 2026-09-23, desk range — not comparable to a 5 km link budget |
| Noise floor | −93 dBm | LocalStats, 2026-09-23 |
| Channel utilisation | 0.0 | same |
| Packets received from other nodes, 2026-09-24 evening | 0 (`num_packets_rx=0`) | meshtasticd journal — a quiet mesh, not a fault |
