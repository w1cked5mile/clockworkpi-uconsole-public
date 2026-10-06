---
id: capture-filter
term: Capture filter (vs display filter)
tooltip: A BPF rule applied before recording that decides what is written to disk; a display filter decides only what is shown afterward.
good_bad: "A capture filter keeps the ring pointed at the traffic that stalls. But what it drops is never saved — unlike a display filter, which only hides packets you can bring back by widening it."
try_this: "On the panel, start a capture with the filter tcp, then one with no filter, and compare the protocol mix."
learn_more: "#/learn/m/M14"
---

Two filters, two different times. A **capture filter** (the panel's filter box → `dumpcap -f`) uses
BPF syntax — `host 192.0.2.1`, `port 53`, `tcp`, `not arp` — and is cheap, because the kernel drops
the rest before it reaches the recorder. A **display filter** uses Wireshark's richer syntax
(`tcp.analysis.retransmission`) and only hides packets when you read the file back. Rule of thumb:
capture broadly and filter narrowly on display — unless the link is so busy that an unfiltered
capture churns the ring too fast to hold the moment you care about.
