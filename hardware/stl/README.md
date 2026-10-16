# Printable parts

3D models and printable parts for this build. The owner's own files are CC BY 4.0 under
[`../../LICENSE`](../../LICENSE). The ClockworkPi-derived files are third-party, see below. Mechanical context and the rules for anything that touches the
pack are in [`../mechanical.md`](../mechanical.md).

## Files

All added by the owner, 2026-10-11. Bambu files are Bambu Studio 02.04.00.70 projects for a
**Bambu Lab A1** at 0.20 mm Standard unless stated.

| File | What it is | Origin / licence | sha256 |
|---|---|---|---|
| `uconsole-3d-models-stp-format-gpl-v3.stp` (35 MB) | The whole uConsole as one STEP assembly. Author field `ClockworkPi.com`, dated 2023-11-23 | ClockworkPi. **GPL-3.0** going by the file name. Third-party | `d95ab58ffa4073a02fa943f57e88f4fb30127465f170ffa9443f48d41da9def0` |
| `1753528-official-clockwork-pi-uconsole-….pdf` | Printables page saved as PDF: "Official Clockwork pi uconsole" by Kilt123, published 2026-06-14, a re-upload of the STEP above | The page labels the model Public Domain. A re-uploader can't relicense ClockworkPi's GPL files, so treat the model as GPL-3.0. Third-party page | `d75bc01ad371fcafdbbc2f254d72562ff41860aea8db6b3386c6bc068666a5dd` |
| `clockworkpi-uconsole.3mf` (6 MB) | The STEP's printable shell parts on 4 plates: 1 the frame, 2 the **stock back cover**, 3 the front panel, 4 the keyboard frame, two strips and the handle (`GUI-JIAO`) | Derived from the STEP, so GPL-3.0. Third-party | `706b1aa8c7f65afa37f2fa983006b6bfaa90317a323ad6982fc94328868ea45a` |
| `clockworkpi-uconsole-backcover-v2.3mf` (6 MB) | The same 4 plates with plate 2 swapped for **`BackCover-v2 (fan+fins+big bay)`**. Plate 2's preview still shows the stock cover (stale thumbnail) | Mix: GPL-3.0 stock parts plus the v2 cover | `b008f56118882a13371e695f8edeed57b2357ab0fa8e5a8231d054d410c28e0b` |
| `back_cover_v2.stl` | The v2 back cover as downloaded: fins, fan mount, and a 122 × 67.4 mm battery bay ≈13.5 mm deep | **MakerWorld** (owner, 2026-10-11). Model URL and licence not recorded. If the licence forbids derivatives (`-ND`), the modified 3MF below can't be shared | `dfef52e458832da53ebcafc5451fe7a49e3f286ffc9e2023fcd44cd1f0655bf7` |
| `back_cover_v2.3mf` | **Modified 2026-10-11/12** for the standoff cage and for two heat sinks in place of the fins and fan (next section). The MakerWorld original is `git show 1e82a6f:hardware/stl/back_cover_v2.3mf` (sha256 `5edd3bc3edf9bb9e1fe55251d29aaa2f3265ef139761b5ff8cb4bbb3cddde503`) | Derivative of the MakerWorld model | `d4a081d0ca98ae4986167bc727665272d4a1ffd528c50195c798032460565a43` |
| `back_cover_v2_cage_bay.py`, `back_cover_v2_write3mf.py` | The scripts that make the modified 3MF from the two originals. Output is byte-identical (checked) | Local, MIT | — |
| `meshnology-10000mah-battery-standoffs.3mf` | Battery cage, below | Owner, CC BY 4.0 | `b6fb41f85d89b289ac205c09947b65bd2dd35a4dca05ffbf1fb822bcebce89fa` |

Every Bambu file has the owner's Bambu account number in `DesignerUserId`. That is an identifier,
not a credential.

## `back_cover_v2` — fan, fins and a battery bay

The **original** (MakerWorld, `back_cover_v2.stl`) is 131.0 × 174.5 × 15.5 mm. A 1.5 mm cover plate
carries a fin field with a fan boss of about 30 mm (*fan size inferred*) over one half, and a
battery bay over the other: 122.0 × 67.4 mm inside, floor ≈13.5 mm past the plate. The standoff cage
(≈120 × 70 × 35 mm) doesn't fit that bay.

### Modified for the standoff cage (`back_cover_v2.3mf`, 2026-10-11)

Owner's brief: the cage slides into guide rails and clips into the cover, the pack sitting 35 mm
proud. All numbers are design values from
[`back_cover_v2_cage_bay.py`](back_cover_v2_cage_bay.py). Coordinates are the STL's, with z = 4.5
the plate's outer face. Nothing has been printed or fitted yet.

| Feature | Design |
|---|---|
| Bay | Old bay removed. New one **122 × 71 mm inside**, 2 mm walls and floor, same centre. Vertical corners rounded to match the original: **6.0 mm outside, 4.0 mm inside**. The original was 6.0 and 4.4 over a 1.6 mm wall. Floor edges square, as on the original. The floor is 35 mm below the plate's outer face, so a seated cage's inner face is **flush with the cover's outer face** and the pack stands **35 mm proud**. Bay outer face is 37 mm proud, and the part is 131 × 174.5 × **39.0 mm** |
| Insertion | The cage goes in from the **inside** of the cover, before the cover is screwed on. Its 35 mm thickness runs along the depth |
| Guide rails | Four channels, two on each long wall, centred on the short frames (x = ±44.55 mm). Each is 4.6 mm wide (4.0 mm band + 0.3 mm a side) between two ribs 1.6 mm wide and 2 mm deep. They run from the floor to 1.2 mm under the latch zone and end in a 45° lead-in chamfer. Clearance to the cage: 1.0 mm at each end, 0.5 mm at the sides, and ≥2.5 mm from rib tips to the pouch |
| Clips | Four cantilever latch beams, one above each channel: 1.6 mm thick, ≈20 mm free length, rooted toward the bay centre, cut free by a 1.2 mm slot through the wall and plate. A local 2 mm bulge on the outside of the wall keeps it closed. Each beam's tip has a barb with a 45° ramp. The barb deflects the beam **1.0 mm** (bending strain ≈0.6 %, *estimate*) and snaps over the top edge of a short frame's end wall, 2.5 mm below the cage face, with 0.2 mm clearance |
| Release | From inside the cover, lever each beam tip outward (toward the bay wall) and lift the cage |
| Leads | The pouch's tab end faces one end wall. Between the long frames there is ≈3.5 mm from the pouch end to the wall for the leads to bend up through the opening. **Dry-fit before relying on it** |

**Checked on the model:** the mesh is watertight, and the corner radii were re-fitted from the mesh (6.0 and 4.0 mm). The inside rounding clears the cage's corners. A cage envelope seated on the floor overlaps
the cover by zero volume. Here the long frames are treated as worst case anywhere across the
pouch width, and the short frames are at their measured positions. Lifted 3 mm, the cage overlaps
only at the four barbs, 1.0 mm each, which is the snap engagement.

### Cyberpunk exterior on the battery box (2026-10-12)

Owner's brief: give the battery box some cyberpunk design elements so it doesn't look boring.
Surface detail only, set by `DECOR` in the script. There are no openings, nothing inside the bay
changes, and walls and floor stay at least 1.4 mm thick.

| Where | Detail |
|---|---|
| Floor edge | 2.5 mm 45° chamfer all round, for a faceted, armour-plate edge. The corner radius steps in to match |
| Floor centre | Raised **armour plate** (1.0 mm, 89.4 × 57.4 mm) with clipped corners, framed by a recessed panel line. It holds a **rounded recess for a copper name plate** (owner, 2026-10-12; it replaced the cut-in FANCY / 1695 lettering). The recess is **85.4 × 53.4 mm**, corner radius 3.2 mm, **1.0 mm deep**, for an **85 × 53 mm** plate with 3 mm corners and 0.2 mm clearance a side. Its floor is the bay floor's outer face, so the full 2 mm floor stays under it. The plate's thickness is unrecorded. `CU_DEPTH` sets the depth (up to 1.6 mm keeps 1.4 mm of floor), and `CU_W`, `CU_H`, `CU_R` set the size |
| Floor, left end | Recessed **hazard stripes** (3 mm at 45°) in a narrower clipped panel (12.5 mm) with its own border line |
| Floor, right end | Three recessed **fake vent slots**, 36 mm long, at 2.2 mm pitch |
| Floor margins | Four raised **circuit traces** (0.8 mm wide, 0.5 mm high, 45° bends) from the plate to **via pads**, two above and two below it |
| Long walls | A **kinked panel line** along each wall, and five slanted slots below its centre. Kept below the latch bulges |
| End walls | Four vertical slots and a cross line |

**Copper name plate, before gluing it in:** confirm its thickness. If it is thicker than 1.0 mm, raise
`CU_DEPTH` so it sits flush, or leave it standing slightly proud. Bond it with a thin epoxy or VHB tape
and allow for that layer in the depth. The recess has no finger notch, so a glued plate isn't meant to
come out.

The raised plate makes the bay **1 mm deeper outside: 38 mm** beyond the cover's outer face (the
pack itself is still 35 mm proud). The part is 40.0 mm tall as printed. All the detail prints
without supports: the floor is the top of the print and the wall detail is vertical. Checks are
unchanged: watertight, the seated cage and sinks don't touch the cover, barbs-only overlap on
insertion.

### Heat sinks in place of the fins and fan (2026-10-12)

Owner's brief: remove the fins behind the CM4 and add two inset areas for **100 × 25 mm** aluminium
heat sinks (**10 mm** tall, fins running **lengthwise**, owner). Leave the area open so the CPU and thermal padding contact the
sinks. Owner's choices: drop the fan; retain the sinks with a ledge and a snug fit.

The original pan over the CM4, measured from the mesh: a 1.25 mm floor (z 1.9–3.15). On the device
side it has a **2.85 mm recess** (x ±57.7, y 5.05–65.45) up to the plate's inner face, apparently
for component clearance. The floor carries the fins, 20 vent slots, a 28.5 mm fan opening, and a
screw post at (0, 6.45).

| Feature | Design |
|---|---|
| Removed | All fins and the fan boss, everything outside the pan floor. The pan, its inside recess, its wall and the screw post are unchanged |
| Pocket | One frame holding the two sinks side by side along y: **100.3 × 51.8 mm** inside (0.15 mm a side, a snug fit). x ±50.15, y 11.2–63.0, clear of the screw post. 1.6 mm walls, **3.0 mm tall** above the cover's outer surface (owner limit, 2026-10-12). They grip the sinks over 3.25 mm, and the fins stand **6.75 mm clear** above the rim. The fins run lengthwise (x), so air passes along the channels above the end walls |
| Two areas | 1.2 mm locating stubs, 6.5 mm long and the same 3 mm height, at both ends of the frame split it into two 25 mm bays. The middle has no divider, so the window is continuous |
| Seat and window | The sinks rest on a **1.5 mm ledge, 1.0 mm thick**. Its inner face is flush with the pan's inner face. The ledge rings **one open window, 97.3 × 48.8 mm**, so the sinks' bases face straight into the recess. Sink base plane: z 2.15, which is **3.85 mm beyond the plate's inner face** |
| Pan floor | The vent slots and fan opening under the frame are closed so the ledge is continuous. The outermost vent slot each side (\|x\| 53.3–54.7) stays open |

**Checked on the model:** seated sinks overlap the cover by zero, and pushed 0.2 mm into the ledge
they overlap it, so they do rest on the ledge. The cage checks are unchanged.

**Open before relying on it:**
- **Thermal pad thickness.** It must span from the CPU to the sink bases, which is the CPU-to-cover
  gap plus 3.85 mm. That gap is unmeasured. Check it with a lump of modelling clay on the CPU and
  the cover screwed down. A copper shim can make up the difference if a single pad would be too
  thick.
- **Window position.** It is centred where the fan was (≈(0, 37)), on the assumption that the
  designer put the fan over the SoC. Confirm the SoC lands inside the window.
- **Retention.** The pad pushes the sinks *outward*, away from the ledge, so only the snug fit holds
  them, now over just 3.25 mm of each sink's side. If they slip, use a bead of adhesive at the rim, or reduce `HS_CLR`.
- Passive cooling only, now the fan is gone. The fins run lengthwise (owner).

**Print setup changed:** tree supports **on**, **build plate only**. The 122 × 71 mm floor prints
as a ceiling 35 mm above the plate, and the supports come out through the opening. The original
project had supports off, because its shallower floor bridged. The rest of the profile (Bambu A1,
0.20 mm Standard) is unchanged. The preview thumbnails are regenerated renders. Bambu Studio
replaces them on save.

**Before printing:**
- Confirm the pouch dimensions, and that the cage fits the 122 × 71 opening, with the cage in hand.
- Confirm that 37 mm of bay won't hit anything behind Fancy, and that the cover screws still reach.
- Use PETG or ASA rather than PLA, for the latch beams' fatigue life and the CM4's heat.
- If the barbs are too stiff or too loose, `BARB_D` (1.5) and `BEAM_FREE` (20) in the script set the
  engagement and flex.

## `meshnology-10000mah-battery-standoffs.3mf`

Standoffs for the Meshnology 10000 mAh LiPo pack (owner, 2026-10-11). Bambu Studio 02.04.00.70
project, one plate, set up for a **Bambu Lab A1, 0.4 mm nozzle, 0.16 mm High Quality**, 2 walls,
15 % infill. The filament is not recorded in the file.

Measured from the mesh. Contact dimensions are to ±0.05 mm, notch positions to ±0.5 mm.

| Part | Qty | Outer | Opening | Walls | Feature |
|---|---|---|---|---|---|
| Long frame | 2 | 35 × 120 × 4 mm | 24.5 × 115 mm | 5.25 mm long sides, 2.5 mm ends | Inside notch on each long side ≈13.5–18 mm from each end, cutting the wall to 2.5 mm, ≈4.5 mm wide |
| Short frame | 2 | 30 × 70 × 4 mm | two 11.0 × 62 mm slots | 2.88 mm sides, 4 mm ends, 2.24 mm divider | Divider down the middle, one slot per pouch |

sha256 of the committed file: `b6fb41f85d89b289ac205c09947b65bd2dd35a4dca05ffbf1fb822bcebce89fa`.

### How the parts go together

Read from the mesh and the inventory photo
[`20261011-lipo-meshnology-frame-and-lead.jpg`](../../images/inventory/20261011-lipo-meshnology-frame-and-lead.jpg),
where the frames are fitted. The photo shows two bands along the pack and two across it. A photo
reading, *unverified* in detail:

| Part | Wraps | What it does |
|---|---|---|
| Short frames, near each end | Around the **width** of the two-pouch stack (62 mm) | One pouch in each 11.0 mm slot. The 2.24 mm divider keeps an air gap between the pouches, and the 4 mm end walls cap the long edges |
| Long frames, at about ⅓ and ⅔ of the width | Around the **length** of the stack (115 mm), crossing over the short frames | Their 2.5 mm ends wrap the pack ends. Their notches take the short frames' 2.88 mm walls almost flush (notch depth 2.75 mm), so at each crossing the short frame fits inside the long frame's 30.0 mm inside width. That locks the four parts together |

Why they are **standoffs:** the long frames' 5.25 mm walls stand proud of both pouch faces, about
2.4 mm more than the short frames. So the pack rests on two rails and sits **≈5.25 mm off the board**.
That keeps an air gap between the pouch and the CM4 and NVMe drive, and lifts the pouch over the
raised holder remnants on the NVMe board (build log, 2026-10-11).

**Assembled envelope:** ≈35 × 70 × 120 mm (thickness × width × length), from the frame outer sizes.

### Checks before it goes in the shell

- **The fit has no slack.** The slots are 11.0 × 62 mm, and the long frame opening is 115 mm long and
  24.5 mm thick, against the pack's 24.24 mm stack. The model number 1163115 suggests a pouch of
  11 × 63 × 115 mm (naming convention, *unverified*). That is level with the slot thickness and
  1 mm wider than it. Measure the pouches. If a frame is pressing on the pouch, it breaks the "never
  compress the pouch" rule in [`../mechanical.md`](../mechanical.md#rules-for-the-modification).
  Re-slice with 0.5–1 mm clearance if so.
- **The long frames' ends cross the tab end of each pouch,** where the protection board and lead
  exit sit. Check that nothing presses on the tabs or pinches the leads.
- **35 mm thick in total.** The rear cavity depth with the cover on is still unmeasured
  (`mechanical.md`). Confirm the cover closes without touching the frames' outer faces.
- **Material:** not recorded in the file. PLA softens around 55–60 °C, and the CM4 and NVMe drive
  run warm under load. PETG or ASA is safer for parts that hold the pack.
