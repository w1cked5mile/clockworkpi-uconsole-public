# hardware/

Schematics, pinouts, mechanical notes, and expansion-card design files (KiCAD, etc.) for this uConsole build.

| Path | Contents |
|---|---|
| [`specs/`](specs/) | Condensed spec sheet per board — interfaces, chipsets, power, dimensions |
| [`datasheets/`](datasheets/) | Index of upstream datasheets and schematic PDFs (links, not mirrors) |
| [`mechanical.md`](mechanical.md) | Clearances, fastener map, antenna routing, thermal stack |

Board-level GPIO and overlay detail lives in [`../docs/reference/pinout-gpio.md`](../docs/reference/pinout-gpio.md);
power math lives in [`../docs/reference/power-budget.md`](../docs/reference/power-budget.md).

Everything here was compiled from vendor pages, upstream repos, and the BOM **before the hardware
arrived**. Rows marked *unverified* are to be confirmed against the physical boards at inventory.
