---
id: M14.tcp-icmp-signals
title: What retransmits, dup-acks, resets and unreachables reveal
est_minutes: 20
glossary: [tcp-retransmission, tcp-dup-ack, tcp-reset, icmp-unreachable]
---

TCP hides packet loss from the application, so a link can be dropping badly while a download still
completes — slowly. The capture is where that hidden loss becomes visible. The tap counts four
signals, and reading them together tells a weak link apart from a broken route or a dead endpoint.

@ref docs/reference/platform-basics/packet-capture.md#tcp-retransmits-dup-acks-and-resets

@ref docs/reference/platform-basics/packet-capture.md#icmp-unreachable

The one number to remember: **zero of all three TCP signals is the healthy baseline.** A clean
capture is supposed to be boring. You are hunting for the counts that *climb* while the link is
associated but slow — that climb is the fingerprint of loss on a marginal link.
