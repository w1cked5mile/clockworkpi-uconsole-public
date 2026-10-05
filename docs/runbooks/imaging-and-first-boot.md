# Imaging & first-boot runbook

Get the CM4 Lite booting, then to a configured baseline.

> **Version-dependent — verify before running.** Bootloader/EEPROM behavior, NVMe-boot support, and image versions change. Confirm against:
> - uConsole images & wiki: https://github.com/clockworkpi/uConsole (Releases) · https://github.com/clockworkpi/uConsole/wiki
> - CM4/CM5 setup guides + scripts (forum): https://forum.clockworkpi.com/t/cm4-cm5-uconsole-setup-guides-with-scripts/22818
> - RPIBOOT on the adapter (forum): https://forum.clockworkpi.com/t/using-rpiboot-on-the-hackergadgets-cm4-5-adapter/21767
> - Raspberry Pi usbboot/rpiboot: https://github.com/raspberrypi/usbboot

## Background

- The CM4 **Lite** has no onboard eMMC. It boots from **microSD** or (with the adapter's PCIe) an **NVMe SSD**.
- Official uConsole CM4 images are prebuilt (pi-gen, `uconsole_arm64` branch) and linked from the uConsole README download table. Most builds flash the prebuilt image — you do not need to build from source.
- **Compression differs by release.** The current `v3.1` image ships as **`.img.bz2`**; only the 2023 `v0.1b` xfce image is `.7z`. Check the extension in the README table before reaching for a decompressor.

## Path A — microSD first boot (simplest)

1. [ ] Download the current image and record its checksum.

   ```bash
   curl -L -C - -O http://dl.clockworkpi.com/uConsole_CM4_v3.1_64bit.img.bz2
   sha256sum uConsole_CM4_v3.1_64bit.img.bz2        # ClockworkPi publishes no sum; record ours
   bunzip2 -k uConsole_CM4_v3.1_64bit.img.bz2       # or: 7z x ...img.bz2 -mmt=on
   ```

   ClockworkPi publishes **no** checksum for this image, so there is nothing upstream to compare
   against — record the locally computed sum in
   [`../logs/firmware-versions.md`](../logs/firmware-versions.md) so a later re-download can be
   compared to the copy that actually booted.

2. [ ] Flash to microSD.

   ```bash
   # Linux / macOS — confirm the device with lsblk FIRST; dd to the wrong one is unrecoverable
   sudo dd if=uConsole_CM4_v3.1_64bit.img of=/dev/sdX bs=4M status=progress conv=fsync
   ```

   On Windows use Raspberry Pi Imager, or the raw-write helper kept alongside the image at
   `D:\Source\uConsole\flash-sd.ps1` (locks and dismounts the card's volumes, writes, then re-reads
   the card and compares SHA-256 against the image).

   Two Windows-specific traps, both hit on 2026-09-15 and detailed in
   [`../logs/known-issues.md`](../logs/known-issues.md):

   - Raw access to `\\.\PhysicalDriveN` requires **Administrator**; an unelevated shell fails with
     "Access to the path is denied" before writing anything.
   - `Set-Disk -IsOffline` does **not** work on a card reader — removable media cannot be set
     offline. Lock and dismount the volumes and hold the handles instead.

3. [ ] Insert microSD, power on. Confirm the display lights immediately (image pulls up GPIO9 at
   boot). *Unverified — no image has been booted on this hardware yet.*

## Path B — NVMe boot (target end state)

1. [ ] First boot from microSD (Path A) to get a working system.
2. [ ] Flash the OS image to the NVMe SSD (e.g. `dd` from the running system, or image it on the host).
3. [ ] Set the CM4 bootloader order to prefer NVMe/PCIe. **Verify the current method** — via `rpi-eeprom-config` / `raspi-config` and the forum setup scripts; NVMe boot on CM4 depends on bootloader EEPROM version.
4. [ ] Remove microSD; confirm it boots from NVMe (`lsblk` shows root on `nvme0n1`).

## Path C — flash CM4 via rpiboot (through the adapter USB-C flash port)

Use when imaging eMMC modules or when you prefer host-side flashing. CM4 Lite has no eMMC, so this is mainly for NVMe/host imaging.

1. [ ] Install usbboot/rpiboot on the host (`git clone https://github.com/raspberrypi/usbboot && cd usbboot && make && sudo ./rpiboot`).
2. [ ] Connect the adapter's USB-C flash port to the host with a **data** cable; put the board in the flash state per the adapter guide.
3. [ ] The target appears as a mass-storage device; flash the image to it.

## First-boot checklist (any path)

- [ ] Expand filesystem (if not automatic).
- [ ] Set locale, timezone, keyboard layout.
- [ ] Set hostname.
- [ ] Connect Wi-Fi; confirm connectivity.
- [ ] `sudo apt update && sudo apt full-upgrade`.
- [ ] Enable SSH (`sudo raspi-config` → Interface → SSH, or `systemctl enable --now ssh`).
- [ ] Install and bring up Tailscale (`curl -fsSL https://tailscale.com/install.sh | sh` → `sudo tailscale up`).
- [ ] Create/confirm user; set a strong password; consider key-only SSH.
- [ ] Confirm display brightness (Fn shortcut), audio, and keyboard all work.
- [ ] Record the image version and EEPROM version in [`../logs/firmware-versions.md`](../logs/firmware-versions.md).

## Next

- Module bring-up and software: [`software-install.md`](software-install.md), then [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md).
