# Antennas & RF interconnect

What each radio on the AIO V2 needs, and what breaks if it gets the wrong thing.

## Per-function requirements

| Function | Frequency | Antenna that works | ¼-wave whip length | Notes |
|---|---|---|---|---|
| LoRa / Meshtastic | 902–928 MHz (US915) | 915 MHz whip, SMA | ≈ 82 mm | **Required before any TX.** Transmitting into an open port risks the SX1262 PA. |
| ADS-B | 1090 MHz | 1090 MHz collinear or ¼-wave + ground plane | ≈ 69 mm | Biggest single range factor; height beats gain. |
| Broadcast FM / VHF / UHF scanning | 88–500 MHz | Telescopic dipole, adjusted per band | λ/4 = 75 / f(MHz) metres | A dipole re-tuned per band beats a fixed whip. |
| GNSS | 1575.42 MHz (L1) | Active patch (preferred) or passive ceramic | — | Active needs DC bias; clear sky view matters more than gain. |
| HF (<24 MHz) | 0.1–24 MHz | Not usable as-is | — | The R860's "100 kHz" low end needs direct sampling or an upconverter — treat HF as out of scope for the stock board. |
| Wi-Fi / BT (AC1200) | 2.4 / 5 / 6 GHz | 4 × IPEX antennas supplied with the card | — | Monitor-mode work wants all antennas fitted. |

Quarter-wave rule of thumb: **length (mm) ≈ 75 000 / f (MHz)**, then trim ~5 % for end effect.

## Port mapping — this build

Decided 2026-09-15, and **fully corroborated** the same day. An edge-on photograph of the closed
device reads every fitted antenna's marking in order — `LoRa`, `Bluetooth`, `Bluetooth`, `Wi-Fi`,
`Wi-Fi`, `Wi-Fi`, then the GNSS puck — which matches this table row for row. The vendor's antenna
set is labelled by function and was installed accordingly; the mapping is not merely a plan.

The breakout strip is a **passive 1:1 fanout** (each `ANTn` u.FL feeds the SMA
beside it), so `ANTn` numbers carry no function of their own — this table *is* the assignment.
Once the shell is closed the jacks are indistinguishable, and two of them are hazardous to guess
at, so treat this as the authoritative record and label the exterior to match.

| Source | Lands on | Antenna fitted | Notes |
|---|---|---|---|
| AIO V2 `SDR` u.FL | **Bulkhead SMA** through the shell — *not on the strip* | telescopic whip | **5 V bias tee on this port.** Being physically off the strip is the useful property: it cannot be confused with the others by feel. |
| AIO V2 `LoRa` u.FL | `ANT1` | stub marked **`LoRa`** — fitted | The only TX port. Keep an antenna on it whenever the rail is enabled. |
| BT1 — AC1200 | `ANT2` | stub marked **`Bluetooth`** — fitted | Antenna on, **card not yet delivered — no radio behind it**. |
| BT2 — AC1200 | `ANT3` | stub marked **`Bluetooth`** — fitted | Antenna on, **card not yet delivered — no radio behind it**. |
| Wi-Fi 1 — **CM4 onboard u.FL** | `ANT4` | stub marked **`Wi-Fi`** — fitted | **Needs `dtparam=ant2`** — see below. |
| Wi-Fi 2 — AC1200 | `ANT5` | stub marked **`Wi-Fi`** — fitted | Antenna on, **card not yet delivered — no radio behind it**. |
| Wi-Fi 3 — AC1200 | `ANT6` | stub marked **`Wi-Fi`** — fitted | Antenna on, **card not yet delivered — no radio behind it**. |
| AIO V2 `GPS` u.FL | `ANT7` | GNSS puck — fitted | Position forced by clearance, not chosen. |

*Mapping is the builder's record; the 1:1 passivity of the strip is inferred from layout and
**not yet traced**. Continuity from each `ANTn` centre pin to its adjacent SMA centre confirms it.*

### Three things this mapping implies

1. **`ANT4` does nothing until `dtparam=ant2` is set.** The CM4's onboard PCB antenna and its u.FL
   are mutually exclusive and the choice is made in software
   ([`../../hardware/specs/cm4-lite-8gb.md`](../../hardware/specs/cm4-lite-8gb.md)). Landing a lead
   on `ANT4` without that line leaves the module still using its internal antenna — the external
   one is simply inert, with no error to tell you. Regulatory note from the same file: the
   FCC/IC/KCC grants cover the module with its *certified* antenna, so an external whip is an
   integrator decision.
2. **`ANT7` carries no bias.** The bias tee is on the **SDR** path, not GPS. If the puck is an
   *active* antenna it needs DC from somewhere, and `ANT7` is the one port in this mapping that
   cannot supply it. Whether the AIO V2 feeds DC on its GPS path is unconfirmed — the spec sheet
   says only "active or passive antenna". Settle it before blaming sky view for a missing fix:
   measure for DC on the `ANT7` centre pin with the GPS rail enabled (`aiov2_ctl GPS on`).
3. **`ANT1` is the only port that transmits.** A stub marked `LoRa` is fitted. Keep an antenna on
   it whenever the rail is enabled — keying the SX1262 into an empty or badly matched port is the
   PA-damage case in the spec sheet. The **jacks** are still unlabelled; the antennas carry the
   labels, so if a stub comes off, this table is the only record of what belongs there.

### What drives BT1/BT2 and Wi-Fi 2/3 — resolved 2026-09-16

The **AC1200 USB-C Wi-Fi card** (MediaTek MT7921AUN, Wi-Fi 6/6E + BT 5.2, 4 × IPEX). It is part of
the build and is now BOM item 7 as a specified component, ordered from HackerGadgets as
[order #12253](../records/order-and-warranty.md). Its four leads are `ANT2`/`ANT3`
(BT1/BT2) and `ANT5`/`ANT6` (Wi-Fi 2/3).

**It has not arrived.** #12253 is a pre-order placed 2026-09-15 with no ship notice as of
2026-09-16. The shell was closed 2026-09-15 with **all four positions having antennas screwed
on but no radio behind them** — an antenna fitted is not a radio connected. Only `ANT1` (LoRa),
`ANT4` (CM4 onboard Wi-Fi), `ANT7` (GPS) and the SDR bulkhead have a radio today.

On CM4 the card runs at USB 2.0 regardless of its USB-C 3.2 Gen1 interface.

## Connectors

| Connector | Where | Cautions |
|---|---|---|
| u.FL / IPEX MHF1 | AIO V2 board pads, AC1200 card | ~30 mating cycles; press flat and straight; lift-off with a proper tool, never by the coax |
| SMA / RP-SMA | External antennas and pigtails | **Check polarity** — RP-SMA (common on Wi-Fi gear) will not mate correctly with SMA RF gear |
| 1.13 mm coax pigtail | u.FL → SMA bulkhead | Keep short; loss at 1 GHz is meaningful over long runs |

## The bias tee

The AIO V2's RTL-SDR path includes a **5 V bias tee**. Consequences:

- Do not attach a DC-shorted antenna (many discone and mobile whips are DC-grounded) while the
  bias tee is enabled — it shorts the supply.
- Do attach it deliberately when powering an LNA or an active GPS/ADS-B preamp.
- Confirm the enable path (software vs jumper) on the shipped board revision at inventory; record
  the answer here. **Still open as of 2026-09-16:** the rear I/O plate carries a `Bias-T` silkscreen
  beside a small aperture, which locates the function but does not say whether the rail is switched
  by `aiov2_ctl` or a jumper, nor whether that aperture is an indicator LED or a switch.

## Inventory expectations

Which antennas ship with the AIO V2 varies by listing and revision. At inventory, count:

- u.FL pigtails on/with the board — **7 counted 2026-09-15**, matching the 7 `ANTn` positions
- external whips supplied, and their labelled bands — **8 counted**; the six stubs are marked
  `LoRa` ×1, `Bluetooth` ×2, `Wi-Fi` ×3, plus the GNSS puck and the telescopic SDR whip
- SMA vs RP-SMA polarity on each — **breakout jacks confirmed standard SMA female**; the antenna
  connectors themselves are still unread, so whether the set mates is open

Missing pieces go on the buy list in [`../accessories.md`](../accessories.md).

## Safety and legality

- Receive-only across these bands is broadly legal in the US; **transmitting** on LoRa/ISM is
  license-free only within Part 15 limits, and amateur bands require a license. See the
  responsible-use section in [`../../knowledge/README.md`](../../knowledge/README.md).
- Never key a transmitter into an unterminated port, and keep the LoRa antenna out of direct body
  contact during TX.
