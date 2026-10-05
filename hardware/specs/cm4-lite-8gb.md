# Raspberry Pi CM4 Lite 8GB (CM4108000) — spec sheet

| Attribute | Value |
|---|---|
| SoC | Broadcom BCM2711, quad-core Cortex-A72 @ 1.5 GHz |
| RAM | 8 GB LPDDR4 |
| Storage | **None onboard** — "Lite" has no eMMC; boots from microSD or PCIe NVMe |
| Wireless | 802.11b/g/n/ac dual-band Wi-Fi, Bluetooth 5.0 (this SKU is the wireless variant) |
| PCIe | 1 lane, Gen 2 (5 GT/s) — used by the adapter for the NVMe board |
| Connectors | 2 × 100-pin high-density board-to-board |
| Module size | 55 × 40 mm |
| Supply | 5 V main rail (via carrier) |
| Thermal | SoC throttles in the low 80s °C; check with `vcgencmd measure_temp` / `get_throttled` |

Datasheet: https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf
Hardware docs: https://www.raspberrypi.com/documentation/computers/compute-module.html

## As received — inspected 2026-09-06

Read from the module and its packaging; photographs in
[`../../images/inventory/`](../../images/inventory/README.md).

| Marking | Value |
|---|---|
| Part code (box label) | `CM4108000` — wireless, 8 GB RAM, no eMMC (Lite) |
| FCC ID | `2ABCB-RPICM4` |
| IC (Canada) | `20953-RPICM4` |
| KCC (Korea) | `R-R-P2R-CM4` |
| Other marks | UKCA, CE, UL/CSA, WEEE |
| Silkscreen | "Raspberry Pi 2021", "Made in the UK", "Uses Technology Licensed From Proant AB" |
| Serial | `<cm4-serial-redacted>` — read at first boot 2026-09-16 with `cat /proc/cpuinfo \| grep Serial` (matches `/sys/firmware/devicetree/base/serial-number`) |
| Board revision | `Raspberry Pi Compute Module 4 Rev 1.1` — from `/sys/firmware/devicetree/base/model`, first boot 2026-09-16 |
| Wi-Fi/BT MAC | `aa:bb:cc:dd:ee:7e` (`wlan0`) — per-unit, tied to this module's wireless package |
| Ethernet MAC | `aa:bb:cc:dd:ee:7d` (`eth0`, carrier-side RJ45 board) |

Physically consistent with the Lite variant: SoC under the central shield, a single LPDDR4 package,
the wireless module and its shield, and **no eMMC package**. Both 100-pin board-to-board connectors
show no visible damage in the inspection photographs — check under magnification before seating.

## Antenna: onboard PCB or external u.FL

The module has both an onboard PCB antenna and a **u.FL/MHF connector**, confirmed present on this
board. They are mutually exclusive and the choice is made in software:

```
dtparam=ant2        # select the external u.FL connector (omit for the onboard PCB antenna)
```

**Confirmed on hardware, first boot 2026-09-16:** `/boot/firmware/config.txt` carries `dtparam=ant2`,
so the external u.FL connector is selected, not the onboard PCB antenna. A link-quality comparison
against the onboard antenna has not been done. This matters inside a metal-adjacent enclosure: the
uConsole shell sits close to the module, and the certified Proant design assumes clearance the
enclosure may not provide.

Regulatory note: the FCC/IC/KCC grants above cover the module with its certified antenna. Fitting a
different external antenna is an integrator decision with compliance implications.

## Consequences for this build

- **No eMMC** → `rpiboot` is not used to flash internal storage. Its role here is host-side access
  to the NVMe through the adapter's USB-C flash port. See
  [`../../docs/runbooks/imaging-and-first-boot.md`](../../docs/runbooks/imaging-and-first-boot.md).
- **PCIe Gen2 ×1** caps NVMe throughput near ~400 MB/s real-world; drive choice barely matters
  above that, so the on-hand SSD is fine if the form factor fits.
- **USB 2.0 only** downstream on CM4 — the RJ45/USB 3.0 board's USB 3 ports and gigabit Ethernet
  run at USB 2.0 speeds. USB 3.0 requires CM5.
- Wi-Fi is 802.11ac and **cannot be relied on for monitor mode** — that is what the optional
  AC1200 MT7921 card is for.
