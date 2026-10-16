# Mechanical notes — clearances, fasteners, routing

Pre-arrival working notes. Every dimension marked *measure* is to be filled in at inventory or
trial fit — do not order thermal material or cells against these until measured.

## Stack-up (bottom to top, as assembled)

1. ClockworkPi v3.14 mainboard (95 × 77 mm)
2. HackerGadgets adapter board + CM4 (55 × 40 mm module, two 100-pin connectors)
3. NVMe battery board — M.2 SSD + 18650 holder
4. AIO V2 on the 52-pin extension connector
5. RJ45 + USB 3.0 side board
6. Shell halves, side plates, screen, keyboard

Assembly order and gotchas: [`../docs/runbooks/assembly.md`](../docs/runbooks/assembly.md).

## Clearances to measure at trial fit

| Gap | Why it matters | Value |
|---|---|---|
| CM4 SoC → shell/shield | Thermal pad thickness (1.0–1.5 mm typical) | *measure* |
| M.2 SSD → adjacent board | Whether a heatspreader or pad fits | *measure* |
| 18650 holder height → shell | Protected cells run ~2–3 mm longer than unprotected | *measure before buying cells* |
| AIO V2 → shell (antenna side) | u.FL lead routing without pinching | *measure* |

## Battery cavity and planned case modification

The pack of record is a **1S LiPo (Meshnology 1163115, 10000 mAh, 37 Wh)** rather than 18650 cells
(it replaced the UDIY-0001L chosen 2026-09-07; see
[`../docs/logs/decisions.md`](../docs/logs/decisions.md)), and a case modification is accepted if the pack does not drop in.
**Fitted 2026-10-11:** both packs in parallel on a Y harness, `JP1` bridged, holder removed (see the
build log). Not yet dry-fitted under the closed cover. Nothing here is measured yet.

| Dimension | Value |
|---|---|
| Pack: length × width × thickness | *measure* |
| Pack: lead length from pouch to connector | *measure* |
| Rear cavity: length × width | *measure* |
| Rear cavity: usable depth with the cover on | *measure* |
| Clearance over the NVMe drive and the CM4 | *measure* |

**Printed standoffs (2026-10-11):** the owner added a Bambu Studio project for four 4 mm
standoff frames for the pack: [`stl/README.md`](stl/README.md). They cage the two-pouch stack and hold it
≈5.25 mm off the board. The envelope is ≈35 × 70 × 120 mm, to be checked against the cavity depth.

**Printed back cover v2 (2026-10-11):** a MakerWorld rear cover with fins and a fan mount, its
battery bay **reworked for the standoff cage**: 122 × 71 mm, the cage clipped in 35 mm proud on guide
rails with four snap latches. Its fins and fan are replaced by two 100 × 25 × 10 mm heat sinks over an open
window onto the CM4. Design, checks and print notes are in [`stl/README.md`](stl/README.md).
Not yet printed or fitted.

### Rules for the modification

These are not preferences — a pouch cell fails differently from a cylindrical one:

- **Never compress the pouch to close a cover.** If it does not fit, remove material from the case,
  not from the pack's clearance. Swelling is a normal end-of-life behaviour and needs room.
- **No sharp edges, swarf, or screw tips facing the pouch.** Deburr anything cut, and line the
  cavity if the modification exposes a rib or boss.
- **Strain-relieve the leads** and keep them clear of screw bosses and the cover's mating surface.
  The lead exit is the most likely place for an internal short.
- **Keep the pack off the heat sources** — the CM4 and the NVMe drive both run warm under load.
- **Do not cut structural ribs or standoff bosses** without deciding how the shell keeps its
  stiffness; the display and keyboard are located off that structure.
- Re-check that the cover still seats fully with the pack, leads, and connector in place, and that
  nothing is pinched at close-up.

### Sequence

1. Measure pack and cavity.
2. Decide: drop-in, trim, or a printed replacement rear cover.
3. Dry-fit with the pack **disconnected**.
4. Only then connect, with `JP1` soldered closed and polarity confirmed.

## Fastener map

Photograph the screw bag layout before the first screw comes out, then fill this in — screw
lengths differ per stage and mixing them strips standoffs.

| Stage | Screw type / length | Qty | Notes |
|---|---|---|---|
| CM4 → adapter | | | |
| M.2 SSD retention | | | 2230/2242/2260/2280 standoff position |
| Battery board → mainboard | | | |
| AIO V2 → mainboard | | | |
| Side plates / shell | | | |

## Antenna routing

- Three u.FL leads on the AIO V2: **SDR**, **LoRa**, **GPS**. Confirm which pad is which against
  the silkscreen before mating — u.FL connectors tolerate roughly 30 mating cycles.
- Route away from the display FPC and the battery leads; do not trap coax under a standoff.
- Press u.FL straight down with the connector flat; angled pressure shears the shell.
- Record which physical SMA/plate position ends up mapped to which function — it is not
  self-evident once the shell is closed.

## Thermal

- CM4 under a sealed shell with no fan is passively cooled through the pad and shield: expect
  throttling under sustained load, and verify with `vcgencmd get_throttled` (test 1.4 in the
  bring-up checklist).
- The adapter exposes a PWM fan header if measurements justify one.
- NVMe SSDs idle warm; a thin pad to the shield is usually enough and costs nothing in clearance
  if measured first.
