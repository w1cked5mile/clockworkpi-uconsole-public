---
id: M7
title: Passive Wi-Fi and Bluetooth survey
themed_title: Passage 7 · Harbour lights
discipline: wardriving
station: wifi
prerequisites:
  - {id: M0, soft: false}
  - {id: M3, soft: false}
sources:
  - knowledge/rf-fundamentals/learned/us-spectrum-and-legal.md
  - knowledge/wardriving/learned/wifi-capture-fundamentals.md
  - knowledge/wardriving/learned/80211-identifiers-and-regdom.md
  - knowledge/wardriving/learned/ble-passive-observation.md
  - knowledge/wardriving/runbooks/passive-survey-session.md
  - knowledge/wardriving/configs/kismet-passive-survey.md
  - software/kismet.md
  - configs/kismet/kismet_site.conf
  - configs/networkmanager/wifi-onboard-only.conf
  - webdash/app/collectors/kismet.py
objectives:
  - "**Distinguish** passive from active observation, and **name** the commands that make Fancy transmit (`bluetoothctl scan on`, `btmgmt find`, Kismet's Bluetooth source)."
  - "**Explain** MAC and Bluetooth address randomisation, and why device counts overstate the number of real devices."
  - "**Run** a Kismet survey on the USB adapter, and **verify** afterwards that the adapter is back in managed mode and `wlan0` was never touched."
  - "**Observe** Bluetooth LE advertisements passively on the recon radio, and **prove** from `btmon`'s record that the scan was passive."
  - "**Write** a finding that holds counts only — no names, no addresses, no coordinates."
est_minutes: 175
today:
  state: ready
  reason: "The AC1200 arrived and is verified on Fancy (2026-09-30): its Wi-Fi (wlan1, mt7921u) does monitor mode on 2.4/5/6 GHz, and its Bluetooth controller (hci1, USB) passed the passive-BLE checks, so both labs run and 5/6 GHz and DFS are now reachable. Two caveats: Kismet's systemd service crash-looped until 2026-09-25 (likely fixed by the loopback bind, not yet re-tested), so the lab uses the foreground run; and LAB-21 must stop bluetoothd before the passive scan (a direct lescan fails with 'Broken pipe' while BlueZ holds the adapter)."
---

Every phone, router and fitness band nearby is already announcing itself, many times a second.
This module listens to those announcements — Wi-Fi beacons and Bluetooth LE advertisements —
and turns them into counts. The survey adapter sends nothing: it never asks a device anything,
never joins a network, and nothing it hears is written down as who was there.

**If Fancy asks, Fancy transmits.** A passive scan only hears what devices already broadcast.
`bluetoothctl scan on`, `btmgmt find` and Kismet's Bluetooth (`linuxbluetooth`) source send
scan requests, and those are transmissions. None of them is used here.

**Recon uses the AC1200, never the onboard radio.** The onboard combo chip is for Fancy's own use:
its Wi-Fi (`wlan0`) is Fancy's network link, and its Bluetooth is for Fancy's paired devices. All
observation uses the AC1200's Wi-Fi and its own Bluetooth controller. The AC1200 arrived 2026-09-30
and is verified: its Wi-Fi (`wlan1`, `mt7921u`) does monitor mode on 2.4/5/6 GHz, and its Bluetooth
controller is `hci1` (USB). (Before it arrived, the RT5370 USB dongle stood in as the Wi-Fi test
adapter — 2.4 GHz only, no Bluetooth; it has been removed.)

The onboard Wi-Fi (`wlan0`) can't do monitor mode anyway; it is never used for the survey. Like any laptop's Wi-Fi it sends probe requests routinely to stay connected —
that is Fancy using its network, not surveying. The survey uses a USB adapter that
NetworkManager is told to leave alone, and the lab checks that it goes back to normal afterwards.
