---
id: rssi
term: RSSI
tooltip: Received signal strength — the total power in the channel while a packet arrived, in dBm.
good_bad: "Useful for comparing readings on one node; as an absolute figure it's uncalibrated. Packets with RSSI but unreadable content point at a key mismatch; nothing arriving at all points at slot or preset."
try_this: Note the RSSI of a node, move Fancy a few metres, and compare.
learn_more: "#/learn/m/M4"
---

RSSI includes noise as well as the signal, so on its own it says how loud, not how clean. Read it
together with SNR. Meshtastic only reports it for packets it managed to demodulate.
