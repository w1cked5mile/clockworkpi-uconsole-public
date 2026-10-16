# Power budget & battery runtime

The **Measured** section is from this build (2026-09-23 onward). Everything else is an estimate
from component-class typicals, labelled as such, and exists to be falsified. Replace estimates with
`aiov2_ctl --power` / `--measure` readings (bring-up test section 4) as they come in.

The fitted pack is **both Meshnology 10000 mAh packs in parallel on a Y harness** (≈74 Wh
nominal; fitted 2026-10-11, `JP1` closed; see [`../logs/decisions.md`](../logs/decisions.md)).
Runtimes are sized against **the energy it delivered on its first in-device discharge: 52.2 Wh in
13.7 h, measured 2026-10-12/13**. That run ended in a hard power cut at ≥3.53 V
with no knee in the curve, so the pack was **probably not empty**. 52 Wh is what Fancy can *use*
today, not the pack's capacity. See [the 2026-10-12 run](#discharge-run-meshnology-pair-2026-10-12)
and [`../logs/known-issues.md`](../logs/known-issues.md).

**Plan around three numbers:** ~3.4 W idle with the screen off, ~4.7 W with it on (2026-10-09), and
**no warning before the cut**. The fuel gauge % is wrong on this pack, so watch the voltage
([below](#low-battery-what-to-watch)).

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
| 2 × 18650 (**retired 2026-10-11**) | BAT1 + BAT2 positions, **parallel**, 3.7 V nominal | **measured ≈6.7 Wh** (≈1.78 Ah, 2026-10-09). The ≈22 Wh figure below assumed genuine 3000 mAh cells and does not apply | The cells fitted on 2026-09-16 were unbranded and wrapped `9900mAh`. A full discharge confirmed the claim is false: about a third of a genuine pair. The holder has since been removed from the board — [`../logs/known-issues.md`](../logs/known-issues.md) |
| 1S LiPo pack (lithium-polymer flat pack) (**fitted 2026-10-11**) | JST connector (a small keyed plug), 3.7/3.85 V nominal | **fitted: 2 × Meshnology 3.7 V × 10 Ah on a Y harness, ≈74 Wh nominal; 52.2 Wh delivered to the cut (measured 2026-10-12/13)** | No cell matching needed beyond joining the two packs at equal voltage; the pack must fit the rear cavity, and a case modification is accepted to make it fit |

*Pack swapped 2026-09-14: the originally selected UDIY-0001L (15 Ah / 55.5 Wh) was dropped for a
Meshnology 10 Ah / 37 Wh pack, already on hand, due to the UDIY-0001L's long shipping time — see
[`../logs/decisions.md`](../logs/decisions.md).*

**JP1 selects the mode.** Board silkscreen, read from a legible photograph (2026-10-11), vendor
spelling kept:

> "Solder JP1 for disperse current when useing JST to connect Lipo battery pack. Must let it open
> for 18650 batteries."

On this build `JP1` was soldered closed 2026-10-11 (owner); continuity *unverified* until metered.

So: **JP1 closed → JST LiPo pack. JP1 open → 18650 cells.** Getting this wrong is a current-path
error on the battery rail, not a cosmetic setting.

| Attribute | 2 × 18650 | 1S LiPo (fitted: 2 × Meshnology, Y harness) |
|---|---|---|
| Nominal voltage | 3.7 V | 3.7 V |
| Pack energy | ≈ 22 Wh for genuine cells (the fitted pair measured ≈6.7 Wh) | **≈74 Wh nominal** (2 × 10000 mAh) |
| Usable energy | ≈ 17–19 Wh (*estimate*) | **52.2 Wh to the cut, measured** (13.8 Ah); more is probably left in the pack below the cut |
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

**Discharge run, 2026-10-09** (interim 18650 pair, LoRa rail only, screen on, idle desktop):
**4.71 W / 1.25 A average** over 81 logged minutes. That is a slightly lower floor than the ~5.0 W
above. The pair delivered **≈6.7 Wh** from 4.20 V before a hard power loss at 3.49 V under load,
with the fuel gauge reading 100 % the whole time. Full numbers:
[`../logs/build-log.md`](../logs/build-log.md) 2026-10-09.

### Discharge run: Meshnology pair, 2026-10-12

Charger off at **14:43:52Z** 2026-10-12 (pack in constant-voltage taper at 4.233 V / 0.37 A, so
near full but not at `Full`). Hard power loss at **04:26:45Z** 2026-10-13. Logged every minute
from `axp20x-battery`; full detail in [`../logs/build-log.md`](../logs/build-log.md) 2026-10-13.

| Measure | Value |
|---|---|
| Delivered to the cut | **52.2 Wh / 13.8 Ah in 13.7 h** (823 samples, no gaps) |
| Average draw | **3.81 W / 1.01 A** |
| Loaded voltage | 4.03 V → 3.91 V (10 Wh) → 3.88 (20 Wh) → 3.77 (30 Wh) → 3.62 (40 Wh) → 3.56 (50 Wh) → 3.526 V last sample |
| End | Hard cut **≥3.53 V under ~1.27 A**, slope only −1.2 mV/min, **no knee**. The 3.45 V guard never fired |
| Fuel gauge | 99 % for 11 h, then 99 → 49 % in the last 2.7 h. Wrong in both phases |

Load during the run: Kismet on the AC1200 in monitor mode throughout, `gpsd` running
(`meshtasticd` not confirmed), GPS and LoRa rails on (boot default), SDR rail off from 15:22Z, USB rail on (the AC1200 is powered from it).
Desktop idle; `swayidle` blanks the display after 600 s.

| State (this run) | Cell power | Basis |
|---|---|---|
| **Idle, screen off**: Kismet + AC1200, GPS + LoRa + USB rails | **3.37 W median** (p10–p90 3.28–3.54 W), 0.88 A | 581 samples |
| **Unexplained high-draw episodes**, same load | **4.6–5.4 W** | 190 samples |
| Step at each episode start | **+2.0 W** (2.01–2.11 W at four separate edges) | Episodes of ~9 min at 18:17, 20:43, 00:37 and 01:42Z, then ≈+1.1 W from 02:07Z to the cut |

**The episodes are not the screen.** The owner reports the screen was off and Fancy unused all
night. An earlier draft of this page credited them to the display waking; that was wrong. Nothing
in the journal lines up with them, and the per-minute SoC temperature that would show a CPU burst
was not readable for that boot (see the build log). The cause is *unknown*. They cost about
**0.4 W averaged over the run**, and the last one ran 2 h 19 min, up to the cut.

| Pack | Usable energy | Runtime, idle screen off (~3.4 W) | Runtime, screen on (~4.7 W) |
|---|---|---|---|
| Interim 18650 pair (retired) | **≈6.7 Wh, measured** | — | **≈85 min, measured** at 4.71 W |
| **2 × Meshnology, Y harness (fitted)** | **52.2 Wh to the cut, measured** | **≈15 h** | **≈11 h** |

The two runtime columns divide the measured energy by the measured draws. Only the mixed
3.81 W average (13.7 h) was actually run end to end.

Charging (measured 2026-09-23): **1.96 A at 3.95–3.96 V** into the pack (~7.7 W), from
`axp20x-battery` with the charger connected. On the Meshnology pair with the system running:
1.65 A (2026-10-11), 1.45–1.50 A (2026-10-13, all four AIO rails on), and on the 2026-10-13 recharge
**1.70 A from a laptop USB-C port** vs **0.59 A from an Apple iPad USB-C wall charger** — the wall
charger is the slower source (it can't use its higher-voltage PD modes into a 5 V-only input; what
limits it to ~0.6 A is unestablished). **Caveat:** these charge currents are what `current_now`
reports, and the 2026-10-13 recharge showed that reading over-reads (next paragraph), so treat them
as upper bounds, not amps into the cells.

**The charge-current reading over-reads — by at least ~1.4×.** Integrating `current_now` over the
2026-10-13 recharge gives **18.9 Ah in**, against **13.8 Ah measured out** on the discharge before
it. A recharge cannot put in less than the previous discharge took out, yet the pack did not start
empty (it rebounded above the cut and had ~20 min of unlogged charge first) and charging is lossy —
so the true charge current was *well under* 13.8 Ah and the ADC over-reads by **more than ~1.4×**.
How much more is not established: a 2× factor is plausible but unconfirmed (the earlier "57 %→99 % of
a 74 Wh pack is impossible" argument leaned on the fuel-gauge %, which this same document calls
wrong, so it cannot settle the factor). The settling measurement is a charge-vs-supply current
comparison — see [the still-to-measure list](#runtime-scenarios-fitted-meshnology-pair) and `TODO`.

**What this means for 52 Wh.** The discharge integral (13.8 Ah / 52.2 Wh, near-full to an early cut)
is physically plausible and is the figure runtime sizing uses; the charge integral is not plausible,
so the charge path is the suspect, not the discharge path. But no independent instrument has
confirmed *either* current ADC — the only discharge cross-check (~0.88 A idle draw) comes from the
same ADC — so **52 Wh carries residual uncertainty until the charge-vs-supply comparison is done**,
and could move if the discharge ADC also reads off. Do not quote a charge-vs-discharge efficiency
from these runs. See [the build log](../logs/build-log.md), 2026-10-13 recharge entry.

## Estimated draw by state (5 V system side)

| State | Est. current | Est. power | Basis |
|---|---|---|---|
| Idle, display on, all AIO rails off | 600–900 mA | 3.0–4.5 W | CM4 + panel + backlight, class typical |
| Display off / blanked | −150 to −250 mA | −0.8 to −1.2 W | backlight dominates. Comparing runs, 4.71 W screen on (2026-10-09, no AC1200) against 3.37 W screen off (2026-10-12, with AC1200) puts it at **≥1.3 W**, *loose* |
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

## Runtime scenarios (fitted Meshnology pair)

Usable energy = the **measured 52 Wh** delivered before the 2026-10-12 cut. Draws marked *(m)* are
measured; *(e)* come from the estimate table above. The two "measured" rows are the 2026-10-12
run's own states; the others add estimated deltas to them.

| Scenario | Build-up of average draw | Avg draw | Runtime on 52 Wh |
|---|---|---|---|
| Passive node: Kismet/AC1200 + GPS + LoRa, **screen off** | 3.37 *(m)* | ~3.4 W | **~15 h** |
| Same, **screen on** (wardriving with the map up) | 3.37 + ≥1.3 screen *(loose, see above)* | ~4.7–5.4 W | **~9.5–11 h** |
| Terminal work, screen on, LoRa only | 4.71 *(m, 2026-10-09)* | ~4.7 W | **~11 h** |
| The 2026-10-12 run as it happened (screen off, with the unexplained episodes) | 3.81 *(m)* | 3.8 W | **13.7 h, measured** |
| ADS-B / SDR receiving, screen on | 4.71 + 0.64 SDR rail *(m)* + ~0.5–1 streaming + decode *(e)* | ~5.9–6.4 W | **~8–9 h** |
| Everything on (SDR + LoRa + GPS + Ethernet + CPU load) | 5.0 + 0.93 rails *(m)* + ~1 Ethernet + 2–3.5 load *(e)* | ~9–10.5 W | **~5–5.8 h** |

These replace the single-pack (≈31 Wh *estimate*) table. Every row assumes the cut comes where it
did on 2026-10-12. If the cut is moved lower or explained, the energy and every runtime grow.

The AC1200 was estimated at +1–1.8 W in monitor mode, but the whole idle system, screen off, measured only
3.37 W with it running. That suggests the estimate is high; its own delta is still unmeasured
(Kismet on vs off, screen off).

**Still to measure:** what cut the power at ≥3.53 V, and how much is left below it; the pack's
resting voltage after a cut; the AC1200's own delta; SDR while `readsb` is actually decoding; the
charge-current ADC scale (compare `current_now` on charge against the current measured at the USB-C
supply); and why the Apple iPad charger only gives ~0.6 A at 5 V.

**Charge time** (recharge logged 2026-10-13, 57 %→99 %): ~15.6 h of logging, but the source changed
partway and the pack did not start empty, so this is not a clean cut-to-`Full` time. The useful
shape of it: **Royal Fortune's laptop USB-C port did the bulk of the refill in ~8.7 h**; the **Apple
iPad wall charger is about 3× slower** and stretches the tail. Budget **roughly half a day on the
laptop port, most of a day on the wall charger** *(one run, confounded by the swap)*. The earlier
"~10 h to `Full`" estimate was built on the same `current_now` readings that proved ~2× high, so it
is unreliable in that direction; charge *wall-clock*, not the gauge or the current integral, is the
thing to trust here.

## Low battery: what to watch

Nothing on the device warns before the cut, and the fuel gauge % is wrong on this pack
([`../logs/known-issues.md`](../logs/known-issues.md)). Watch `voltage_now` instead. From the
2026-10-12 run, at ~1.26 A (during the last high-draw episode). At the 0.88 A idle the reading
sits ~0.04 V higher at the same charge:

| Loaded voltage stays below | Time left before the cut | Energy left |
|---|---|---|
| 3.65 V | ~2 h 20 min | ~10.5 Wh |
| 3.60 V | ~65 min | ~4.8 Wh |
| 3.58 V | ~47 min | ~3.5 Wh |
| 3.55 V | ~17 min | ~1.3 Wh |

One run only, and the discharge curve is flat here: 0.1 V spans the last two hours. Treat
**3.60 V as "plug in now"** and **3.55 V as "shut down now"**. A low-voltage guard set at 3.45 V
(as on 2026-10-12) never fires, because the device cuts out first.

```bash
watch -n 30 "grep . /sys/class/power_supply/axp20x-battery/{voltage_now,current_now,status}"
```

## Why the SDR rail default matters

Upstream `BOOT_DEFAULTS` in `aiov2_ctl` sets the SDR rail (BCM 7) **on**. If CM4 behaves the same
way, every boot starts ~1.5 W into the budget — roughly two hours of the fitted pair's ~11 h in
the terminal-work scenario — for a radio nothing is using. On this build `--boot-rails-status`
reports SDR and USB **off** at boot, yet `--status` read all four rails **on** a few minutes into the
2026-10-13 04:29Z boot. What turned them on is *unverified*.

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
| `capacity` | `100%` | the PMIC's fuel-gauge estimate. **Not trustworthy on this build.** The device tree describes a 6.7 Ah / 24.79 Wh battery (`charge_full_design`), the fitted pair is ≈20 Ah nominal, and on 2026-10-12 the % sat at 99 for 11 h and then fell 50 points in 3.4 Ah. Use `voltage` ([Low battery](#low-battery-what-to-watch)) |

To measure what something costs, read `power` **on battery**, before and after, with everything
else unchanged. That is how the SDR rail's +0.64 W was measured (the Measured table).

**Energy and runtime.** Energy in watt-hours is voltage × amp-hours: one Meshnology pack,
3.7 V × 10 Ah, holds about 37 Wh nominal, and the fitted pair about 74 Wh. Runtime ≈ usable Wh ÷
average W. The pair measured 52 Wh usable at an average of 3.8 W, which ran Fancy for 13.7 h
(2026-10-12).

**Why "9900 mAh" on an 18650 is implausible.** An 18650 cell is 18 mm × 65 mm. The best cells of
that size hold about 3,500 mAh; a label claiming 9,900 mAh is claiming nearly three times what
the chemistry fits in that volume. This build's pair bore that out: measured
≈6.7 Wh for the pair on 2026-10-09, about a third of a genuine 3000 mAh pair. Never rely on such
cells for a long battery lab.

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
