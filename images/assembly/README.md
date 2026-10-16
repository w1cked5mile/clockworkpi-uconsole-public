# Assembly & commissioning photographs

Milestone frames of the assembled device — distinct from the as-received warranty evidence in
[`../inventory/`](../inventory/README.md). Committed copies are downscaled to a 1600 px long edge;
the full-resolution originals are kept off the repository and identified by the checksum of the
original file.

## 2026-09-25 — "Fancy" assembled, booted, and commissioned

| File | Subject | Source file | sha256 (source) |
|---|---|---|---|
| [`20260925-fancy-open-booted-placard.jpg`](20260925-fancy-open-booted-placard.jpg) | Device open and running — engraved copper lid plate raised, Debian desktop up on the main display, gamepad cluster (Y/X/B/A), trackball, D-pad and keyboard visible. Lid placard reads `NAME FANCY`, `OPERATOR WICKEDSMILE`, `OS DEBIAN ARM64`, radios `RTL-SDR / LORA / GPS / WIFI 2.4 / 5 / 6 GHZ / BLUETOOTH`, `COMMISSIONED 2026`. Placard text is a photo reading — *unverified* against the running configuration | 1932x2576, 1.5 MB | `fa1e1336bb541d637507d1d689c07380e3daf7154d168782540d15d09555fce2` |
| [`20260925-fancy-lid-plate-detail.jpg`](20260925-fancy-lid-plate-detail.jpg) | Engraved copper lid plate, close — steampunk gear-train motif, `FANCY` title, chain border, banner motto `TEMPUS NEMINEM EXPECTAT`; the top-edge antenna strip and `clockwork` badge behind it | 1932x2576, 1.7 MB | `34c9fcbe31c383bd544f1c83845dd70b0f2c102587333bbe16ddad7ca444feda` |
| [`20260925-fancy-front-angle-lid-open.jpg`](20260925-fancy-front-angle-lid-open.jpg) | Three-quarter view, lid folded forward — full front face: keyboard, D-pad, L/R and gamepad buttons, trackball, and the top-edge SMA antenna bank fitted | 1932x2576, 1.5 MB | `f03d6c18e07d1ef5d4cee41c0c6134d1089183ab51dadd24f2bf1ff1b85450b5` |

The frames carry no usable EXIF — no `DateTimeOriginal`, camera make/model, or GPS block on any of
the three; the `20260925-*` prefix is the date the files were supplied to the documenting session.
The checksums above are of the files as supplied, which may already be a phone-side downscale of the
camera original. If the camera originals still exist, record their checksums here and correct the
"Source file" column.

## 2026-10-11 — NVMe battery board modified for the Meshnology LiPo

Owner-stated: the 18650 holder was removed from the HackerGadgets NVMe battery board and `JP1` was
soldered closed, so the board takes the 1S LiPo pack on the JST connector. Everything below beyond
that statement is a *photo reading, unverified* — `JP1` continuity has not been metered, and no
frame shows the LiPo connected.

| File | Subject | Source file | sha256 (source) |
|---|---|---|---|
| [`20261011-nvme-board-holder-removed-overview.jpg`](20261011-nvme-board-holder-removed-overview.jpg) | **Overview, holder removed** — CM4 on the Adapter Pro and AIO V2 under the frame bar; NVMe battery board with the `BAT1`/`BAT2` outline empty and four tinned pad remnants where the holder contacts were; the WD SN730 fitted below. See the redaction note | 2576x1932, 1.5 MB | `56b5badbb755f37126c78d69d0933d4e46ee49c31828de3b9900929880381f9f` |
| [`20261011-nvme-board-jp1-closed-closeup.jpg`](20261011-nvme-board-jp1-closed-closeup.jpg) | **`JP1` close-up** — pads appear bridged with solder; location: right of the 2-pin JST connector and `R14`, on the top edge of the `BAT2` outline, with the silkscreen note's arrow pointing to it. Silkscreen legible: "Solder JP1 for disperse current when useing JST to connect Lipo battery pack. Must let it open for 18650 batteries." | 2576x1932, 1.4 MB | `e50bd93fc40356f2399b7b6bf85d1be81ed316f87d51e9bffa9009cae8312363` |
| [`20261011-nvme-board-jp1-closed-ac1200.jpg`](20261011-nvme-board-jp1-closed-ac1200.jpg) | Same board, wider — `JP1` bridged, JST connector empty, AC1200 card with its antenna pigtails at the right edge. See the redaction note | 2576x1932, 1.4 MB | `29e6b707d3a20df073d98e61d60ec5e5380bf17a9df0007400994d052f53aa12` |

**Redaction.** Two frames include the SSD label, and at 1600 px its PSID (the OPAL revert code) was
legible. The committed copies have that line and both 2D codes blacked out, per the handling note
in [`../inventory/README.md`](../inventory/README.md). The source files are unredacted — keep them
off the repository. Frames carry no usable EXIF and no GPS block.

## 2026-10-12 — Back cover v2 printed, LiPo bay and copper name plate fitted

Owner-supplied frames of the printed `back_cover_v2` ([`../../hardware/stl/README.md`](../../hardware/stl/README.md))
on the device. Everything in the Subject column is a *photo reading, unverified*.

| File | Subject | Source file | sha256 (source) |
|---|---|---|---|
| [`20261012-back-cover-v2-open-lipo-tray.jpg`](20261012-back-cover-v2-open-lipo-tray.jpg) | **Cover open beside the device.** Left: CM4 on the Adapter Pro, AIO V2, 7x SMA quick-mount bar, NVMe battery board with the `BAT1`/`BAT2` outline empty, WD SN730 fitted; green LED lit top-left and red LED lit beside the SSD. The red LED sits where the 2026-10-11 overview frame shows the board's `PWR` silkscreen, so it reads as the power LED, not the reverse-polarity indicator (that one is labelled `Battery Reverse Warning`, at the right edge of the `BAT1`/`BAT2` outline, hidden here by the AC1200 card and the lead). A red/black lead leaves the board's 2-pin JST and splits into **two mated 2-pin connectors**, each to a red/black pair routed into the cover. Right: printed cover with a **Meshnology 10000 mAh 3.7 V (37 Wh) pack** held by two straps in the lower pocket; the upper pocket is the heat-sink window, and the white layer in it is most likely the heat sink's thermal pad, which lands on the CM4's blue pad when the cover closes. The two `−` holder remnants at the left edge of the outline show no Kapton in this frame; the `+` pair is not visible. Whether two packs are wired in parallel is *unverified*. See the redaction note | 2576x1932, 1.5 MB | `2c18ab065c0dc03e19e8c25e9eb2dcaa299f5c0db8ffc94d612b1a5640cfce10` |
| [`20261012-back-cover-v2-closed-copper-plate.jpg`](20261012-back-cover-v2-closed-copper-plate.jpg) | **Cover closed, rear view.** Finned heatsink exposed through the cover window; battery box with the copper name plate seated in its recess — legible fields `NAME FANCY`, `OPERATOR WICKEDSMILE` (partly obscured), `OS DEBIAN ARM64`, `FREQ RTL-SDR / LORA / GPS / WIFI 2.4 / 5 / 6 GHZ / BLUETOOTH`, `COMMISSIONED 2026` (year partly obscured); chain border; 7x SMA bar fitted with six rubber-duck antennas and the puck antenna; right-angle SMA whip on the right side. Plate thickness and fit flush/proud not measurable from the frame | 1932x2576, 1.3 MB | `a7de7c6d22cbd918c4113fea79c68f896e8d8506098da365b2d3b1be823e70b3` |

**Redaction.** The open-cover frame shows the SSD label. The committed copy has the PSID, serial
and part-number block, linear barcodes and both 2D codes blacked out. The source file is
unredacted — keep it off the repository. Neither frame carries usable EXIF or a GPS block.

## Convention

Same as [`../inventory/README.md`](../inventory/README.md): keep originals off-repo, commit
downscaled copies, and treat anything read off a frame — placard text, silkscreen, connector types —
as a photo reading marked *unverified* until confirmed against the device.
