---
id: tcp-retransmission
term: TCP retransmission
tooltip: The sender sent the same data again because it was not acknowledged in time.
good_bad: "A few are normal on any link. A count that climbs while the link is associated but slow means packets are being lost in flight — the weak-signal loss pattern."
try_this: "Capture on wlan0 while you ping the gateway, and watch whether the retransmit count climbs."
learn_more: "#/learn/m/M14"
live: tshark.findings.tcp_retransmit
live_prompt: "This many retransmissions are in the newest segment right now — baseline noise, or a link losing packets?"
example: 0
---

TCP hides loss from the application by resending unacknowledged data, so a link can be dropping
badly while a download still (slowly) completes. The retransmission count is where that hidden loss
becomes visible. It is the headline symptom of a marginal Wi-Fi link: on Fancy's `wlan0` at
−71 dBm, retransmits and dup-acks climbed under load until Wi-Fi power-save was disabled (see
`docs/logs/known-issues.md`).
