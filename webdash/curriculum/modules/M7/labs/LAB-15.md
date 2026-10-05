---
id: LAB-15
title: Passive Wi-Fi survey
themed_title: Sea trial · Harbour survey
mode: guided
est_minutes: 45
requires: {rails: [], services: [], assessments: [M7.quiz]}
transmits: false
world: "Wi-Fi networks in range — almost always true indoors. The AC1200 (wlan1) covers 2.4, 5 and 6 GHz; this survey hops the default channel set."
steps:
  - id: prepare
    text: "Get ready. Install sqlite3 if it is missing (sudo apt install sqlite3; Fancy has it since 2026-09-25) and make the folders (mkdir -p ~/labs ~/kismet-logs). Then run sqlite3 --version and paste the output."
    check: {type: paste, parser: regex, pattern: '^3\.[0-9]+', min_matches: 1}
  - id: service-stopped
    text: "Make sure Kismet's systemd service is stopped: sudo systemctl stop kismet. It crash-looped until 2026-09-25 and a fixed start is not yet re-tested, so the lab runs Kismet in a terminal instead."
    check: {type: status, path: services.kismet.active, op: in, value: [inactive, failed]}
  - id: site-config
    text: "Apply the staged site config: sudo cp ~/clockworkpi-uconsole/configs/kismet/kismet_site.conf /etc/kismet/kismet_site.conf. The lab checks that data-frame logging is off."
    check: {type: file, op: regex_count, path: /etc/kismet/kismet_site.conf, pattern: '^kis_log_data_packets=false', min: 1}
  - id: nm-unmanaged
    text: "Before the adapter goes in, confirm NetworkManager will leave it alone. Fancy's NetworkManager manages only the onboard radio (wlan0); a Wi-Fi interface it managed would be scanned actively, which sends probe requests, and might even join a saved network. Run grep -h unmanaged-devices /etc/NetworkManager/conf.d/*.conf and paste the output. If the line is missing, deploy it: sudo cp ~/clockworkpi-uconsole/configs/networkmanager/wifi-onboard-only.conf /etc/NetworkManager/conf.d/ && sudo nmcli general reload."
    check: {type: paste, parser: regex, pattern: 'unmanaged-devices\+=type:wifi;except:driver:brcmfmac', min_matches: 1}
  - id: adapter
    text: "The AC1200 is fitted on the AIO V2's internal USB-C port and comes up as wlan1 in managed mode. If wlan1 isn't present, turn its USB rail on: aiov2_ctl USB on (default off), then wait a few seconds for it to enumerate."
    check: {type: status, path: net.wlan1.mode, op: eq, value: managed}
    timeout_s: 60
  - id: adapter-quiet
    text: "Confirm NetworkManager is leaving it alone and that it is the AC1200: run nmcli -t dev | grep wlan1; basename \"$(readlink -f /sys/class/net/wlan1/device/driver)\" and paste the output. Expect wlan1:wifi:unmanaged: and mt7921u. If it says disconnected instead of unmanaged, re-check the wifi-onboard-only.conf step above (sudo nmcli general reload)."
    check: {type: paste, parser: regex, pattern: '(?s):unmanaged.*mt7921u', min_matches: 1}
  - id: regdom
    text: "Run iw reg get and paste the output. The global block should say country US, and the only phy# block should be phy#0, the onboard radio: the USB adapter follows the global table, so no new phy# block appears for it. If one does, the step fails — note what it says in your finding."
    check: {type: paste, parser: regex, pattern: 'country US:', min_matches: 1, reject: 'phy#[1-9]'}
  - id: kismet-up
    text: "In a terminal on Fancy, start Kismet: sg kismet -c 'kismet --no-ncurses-wrapper'. Leave that terminal open. webdash shows Kismet as running, or locked — both are fine. If Kismet can't open wlan1, your account isn't in the kismet group yet — see software/kismet.md, Running."
    check: {type: status, path: kismet.state, op: in, value: [running, locked]}
    timeout_s: 90
  - id: monitoring
    text: "Kismet has put the adapter into monitor mode: it adds a monitor interface, wlan1mon, next to wlan1, which stays in managed mode."
    check: {type: status, path: net.monitor_ifaces, op: gte, value: 1}
    timeout_s: 60
  - id: wlan0-untouched
    text: "wlan0 — Fancy's own network link — is still in managed mode."
    check: {type: status, path: net.wlan0.mode, op: eq, value: managed}
  - id: survey
    text: "Survey for 10 minutes. Stay put; don't change Kismet's channel settings. The adapter must stay in monitor mode the whole time."
    check: {type: computed, fn: mean, path: net.monitor_ifaces, window_s: 600, op: gte, value: 1, save_as: monitor_mean}
  - id: look
    text: "Open Kismet's web UI on Fancy at http://localhost:2501 (not the tailnet address); Kismet asks you to set an admin login the first time. In the device list, show only Wi-Fi APs, then sort by Crypto and count WPA3 (count WPA2/WPA3 mixed as WPA3), WPA2, WEP and Open. Sort by Channel and count 1, 6 and 11. Don't enable any Bluetooth source (hci0, or later the AC1200's controller) under Data Sources, and don't select or join any network."
    check: {type: attest, prompt: "I noted counts only — no SSIDs, no addresses — left every Bluetooth source disabled in Kismet, and joined nothing."}
  - id: kismet-stop
    text: "Stop Kismet with Ctrl-C in its terminal, and wait for it to exit. A clean stop finishes the log."
    check: {type: status, path: kismet.state, op: eq, value: stopped}
    timeout_s: 60
  - id: monitor-gone
    text: "No interface is left in monitor mode. Kismet leaves wlan1mon up even after a clean exit, so remove it: sudo iw dev wlan1mon del. wlan1 stays, in managed mode. A USB-rail cycle (aiov2_ctl USB off then on) also clears it."
    check: {type: status, path: net.monitor_ifaces, op: eq, value: 0}
    timeout_s: 60
  - id: counts
    text: "Count devices by type from the log. Run sqlite3 \"$(ls -t ~/kismet-logs/uconsole-*.kismet | head -1)\" 'SELECT phyname, type, COUNT(*) FROM devices GROUP BY phyname, type;' and paste the output. It holds no addresses. A Bluetooth row would mean a Bluetooth source was enabled — that fails the step."
    # sqlite3's default list output is "phyname|type|count" per row, e.g. "IEEE802.11|Wi-Fi AP|4"
    # (verified on Fancy 2026-09-25); the pattern only asks for rows that end in a number. The
    # reject catches a Bluetooth source.
    check: {type: paste, parser: regex, pattern: '\|[0-9]+\s*$', min_matches: 1, reject: '(?i)bluetooth|btle'}
  - id: finding
    text: "File a finding: on this page save a note, use Copy as finding, and save it in the repo on Fancy as knowledge/wardriving/findings/<date>-wifi-survey.md (date as YYYY-MM-DD, UTC). Record UTC times, grid square (or city), adapter (AC1200 / MT7921, 2.4/5/6 GHz), the bands/channels you actually hopped, and counts: access points, clients, security mix, channels. No SSIDs, no addresses, never coordinates."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/wardriving/findings/*-wifi-survey.md", pattern: '^# Finding:', min: 1, fresh: true}
  - id: finding-clean
    text: "No finding holds a MAC address."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/wardriving/findings/*-wifi-survey.md", pattern: '[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}|\b(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{12}\b', min: 0, max: 0}
  - id: log-away
    text: "Delete this run's log: rm ~/kismet-logs/uconsole-*.kismet* — it lists every address heard, and with a GPS fix where, so it never goes in the repo and isn't kept."
    check: {type: file, op: absent, path: "~/kismet-logs/uconsole-*.kismet*"}
  - id: resting-state
    text: "The AC1200 is internal, so there is nothing to unplug — leave wlan1 in managed mode. If you want it powered down between sessions, turn its rail off: aiov2_ctl USB off. The NetworkManager file stays in place; it only matches the survey adapters."
    check: {type: status, path: net.wlan1.mode, op: eq, value: managed}
    timeout_s: 60
restore:
  - {type: status, path: kismet.state, op: eq, value: stopped}
  - {type: status, path: net.monitor_ifaces, op: eq, value: 0}
  - {type: status, path: net.wlan0.mode, op: eq, value: managed}
  - {type: file, op: regex_count, path: /etc/kismet/kismet_site.conf, pattern: '^source=wlan0', min: 0, max: 0}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: [kismet.devices, net.monitor_ifaces]
---

Receive only. Kismet listens on the AC1200 (`wlan1`), and the survey adapter sends nothing: Kismet
only listens, and NetworkManager is told not to scan with it. `wlan0`, Fancy's own network link, keeps
sending probe requests routinely like any laptop's Wi-Fi; that is Fancy using its network, not
the survey. The lab never starts a service for you (it may ask you to turn the AC1200's USB rail on).
The AC1200's draw is an *estimate* (not yet measured on Fancy), so run on AC or a charged pack.

The NetworkManager file is a standing part of Fancy's setup, not something this lab adds or
removes: the onboard radio is for Fancy's network link only, and every other Wi-Fi adapter (the
AC1200, by its `mt7921u` driver) is left unmanaged for survey work. The rule was verified 2026-09-25:
`nmcli -t dev` shows the survey adapter as `wlan1:wifi:unmanaged:`, and `wlan0` keeps the only
default route.

Evidence keeps counts only — Kismet's device count if webdash could read it, and how many
interfaces were in monitor mode. The finding is yours to write, and holds counts only.

The `look` step can also be done from the log after Kismet stops, instead of the web UI. Each row
of the log's `devices` table has a `device` column holding Kismet's JSON record, and sqlite's
`json_extract` reads the crypt and channel fields out of it. Aggregate queries only — never select
`devmac` or any other address column:

```bash
LOG="$(ls -t ~/kismet-logs/uconsole-*.kismet | head -1)"
sqlite3 "$LOG" <<'SQL'
SELECT json_extract(CAST(device AS TEXT), '$."kismet.device.base.crypt"') AS crypt, COUNT(*)
  FROM devices WHERE type = 'Wi-Fi AP' GROUP BY crypt;
SELECT json_extract(CAST(device AS TEXT), '$."kismet.device.base.channel"') AS channel, COUNT(*)
  FROM devices WHERE type = 'Wi-Fi AP' GROUP BY channel;
SQL
```

Kismet's field names contain dots, so they are quoted inside the JSON path.

An access point heard only through non-beacon frames has a blank crypt field. That means
*unknown* — Kismet never read its capabilities — not open.

If the lab stops partway, put Fancy back: Ctrl-C Kismet, and if `iw dev` still shows `wlan1mon`,
remove it with `sudo iw dev wlan1mon del` (or cycle the USB rail: `aiov2_ctl USB off` then `on`). Delete any log it wrote (`rm ~/kismet-logs/uconsole-*.kismet*`).
`wlan0` is never part of this lab.
