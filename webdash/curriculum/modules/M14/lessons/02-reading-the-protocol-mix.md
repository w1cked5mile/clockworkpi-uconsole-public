---
id: M14.protocol-mix
title: Reading the protocol mix
est_minutes: 15
glossary: [protocol-hierarchy]
---

The first thing a capture tells you is *what kind* of traffic is on the link. The tap reports the
top protocols by packet count — you read it for shape, not exact numbers.

@ref docs/reference/platform-basics/packet-capture.md#reading-the-protocol-mix

On the dashboard this is the `protocols` list: the top eight protocol names with their packet
counts for the newest ring segment. A link that is mostly ARP and retransmission with little
payload is trying and failing; a link with bulk TCP or QUIC under load is simply busy.
