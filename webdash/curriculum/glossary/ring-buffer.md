---
id: ring-buffer
term: Ring buffer
tooltip: A capture that writes a fixed set of fixed-size files and overwrites the oldest once they fill.
good_bad: "Good for leaving a capture running for an intermittent fault — disk can't run away. The cost is history: only the most recent window is kept."
try_this: "Leave a capture running and watch ~/labs/tshark: the segment count stops growing once the ring is full."
learn_more: "#/learn/m/M14"
live: tshark.segment_kb
live_prompt: "The newest ring segment is this big right now — is the ring turning over fast enough to hold the moment you care about?"
example: 420
---

Fancy's tap defaults to about 10 files of ~10 MB, so roughly 100 MB at most, in `~/labs/tshark`. It
can never fill the SD card. The tap reads only the newest segment to build its summary, which keeps
the cost low on the Pi. On a busy link the ring may only hold the last minute or two — make the
files bigger, or the capture filter narrower, when you need to keep more of the window around a rare
event.
