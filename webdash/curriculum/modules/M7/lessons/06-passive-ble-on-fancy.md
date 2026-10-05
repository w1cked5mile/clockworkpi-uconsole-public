---
id: M7.blescan
title: Passive BLE on Fancy
est_minutes: 15
glossary: [passive-scan, ble-advertisement]
---

## Which radio listens

Recon uses the **AC1200's Bluetooth controller**, never the onboard one. The onboard radio (`hci0`)
belongs to Fancy's own paired devices; the AC1200's controller has no paired devices at all. The
AC1200 sits on the AIO V2's internal USB-C port, so its USB rail must be on
({live:aiov2.rails.USB.on} now). Tell the two controllers apart by their bus:

```bash
hciconfig | grep '^hci'     # onboard: Bus: UART.  AC1200: Bus: USB
```

The AC1200's controller comes up as `hci1` (Bus: USB), confirmed on Fancy 2026-09-30. If it ever
gets another name, use that name everywhere `hci1` appears below.

## The method (verified on the AC1200, 2026-09-30)

`hcitool` talks to the controller over a raw HCI socket, but while `bluetoothd` is managing the
adapter that socket is blocked — a direct `lescan --passive` fails with **`Set scan parameters
failed: Broken pipe`** (not a controller refusal, just BlueZ holding the adapter). So the reliable
path is to stop `bluetoothd`, scan, then start it again — safe here because the onboard `hci0` has
no active connections or bonds (check `hcitool -i hci0 con`). With a `btmon -i hci1` recorder
running in another terminal — LAB-21 gives the exact command, which keeps only a few line types and
no addresses:

```bash
sudo systemctl stop bluetooth
sudo hciconfig hci1 up        # confirm "UP RUNNING" before scanning
sudo timeout -s INT 60 hcitool -i hci1 lescan --passive --duplicates \
  | awk '$1 ~ /:/ {print $1}' | sort -u | wc -l
sudo systemctl start bluetooth
```

`-i hci1` keeps the scan off the onboard radio. `-s INT` matters: `hcitool` only turns the scan
off when it gets Ctrl-C (SIGINT). Nothing prints while it listens; the count appears and the
prompt comes back after 60 seconds. The `awk | sort -u | wc -l` turns addresses into a single
number before anything is written down.

## What the one-off test on `hci0` showed (2026-09-25)

Before the AC1200 arrived, the method was checked once on the onboard radio, to prove that a
passive scan works on this BlueZ. That was a verification, not the procedure. There,
`hcitool lescan --passive` on its own failed:

```text
Set scan parameters failed: Input/output error
```

`btmon` showed the controller's real answer, `Status: Command Disallowed (0x0c)`. The scanner was
already busy: `bluetoothd` keeps a **background passive scan** running on a controller with paired
devices, so it notices when one comes back into range, and a controller won't change scan settings
while a scan is on. Pausing that scan (`hcitool cmd 0x08 0x000c 00 00`, *LE Set Scan Enable* =
off, a message to the chip that transmits nothing), scanning, then `sudo systemctl restart
bluetooth` to put the background scan back worked: 12 addresses counted, and `btmon` logged
`Type: Passive` with no `Type: Active` and no `SCAN_RSP`.

The AC1200's controller has no paired devices, so `bluetoothd` keeps **no background scan** on it —
verified 2026-09-30: `btmon` showed the controller brought up with no `LE Set Scan Enable` and no
auto-connect. So the `Command Disallowed` seen on `hci0` does **not** happen here. What does happen
is the `Broken pipe` above — `bluetoothd` holding the adapter — which is why the method stops
`bluetoothd` first rather than just pausing a scan. With that, the passive scan ran cleanly on
`hci1`: `Type: Passive (0x00)`, 304 advertising reports from 16 advertisers, no `SCAN_RSP`.

## How you prove it was passive

`btmon` decodes every command Fancy sends to a Bluetooth controller. These are the lines it
printed on this build:

@ref knowledge/wardriving/learned/ble-passive-observation.md#btmon-wording-on-this-build

No `SCAN_RSP` means nobody asked.

@ref knowledge/wardriving/learned/ble-passive-observation.md#what-this-cannot-tell-you
