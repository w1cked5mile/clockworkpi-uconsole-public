---
id: protocol-hierarchy
term: Protocol mix (hierarchy)
tooltip: What kinds of traffic are on the link, ranked by how many packets each protocol carried.
good_bad: "Read it for shape, not exact numbers. Mostly ARP and retransmission with little payload is a link trying and failing; bulk TCP or QUIC is a link simply busy."
try_this: "Capture for a minute on wlan0 and name the top three protocols on the panel."
learn_more: "#/learn/m/M14"
---

The first thing a capture tells you is *what kind* of traffic is crossing the link. Wireshark calls
it the protocol hierarchy; the tap reports the top eight protocols by packet count for the newest
ring segment. A healthy idle link is mostly background — ARP, DNS, mDNS/SSDP, a little TLS. The mix
also sanity-checks your filter: if you captured `port 53` and see anything but DNS, the filter is
not doing what you thought.
