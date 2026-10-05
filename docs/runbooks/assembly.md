# Assembly runbook

Order of operations for the uConsole + CM4 + HackerGadgets adapter/NVMe + AIO V2 build.

> Verify against the current vendor guides before starting — board revisions change seating order and clearances:
> - ClockworkPi uConsole wiki: https://github.com/clockworkpi/uConsole/wiki
> - HackerGadgets adapter/upgrade kit: https://hackergadgets.com/products/uconsole-upgrade-kit
> - AIO V1/V2 setup guide: https://hackergadgets.com/pages/hackergadgets-uconsole-rtl-sdr-lora-gps-rtc-usb-hub-all-in-one-extension-board-setup-guide
> - RPIBOOT on the adapter (forum): https://forum.clockworkpi.com/t/using-rpiboot-on-the-hackergadgets-cm4-5-adapter/21767

## Before you start

- [ ] Inventory & inspection complete ([`../checklists/inventory-and-inspection.md`](../checklists/inventory-and-inspection.md)).
- [ ] ESD strap on; work on the ESD mat.
- [ ] Photograph each stage (feeds the [build log](../logs/build-log.md)).

## Sequence

1. **CM4 onto the adapter board.**
   - [ ] Align both board-to-board connectors; press evenly. No bent pins.
   - [ ] Apply the thermal pad to the CM4 SoC per shell clearance.
2. **Flash before final assembly (recommended).**
   - [ ] With the adapter's USB-C flash port, run `rpiboot` and image the CM4 / set up NVMe boot now, while access is easy. See [`imaging-and-first-boot.md`](imaging-and-first-boot.md).
3. **NVMe battery board.**
   - [ ] Seat the M.2 NVMe SSD (correct 2230–2280 standoff); secure the retention screw.
   - [ ] **Set `JP1` for the battery you are actually fitting — before connecting anything.**
         Open for 2 × 18650 in the BAT1/BAT2 positions; soldered closed for a 1S LiPo pack on the
         JST connector. See [`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md).
   - [ ] Connect the battery. **Confirm polarity** — the reverse-polarity LED is a warning, not a guarantee. With 18650s use a matched pair (parallel cells at different states of charge push current into each other on connection); with a LiPo pack confirm it is **single cell**.
4. **Mainboard integration.**
   - [ ] Seat the adapter/CM4 stack onto the ClockworkPi v3.14 mainboard per the vendor guide.
   - [ ] Reconnect display FPC, keyboard, and speaker leads if detached. Seat FPC connectors fully and latch them.
5. **AIO V2 expansion board.**
   - [ ] Mount the AIO V2; connect the internal USB link to the mainboard/adapter.
   - [ ] **Land u.FL leads per the port mapping** in
         [`../reference/antennas-and-rf-connectors.md`](../reference/antennas-and-rf-connectors.md).
         The `ANTn` numbers carry no function of their own — that table is the assignment, and once
         the shell is closed the jacks are indistinguishable.
   - [ ] Land the leads on the AIO V2 **while it is still accessible**, before final mounting if
         clearance is tight. Press flat and straight down; u.FL shears when angled and is good for
         roughly 30 mating cycles, so plan the route before pressing.
   - [ ] Route, then land the strip end, then mount the strip. The SMAs are board-mounted, so the
         strip is the anchor. The `SDR` bulkhead is the exception: thread it through the shell and
         tighten the nut first, then press its u.FL.
   - [ ] Keep bend radius gentle — **≳5 mm on 1.13 mm coax** (typical figure, not a datasheet value
         for this cable); a crease is a permanent impedance discontinuity. Leave a short service
         loop, not a coil.
   - [ ] Route clear of the PMIC, the switching regulators and the display FPC. Nothing over the
         CM4 SoC — that is where the thermal pad sits. Cross other cables at right angles.
   - [ ] Dry-fit the shell before screwing down and check for pinch points at screw bosses,
         standoffs and the parting line.
   - [ ] **Label the exterior** — at minimum the LoRa jack (the only TX port) and the SDR bulkhead
         (the bias-tee port, 5 V present).
6. **RJ45 + USB 3.0 board** (if using the side-port board).
   - [ ] Mount and connect per guide. Note: USB 3.0 requires CM5; on CM4 these run at USB 2.0.
7. **Close up.**
   - [ ] Verify no pinched cables; screens/keyboard reconnected; battery secured.
   - [ ] Fit side plates and shell; install screws.

## Fragile / gotcha points

- FPC connectors: lift the latch fully before inserting, seat square, then close the latch. Forcing a partially-latched FPC damages the connector.
- u.FL connectors: align flat and press straight down; they shear if angled.
- Antenna ports are not interchangeable once closed up: the SDR path carries a **5 V bias tee** and
  the LoRa path is the **only transmitter**. A DC-shorted antenna on the former shorts the supply;
  the latter keyed into the wrong or an empty jack risks the PA. Both failure modes are silent
  until they are not — label the shell.
- Battery polarity and type must match the board's `JP1` setting. The board takes 2 × 18650 (parallel, JP1 open) or a 1S LiPo pack on the JST connector (JP1 soldered). A 2S pack must never be fitted — the mainboard PMIC (AXP228) is a single-cell part.
- AIO V2 connector: forum reports it sometimes needs reseating on the mainboard connector before it starts responding — don't assume a dead board on first try.
- Keep track of screw lengths by stage (photograph the screw bag layout).

## First power-on

- [ ] Do not close the shell fully until after a successful first boot ([`imaging-and-first-boot.md`](imaging-and-first-boot.md)) — reopening to reflash is common.
