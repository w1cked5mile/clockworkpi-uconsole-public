# Firmware & image version log

Record what is flashed so upgrades are traceable. Update whenever anything changes.

## Target versions (pre-arrival, from upstream — verify at flash time)

| Component | Target | Source |
|---|---|---|
| uConsole CM4 OS image | `uConsole_CM4_v3.1_64bit.img.bz2` — 14 Apr 2026, Linux **6.12.62**, 2.06 GB compressed | https://github.com/clockworkpi/uConsole (README download table) → http://dl.clockworkpi.com/uConsole_CM4_v3.1_64bit.img.bz2 |
| CM4 bootloader EEPROM | latest `default` channel release; required for reliable NVMe boot | `sudo rpi-eeprom-update -a`, https://github.com/raspberrypi/rpi-eeprom |
| aiov2_ctl | current `main` — GPIO map verified 2026-09-06 (GPS 27 / LORA 16 / SDR 7 / USB 23; SDR default-on) | https://github.com/hackergadgets/aiov2_ctl |
| Keyboard firmware | flasher + firmware in `Code/uconsole_keyboard/` | https://github.com/clockworkpi/uConsole |
| Meshtastic firmware | current stable; region **US915** for your location | https://meshtastic.org/ |

## As-flashed record

| Date | Component | Version | Source / notes |
|---|---|---|---|
| 2026-09-15 | uConsole OS image | `uConsole_CM4_v3.1_64bit` | Flashed to the 32 GB microSD (29.54 GB usable) from a Windows host. Read-back SHA-256 matched the image — see [Local image copies](#local-image-copies). **Not yet booted** (mainboard in transit). |
| 2026-09-20 | CM4 bootloader EEPROM | `2023/01/11 17:40:52` (commit `8ba17717`, `release` branch) — read via `vcgencmd bootloader_version` | **Stale, ~3 years behind the `default` channel target above.** Not caught by `apt upgrade` — CM4 doesn't self-manage EEPROM updates by default (`rpi-eeprom-update` confirmed disabled on this build). Raspberry Pi's supported path for CM4 is external: put the module in USB boot mode and flash from another PC via `rpiboot` (`raspberrypi/usbboot`), not an in-place update from the running OS. **Not yet done** — tracked in `TODO.md`. Affects NVMe boot reliability per the target-versions note above, relevant once the NVMe board arrives. |
| 2026-09-23 | CM4 bootloader EEPROM | `2026/05/17 20:13:18` (commit `224877da`, `release`), `BOOT_ORDER=0xf416` | Read via `sudo vcgencmd bootloader_version` / `sudo rpi-eeprom-config` after the NVMe migration. **Updated from the 2023/01/11 build recorded 2026-09-20**, and now current enough for NVMe boot (it booted from NVMe). How and exactly when it was flashed was not recorded; presumably via `rpiboot` during the #11953 install. `rpi-eeprom-update` is still disabled OS-side, which is the CM4 default. |
| 2026-09-23 | NVMe SSD firmware | WD PC SN730 `SDBQNTY-256G-1001`, FW `11130101` | `nvme id-ctrl /dev/nvme0`. Reused drive, not reflashed. |
| 2026-09-23 | Kernel | `6.12.62-v8+` (#2 SMP PREEMPT Thu Dec 18 15:38:04 CST 2025), Debian 13 trixie | `uname -a`, now running from the NVMe root |
| | Kernel | (`uname -r`) | ClockworkPi fork — confirm with `uname -r` on first boot; the image is published as 6.12.62 |
| | Keyboard firmware | | uConsole repo |
| | aiov2_ctl | (git commit) | https://github.com/hackergadgets/aiov2_ctl |
| | Meshtastic firmware | | region set: |

## Commands to capture current versions

```bash
uname -a
cat /etc/os-release
rpi-eeprom-update
vcgencmd version 2>/dev/null || true
vcgencmd bootloader_version 2>/dev/null || true
aiov2_ctl --status
git -C ~/aiov2_ctl rev-parse --short HEAD 2>/dev/null || true
meshtastic --info 2>/dev/null | head -20 || true
```

## Checksum discipline

Record the checksum of every image you flash, next to the version:

```bash
sha256sum uConsole_CM4_v3.1_64bit.img.bz2
```

A mismatch between the vendor-published sum and the local file is the cheapest explanation for
a board that "won't boot" — check it before disassembling anything.

**ClockworkPi publishes no checksum for the CM4 images** (checked 2026-09-15 against the README
download table and the wiki), so there is no upstream value to compare against. The sums below are
therefore *provenance for our own copy*, not an authenticity check: they confirm a later
re-download is byte-identical to the copy that was flashed, nothing more.

### Local image copies

| Acquired (UTC) | File | Bytes | SHA-256 |
|---|---|---|---|
| 2026-09-15 | `uConsole_CM4_v3.1_64bit.img.bz2` | 2,212,739,229 | `ef95242cdb0125e8ed08157400a26d4665acddd083481ec2314acd6e073b74ab` |
| 2026-09-15 | `uConsole_CM4_v3.1_64bit.img` (decompressed) | 7,407,140,864 | `a7b0a2bfa86a45150af1ae70a94ed432718bfec90ffdef54952564bd34f0d788` |

Held outside the repo at `D:\Source\uConsole\` (images are gitignored). Structure confirmed before
flashing: MBR signature `55aa`, partition 1 type `0c` FAT32 labelled `bootfs` (512 MB at LBA 8192),
partition 2 type `83` Linux (6.87 GB). The bzip2 CRC passed on extraction.
