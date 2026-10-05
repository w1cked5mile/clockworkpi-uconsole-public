---
id: M7.channels
title: Beacons, probes and channels
est_minutes: 20
glossary: [monitor-mode, beacon, probe-request, bssid, regulatory-domain, channel-hopping]
---

A Wi-Fi card normally hands the computer only the frames addressed to it. **Monitor mode**
hands over every frame it decodes on its channel, with the signal strength attached. It still
only listens.

On Fancy that means a USB adapter. The onboard `wlan0` (Broadcom, `brcmfmac`) has **no monitor
mode at all** — `iw list` shows none (verified 2026-09-25) — and it carries Fancy's own network
connection, so it is never used for a survey, and its firmware is never patched to change that.
Right now `wlan0` is **{live:net.wlan0.mode}**, the USB adapter `wlan1` is present:
**{live:net.wlan1.present}**, and **{live:net.monitor_ifaces}** interfaces are in monitor mode.

| Adapter | Bands | Monitor mode on Fancy |
|---|---|---|
| AC1200 — MediaTek MT7921AUN (`mt7921u`), `wlan1` | 2.4, 5, 6 GHz | **Verified 2026-09-30:** monitor mode (incl. active monitor) on all three bands; Kismet adds a `wlan1mon` interface next to `wlan1` |
| ~~RT5370 USB dongle (`rt2800usb`)~~ | 2.4 GHz only | Interim stand-in before the AC1200 arrived (verified 2026-09-21/25); now removed |

The AC1200 sits on the AIO V2's internal USB-C port behind the USB rail (now
{live:aiov2.rails.USB.on}) and comes up as `wlan1`. (The RT5370 was an external-USB stand-in that
needed no rail, before the AC1200 arrived.)

## What is in the air

@ref knowledge/wardriving/learned/wifi-capture-fundamentals.md#what-broadcast-frames-contain

The **BSSID** is one access point radio's own address; the **SSID** is the network name people
see. One SSID can have many BSSIDs — a mesh system, or one router on two bands — so counting
BSSIDs counts radios, not networks. Both stay out of findings.

## Channels

In the US the 2.4 GHz channels run 1 to 11, and each centre frequency is 2407 + 5 × *n* MHz:

```text
channel 1  = 2407 + 5 × 1  = 2412 MHz
channel 6  = 2407 + 5 × 6  = 2437 MHz
channel 11 = 2407 + 5 × 11 = 2462 MHz
```

Channels are 5 MHz apart but a Wi-Fi signal is about 20 MHz wide, so neighbours overlap. 1, 6
and 11 are 25 MHz apart: the only three that don't. 5 GHz (36–177) and 6 GHz are covered by the
AC1200 — add those channels to the hop list to survey there (the default config hops the bands the
radio supports).

A radio hears one channel at a time, so Kismet **hops**: Fancy's config retunes 5 times a second.
Each network beacons about 10 times a second on its own channel, so a hopping survey hears only
a share of them — enough to find it, not every frame.

## Regulatory domain

A regulatory domain is a country's table of allowed channels and power. `iw reg get` shows it:

@ref knowledge/wardriving/learned/80211-identifiers-and-regdom.md#two-blocks-on-this-build

```bash
iw reg get
```

LAB-15 runs this again with the AC1200 as `wlan1`: confirm the regulatory domain with `iw reg get`
(a USB radio that follows the global table adds no separate `phy#` block of its own). DFS — the
radar rules on 5 GHz channels 52–144 — now applies for real, since the AC1200 can tune 5 GHz; check
the rules in force before surveying a DFS channel.
