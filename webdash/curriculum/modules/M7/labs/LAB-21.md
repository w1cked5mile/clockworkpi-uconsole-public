---
id: LAB-21
title: Passive BLE advertisements
themed_title: Sea trial · Running lights
mode: guided
est_minutes: 20
requires: {rails: [USB], services: [], assessments: [M7.quiz]}
transmits: false
world: "The AC1200 fitted in the AIO V2's internal USB-C port (its controller verified as hci1, 2026-09-30). At least one Bluetooth LE device advertising nearby — a phone, watch, earbuds case or tracker. Almost always true; if the count is 0, move closer to people or devices and scan again."
steps:
  - id: usb-rail
    text: "Switch the USB rail on (the switch is on this page, or aiov2_ctl USB on). It powers the AIO V2's internal USB-C port, where the AC1200 sits. Its Wi-Fi comes up too; NetworkManager leaves it alone, and this lab doesn't use it."
    check: {type: status, path: aiov2.rails.USB.on, op: eq, value: true}
  - id: controller
    text: "Find the recon controller. Run hciconfig | grep '^hci' and paste the output (the grep drops the address lines). Expect two controllers: hci0 on Bus: UART is the onboard radio — Fancy's own paired devices use it, and this lab never touches it. The one on Bus: USB is the AC1200's. It is written hci1 below; if yours has another name, use that name in every command. If only hci0 appears, wait a few seconds for the card to come up and run it again."
    check: {type: paste, parser: regex, pattern: '(?s)\A(?=.*Bus: UART)(?=.*Bus: USB)', min_matches: 1}
  - id: stop-bluetoothd
    text: "Stop bluetoothd so hcitool can drive hci1 directly. While bluetoothd manages the adapter a direct passive scan fails with 'Set scan parameters failed: Broken pipe' (BlueZ holding the adapter — verified 2026-09-30). First check the onboard radio is idle: sudo hcitool -i hci0 con should list no connections. Then run sudo systemctl stop bluetooth, then sudo hciconfig hci1 up (confirm UP RUNNING), then paste the output of: systemctl is-active bluetooth; true. This briefly drops any paired device on the onboard hci0 — they return when you restart bluetooth near the end."
    check: {type: paste, parser: regex, pattern: '^inactive', min_matches: 1}
  - id: record
    text: "Terminal A: start the recorder for the recon controller only. Run mkdir -p ~/labs, then sudo stdbuf -oL btmon -i hci1 | grep --line-buffered -E 'Type: (Passive|Active)|Scanning: |Event type:|SCAN_RSP' > ~/labs/ble-hci-$(date -u +%Y%m%dT%H%MZ).log and leave it running. Only those lines are kept — they hold no addresses. Don't restart the recorder; if you do, stop and restart the lab."
    check: {type: file, op: mtime_after_step, path: "~/labs/ble-hci-*.log"}
  - id: scan
    text: "Terminal B: listen for 60 seconds on the recon controller and keep only the number of different addresses. Run sudo timeout -s INT 60 hcitool -i hci1 lescan --passive --duplicates | awk '$1 ~ /:/ {print $1}' | sort -u | wc -l > ~/labs/ble-count-$(date -u +%Y%m%dT%H%MZ).txt — then wait. Nothing prints; the prompt comes back after 60 seconds. If it prints 'Broken pipe', bluetoothd is still running — redo the stop step. If it prints 'Network is down', run sudo hciconfig hci1 up first."
    check: {type: file, op: regex_count, path: "~/labs/ble-count-*.txt", pattern: '^[1-9][0-9]*$', min: 1, fresh: true}
    timeout_s: 120
    world_wait: true
  - id: passive
    text: "btmon recorded the scan starting as passive: Type: Passive (0x00)."
    check: {type: file, op: regex_count, path: "~/labs/ble-hci-*.log", pattern: 'Type: Passive \(0x00\)', min: 1}
  - id: no-active
    text: "btmon recorded no active scan: Type: Active never appears."
    check: {type: file, op: regex_count, path: "~/labs/ble-hci-*.log", pattern: 'Type: Active', min: 0, max: 0}
  - id: no-scan-response
    text: "No device sent a scan response — which only happens when something asks. Nobody asked."
    check: {type: file, op: regex_count, path: "~/labs/ble-hci-*.log", pattern: 'SCAN_RSP', min: 0, max: 0}
  - id: no-addresses
    text: "The recorder's log holds no Bluetooth addresses."
    check: {type: file, op: regex_count, path: "~/labs/ble-hci-*.log", pattern: '[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}|\b(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{12}\b', min: 0, max: 0}
  - id: stop-record
    text: "Terminal A: stop the recorder with Ctrl-C. The filtered log can stay in ~/labs. If you ever saved a full btmon recording (btmon -w, a .snoop or .btsnoop file), delete it now — those hold every address heard."
    check: {type: file, op: absent, path: "~/labs/*snoop"}
  - id: start-bluetoothd
    text: "Restart bluetoothd so Fancy's own Bluetooth comes back: sudo systemctl start bluetooth. The onboard hci0 and any paired devices return. Paste the output of: systemctl is-active bluetooth."
    check: {type: paste, parser: regex, pattern: '^active', min_matches: 1}
  - id: usb-rail-off
    text: "Switch the USB rail back off (the switch on this page, or aiov2_ctl USB off). The AC1200 powers down; the onboard radio and its paired devices are untouched."
    check: {type: status, path: aiov2.rails.USB.on, op: eq, value: false}
  - id: finding
    text: "File a finding: on this page save a note, use Copy as finding, and save it in the repo on Fancy as knowledge/wardriving/findings/<date>-ble-count.md (date as YYYY-MM-DD, UTC). Record UTC time, grid square (or city), the recon controller (the AC1200's, and the name it came up as), the 60-second window and the unique-address count (cat ~/labs/ble-count-*.txt) — and say that the count overstates devices because addresses rotate. No addresses, no names, never coordinates."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/wardriving/findings/*-ble-count.md", pattern: '^# Finding:', min: 1, fresh: true}
  - id: finding-clean
    text: "No finding holds a MAC address."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/wardriving/findings/*-ble-count.md", pattern: '[0-9A-Fa-f]{2}([:-][0-9A-Fa-f]{2}){5}|\b(?=[0-9A-Fa-f]*[A-Fa-f])[0-9A-Fa-f]{12}\b', min: 0, max: 0}
restore:
  - {type: status, path: aiov2.rails.USB.on, op: eq, value: false}
  - {type: file, op: absent, path: "~/labs/*snoop"}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: []
---

Recon uses the AC1200's own Bluetooth controller — `hci1` (Bus: USB), verified 2026-09-30. The
onboard radio (`hci0`) is reserved for Fancy's own paired devices and is never used for observation.

Receive only. Nothing in this lab makes a Bluetooth radio transmit; `bluetoothctl scan on`,
`btmgmt find` and Kismet's Bluetooth source would, and none of them is used. `hci1` in the steps
stands for the AC1200's controller, or whatever it comes up as — `hciconfig` shows the onboard
radio on `Bus: UART` and the AC1200's on `Bus: USB`.

**Why bluetoothd is stopped first (verified 2026-09-30).** The AC1200's controller has no paired
devices, so `bluetoothd` keeps **no background scan** on it — `btmon` showed it brought up with no
`LE Set Scan Enable` and no auto-connect — so you don't get the `Command Disallowed` that a busy
scanner causes. What you *do* get, while `bluetoothd` is running, is `Set scan parameters failed:
Broken pipe`: BlueZ holds the adapter and blocks `hcitool`'s raw socket. Stopping `bluetoothd`
(the stop step) releases it, and the passive scan then runs cleanly — confirmed on `hci1` as
`Type: Passive (0x00)`, 304 advertising reports from 16 advertisers, no `Type: Active`, no
`SCAN_RSP`. Stopping `bluetoothd` is safe here because the onboard `hci0` has no active connections
or bonds; it briefly affects any paired device, which returns when you restart it. If a check never
passes, read the log with `cat ~/labs/ble-hci-*.log` — it holds no addresses.

**If the lab stops partway,** restart Fancy's Bluetooth yourself: `sudo systemctl start bluetooth`,
and turn the USB rail off (`aiov2_ctl USB off`).

**Historical note.** The method was first proven on 2026-09-25 on the onboard `hci0` (BlueZ 5.82),
which *does* carry paired devices: there `hcitool lescan --passive` failed with `Command Disallowed`
because `bluetoothd`'s background scan held the controller, and pausing that scan
(`hcitool -i hci1 cmd 0x08 0x000c 00 00`) was the fix. `hci1` behaves differently — no background
scan, but the daemon still owns the socket — which is why the step here stops `bluetoothd` outright
rather than pausing a scan.

The checks read only the recorder's filtered lines and the single number in the count file:
evidence is booleans and counts. The unique-address count overstates how many devices were there
— phones rotate their Bluetooth address about every 15 minutes, and one device can advertise
more than one address.
