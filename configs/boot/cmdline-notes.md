# `cmdline.txt` changes

File: `/boot/firmware/cmdline.txt` (Bookworm/Trixie) or `/boot/cmdline.txt` (older images).
It is a **single line** — do not add newlines.

## Required on CM4 for GPS

Remove:

```
console=serial0,115200
```

Leave `console=tty1` and everything else intact. With the serial console enabled the kernel
holds the GPS UART (`/dev/serial0` -- `/dev/ttyS0` on this build, see below), and GPS output
works intermittently or not at all.

Before:

```
console=serial0,115200 console=tty1 root=PARTUUID=xxxxxxxx-02 rootfstype=ext4 fsck.repair=yes rootwait
```

After:

```
console=tty1 root=PARTUUID=xxxxxxxx-02 rootfstype=ext4 fsck.repair=yes rootwait
```

## Removed on this build: `resize`

The imaged card's line carried a `resize` flag, left over from first-boot filesystem expansion. It
was removed 2026-09-23 after the NVMe migration, since root already fills the drive. Current line:

```
console=tty1 root=PARTUUID=e10af45d-02 rootfstype=ext4 fsck.repair=yes rootwait quiet splash plymouth.ignore-serial-consoles cfg80211.ieee80211_regdom=US
```

## Verification

```bash
cat /proc/cmdline                 # confirm console=serial0 is gone after reboot
sudo systemctl status serial-getty@ttyS0.service   # should be inactive/masked -- this
                                                    # build's GPS UART is ttyS0, not ttyAMA0
                                                    # (onboard Bluetooth holds the PL011 as
                                                    # ttyAMA1); check `ls -l /dev/serial0` if
                                                    # a future image maps it differently
```

If a getty is still bound to the UART:

```bash
sudo systemctl disable --now serial-getty@ttyS0.service
```

## Rollback

Keep a copy before editing:

```bash
sudo cp /boot/firmware/cmdline.txt /boot/firmware/cmdline.txt.bak
```

A broken `cmdline.txt` prevents boot. Recover by mounting the boot partition on another machine
and restoring the `.bak` — this is why the microSD stays in the kit even after NVMe boot works.
