# Backup & restore runbook

Capture a known-good baseline after acceptance, and get back to it when an experiment breaks the
system. Closes the "back up the baseline image" item in [`../../TODO.md`](../../TODO.md).

## What counts as the baseline

The state at which [`../checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md)
passes: OS flashed and updated, overlays applied, `aiov2_ctl` installed, companion apps present,
network and SSH working. Take the image **before** starting RF experiments, not after.

## Method A — full image, offline (most faithful)

Power off, pull the storage, image it from another machine:

```bash
# microSD or NVMe in a reader on the host
sudo dd if=/dev/sdX of=uconsole-baseline-$(date -u +%Y%m%d).img bs=4M status=progress conv=fsync
xz -T0 -9 uconsole-baseline-$(date -u +%Y%m%d).img       # ~2–3× smaller
sha256sum uconsole-baseline-*.img.xz | tee uconsole-baseline.sha256
```

Restore:

```bash
xzcat uconsole-baseline-YYYYMMDD.img.xz | sudo dd of=/dev/sdX bs=4M status=progress conv=fsync
```

## Method B — image from the running system to external storage

Acceptable when the target is idle; not atomic, so expect a filesystem that needs a check on
first restore.

```bash
sudo apt install -y pv
sudo dd if=/dev/nvme0n1 bs=4M status=progress | pv | gzip > /mnt/usb/uconsole-baseline.img.gz
```

## Method C — file-level (fast, incremental)

Good for "don't lose my configs" rather than bare-metal recovery:

```bash
sudo tar --numeric-owner --one-file-system \
  --exclude=/proc --exclude=/sys --exclude=/dev --exclude=/tmp --exclude=/run \
  -czf /mnt/usb/uconsole-rootfs-$(date -u +%Y%m%d).tar.gz /
```

## What to keep in git instead of in an image

Configs, not blobs. Anything under [`../../configs/`](../../configs/) that you actually applied,
plus the as-applied exports:

```bash
meshtastic --export-config > configs/meshtastic/as-applied.yaml
cp /boot/firmware/config.txt   configs/boot/as-applied-config.txt
cp /boot/firmware/cmdline.txt  configs/boot/as-applied-cmdline.txt
aiov2_ctl --boot-rails-status  > configs/as-applied-boot-rails.txt
```

`.gitignore` already excludes `*.img`, `*.img.xz`, `*.7z`, `*.zip` — images stay out of the repo
by design. Store them on external media and record location + checksum in
[`../logs/firmware-versions.md`](../logs/firmware-versions.md).

## Restore drill

An untested backup is not a backup. Once, deliberately:

- [ ] Restore the baseline image to a **spare** microSD.
- [ ] Boot from it, confirm login and network.
- [ ] Note the elapsed time in the build log — that number is what you are buying.

## Retention

| Keep | Why |
|---|---|
| Baseline (post-acceptance) | The known-good floor |
| Latest working config export | Rebuild without re-deriving settings |
| One pre-major-change image | Cheap rollback for kernel/EEPROM changes |

Delete older images once a newer one has passed the restore drill.
