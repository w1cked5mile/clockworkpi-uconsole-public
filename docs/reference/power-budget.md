# Power budget & battery runtime

The **Measured** section is from this build (2026-09-23). Everything else is an estimate from
component-class typicals, labelled as such, and exists to be falsified. Replace estimates with
`aiov2_ctl --power` / `--measure` readings (bring-up test section 4) as they come in.

Runtimes are sized against the **pack of record, the Meshnology 10000 mAh / 37 Wh LiPo** (≈31 Wh
usable). The 18650 pair fitted today has **no known capacity**, so it gets no runtime figure.

## Battery: the system is 1S

The mainboard's PMIC is an **AXP228** — a single-cell Li-ion part, battery input 3.6–4.2 V with an
integrated charger. Confirmed from `clockwork_Mainboard_V3.14_Schematic.pdf` (nets `VBAT`,
`BATSENSE`, `N_BATDRV`, `PGND_CHG`, connector `J101`) and corroborated by `aiov2_ctl`, which reads
`/sys/class/power_supply/axp20x-battery` and `axp22x-ac`.

Consequence: **the two 18650 positions are in parallel, not series.** An earlier revision of this
document said series at 7.4 V — that was wrong. Pack energy happens to be unchanged, but the
voltage and the failure modes are not.

## Two supported battery options

The HackerGadgets NVMe battery board accepts either, selected by a solder jumper:

| Option | Configuration | Energy | Notes |
|---|---|---|---|
| 2 × 18650 (**fitted, interim**) | BAT1 + BAT2 positions, **parallel**, 3.7 V nominal | **unmeasured** — the ≈22 Wh figure assumed 3000 mAh matched cells | The cells fitted on 2026-09-16 are unbranded and wrapped `9900mAh`, a physically impossible claim, so **no capacity figure here applies to them**. They sit in the NVMe battery board's holder until the Meshnology pack replaces them. They still need weighing and a capacity test — [`../logs/known-issues.md`](../logs/known-issues.md) |
| 1S LiPo pack (lithium-polymer flat pack) | JST connector (a small keyed plug), 3.7/3.85 V nominal | **selected pack: Meshnology, 3.7 V × 10 Ah = 37 Wh** | ~1.7× the 18650 pair; no cell matching; pack must fit the rear cavity, and a case modification is accepted to make it fit |

*Pack swapped 2026-09-14: the originally selected UDIY-0001L (15 Ah / 55.5 Wh) was dropped for a
Meshnology 10 Ah / 37 Wh pack, already on hand, due to the UDIY-0001L's long shipping time — see
[`../logs/decisions.md`](../logs/decisions.md).*

**JP1 selects the mode.** Board silkscreen, transcribed from a photograph — *confirm on the
physical board before powering*:

> "Solder JP1 for disperse current when using JST for Lipo battery pack. Must let it open for
> 18650 batteries."

So: **JP1 closed → JST LiPo pack. JP1 open → 18650 cells.** Getting this wrong is a current-path
error on the battery rail, not a cosmetic setting.

| Attribute | 2 × 18650 | 1S LiPo (selected: Meshnology) |
|---|---|---|
| Nominal voltage | 3.7 V | 3.7 V |
| Pack energy | ≈ 22 Wh | **37 Wh** (10000 mAh) |
| Usable energy | ≈ 17–19 Wh | ≈ 30–32 Wh |
| JP1 | open | soldered closed |
| Cell matching | required (parallel cells at different states of charge push current between each other on first connection) | not applicable |

Runtime = usable Wh ÷ average system watts.

## Measured (supersedes rows below where they overlap)

2026-09-23, on battery via `aiov2_ctl --status` / `--measure`, NVMe root, screen on. Measured at the
cell, so these are not directly comparable to the 5 V-side estimates below. Full numbers are in
[`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md) §4.

| State | Measured |
|---|---|
| GPS + LoRa rails on, SDR/USB off, idle desktop | **~5.3 W** (1.44–1.46 A at 3.66–3.68 V) |
| SDR rail Δ | +0.64 W |
| GPS rail Δ (no fix) | +0.29 W |
| LoRa rail Δ (idle RX) | ≈ 0 |
| Peak seen (SDR + USB on, `rtl_test` starting) | 7.3 W / 2.01 A |

The measured idle is **above** the 3.0–4.5 W estimate, so the runtime table below is built on
the measured ~5.0 W floor, not on the estimates. Because these readings are at the cell, they
divide straight into pack Wh with no converter-loss factor. The ~5.0 W floor had session shells
running; a clean idle with the screen blanked is still to measure.

Charging (measured 2026-09-23): **1.96 A at 3.95–3.96 V** into the pack (~7.7 W), from
`axp20x-battery` with the charger connected.

## Estimated draw by state (5 V system side)

| State | Est. current | Est. power | Basis |
|---|---|---|---|
| Idle, display on, all AIO rails off | 600–900 mA | 3.0–4.5 W | CM4 + panel + backlight, class typical |
| Display off / blanked | −150 to −250 mA | −0.8 to −1.2 W | backlight dominates |
| CPU sustained load (4 cores) | +400–700 mA | +2–3.5 W | BCM2711 under load |
| NVMe idle | +30–80 mA | +0.2–0.4 W | drive-dependent |
| NVMe sustained read/write | +200–600 mA | +1–3 W | burst, not continuous |
| **SDR rail on**, `rtl_test` streaming | +250–350 mA | +1.3–1.8 W | RTL2832U + R860 class typical |
| GPS rail on, acquiring | +30–50 mA | +0.2 W | drops after fix |
| GPS rail on, tracking | +20–30 mA | +0.1 W | |
| LoRa rail on, RX/listen | +10–20 mA | +0.1 W | SX1262 RX |
| LoRa TX burst @ 22 dBm | +120–150 mA (3.3 V side) | ~0.5 W | milliseconds per packet; negligible average at low duty cycle |
| Ethernet link up (RJ45 board) | +150–250 mA | +0.8–1.3 W | PHY + USB bridge |
| AC1200 card, monitor mode | +200–350 mA | +1–1.8 W | if fitted |

## Runtime scenarios (Meshnology 37 Wh pack)

Base = the **measured** ~5.0 W idle floor. Measured deltas are marked *(m)*; the rest come from
the estimate table above *(e)*. Usable energy is taken as ~31 Wh (≈85 % of 37 Wh), which is
itself an estimate until the pack is discharge-tested.

| Scenario | Build-up of average draw | Avg draw | Runtime on ~31 Wh |
|---|---|---|---|
| Terminal work, screen on, no radios | 5.0 *(m)* | ~5.0 W | **~6 h** |
| Meshtastic node, screen mostly off | 5.0 *(m)* − ~1.0 backlight *(e)* + LoRa ≈0 *(m)* | ~4.0 W | **~7.5 h** |
| ADS-B / SDR receiving, screen on | 5.0 + 0.64 SDR rail *(m)* + ~0.5–1 streaming + decode *(e)* | ~6.2–6.6 W | **~4.7–5 h** |
| Wardriving: AC1200 monitor + GPS + screen | 5.0 + 0.29 GPS *(m)* + 1–1.8 AC1200 *(e)* | ~6.3–7.1 W | **~4.4–4.9 h** |
| Everything on (SDR + LoRa + GPS + Ethernet + CPU load) | 5.0 + 0.93 rails *(m)* + ~1 Ethernet + 2–3.5 load *(e)* | ~9–10.5 W | **~3–3.4 h** |

These replace the earlier table, whose 2.5–3.5 W averages came from estimates the 2026-09-23
measurement showed were ~1.5 W low; its terminal-work figure of ~9 h is now ~6 h.

**Still to measure** before these become measurements: a full discharge of the Meshnology pack
(real usable Wh), clean idle with the screen blanked, SDR while `readsb` is actually decoding, and
the AC1200 once it arrives.

**Charge time:** at the measured ~1.96 A, 10 Ah takes roughly 5 h in the constant-current phase
plus a constant-voltage taper, so expect **~6 h from empty** *(estimate — log a full charge to
confirm)*.

## Why the SDR rail default matters

Upstream `BOOT_DEFAULTS` in `aiov2_ctl` sets the SDR rail (BCM 7) **on**. If CM4 behaves the same
way, every boot starts ~1.5 W into the budget — roughly an hour of runtime in the terminal-work
scenario — for a radio nothing is using.

Check and, if confirmed, change it:

```bash
aiov2_ctl --status                 # rail state after a cold boot
aiov2_ctl --boot-rails-status      # what the boot service applies
aiov2_ctl --boot-rail SDR off      # persist SDR off at boot
```

## Reading the power numbers

The Power station and `aiov2_ctl --status` report what the PMIC (the power-management chip, an
AXP228) measures at the cell.

| Field | Example | Meaning |
|---|---|---|
| `source` | `AC` / battery | whether the charger is connected |
| `direction` | `charging` / `discharging` | which way current flows through the pack |
| `voltage` | `4.2 V` | cell voltage. A 1S Li-ion cell runs about 4.2 V full to about 3.0 V empty; under load it sags |
| `current` | `0.17 A` | current into or out of the pack |
| `power` | `0.71 W` | voltage × current at the cell. **On AC while charging, this is not what the device draws** — the charger supplies the system directly |
| `capacity` | `100%` | the PMIC's fuel-gauge estimate (voltage plus a coulomb count; how the AXP228 is configured here is *unverified*); rough until it has seen a full cycle |

To measure what something costs, read `power` **on battery**, before and after, with everything
else unchanged. That is how the SDR rail's +0.64 W was measured (the Measured table).

**Energy and runtime.** Energy in watt-hours is voltage × amp-hours: the planned Meshnology pack,
3.7 V × 10 Ah, holds about 37 Wh. Runtime ≈ usable Wh ÷ average W — 37 Wh at the ~5 W idle is
about 7 h, less once the usable fraction is known (*estimate* until a full discharge is measured).
The idle figure is ~5.0 W: the 5.3 W row in the Measured table had extra programs running.

**Why "9900 mAh" on an 18650 is implausible.** An 18650 cell is 18 mm × 65 mm. The best cells of
that size hold about 3,500 mAh; a label claiming 9,900 mAh is claiming nearly three times what
the chemistry fits in that volume. Treat such cells as unknown until weighed and capacity-tested
(CLAUDE.md blocker) — and never rely on them for a long battery lab.

**Series or parallel.** The AXP228 is a single-cell (1S) charger, so two 18650s sit in
**parallel**: same 3.7 V nominal, capacities add. In series they would be 7.4 V, which a 1S
charger must never see.

## Charging

- Input is USB-C on the mainboard; use a **5 V ≥ 3 A** supply. A 5 W phone charger will charge
  slowly or not at all while the system runs with radios enabled.
- Charge current and termination are handled by the PMIC and the NVMe battery board; read state
  with `aiov2_ctl --power` or directly:

```bash
grep . /sys/class/power_supply/axp20x-battery/{status,voltage_now,current_now,capacity} 2>/dev/null
grep . /sys/class/power_supply/axp22x-ac/online 2>/dev/null
```

## Battery safety

**If using 18650s (JP1 open):**

- Use a **matched pair** — same make, model, capacity, and state of charge. Cells in parallel at
  different states of charge drive current into each other the moment they are connected; a large
  delta means a large inrush.
- Measure each cell's resting voltage before install (~3.6–3.8 V for storage charge, both within
  ~0.05 V of each other).
- Verify orientation before first power-on; the reverse-polarity LED is a diagnostic, not a fuse.
- Do not install a deeply discharged (<2.5 V) cell; replace it.

**If using a 1S LiPo pack (JP1 soldered):**

- The pack must be **single cell** (3.7 or 3.85 V nominal). A 2S pack would present ~7.4 V to a
  charger that expects one cell.
- Confirm JST polarity against the board before connecting — connector keying is not a guarantee
  that a third-party pack is wired the same way.
- Prefer a pack with integrated protection (over-discharge, over-current).
- Check physical fit in the rear cavity, and that leads are not pinched when the cover closes.
