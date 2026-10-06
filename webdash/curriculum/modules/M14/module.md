---
id: M14
title: Reading a packet capture — the troubleshooting tap
themed_title: Passage 14 · Taking soundings
discipline: platform
station: system
prerequisites:
  - {id: M1b, soft: false}
sources:
  - docs/reference/platform-basics/packet-capture.md
  - docs/reference/webdash-architecture.md
  - docs/logs/known-issues.md
  - webdash/app/collectors/tshark.py
  - webdash/host-helpers/tshark-capture.sh
objectives:
  - "**Explain** what a passive capture records, and why Fancy's tap can watch a link without sending anything on it."
  - "**Distinguish** a capture filter from a display filter, and say which one loses data you can't get back."
  - "**Describe** the ring buffer's bound (file size × count) and the history-vs-disk trade it makes."
  - "**Interpret** a protocol mix and the tap's TCP retransmit / dup-ack / reset and ICMP-unreachable counts, and tell a weak-link loss pattern from a routing or endpoint fault."
  - "**Run** a short passive capture on one of Fancy's own interfaces and read the address-free summary as it fills."
est_minutes: 90
today:
  state: ready
  reason: "The capture tap (tshark-bridge on 127.0.0.1:8768, the dumpcap/tshark wrapper via scoped sudoers) was added and *verified end-to-end on Fancy 2026-10-06*: a capture on `wlan0` runs, `tshark.running` goes true, `tshark.stage` reaches `capturing`, `segment_packets` rises, and the findings and protocol mix populate. Note that LAB-23 step 1 (`tshark.state` = ok) only proves the bridge is reachable — the collector reports `ok` whenever its HTTP read succeeds, regardless of capture health; the real end-to-end proof is steps 2–4 (`tshark.running` true, `tshark.stage` = capturing, `segment_packets` rising). The lab captures on `wlan0`, Fancy's own link, so the findings it shows are real."
---

When a link stutters, guessing is slow and a capture is fast: it shows you exactly which frames
crossed the wire and which ones TCP had to send twice. This module is about reading that picture
from the dashboard's passive tap — what a capture is, the two kinds of filter, the ring buffer that
keeps it from filling the disk, and what the retransmit, dup-ack, reset and unreachable counts say
about a flaky link.

The tap only listens. It captures on Fancy's **own** interfaces to investigate the hang/dropout
hunt (`docs/logs/known-issues.md`): there is no transmit path, no injection and no probing, and the
summary the dashboard shows carries counts and protocol names only — never an address.
