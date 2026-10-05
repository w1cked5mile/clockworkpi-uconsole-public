---
id: M4.packets
title: Reading a signal report
est_minutes: 35
glossary: [snr, rssi]
---

@ref knowledge/rf-fundamentals/learned/db-and-link-budget.md#noise-floor-and-snr

@ref knowledge/mesh-networks/learned/reading-packets.md#rssi-and-snr-are-different-questions

@ref knowledge/mesh-networks/learned/reading-packets.md#why-snr-can-be-negative-and-still-decode

@ref knowledge/mesh-networks/learned/reading-packets.md#diagnosing-with-the-two-numbers

Since webdash started, Fancy has heard {live:mesh.rx_packets} packets from {live:mesh.rx_nodes}
other nodes; the last one {live:mesh.last_rx_ts} at SNR {live:mesh.last_rx_snr} dB, RSSI
{live:mesh.last_rx_rssi} dBm.

@ref knowledge/mesh-networks/learned/reading-packets.md#hops-and-the-nodedb
