# BLE passive observation — what a listening radio hears

Scope note: this discipline is **passive observation of broadcast advertisements only**. No
connecting, pairing, active scanning, or following connections. See [`../README.md`](../README.md)
and the responsible-use section in [`../../README.md`](../../README.md#responsible--legal-use).

**If Fancy asks, Fancy transmits.** A passive scan only hears what devices already broadcast.
`bluetoothctl scan on`, `btmgmt find` and Kismet's `linuxbluetooth` source send scan requests,
and those are transmissions.

Markers used here: *verified on this build* (run on Fancy, date given), *sourced* (Bluetooth Core
Specification or upstream code), *unverified* (not yet confirmed; the settling command is named).

## Advertising and channels

Bluetooth Low Energy splits 2400–2483.5 MHz into 40 channels 2 MHz apart. Three of them are the
**primary advertising channels**; the other 37 (0–36) carry connections and extended-advertising
payloads. *Sourced: Core Specification, Vol 6 Part B.*

| Channel | Centre | Placement |
|---|---|---|
| 37 | 2402 MHz | below Wi-Fi channel 1 (2412 MHz) |
| 38 | 2426 MHz | between Wi-Fi channels 1 and 6 |
| 39 | 2480 MHz | above Wi-Fi channel 11 (2462 MHz) |

An advertiser sends each **advertising event** on its advertising channels in turn, normally all
three. Legacy advertising repeats every 20 ms to 10.24 s, plus a random 0–10 ms delay per event so
two devices on the same interval do not keep colliding. A legacy advertisement carries at most
31 bytes of data. *Sourced: Core Specification, Vol 6 Part B §4.4.2.*

| PDU | Sent by | Meaning |
|---|---|---|
| `ADV_IND` | advertiser | connectable, scannable, undirected — the common "I am here" |
| `ADV_DIRECT_IND` | advertiser | connectable, addressed to one known peer |
| `ADV_NONCONN_IND` | advertiser | broadcast only — beacons, trackers, sensors |
| `ADV_SCAN_IND` | advertiser | scannable, not connectable |
| `SCAN_REQ` | **scanner** | "send me more" — an active scan's transmission |
| `SCAN_RSP` | advertiser | reply to a `SCAN_REQ`, up to 31 more bytes |
| `CONNECT_IND` | initiator | opens a connection — out of scope here |

Bluetooth 5 added **extended advertising**: a short pointer on the primary channels and the
payload on a data channel. A host that scans with the legacy HCI commands (as `hcitool lescan`
does) is sent only legacy advertisements, so extended-only advertisers are missing from what
follows. *Sourced: Core Specification, Vol 4 Part E §3.1.1; not checked on this build.*

## Passive vs active scanning

| Scan type | What the scanner sends | What it hears |
|---|---|---|
| **Passive** | nothing | every advertisement on the channel it is listening to |
| **Active** | a `SCAN_REQ` to each scannable advertiser | advertisements plus `SCAN_RSP` replies |
| BR/EDR inquiry (classic Bluetooth) | inquiry packets on hopping channels | classic devices that answer |

Active scanning is not a matter of degree: every `SCAN_REQ` is a transmission addressed to
someone else's device. That puts it outside this discipline even though it is routine for phones.

### Forbidden on this build

| Command or setting | Why |
|---|---|
| `bluetoothctl scan on` | active LE scan **and** BR/EDR inquiry |
| `btmgmt find` | the same kernel discovery procedure — active |
| `hcitool lescan` **without** `--passive` | hcitool's default scan type is active |
| `hcitool scan`, `hcitool inq` | BR/EDR inquiry — transmits |
| Kismet `linuxbluetooth` source, or enabling any Bluetooth adapter (`hci0`, or the AC1200's) in Kismet's Data Sources UI | Kismet auto-detects each adapter and offers it; its Bluetooth source runs discovery, which scans actively |
| connecting, pairing, `gatttool`, reading services | talks to the device |
| any observation on the onboard `hci0` | not a legal limit but a role one: `hci0` is reserved for Fancy's own paired devices; recon uses the AC1200's controller |
| Uploading logs to WiGLE or any map | publishes addresses and coordinates |

### How to tell from `btmon`

A passive scan's parameters command shows `Type: Passive (0x00)`. A passive scan's reports never
include `Event type: Scan response - SCAN_RSP`; an active scan's would. *Verified on this build
2026-09-25 (bluez 5.82, on `hci0`) — the `SCAN_RSP` absence was checked for the passive case only.*

## Address types and randomisation

Every advertisement carries the advertiser's 48-bit device address and a flag (`TxAdd`) saying
whether it is **public** or **random**. Random addresses are subdivided by their two most
significant bits (the first two bits of the first octet as written). *Sourced: Core
Specification, Vol 6 Part B §1.3.*

| Type | Top bits | First hex digit | Lifetime | OUI meaningful? |
|---|---|---|---|---|
| Public | — (flag says public) | any | fixed, IEEE-assigned | **yes** |
| Random static | `11` | `C`–`F` | fixed until power cycle, or for the device's life | no |
| Resolvable private (RPA) | `01` | `4`–`7` | rotates, commonly about every 15 min | no |
| Non-resolvable private | `00` | `0`–`3` | rotates | no |

- Only a public address has an OUI. **Never OUI-lookup a random address** — its first octet is
  random bits plus the type marker, so a "match" is coincidence.
- The top-bits rule applies only when the flag says random. A public address can start with
  any digit, which is why the flag, not the first digit, decides.
- The 802 **locally administered bit** (`0x02` in the first octet) is the Wi-Fi-side test — see
  [`80211-identifiers-and-regdom.md`](80211-identifiers-and-regdom.md#the-locally-administered-bit).
  In a public BLE address it is 0, but in a random address it is just another random bit, so it
  does not tell you the type.
- An RPA can be resolved to a stable identity only by a device holding that peer's Identity
  Resolving Key, which you get by bonding. A passive observer has no key and should not want one.
- Most phones advertise with RPAs, so one phone shows up as a new address every rotation. Count
  addresses as **addresses**, never as people or devices.

## Passive observation on this build

**Recon uses the AC1200's Bluetooth controller; the onboard radio is reserved** (owner decision,
2026-09-25). The onboard combo chip serves Fancy itself — `wlan0` for its network link, `hci0` for
its paired devices — and is never used for observation.

| Controller | Hardware | Role |
|---|---|---|
| `hci0` | CM4 onboard Cypress, Bluetooth 5.0, `Bus: UART`. *Verified on this build 2026-09-25.* | Fancy's own paired devices (three bonded). Never used for recon. |
| `hci1`, or whatever it comes up as | AC1200, vendor-claimed MediaTek MT7921AUN, Bluetooth 5.2, `Bus: USB`, on the AIO V2's USB rail. *Unverified — the card has shipped but not arrived.* | Recon: all passive BLE observation |

Software: `bluez` 5.82 with `hcitool`, `btmon`, `btmgmt` and `bluetoothctl` installed. *Verified
on this build 2026-09-25.*

### Identifying the recon controller

The AC1200 sits in the AIO V2's internal USB-C port, which the USB rail powers (`aiov2_ctl USB
on`, default off). With the rail on:

```bash
hciconfig | grep '^hci'    # expect two lines: hci0 ... Bus: UART, and the AC1200 ... Bus: USB
```

The `Bus: USB` controller is the recon one. It is expected to be `hci1` but the index is whatever
it enumerates as, which is *unverified* until the card is here. `btmgmt info` lists the same
controllers by index. The `grep` keeps the controllers' own address lines out of the output.

### The procedure on the AC1200 — verified 2026-09-30

The AC1200's controller is **`hci1` (Bus: USB)**, and its passive-only behaviour was confirmed on
Fancy with `btmon`:
- **No bonded devices** on `hci1`, so no kernel auto-connect/background scan is queued. On bring-up
  (`hciconfig hci1 reset` under `btmon`) `bluetoothd` issued **only setup commands — no `LE Set Scan
  Enable`, no `Create Connection`** — and cleared the accept/resolving lists; `Scanning: Enabled`
  never appeared while idle.
- A **passive scan is allowed**: `hcitool -i hci1 lescan --passive` set `Type: Passive (0x00)` and
  ran with **no `Command Disallowed`** (304 advertising reports from 16 advertisers). `hci1` returned
  to `bluetoothd` idle afterwards, no bonds created.

**But `hcitool … lescan --passive` fails with "Broken pipe" while `bluetoothd` is running** — a
user-channel/socket conflict, not a controller rejection. Stop `bluetoothd` first (safe when `hci0`
has no active connections or bonds — check `hcitool -i hci0 con`), then scan, then restart it:

```bash
sudo systemctl stop bluetooth
sudo hciconfig hci1 up      # confirm "UP RUNNING" before scanning
# ... passive scan (below) ...
sudo systemctl start bluetooth
```

Pair nothing to `hci1` — a bond would bring back `bluetoothd`'s background scan.

```bash
# Terminal A — record only the btmon lines that matter, for the recon controller only
#    (Ctrl-C when the scan ends). The filter keeps scan type, scan on/off and event types;
#    no addresses reach the disk.
mkdir -p ~/labs
sudo stdbuf -oL btmon -i hci1 | grep --line-buffered -E 'Type: (Passive|Active)|Scanning: |Event type:|SCAN_RSP' \
  > ~/labs/ble-hci-$(date -u +%Y%m%dT%H%MZ).log
```

```bash
# Terminal B — passive scan for 60 s on the recon controller, printing only a count of unique
#    addresses. -s INT matters: hcitool turns the scan off only on SIGINT. Nothing prints until
#    the prompt comes back after 60 s.
sudo timeout -s INT 60 hcitool -i hci1 lescan --passive --duplicates \
  | awk '$1 ~ /:/ {print $1}' | sort -u | wc -l
```

`stdbuf -oL` stops `btmon` holding its output back; `btmon -i hci1` records only that controller,
so the onboard radio's traffic stays out of the log. Replace `hci1` with the name `hciconfig`
showed. Afterwards the USB rail can go back off (`aiov2_ctl USB off`).

**Fallback, only if the scan fails with `Input/output error`** and `btmon` shows `Status: Command
Disallowed (0x0c)` — something already holds a scan on the recon controller:

```bash
sudo hcitool -i hci1 cmd 0x08 0x000c 00 00    # LE Set Scan Enable = off, recon controller only
# ...run the scan above again, then restore:
sudo systemctl restart bluetooth               # bluetoothd restarts whatever scan it had
```

`bluetoothd` serves both controllers, so the restart also briefly drops the onboard radio's
bonded devices — a Bluetooth keyboard or mouse in use disconnects for a moment.

### Why `hcitool lescan --passive` alone fails

This is the record of a one-off verification on the onboard `hci0`, 2026-09-25, made before the
recon/onboard split to prove that the passive method works on BlueZ 5.82. It shows what BlueZ does
on a controller **with bonded devices**; it is not the procedure.

`bluetoothd` keeps a kernel **background passive scan** running so the three bonded devices can
reconnect. That scan uses the controller's accept-list filter, so it reports only those devices.
While it runs, `hcitool lescan --passive` stops with:

```text
Set scan parameters failed: Input/output error
```

and `btmon` shows the controller refusing the parameters command: `Status: Command Disallowed
(0x0c)` — scan parameters cannot be changed while scanning is enabled. Stopping `bluetoothd` did
not help (something restarted it immediately; the unit responsible is *unverified*), and a
`bluetoothctl` advertisement monitor registered but produced no reports. *Verified on this build
2026-09-25, on `hci0`.*

### The pause-and-restore sequence (verified on `hci0`)

The sequence that worked on `hci0` on 2026-09-25. *Verified on this build 2026-09-25; recorded
here as evidence, not to be repeated on `hci0`.*

```bash
# Terminal A: the filtered recorder as above, without -i (all controllers)
# Terminal B:
sudo hcitool cmd 0x08 0x000c 00 00                      # pause the background scan
sudo timeout -s INT 60 hcitool lescan --passive --duplicates \
  | awk '$1 ~ /:/ {print $1}' | sort -u | wc -l
sudo systemctl restart bluetooth                        # restore it
grep -c 'Scanning: Enabled (0x01)' ~/labs/ble-hci-*.log   # was 2 or more
```

`systemctl is-active bluetooth` was no test of the restore: it says `active` whether or not the
background scan came back. The recorder's log was: the scan logged one `Scanning: Enabled (0x01)`,
and after the restart `btmon` showed the kernel re-enabling its background scan —
`LE Set Scan Parameters` with `Type: Passive (0x00)`, then another `Scanning: Enabled (0x01)`. A
test log held four. Without the restart, the background scan for the bonded devices would have
stayed off until the next reboot.

A 20 s run counted **10 unique addresses in 1,348 advertising reports**; the filtered-recorder
pipeline, run end to end the same day, counted 12 and logged four `Type: Passive (0x00)` lines, no
`Type: Active`, no `SCAN_RSP` and no addresses. These are reference points indoors in grid EM95,
not expected values; they depend on what is nearby.

`hcitool cmd 0x08 0x000c 00 00` is OGF `0x08` (LE controller commands), OCF `0x000c` (LE Set
Scan Enable), parameters `LE_Scan_Enable = 0x00` and `Filter_Duplicates = 0x00`.

### `btmon` wording on this build

| Line | Meaning |
|---|---|
| `Type: Passive (0x00)` | the scan parameters are passive — the line to check |
| `Scanning: Enabled (0x01)` / `Scanning: Disabled (0x00)` | LE Set Scan Enable on / off |
| `Event type: Connectable undirected - ADV_IND (0x00)` | an `ADV_IND` report |
| `Event type: Non connectable undirected - ADV_NONCONN_IND (0x03)` | an `ADV_NONCONN_IND` report |
| `Status: Command Disallowed (0x0c)` | the controller refused — usually a scan already running |

*All six verified on this build 2026-09-25, on `hci0`; expected to read the same on the AC1200's
controller, since `btmon` decodes the standard HCI commands.* An active scan would show `Type: Active (0x01)` and
`SCAN_RSP` event types. Match `SCAN_RSP`, not "Scan response": restarting `bluetoothd` logs an
unrelated `Scan response length` line.

### Full recording (debugging only)

When the filtered log is not enough to see what went wrong, record everything instead — but that
file holds every address heard, so it lives in `~/labs` only and is deleted the same session:

```bash
sudo btmon -i hci1 -w ~/labs/ble-$(date -u +%Y%m%dT%H%MZ).snoop    # instead of the recorder
btmon -r ~/labs/ble-<UTC>.snoop | less                     # read it back
rm ~/labs/*.snoop                                          # delete it when done
```

### Kismet

Kismet's Bluetooth source runs active discovery. Never add an `hci`/`linuxbluetooth` source to
[`kismet_site.conf`](../../../configs/kismet/kismet_site.conf), and never enable a Bluetooth
adapter (`hci0`, or the AC1200's) in Kismet's Data Sources page, where each appears automatically. See
[`../../../software/kismet.md`](../../../software/kismet.md).

## Privacy and handling

- `.snoop`/`.btsnoop` files contain device addresses, names and manufacturer data. Keep them under
  `~/labs/`, never in this repo (`.gitignore` excludes both extensions as a backstop), and delete
  them when the lab is done.
- **Count; do not list.** Never print, store or publish addresses. The pipeline above counts
  without displaying them.
- Do not follow one device over time or place, even by its name or manufacturer data. That is
  tracking a person.
- Findings record aggregate counts, general location (city or grid) and technical notes — see
  [`../../_templates/finding.md`](../../_templates/finding.md).
- US legal pointer, not legal advice: 18 U.S.C. §2511(2)(g)(i) permits intercepting
  communications "readily accessible to the general public", and advertisements are broadcasts to
  anyone listening. Transmitting to other people's devices, connecting, or decoding their
  traffic is a different question — see
  [`../../rf-fundamentals/learned/us-spectrum-and-legal.md`](../../rf-fundamentals/learned/us-spectrum-and-legal.md).

## What this cannot tell you

- **Which channel** an advertisement arrived on. HCI advertising reports have no channel field;
  per-channel reception needs a dedicated receiver — Nordic's nRF52840 dongle or a TI
  CC1352/CC26x2 board. None is on hand.
- **Connections.** Connection traffic hops across the 37 data channels; a standard controller cannot follow it.
  A dedicated receiver can, but following connections records traffic contents, which is out of
  scope.
- **Extended advertising**, including long-range (Coded PHY) advertisers — the legacy scan above
  does not report it. Whether the AC1200's controller supports extended scanning is *unverified*
  (`btmgmt --index 1 info` lists supported settings; `btmon` during `bluetoothd` start shows the
  feature bits).
- **How many devices.** Rotating addresses inflate counts; slow advertisers (up to 10.24 s) and
  devices in connections that stop advertising deflate them.
- **Distance.** RSSI from an uncalibrated receiver varies by many dB with orientation and the body
  in between; it ranks near from far, no more.
