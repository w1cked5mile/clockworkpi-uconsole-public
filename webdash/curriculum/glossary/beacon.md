---
id: beacon
term: Beacon
tooltip: The short announcement a Wi-Fi access point broadcasts about ten times a second so devices can find it.
good_bad: "Every network nearby beacons whether or not anyone listens; hearing beacons is passive."
try_this: "In Kismet's web UI, watch an access point's packet count climb — about once a second while Kismet hops; about 10 a second if the source is locked to that AP's channel."
learn_more: "#/learn/m/M7"
---

A beacon carries the network's name (SSID, unless hidden), its radio address (BSSID), channel,
capabilities and security type. The default interval is 102.4 ms. Beacons are unencrypted by
design — they are how discovery works — so receiving them is what every phone does all day.
