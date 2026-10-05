# NVMe boot runbook

Move root from microSD to the NVMe SSD on the HackerGadgets battery board. Split out of
[`imaging-and-first-boot.md`](imaging-and-first-boot.md) Path B.

> **Version-dependent — verify before running.** CM4 NVMe boot depends on the bootloader EEPROM
> version and `BOOT_ORDER`. Confirm against:
> - https://github.com/raspberrypi/rpi-eeprom
> - https://www.raspberrypi.com/documentation/computers/compute-module.html
> - CM4/CM5 setup guides (forum): https://forum.clockworkpi.com/t/cm4-cm5-uconsole-setup-guides-with-scripts/22818

## Preconditions

- [ ] System boots from microSD and is updated (`sudo apt update && sudo apt full-upgrade`).
- [ ] SSD is seated in the correct 2230–2280 standoff with its retention screw.
- [ ] **Keep the microSD** — it is the recovery path for every step below.

## 1. Confirm the drive is visible

```bash
lsblk -o NAME,SIZE,MODEL
sudo lspci                      # NVMe controller should enumerate
sudo lspci -vv | grep -A3 'Non-Volatile'   # LnkSta shows negotiated width/speed
sudo nvme list                  # if nvme-cli is installed
```

Not visible → the problem is PCIe/seating/power, not boot order. Stop here and fix that first.

## 2. Update the bootloader EEPROM

```bash
sudo rpi-eeprom-update          # what is installed / available
sudo rpi-eeprom-update -a
sudo reboot
```

## 3. Set BOOT_ORDER

```bash
rpi-eeprom-config
sudo -E rpi-eeprom-config --edit
```

`BOOT_ORDER` is read **right to left**. Useful values:

| Digit | Meaning |
|---|---|
| `1` | SD card |
| `4` | USB mass storage |
| `6` | NVMe |
| `f` | restart the sequence (loop) |

- `BOOT_ORDER=0xf461` — NVMe first, then USB, then SD, then loop. Safe default while testing:
  a failed NVMe boot still falls back to the card.
- `BOOT_ORDER=0xf6` — NVMe only. Do not set this until NVMe boot has worked repeatedly.

**As found on this build, 2026-09-23:** `BOOT_ORDER=0xf416` (NVMe → SD → USB → loop). It also
falls back to the card. On CM4, `rpi-eeprom-update` is **disabled by default** and prints a
pointer to `rpiboot` instead. Read the live config with `sudo rpi-eeprom-config` and the version
with `sudo vcgencmd bootloader_version` (`/dev/vcio` is root-only).

Reboot after saving.

## 4. Copy the system to NVMe

Option A — clone the running system (simplest):

```bash
sudo apt install -y rpi-clone     # or use the image-based option below
sudo rpi-clone nvme0n1
```

Option B — write the image directly:

```bash
sudo dd if=uConsole_CM4_v3.1_64bit.img of=/dev/nvme0n1 bs=4M status=progress conv=fsync
sudo partprobe /dev/nvme0n1
```

Then check that `/boot/firmware/cmdline.txt` and `/etc/fstab` on the NVMe reference the **NVMe**
PARTUUIDs, not the card's:

```bash
sudo blkid                       # note PARTUUIDs
# mount the NVMe boot + root partitions and correct root=PARTUUID=... and fstab if needed
```

Mismatched PARTUUIDs are the usual cause of a boot that starts and then drops to initramfs.

## 5. Boot without the card

```bash
sudo poweroff
# remove the microSD, power on
lsblk                            # root should be on nvme0n1
findmnt /                        # confirm the source device
```

## 6. Verify health and throughput

```bash
sudo apt install -y nvme-cli smartmontools fio
sudo nvme smart-log /dev/nvme0         # critical_warning 0, media_errors 0; note percentage_used
sudo smartctl -H /dev/nvme0            # PASSED
sudo nvme error-log /dev/nvme0 -e 4    # entries with error_count 0 are empty slots
sudo dmesg | grep -iE 'nvme|aer'       # no timeouts, resets or AER errors

D=/var/tmp/fiotest; sudo mkdir -p $D; sudo chown $USER $D
fio --name=seqread --filename=$D/f --size=2G --rw=read --bs=1M --iodepth=8 \
    --ioengine=libaio --direct=1 --runtime=20 --time_based
fio --name=randread --filename=$D/f --size=2G --rw=randread --bs=4k --iodepth=32 \
    --ioengine=libaio --direct=1 --runtime=20 --time_based
rm -rf $D
```

**Do not benchmark in `/tmp`.** It is tmpfs on Debian trixie, so you measure RAM. A result above
~450 MB/s is impossible over the CM4's Gen2 ×1 link and gives this away. Reference on this build
(WD SN730, 2026-09-23): seq read 398 MiB/s, 4K random read 55k IOPS at QD32.

## 7. Record

- [ ] EEPROM version and `BOOT_ORDER` → [`../logs/firmware-versions.md`](../logs/firmware-versions.md)
- [ ] Boot time and `lspci` link speed → [`../logs/build-log.md`](../logs/build-log.md)
- [ ] Any deviation from these steps → [`../logs/known-issues.md`](../logs/known-issues.md)

## Rollback

Re-insert the microSD. With `BOOT_ORDER=0xf461` it boots from the card whenever NVMe fails.
If the EEPROM itself is the problem, recover with `rpiboot` in EEPROM-recovery mode through the
adapter's USB-C flash port.
