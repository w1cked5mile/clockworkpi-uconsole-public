---
id: hdop
term: HDOP
tooltip: Horizontal dilution of precision — how good the satellite geometry is for a position fix.
good_bad: "In this repo's working bands: under 2 is good, 2–5 fair, above 5 poor."
try_this: After the GPS rail has been off, watch HDOP fall as more satellites are used.
learn_more: "#/learn/m/M3"
live: gps.hdop
live_prompt: "Right now GPS reports HDOP {value}. Is that position geometry good, fair or poor?"
example: "1.1"
---

HDOP is the multiplier that turns the receiver's ranging error into horizontal position error.
Satellites spread across the sky give a low HDOP; satellites bunched in one part of the sky give
a high one, even when there are many of them.
