---
id: LAB-06
title: Keep watch — first packet
themed_title: Sea trial · Listening watch
mode: guided
est_minutes: 10
requires: {rails: [LORA], services: [meshtasticd]}
transmits: false
world: "Another Meshtastic node on SCMesh within range. The local mesh has been quiet; the owner's Heltec V3 on SCMesh is the reliable way to satisfy this."
steps:
  - id: dry-run
    text: 'Check the first-packet alert without waiting. Run printf ''num_packets_tx=1, num_packets_rx=2, num_packets_rx_bad=0\n'' | ALERT_DRY_RUN=1 ~/.local/bin/meshtastic-first-packet-alert --stdin and paste the output.'
    check: {type: paste, parser: regex, pattern: '^ALERT: Meshtastic: first packet received', min_matches: 1}
  - id: heard
    text: "Receive a packet from another node — any kind, not only a text message. This completes by itself when one arrives."
    check: {type: computed, fn: rise, path: mesh.rx_packets, op: gte, value: 1}
    world_wait: true
  - id: report
    text: "Read the packet's signal report (on this page, or the Mesh station) and write down the SNR and RSSI in a note."
    check: {type: attest, prompt: "I noted the SNR and RSSI and what they mean."}
  - id: finding
    text: "File a finding: use Copy as finding on your note and save it in the repo on Fancy as knowledge/mesh-networks/findings/<date>-first-packet.md (date as YYYY-MM-DD, UTC). Record which node, its SNR and RSSI, and hops. Grid square only, never coordinates."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/mesh-networks/findings/*.md", pattern: '^# Finding:', min: 1, fresh: true}
restore: []
evidence: [mesh.rx_packets, mesh.rx_nodes, mesh.last_rx_snr, mesh.last_rx_rssi]
---

This lab sends nothing itself, but meshtasticd may still beacon and relay on its own while the
LORA rail is on. The packet count is since webdash last started, so the lab counts only packets
that arrive after the step begins.
