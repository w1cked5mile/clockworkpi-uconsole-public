# Datasheets & schematics — index

Links only; PDFs are not mirrored here (see the `.gitignore` policy on large binaries). Download
what you need locally at assembly time.

## ClockworkPi — published in https://github.com/clockworkpi/uConsole (repo root unless noted)

| File | Covers |
|---|---|
| `Clockwork_uConsole_Assembly_Guidelines.pdf` | Official assembly sequence |
| `clockwork_Mainboard_V3.14_Schematic.pdf` | Mainboard v3.14 |
| `clockwork_Mainboard_V3.14_V5_Schematic.pdf` | Mainboard v3.14 (V5 revision) |
| `clockwork_Adapter_CM4_Schematic.pdf` | ClockworkPi's own CM4 adapter (not the HackerGadgets one — useful for signal reference) |
| `clockwork_DevTerm_A06_Core_for_Mainboard_V3.14_Schematic.pdf` | A06 core (interface reference) |
| `clockwork_DevTerm_R01_Core_for_Mainboard_V3.14_Schematic.pdf` | R01 core (interface reference) |
| `JD9365DA-H3_DS_V0.01_20200819.pdf` | Display driver IC datasheet |
| `JD9365DA-H3_User_Guide_Preliminary_V0.00_20200827.pdf` | Display driver IC user guide |
| `keyboard_220816.pdf` | Keyboard schematic |
| `clockwork_UC_4G_Schematic.pdf`, `clockwork_UC_4G_drawing.pdf` | 4G expansion module (not in this build) |
| `SIM7500_SIM7600 Series_AT Command Manual_V3.00.pdf` | 4G modem AT commands (not in this build) |
| `PCB/CPI_3.14_Mainboard_V5_Gerber.7z` | Mainboard gerbers |
| `PCB/RPI CM4 to CPI v3.14 Adapter.zip` | Adapter design files |
| `Code/patch`, `Code/scripts`, `Code/uconsole_keyboard` | Kernel patches, helper scripts, keyboard firmware + flasher |

## Silicon

| Part | Function | Datasheet |
|---|---|---|
| Broadcom BCM2711 / CM4 | Compute module | https://datasheets.raspberrypi.com/cm4/cm4-datasheet.pdf |
| Semtech SX1262 | LoRa transceiver | https://www.semtech.com/products/wireless-rf/lora-connect/sx1262 |
| Realtek RTL2832U | SDR demodulator/USB bridge | https://www.realtek.com/ (see also https://osmocom.org/projects/rtl-sdr/wiki) |
| Rafael Micro R860 | SDR tuner | vendor datasheet not publicly published — behavior documented at https://www.rtl-sdr.com/ |
| NXP PCF85063A | RTC | https://www.nxp.com/products/PCF85063A |
| MediaTek MT7921AU | Wi-Fi 6 / BT 5.2 (optional card) | https://www.mediatek.com/ |
| X-Powers AXP-series | Mainboard PMIC (reported via `axp20x-battery` / `axp22x-ac`) | https://linux-sunxi.org/AXP_PMICs (was `/AXP`, 404 on 2026-09-24) |

## Vendor documentation

- AIO V1/V2 setup guide — https://hackergadgets.com/pages/hackergadgets-uconsole-rtl-sdr-lora-gps-rtc-usb-hub-all-in-one-extension-board-setup-guide
- Upgrade kit — https://hackergadgets.com/products/uconsole-upgrade-kit
- AIO V2 (OpenSourceSDRLab) — https://opensourcesdrlab.com/products/opensourcesdrlab-uconsole-aio-v2-rtl-sdr-lora-gps-rtc-usb-hub-usb-30-rj45-ethernet

Full link index: [`../../docs/documentation-index.md`](../../docs/documentation-index.md).
