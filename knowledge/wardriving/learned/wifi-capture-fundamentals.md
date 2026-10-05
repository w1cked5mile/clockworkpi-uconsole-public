# Wi-Fi capture fundamentals — what passive observation actually sees

Scope note: this discipline is **passive observation of broadcast frames only**. No association,
no deauthentication, no handshake capture, no cracking. See
[`../README.md`](../README.md) and [`../../README.md`](../../README.md).

## Monitor mode

A normal Wi-Fi interface only delivers frames addressed to it, on the channel it is associated
with. **Monitor mode** delivers every frame the radio decodes on the tuned channel, with a
radiotap header carrying signal strength and channel metadata.

The CM4's onboard Wi-Fi (`brcmfmac`, `wlan0`) **has no monitor mode** — `monitor` is absent from
its `Supported interface modes` (*verified on this build 2026-09-21 and 2026-09-25*). It is also
Fancy's network link: never put it in monitor mode and never patch its firmware (nexmon). Survey
work uses a USB adapter: the AC1200 (MediaTek **MT7921AUN**, `wlan1`, `mt7921u`), arrived and
installed 2026-09-30, with monitor mode (incl. active monitor) **verified on-device across
2.4/5/6 GHz**. The RT5370 (`rt2800usb`, 2.4 GHz only, monitor mode verified 2026-09-21) was the
interim stand-in before it arrived, now removed.

```bash
iw dev                                            # interface names
iw phy | grep -A3 'Supported interface modes'     # look for "monitor"
```

Kismet manages mode and channel hopping itself — do not hand-configure the interface first. On
Linux it does not switch the existing interface: it adds a second, monitor-mode virtual interface
on the same radio (`wlan1mon` next to `wlan1`, which stays managed). On this build it left
`wlan1mon` up after a clean exit (seen 2026-09-25), so remove it afterwards with
`sudo iw dev wlan1mon del`.

## What broadcast frames contain

| Frame | Sent by | Contains |
|---|---|---|
| Beacon | Access points, ~10×/second (default interval 102.4 ms) | SSID (unless hidden), BSSID, channel, capabilities, security type |
| Probe request | Client devices | Requested SSID (sometimes), source MAC |
| Probe response | APs | Same fields as a beacon, directed |

Beacons are unencrypted by design — they are how discovery works. Phones mostly don't wait for
them: they **scan actively**, sending probe requests on each channel and collecting the
responses. That is why probe requests are so common in a survey, and why a monitor interface that
only listens is doing less than an ordinary phone does.

## MAC randomization

Modern phones randomize the MAC in probe requests, and since iOS 14 and Android 10 they also use a
separate random MAC **per saved network** when they associate, so the burned-in address rarely
appears at all. Randomised addresses set the locally administered bit
([`80211-identifiers-and-regdom.md`](80211-identifiers-and-regdom.md#the-locally-administered-bit)).
Expect client counts to overstate unique devices, and do not treat a randomized MAC as an identity.

## Channels

| Band | Channels | Notes |
|---|---|---|
| 2.4 GHz | 1–11 (US) | Only 1, 6, 11 are non-overlapping |
| 5 GHz | 36–177 (US regdb) | DFS on 52–64 and 100–144, often quiet; 169–177 indoor only |
| 6 GHz | 1–233 (Wi-Fi 6E) | Requires 6E-capable hardware |

On this build only 2.4 GHz is observable today (RT5370). Reading the regulatory domain, and why
`iw reg get` shows two different tables, is in
[`80211-identifiers-and-regdom.md`](80211-identifiers-and-regdom.md#regulatory-domain). Bluetooth
LE shares 2.4 GHz; see [`ble-passive-observation.md`](ble-passive-observation.md).

A single radio can only listen to one channel at a time. Hopping (5 channels/sec is a common
default) trades dwell time for coverage: fast hopping finds more networks, slow hopping catches
more frames per network.

## Geolocation

Survey value comes from pairing observations with position, which is why gpsd runs against the AIO
GNSS. Without a fix, a capture is a list of names with no map.

## Privacy and handling

Capture files contain MAC addresses, SSIDs, timestamps, and precise coordinates — that is
personal-adjacent data about other people.

- Keep raw `.kismet` files **out of this repo**.
- Findings record general location (city/grid), aggregate counts, and technical observations — not
  identifiable device lists.
- Do not publish anything that maps an individual's movements.

## What this cannot tell you

- Anything about traffic contents on encrypted networks.
- Reliable device identity where MAC randomization is active.
- Whether a network is "vulnerable" — that determination requires interaction, which is out of scope.
