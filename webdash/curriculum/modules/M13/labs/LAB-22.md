---
id: LAB-22
title: Capture a handshake from your own AP
themed_title: Sea trial · Take a sounding
mode: guided
est_minutes: 45
transmits: true
legal_basis: "Own network, or a documented written authorization to test (CFAA 18 U.S.C. §1030; interference 47 U.S.C. §333). Deauthentication is targeted at a client the operator owns — never a broadcast, never another network. Gated behind the M13.quiz legal check; the first step attests the target is in scope."
requires: {rails: [], services: [], assessments: [M13.quiz]}
world: "Your own WPA2 access point in range — the AC1200 covers 2.4, 5 and 6 GHz, so a 2.4 or 5 GHz AP both work — and a client you own that you can make reconnect."
steps:
  - id: authorization
    text: "Confirm scope before anything transmits. This step is the whole basis of the lab: attest that the access point you are about to test is yours, or that you hold written authorization to test it, and that you have recorded which. If you cannot, stop here."
    check: {type: attest, prompt: "This AP is my own network, or I hold written authorization to test it, and I have recorded which."}
  - id: workdir
    text: "Make a working directory outside the repo for the capture: run mkdir -p ~/labs/wpa && cd ~/labs/wpa && export LANG=C.UTF-8 && echo ready and paste the output. (The LANG line silences airodump-ng's non-UNICODE-terminal warning — Fancy's default locale is empty.) Captures never go in the repo tree."
    check: {type: paste, parser: regex, pattern: 'ready', min_matches: 1}
  - id: adapter
    text: "The AC1200 is fitted on the AIO V2's internal USB-C port and comes up as wlan1 in managed mode. If wlan1 isn't present, turn its USB rail on: aiov2_ctl USB on (default off), then wait a few seconds. (The onboard wlan0 has no monitor mode and is never used here.)"
    check: {type: status, path: net.wlan1.mode, op: eq, value: managed}
    timeout_s: 60
  - id: adapter-quiet
    text: "Confirm NetworkManager leaves wlan1 alone (otherwise wpa_supplicant fights monitor mode): run nmcli -t dev | grep wlan1; basename \"$(readlink -f /sys/class/net/wlan1/device/driver)\" and paste the output. Expect wlan1:wifi:unmanaged: and mt7921u. If it says disconnected instead of unmanaged, deploy the config: sudo cp ~/clockworkpi-uconsole/configs/networkmanager/wifi-onboard-only.conf /etc/NetworkManager/conf.d/ && sudo nmcli general reload."
    check: {type: paste, parser: regex, pattern: '(?s):unmanaged.*mt7921u', min_matches: 1}
  - id: monitor-up
    text: "Put the AC1200 into monitor mode: sudo airmon-ng start wlan1 (it becomes wlan1mon). Do not run airmon-ng check kill on this build — it would stop services Fancy depends on. If this times out, wlan1 isn't present or free — recheck the adapter step."
    check: {type: status, path: net.monitor_ifaces, op: gte, value: 1}
    timeout_s: 60
  - id: wlan0-untouched
    text: "wlan0 — Fancy's own network link — is still in managed mode and stays that way for the whole lab."
    check: {type: status, path: net.wlan0.mode, op: eq, value: managed}
  - id: find-target
    text: "Survey with sudo airodump-ng wlan1mon and read off YOUR AP's BSSID and channel (ENC should be WPA2). Ctrl-C when you have them. Attest that the row you picked is your own AP."
    check: {type: attest, prompt: "I identified my own AP's BSSID and channel, and it is WPA2."}
  - id: capture
    text: "Lock the capture to your AP: sudo airodump-ng -c <channel> --bssid <BSSID> -w ~/labs/wpa/handshake wlan1mon. Leave it running. This step only confirms the capture is writing — the handshake itself is confirmed at the verify step. Watch the header for 'WPA handshake: <BSSID>'."
    check: {type: file, op: mtime_after_step, path: "~/labs/wpa/handshake-*.cap"}
    timeout_s: 300
  - id: force-if-needed
    text: "If no client reconnects on its own and you need to force one, in a second shell send a FEW targeted deauths at a client you own: sudo aireplay-ng --deauth 3 -a <BSSID> -c <CLIENT-MAC> wlan1mon. Attest you targeted only your own client — never a broadcast, never another network's client. Skip and still attest if you didn't need it."
    check: {type: attest, prompt: "Any deauth I sent was a few frames at a specific client I own — no broadcast, no other network."}
  - id: verify
    text: "Confirm the capture actually holds a complete handshake before you tear down, while you can still re-capture: run aircrack-ng ~/labs/wpa/handshake-*.cap and paste the output (the glob covers -01, -02, … since airodump increments the suffix each run). Your AP's row should say '1 handshake' (or more). aircrack-ng then prompts for a target network — Ctrl-C after you've copied the output."
    check: {type: paste, parser: regex, pattern: '[1-9][0-9]* handshake', min_matches: 1}
  - id: teardown
    text: "First Ctrl-C the airodump-ng (and any aireplay-ng) so nothing is using wlan1mon, then bring the adapter back: sudo airmon-ng stop wlan1mon. No interface is left in monitor mode."
    check: {type: status, path: net.monitor_ifaces, op: eq, value: 0}
    timeout_s: 60
  - id: wlan0-still-managed
    text: "wlan0 is still in managed mode — Fancy's network link was never part of this."
    check: {type: status, path: net.wlan0.mode, op: eq, value: managed}
  - id: data-off
    text: "Move the capture, and anything you recovered, off Fancy to storage you control (e.g. scp to gpu-host or backup-host over the tailnet for the GPU crack), then delete the local copies: rm -f ~/labs/wpa/handshake-*. Attest none of it went into the repo."
    check: {type: attest, prompt: "I moved the capture and any recovered passphrase off Fancy, deleted the local copies, and committed none of it."}
  - id: local-clean
    text: "No capture is left in the working directory."
    check: {type: file, op: absent, path: "~/labs/wpa/handshake-*"}
  - id: finding
    text: "File a finding recording the RESULT in words only — no capture, no cleartext passphrase. Save it in the repo on Fancy as knowledge/wardriving/findings/<date>-wpa-audit.md (date YYYY-MM-DD, UTC). Record UTC time, grid square or city, that the AP was your own, and the outcome: handshake captured yes/no, and cracked yes/no with a note to rotate the passphrase if yes."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/wardriving/findings/*-wpa-audit.md", pattern: '^# Finding:', min: 1, fresh: true}
  - id: finding-clean
    text: "The finding holds no passphrase and no MAC address — result in words only."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/wardriving/findings/*-wpa-audit.md", pattern: '[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}|\b(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{12}\b', min: 0, max: 0}
restore:
  - {type: status, path: net.monitor_ifaces, op: eq, value: 0}
  - {type: status, path: net.wlan0.mode, op: eq, value: managed}
  - {type: file, op: absent, path: "~/labs/wpa/handshake-*"}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: [net.monitor_ifaces]
---

This lab transmits. It is the one place in the wardriving material where Fancy sends frames at a
network — a few targeted deauthentications, to make your own client reconnect so you can capture the
four-way handshake it produces. Everything about it is gated: the module quiz must pass first, the
first step attests the target is yours, and the deauth is aimed at a client you own, never broadcast.

The capture goes to `~/labs/wpa/`, never the repo. Fancy is capture-only — the actual crack runs on
a GPU host on the tailnet; see the full runbook `docs/runbooks/wifi-wpa2-handshake-audit.md`. The
finding you file at the end holds the result in words: whether a handshake was caught, whether it
cracked, and — if it did — that the passphrase needs rotating. No capture file, no address, no
cleartext passphrase ever leaves as a record.

If the lab stops partway, put Fancy back: Ctrl-C airodump/aireplay, `sudo airmon-ng stop wlan1mon`
(or cycle the USB rail, `aiov2_ctl USB off` then `on`, so no interface is left in monitor mode), and
delete any capture in `~/labs/wpa/`. `wlan0` is never part of this lab.
