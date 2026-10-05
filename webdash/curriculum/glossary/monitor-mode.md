---
id: monitor-mode
term: Monitor mode
tooltip: A Wi-Fi card setting that hands over every frame heard on a channel, not just the ones addressed to it.
good_bad: "During a survey one interface (wlan1mon) is in monitor mode; afterwards none is. wlan0 never is — it can't."
try_this: "Run iw dev before and after a Kismet run and compare the interface types."
learn_more: "#/learn/m/M7"
---

Normally a Wi-Fi card filters: it passes up only frames sent to it on the network it has joined.
In monitor mode it stops filtering and passes up every frame it can decode on the channel it is
tuned to, with signal strength attached. It still only listens. On Fancy only the USB adapter
does it; the onboard `wlan0` has no monitor mode.
