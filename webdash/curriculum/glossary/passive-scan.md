---
id: passive-scan
term: Passive scan
tooltip: Listening for what devices already broadcast, without sending anything.
good_bad: "btmon shows Type: Passive (0x00) and no SCAN_RSP for a passive scan. Type: Active means Fancy asked — and transmitted."
try_this: "After LAB-21, read your ~/labs/ble-hci-*.log and find the Type: Passive line."
learn_more: "#/learn/m/M7"
---

An active scan sends a request and collects the replies; a passive scan only receives. For Wi-Fi,
monitor mode with Kismet is passive. For Bluetooth LE, `hcitool lescan --passive` is; `bluetoothctl
scan on`, `btmgmt find` and Kismet's Bluetooth source are active. If Fancy asks, Fancy transmits.
