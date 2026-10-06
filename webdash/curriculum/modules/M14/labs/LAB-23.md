---
id: LAB-23
title: Take a sounding of the link
themed_title: Sea trial · Sounding the link
mode: guided
est_minutes: 25
requires: {rails: [], services: []}
transmits: false
world: "Ordinary background traffic on wlan0 (always present while Fancy is online), plus the traffic you generate in the capture window. No external station or band conditions are needed."
steps:
  - id: tap-up
    text: "Open the Packet capture panel on the dashboard. webdash can reach the capture bridge. If the panel shows the tap as unavailable, start it on Fancy with: systemctl --user start tshark-bridge (then re-check). The bridge listens only on 127.0.0.1:8768."
    check: {type: status, path: tshark.state, op: eq, value: ok}
    timeout_s: 30
  - id: start
    text: "Start a short, bounded capture from the panel on interface wlan0 (Fancy's own Wi-Fi link — the one with the known weak-signal stutter). Set Duration to 120 s; leave the filter box empty for the first run, or type tcp to narrow it. Keep the ring at its default (about 10 MB x 10). Then press Start capture."
    check: {type: status, path: tshark.running, op: eq, value: true}
    timeout_s: 60
  - id: capturing
    text: "The tap reports that it is capturing on wlan0. Nothing is transmitted to make this happen — dumpcap only copies the frames wlan0 already receives."
    check: {type: status, path: tshark.stage, op: eq, value: capturing}
    timeout_s: 30
  - id: packets
    text: 'Make Fancy use the link so the summary fills. In a terminal run: ping -c 20 "$(ip route | awk ''/^default/{print $3; exit}'')". Watch the summary packet count climb on the panel.'
    check: {type: computed, fn: rise, path: tshark.segment_packets, op: gte, value: 1}
    timeout_s: 60
  - id: protomix
    text: "Read the protocols list on the panel (the top protocols by packet count for the newest ring segment). Recognise the shape: mostly background and your pings on an idle link, or bulk TCP/QUIC if something is downloading."
    check: {type: attest, prompt: "I read the protocol list and recognised the shape of the traffic."}
  - id: anomalies
    text: "Read the four findings: tcp_retransmit, tcp_dup_ack, tcp_reset and icmp_unreachable. On a healthy link all four sit at or near zero. If wlan0 is on a weak signal, watch whether retransmits and dup-acks climb while you ping — that climb is loss on a marginal link, the symptom behind the wlan0 stutter."
    check: {type: attest, prompt: "I read the four findings and I know that zero of the three TCP signals is the healthy baseline, and that a climbing retransmit/dup-ack count points at loss on a weak link."}
  - id: stop
    text: "Let the capture run out its 120 s, or press Stop. The capture ends and nothing is left running."
    check: {type: status, path: tshark.running, op: eq, value: false}
    timeout_s: 150
  - id: pcap
    text: "The ring left a .pcapng on disk in ~/labs/tshark — this is the full capture, with addresses, for a Wireshark deep-dive on a workstation. Confirm it is there: ls -lh ~/labs/tshark/*.pcapng."
    check: {type: file, op: exists, path: "~/labs/tshark/*.pcapng"}
  - id: note
    text: "Write a short sounding note on Fancy and save it as ~/labs/tshark/<date>-sounding.md (date YYYY-MM-DD, UTC). Record the interface, the duration, the protocol shape, and the four finding counts. Counts and protocol names only — no addresses, no coordinates."
    check: {type: file, op: regex_count, path: "~/labs/tshark/*-sounding.md", pattern: '^#', min: 1, fresh: true}
  - id: pcap-discipline
    text: "The .pcapng contains addresses — that is why it is kept off the dashboard. It stays on Fancy, never goes in the repo, and you delete it when the investigation is done (rm ~/labs/tshark/fancy-wlan0-*.pcapng)."
    check: {type: attest, prompt: "I understand the .pcapng holds addresses, stays on Fancy, never goes in the repo, and gets deleted when the investigation is done."}
restore:
  - {type: status, path: tshark.running, op: eq, value: false}
evidence: [tshark.segment_packets, tshark.findings.tcp_retransmit, tshark.findings.tcp_dup_ack, tshark.findings.tcp_reset, tshark.findings.icmp_unreachable]
---

Receive only. This lab transmits nothing on any radio: `dumpcap` copies the frames `wlan0` already
receives to do its job, and the capture is on Fancy's **own** link. The pings in the `packets` step
are Fancy using its network normally — the capture itself stays passive.

The capture subsystem is a troubleshooting tap for the hang/dropout hunt
(`docs/logs/known-issues.md`), not an auditing tool: no injection, no deauth, no association, no
probing. The dashboard summary is address-free — counts, rates and protocol names only — so this
lab never puts a MAC or IP in front of you. The addresses live in the on-disk `.pcapng`, which is
yours to open in Wireshark on a workstation and yours to delete; it never enters the repo.

If the lab stops partway, put Fancy back: press **Stop** on the panel (or `systemctl --user
restart tshark-bridge` if it is wedged) so no capture is left running, and delete any `.pcapng`
the run wrote once you are done with it.
