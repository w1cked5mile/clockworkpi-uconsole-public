# 802.11 identifiers and regulatory domain

Scope note: reading identifiers that devices broadcast, and the rules a radio applies to itself.
Passive observation only — see [`../README.md`](../README.md) and the responsible-use section in
[`../../README.md`](../../README.md#responsible--legal-use).

Markers used here: *verified on this build* (run on Fancy, date given), *sourced* (standard,
regulation or upstream code), *unverified* (not yet confirmed; the settling command is named).

## OUI, BSSID and SSID

A Wi-Fi MAC address is 48 bits, written as six octets (`aa:bb:cc:dd:ee:ff`).

| Term | What it is | Unique? |
|---|---|---|
| **OUI** | The first 24 bits of a universally administered address, assigned to an organisation by the IEEE Registration Authority (an "MA-L" block) | per organisation; one company can hold many |
| **BSSID** | The MAC address that identifies one basic service set — one AP radio serving one network | per radio and network; a multi-SSID AP uses several |
| **SSID** | The network's name, 0–32 bytes, chosen by whoever set it up | **no** — thousands of networks share `linksys` |

- The IEEE also sells smaller blocks (MA-M, 28 bits; MA-S, 36 bits), so the first three octets
  can be shared by many companies. A three-octet lookup is a lead, not an answer. *Sourced: IEEE
  Registration Authority.*
- An OUI names whoever bought the block — often the Wi-Fi chip or module maker, not the brand on
  the product.
- A **hidden** network still beacons; it sends a zero-length or zero-filled SSID. Its BSSID is
  in every beacon regardless.
- Multi-SSID APs commonly derive their extra BSSIDs by setting the locally administered bit or
  changing the last octet, so one box can look like several networks.

Read addresses on this device without touching other people's:

```bash
iw dev                      # each interface's own addr
```

## The locally administered bit

### Reading the bit

The two lowest bits of the **first** octet are flags, not part of the OUI:

| Bit | Mask | 0 | 1 |
|---|---|---|---|
| I/G | `0x01` | individual (unicast) | group (multicast) |
| U/L | `0x02` | universally administered — has an OUI | **locally administered** — no OUI |

A locally administered address has `2`, `3`, `6`, `7`, `A`, `B`, `E` or `F` as its **second** hex
digit (`x2:…`, `xA:…`); for a unicast address — every client and AP address — that narrows to `2`,
`6`, `A` or `E`. Test one in the shell:

```bash
printf '%d\n' $(( 0x82 & 0x02 ))    # 2 → locally administered; 0 → universally administered
```

The rule that matters: **if the bit is set, do not OUI-lookup the address.** Any match is
coincidence. BLE random addresses follow different rules — see
[`ble-passive-observation.md`](ble-passive-observation.md#address-types-and-randomisation).

### Where locally administered addresses come from

- **MAC randomisation.** Phones use random addresses in probe requests, and since iOS 14 and
  Android 10 a separate random address per saved network when they associate. All of them set
  this bit.
- **Virtual interfaces.** On Fancy the P2P-device address is `wlan0`'s address with `0x02` set
  (`d8:…` becomes `da:…`). *Verified on this build 2026-09-25 with `iw dev`.*
- **IEEE CIDs.** A Company ID is IEEE-assigned but sits in the locally administered space (second
  digit `A`). It is not an OUI and does not identify a universally administered device.
  *Sourced: IEEE 802c.*

## Regulatory domain

A regulatory domain is a country's table of allowed frequency ranges, maximum power and flags.
On Linux, `cfg80211` applies it from `wireless-regdb`; Fancy sets the country at boot with
`cfg80211.ieee80211_regdom=US` on the kernel command line
([`../../../configs/boot/cmdline-notes.md`](../../../configs/boot/cmdline-notes.md)).

### Two blocks on this build

`iw reg get` prints **two** blocks on this build, and they disagree. *Verified on this build
2026-09-25:*

```text
global
country US: DFS-FCC
	(2400 - 2472 @ 40), (N/A, 30), (N/A)
	(5150 - 5250 @ 80), (N/A, 23), (N/A), AUTO-BW
	(5250 - 5350 @ 80), (N/A, 24), (0 ms), DFS, AUTO-BW
	(5470 - 5730 @ 160), (N/A, 24), (0 ms), DFS
	(5730 - 5850 @ 80), (N/A, 30), (N/A), AUTO-BW
	(5850 - 5895 @ 40), (N/A, 27), (N/A), NO-OUTDOOR, AUTO-BW, PASSIVE-SCAN
	(5925 - 7125 @ 320), (N/A, 12), (N/A), NO-OUTDOOR, PASSIVE-SCAN
	...
phy#0
country 99: DFS-UNSET
	(2402 - 2482 @ 40), (6, 20), (N/A)
	(2474 - 2494 @ 20), (6, 20), (N/A)
	(5140 - 5360 @ 160), (6, 20), (N/A)
	(5460 - 5860 @ 160), (6, 20), (N/A)
```

(The global block also lists 902–928 MHz and 60 GHz rules, trimmed here.)

| Block | Applies to | Notes |
|---|---|---|
| `global` — `country US` | radios that follow cfg80211's regulatory domain; a USB adapter such as the RT5370 is expected to (*verify with `iw reg get` after plugging it in* — a USB radio that follows global gets no `phy#` block of its own) | each line: range @ max bandwidth (MHz), (antenna gain, max EIRP dBm), (DFS CAC time), flags |
| `phy#0` — `country 99` | the onboard `brcmfmac` radio (`wlan0`) | `99` is not a country: it is `brcmfmac`'s own built-in table, applied to that radio instead of the global one (*sourced: `brcmf_regdom` in the kernel's `brcmfmac/cfg80211.c`, which matches these four lines*). What the chip's firmware enforces is *unverified* |

The gotcha: `country US` in the global block does not mean the onboard radio is using US rules.
Read both blocks. `wlan0` has no monitor mode anyway (`iw list`), so for survey work the global
block is the one that constrains the adapter. A USB adapter is expected to follow the global US
table — check that no new `phy#` block appears when it is plugged in. *Verified for the RT5370
2026-09-25:* with it in (`phy#1`), `iw reg get` still shows only the global and `phy#0` blocks,
and `iw phy phy1 info` enables channels 1–11 with 12–14 disabled. Check the AC1200 the same way.

### What the US table allows

As channels:

| Band | Rule | Channels (centre = base + 5 × n) | Notes |
|---|---|---|---|
| 2.4 GHz | 2400–2472 | 1–11 (2407 + 5n: 1 = 2412, 6 = 2437, 11 = 2462 MHz) | 1, 6 and 11 don't overlap |
| 5 GHz U-NII-1 | 5150–5250 | 36–48 (5000 + 5n) | |
| 5 GHz U-NII-2A | 5250–5350 | 52–64 | DFS |
| 5 GHz U-NII-2C | 5470–5730 | 100–144 | DFS |
| 5 GHz U-NII-3 | 5730–5850 | 149–165 | |
| 5 GHz U-NII-4 | 5850–5895 | 169–177 | indoor only, passive scan |
| 6 GHz | 5925–7125 | 1–233 (5950 + 5n) | indoor only, passive scan |

`PASSIVE-SCAN` means the radio may not send probe requests there until it has heard an AP.
`NO-OUTDOOR` restricts transmitters. Neither restricts a monitor interface, which only listens.

On this build: the RT5370 is **2.4 GHz only**, so channels 1–11 are all Fancy can survey today.
5 and 6 GHz need the AC1200, whose monitor mode and 6 GHz support are *unverified* (not arrived).

## DFS

**Dynamic Frequency Selection** protects radar in 5250–5350 and 5470–5725 MHz (channels 52–144).
A device that starts a network there must listen for radar first — the channel availability
check — and move off if it detects any; its clients follow. *Sourced: 47 CFR §15.407(h); FCC KDB
905462.*

- DFS limits **transmitters**. Listening on a DFS channel in monitor mode is not restricted.
- DFS channels are often quiet: many APs avoid them, and an AP that detected radar has moved away
  for at least 30 minutes.
- The `(0 ms)` field in `iw reg get` is the CAC time; 0 means the kernel default of 60 s
  (*sourced: `IEEE80211_DFS_MIN_CAC_TIME_MS` in the kernel's cfg80211*).
- `DFS-FCC` names the rule set; `DFS-UNSET` in the `phy#0` block means that table carries none.

On this build the AC1200 (MT7921AUN, `wlan1`) **arrived 2026-09-30 and covers 5 GHz (and 6 GHz)**,
so DFS channels are now reachable in monitor mode — no longer explain-only. (`wlan0` still has no
monitor mode; the retired RT5370 had no 5 GHz.) Confirm the DFS rules in force with `iw reg get`
before relying on a DFS channel.

## OUI false positives

Matching devices by OUI alone — as ALPR-detector lists do — produces false positives for four
reasons:

| Cause | Example | Check |
|---|---|---|
| The prefix is locally administered, so it is not an OUI at all | `82:6B:F2` in the flock-finder list ([`flock-safety-alpr-signatures.md`](flock-safety-alpr-signatures.md#wifi-signatures)): `0x82 & 0x02 = 2`. Any randomised phone address can start with it | test the bit before looking up |
| The OUI belongs to a module or chip maker used in many products | the same Wi-Fi module in a camera, a doorbell and a thermostat | require a second signature |
| A default or test address | `CC:CC:CC` — the flock doc already flags it | treat as no evidence |
| A shared or reassigned block | MA-M/MA-S sub-blocks under one 24-bit prefix | look up the full 28/36-bit block |

How to use an OUI hit:

- Treat it as one clue. Require corroboration — an SSID pattern, an information-element
  fingerprint, or a visual check — before calling anything a match, and grade the confidence as in
  [`../../rf-fundamentals/learned/signal-identification-workflow.md`](../../rf-fundamentals/learned/signal-identification-workflow.md).
- Never record the matched MAC in a finding. Record the count, the signature used, and the
  confidence.
