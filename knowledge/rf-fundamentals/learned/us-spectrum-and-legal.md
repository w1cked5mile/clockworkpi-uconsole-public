# US spectrum: receiving, decoding, transmitting

Practical boundaries for this platform in the United States. Not legal advice; rules differ
outside the US and change over time — verify against the current FCC rules and ARRL summaries.

## Receiving

Owning and operating a receiver is generally lawful, and most of what this build does is passive
reception: ADS-B, AIS, weather satellites, broadcast, NOAA weather radio, amateur bands.

Two constraints matter more than "can I tune it":

- **ECPA (18 U.S.C. § 2511)** restricts intentionally intercepting, using, or **divulging** the
  contents of certain private communications — including many encrypted or scrambled transmissions
  and some cellular/private carrier traffic — even when the signal is receivable.
- **Communications Act § 605** restricts divulging or benefiting from the contents of intercepted
  radio communications not intended for the general public.

Practical rule: **classify freely, decode open standards, do not decode or share protected,
private, or encrypted traffic.**

## Transmitting

| Activity | Requirement |
|---|---|
| LoRa / Meshtastic in 902–928 MHz ISM | License-free under **FCC Part 15** within its power and bandwidth rules (below). The AIO V2's certification is *unverified* (no FCC ID on record), and the operator is responsible for compliance. |
| Amateur bands (2 m, 70 cm, HF, satellites) | **Amateur license required** — Technician class covers all VHF/UHF privileges relevant here. See [`../../ham-radio/learned/licensing-path-us.md`](../../ham-radio/learned/licensing-path-us.md). |
| Public safety, aviation, marine, GMRS/FRS on this hardware | Not applicable — this build has no transmitter for these services, and using one without authorization is unlawful. |

**This build's only transmitter the dashboard controls is the SX1262 (LoRa).** The RTL-SDR is
receive-only; the Wi-Fi and Bluetooth radios transmit only as ordinary network links.

### Part 15 detail for the mesh radio

§15.247 covers intentional radiators in 902–928 MHz. It has two routes, and single-channel LoRa
fits neither cleanly:

| Route | Requirement | Meshtastic LONG_FAST |
|---|---|---|
| Digital transmission system (DTS) | 6 dB bandwidth ≥ 500 kHz; up to 1 W conducted, 4 W EIRP with a ≤ 6 dBi antenna | 250 kHz — narrower than DTS requires |
| Frequency hopping (FHSS) | hops across many channels with dwell-time limits | doesn't hop |
| §15.249 low-power | field strength ≤ 50 mV/m at 3 m (about −1 dBm EIRP), no bandwidth minimum | fits, but only far below 22 dBm |

Many argue it is covered under hybrid or other provisions, and certified LoRa devices are sold on
this basis; the detail is debated, and this build's own certification is *unverified*. In
practice: keep the region set to US, never raise transmit power, never change channel settings to
"improve" range. There is no duty-cycle limit in the US (unlike the EU's 1 %).

**RF exposure.** The limits are in 47 CFR §1.1310 (and §2.1093 for portable devices); FCC OET
Bulletin 65 describes how to evaluate them. At 22 dBm (about 160 mW) with a small
antenna held away from the body, a device like this is normally far below them; a formal
evaluation for this build hasn't been done (*unverified*). Don't transmit with the antenna
against your body.

## Wi-Fi and Bluetooth

Passive observation of broadcast beacons and probe requests — the basis of WiGLE-style survey — is
what the wardriving discipline covers. Associating without authorization, deauthentication,
handshake capture against networks you do not own, and cracking are out of scope here and
potentially criminal under the CFAA and state law. See
[`../../wardriving/README.md`](../../wardriving/README.md).

## Privacy conventions in this repo

- Record **general** location only: city or Maidenhead grid.
- Do not commit raw captures containing MAC addresses, precise coordinates, or message contents.
- Do not publish anything that identifies an individual's location or activity.

## When in doubt

Ask three questions: *Is it intended for the general public? Am I decoding or just observing?
Am I transmitting under a license or exemption I actually hold?* If any answer is unclear, log
the observation without content and move on.
