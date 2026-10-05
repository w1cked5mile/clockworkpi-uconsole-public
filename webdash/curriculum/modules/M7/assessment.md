---
id: M7.quiz
kind: quiz
pass_threshold: 0.78
items:
  - id: ble-commands
    concept_tags: [C01, C31]
    type: single
    required: true
    prompt: You want to see which Bluetooth LE devices are advertising nearby. Which command may you run?
    choices:
      - "bluetoothctl scan on"
      - "btmgmt find"
      - "sudo hcitool -i hci1 lescan --passive, on the AC1200's controller"
      - "sudo hcitool lescan"
    answer: 2
    explanation: Only a passive scan hears without asking, and it runs on the recon controller, not the onboard hci0. bluetoothctl scan on, btmgmt find and hcitool lescan without --passive (its default is active) all send requests — they transmit.
  - id: open-network
    concept_tags: [C01, C32]
    type: single
    required: true
    prompt: The survey shows an open network with no password. What do you do?
    choices:
      - "Count it as open in the security mix, and never connect to it"
      - "Connect briefly to check it works, then disconnect"
      - "Record its name so others know it's open"
    answer: 0
    explanation: Open is an observation, not an invitation. Joining a network you don't own is access without authorisation, and its name stays out of the finding.
  - id: finding-contents
    concept_tags: [C02, C03]
    type: multi
    required: true
    prompt: Which of these may go in an M7 finding?
    choices:
      - "The number of access points, and how many use WPA2 or WPA3"
      - "The grid square and UTC times"
      - "The SSIDs of the three strongest networks"
      - "The Bluetooth address that appeared most often"
      - "How many access points sat on channels 1, 6 and 11"
    answer: [0, 1, 4]
    explanation: Counts, grid square and times only. Names and addresses are records about other people.
  - id: wlan0
    concept_tags: [C31, C32]
    type: single
    required: true
    prompt: Which interface never goes into monitor mode on Fancy, and why?
    choices:
      - "wlan1 — it carries Fancy's network link"
      - "wlan0 — it has no monitor mode, and it is Fancy's own network link"
    answer: 1
    explanation: iw list shows no monitor mode for brcmfmac, and patching its firmware is out of scope. wlan1 is the AC1200 survey adapter (MT7921). The survey uses it; wlan0 stays managed, and the lab checks it.
  - id: recon-radio
    concept_tags: [C31, C32]
    type: single
    required: true
    prompt: Which radio does Fancy use for recon?
    choices:
      - "The onboard radio — wlan0 for Wi-Fi and hci0 for Bluetooth"
      - "The AC1200 — its Wi-Fi and its own Bluetooth controller"
      - "Whichever radio is free at the time"
    answer: 1
    explanation: The onboard wlan0 and hci0 are for Fancy's own network link and paired devices. Recon uses the AC1200's Wi-Fi (wlan1) and its own Bluetooth controller (hci1), both verified on Fancy 2026-09-30.
  - id: raw-files
    concept_tags: [C02, C32]
    type: single
    required: true
    prompt: Where do raw .kismet logs and .snoop Bluetooth recordings belong?
    choices:
      - "In knowledge/wardriving/findings/, next to the finding"
      - "Outside the repo — ~/kismet-logs and ~/labs — and deleted when no longer needed"
      - "In the repo, as long as the commit message says they contain addresses"
    answer: 1
    explanation: Both hold every address heard. They never go in the repo; findings hold counts only.
  - id: kismet-hci0
    concept_tags: [C01, C32]
    type: single
    required: true
    prompt: Kismet lists a Bluetooth adapter (hci0, or later the AC1200's) under Data Sources. If you enable it, does Fancy transmit?
    choices:
      - "No — Kismet is a passive tool"
      - "Yes — Kismet's Bluetooth source scans actively, sending scan requests"
      - "Only if a paired device is nearby"
    answer: 1
    explanation: If Fancy asks, Fancy transmits. Bluetooth is observed with the passive method in LAB-21, never through Kismet.
  - id: probe-macs
    concept_tags: [C31]
    type: single
    prompt: Kismet shows 25 client MAC addresses sending probe requests over 5 minutes. How many phones were there?
    choices:
      - "25"
      - "Can't tell — randomised addresses make one phone look like several"
      - "12, because each phone uses two addresses"
    answer: 1
    explanation: Most phones randomise probe addresses. Report 25 client addresses and say the device count is unknown.
  - id: non-overlapping
    concept_tags: [C31]
    type: multi
    prompt: Which US 2.4 GHz channels don't overlap each other?
    choices:
      - "1"
      - "3"
      - "6"
      - "9"
      - "11"
    answer: [0, 2, 4]
    explanation: Channels are 5 MHz apart and a signal is about 20 MHz wide; 1, 6 and 11 (2412, 2437, 2462 MHz) are 25 MHz apart.
  - id: survey-bands
    concept_tags: [C31]
    type: single
    prompt: The AC1200 covers 2.4, 5 and 6 GHz. If a survey still shows only 2.4 GHz networks, what is the most likely reason?
    choices:
      - "The regulatory domain blocks 5 and 6 GHz in the US"
      - "The channel hop list only includes 2.4 GHz — add 5/6 GHz channels to the Kismet source"
      - "Monitor mode works only on 2.4 GHz"
    answer: 1
    explanation: The MT7921 tunes all three bands (verified 2026-09-30), so this is a hop-list/config matter — include 5 and 6 GHz channels in the source. (The old RT5370 stand-in genuinely couldn't tune 5/6 GHz; it has been removed.)
  - id: ble-channels
    concept_tags: [C31]
    type: single
    prompt: On which channels do Bluetooth LE devices advertise?
    choices:
      - "37, 38 and 39 — 2402, 2426 and 2480 MHz"
      - "1, 6 and 11"
      - "All 40 channels in turn"
    answer: 0
    explanation: Three fixed advertising channels, spread across the band to dodge the busiest Wi-Fi channels.
  - id: oui-match
    concept_tags: [C31, C33]
    type: single
    prompt: An address's first three bytes match a camera maker's OUI. What does that prove?
    choices:
      - "That it is that maker's camera"
      - "Only that the bytes are registered to that maker — and nothing at all if the address is locally administered or random"
      - "Who owns the device"
    answer: 1
    explanation: An OUI names who registered the prefix, not what the device is. Random addresses have no OUI.
  - id: locked
    concept_tags: [C10, C32]
    type: single
    prompt: The Wi-Fi station shows Kismet as locked. What does that mean?
    choices:
      - "Kismet has crashed"
      - "Kismet is running, but webdash has no API token to read its device count — normal here"
      - "Someone else is using the adapter"
    answer: 1
    explanation: locked is a normal state on this build; the survey still works. stopped means Kismet isn't running.
  - id: disallowed
    concept_tags: [C08, C31]
    type: single
    prompt: "In the one-off 2026-09-25 test on the onboard radio, sudo hcitool lescan --passive failed with Command Disallowed. The AC1200's controller does not fail that way — why?"
    choices:
      - "The AC1200's chip is newer, and newer chips never refuse commands"
      - "The onboard radio has paired devices, so bluetoothd keeps a background scan running that holds the scanner; the AC1200's controller has none, so there is no background scan"
      - "hcitool only works on USB controllers"
    answer: 1
    explanation: A controller won't change scan settings while a scan is on, and bluetoothd runs its background scan only to find paired devices. Verified on hci1 2026-09-30 — no background scan, so no Command Disallowed. Its own gotcha is different — while bluetoothd runs it holds the adapter and lescan fails with Broken pipe, so LAB-21 stops bluetoothd first.
  - id: btmon-asked
    concept_tags: [C01, C31]
    type: single
    required: true
    prompt: Your btmon record is the proof that the scan was passive. Which btmon line would show that Fancy asked?
    choices:
      - "Type: Active (0x01), or an Event type ending SCAN_RSP"
      - "Type: Passive (0x00)"
      - "Scanning: Disabled (0x00)"
      - "Status: Command Disallowed (0x0c)"
    answer: 0
    explanation: An active scan's parameters say Type Active, and SCAN_RSP replies exist only because a scanner sent a request. Passive is the line you want; Disabled is scanning switched off; Command Disallowed is the controller refusing because another scan is running.
---

Twelve of fifteen to pass, and all eight questions about transmitting, privacy, handling and
which radio recon uses must be right.
