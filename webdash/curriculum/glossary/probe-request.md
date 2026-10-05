---
id: probe-request
term: Probe request
tooltip: A frame a phone or laptop sends asking "is network X here?" or "who's here?".
good_bad: "Hearing other people's probes is passive. Sending probes is active — Fancy's survey never does."
try_this: "Count probe-sending clients in Kismet, then ask yourself how many are the same phone with a new address."
learn_more: "#/learn/m/M7"
---

Client devices send probe requests to find networks faster than waiting for beacons. A probe may
name a network the device has joined before, and it carries a source address — usually a
randomised one on modern phones, which is why probe counts overstate devices.
