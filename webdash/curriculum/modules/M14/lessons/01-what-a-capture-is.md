---
id: M14.capture-basics
title: What a capture is, the two filters, and the ring buffer
est_minutes: 20
glossary: [capture-filter, ring-buffer]
---

A capture is a recording of the frames crossing one interface — Fancy copies what it already
receives, and sends nothing to make it happen. That is what lets the tap watch a link that is
misbehaving without changing the link.

@ref docs/reference/platform-basics/packet-capture.md#what-a-capture-is

The single most common beginner mistake is to confuse the two filters. One decides what is
**saved**; the other decides what is **shown**. Only one of them loses data you cannot get back.

@ref docs/reference/platform-basics/packet-capture.md#capture-filters-and-display-filters

Finally, the mechanism that lets you leave a capture running for an intermittent fault without
filling the SD card: the ring buffer. Its disk use is bounded no matter how long it runs; what it
trades away is history.

@ref docs/reference/platform-basics/packet-capture.md#the-ring-buffer
