# firmware/

Keyboard, expansion, and board firmware images plus flashing notes. Images themselves are **not
committed** (`.gitignore` excludes `*.img`, `*.7z`, `*.zip`) — this file records where they come
from, how to verify them, and what is currently flashed.

Version-of-record log: [`../docs/logs/firmware-versions.md`](../docs/logs/firmware-versions.md).

## 1. uConsole CM4 OS image

Source: https://github.com/clockworkpi/uConsole (README download table / Releases)

Current upstream target: **`uConsole_CM4_v3.1_64bit`** — April 2026, Linux 6.12.62, ~2.1 GB compressed.

```bash
# download, then always record the checksum next to the version
sha256sum uConsole_CM4_v3.1_64bit.img.7z
7z x uConsole_CM4_v3.1_64bit.img.7z
# flash with Raspberry Pi Imager, or:
sudo dd if=uConsole_CM4_v3.1_64bit.img of=/dev/sdX bs=4M status=progress conv=fsync
```

Flashing procedure and boot paths: [`../docs/runbooks/imaging-and-first-boot.md`](../docs/runbooks/imaging-and-first-boot.md).

## 2. CM4 bootloader EEPROM

Governs whether NVMe boot is possible at all.

```bash
sudo rpi-eeprom-update            # current version + available update
sudo rpi-eeprom-update -a         # stage an update, then reboot
rpi-eeprom-config                 # inspect BOOT_ORDER
sudo -E rpi-eeprom-config --edit  # change BOOT_ORDER
```

Details and BOOT_ORDER values: [`../docs/runbooks/nvme-boot.md`](../docs/runbooks/nvme-boot.md).

## 3. Keyboard firmware

Flasher and firmware live in `Code/uconsole_keyboard/` in the uConsole repo; the keyboard
schematic is `keyboard_220816.pdf` in the same repo. Only flash if a key/Fn-layer fault points
at firmware — a working keyboard needs nothing here.

## 4. AIO V2

The AIO V2 has no user-flashable firmware in the normal path; its behavior comes from the host
side (`aiov2_ctl`, device-tree overlays). Meshtastic firmware runs on the host, not on the SX1262.

## 5. NVMe SSD firmware

```bash
sudo nvme id-ctrl /dev/nvme0 | grep -E '^(fr|mn|sn)'   # firmware rev, model, serial
```

Record the revision at inventory; vendor tools for updating it are host-OS specific.

## Discipline

- Record every flash (component, version, checksum, date) in the firmware-version log.
- Keep the last known-good image and its checksum until the new one has passed the bring-up
  checklist.
- Never flash bootloader EEPROM and OS image in the same sitting — one variable at a time makes a
  failure diagnosable.
