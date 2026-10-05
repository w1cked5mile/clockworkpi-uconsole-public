# Known issues & troubleshooting log

Symptoms, causes, fixes. Seed from forum threads; add your own as you hit them.

## Reference threads

- uConsole Mod Megathread: https://forum.clockworkpi.com/t/uconsole-mod-megathread/12227
- CM4/CM5 setup guides + scripts: https://forum.clockworkpi.com/t/cm4-cm5-uconsole-setup-guides-with-scripts/22818
- AIO board package thread: https://forum.clockworkpi.com/t/hackergadgets-aio-board-package/17875
- RPIBOOT on the adapter: https://forum.clockworkpi.com/t/using-rpiboot-on-the-hackergadgets-cm4-5-adapter/21767

## Entries

### Fancy's network link stutters / drops packets on a weak Wi-Fi signal — onboard `wlan0` power save

**Symptom.** SSH / tailnet sessions to Fancy lag and stall and look like they are "losing
connection", though `wlan0` stays associated to the AP the whole time.

**Observed 2026-09-30.** `wlan0` (onboard brcmfmac) on 2.4 GHz channel 1 at **−69 to −71 dBm**, tx
rate collapsed to **5.5 Mbit/s** with ~3,800 `tx failed`; ping showed **20–30% loss and 70 ms+
latency even to the local gateway**. Not tailscale (fancy was online) and not the AC1200 (`wlan1`
was down, on a separate USB bus; its two bring-up USB resets at 600 / 726 s uptime had already
settled).

**Cause.** Wi-Fi power save (the driver default) turns a marginal signal into actual packet loss.

**Fix (mitigation).** Disable power save on the managed radio:
- Runtime: `sudo iw dev wlan0 set power_save off` — loss went **20–30% → 0%**, latency **70 → ~20 ms**.
- Persistent: [`../../configs/networkmanager/wifi-powersave-off.conf`](../../configs/networkmanager/wifi-powersave-off.conf)
  (`[connection] wifi.powersave = 2`), deployed to `/etc/NetworkManager/conf.d/` 2026-09-30. Scoped
  to the managed radio only — the AC1200 (`wlan1`) is left unmanaged, so it is untouched.

**Root cause still open.** The signal is still weak (−71 dBm, 5.5/11 Mbit). Power save off stops the
loss but does not strengthen the link. Real fixes: **re-seat the onboard Wi-Fi u.FL antenna**
(possibly disturbed during the 2026-09-30 AC1200 install), move Fancy closer to the AP, or use
Ethernet (`eth0`, 1 Gbps, currently unplugged).

### Flashing a microSD on Windows: `Set-Disk -IsOffline` fails with "Not Supported"

- **Observed:** `Set-Disk -Number N -IsOffline $true` against the card reader returns
  `Not Supported — Extended information: Removable media cannot be set to offline.` Hit 2026-09-15
  while flashing the v3.1 image.
- **Cause:** Windows only supports the offline/online state on *fixed* disks. A card reader
  enumerates as removable, so the usual "take the disk offline, then write raw" recipe does not
  apply to it at all.
- **Fix:** Lock and dismount each **volume** instead of the disk — `FSCTL_LOCK_VOLUME` (`0x00090018`)
  then `FSCTL_DISMOUNT_VOLUME` (`0x00090020`) on `\\.\X:` — and hold those handles open for the
  whole write. Releasing them early lets Windows remount the card the moment the new partition
  table lands, mid-write. This is what Win32DiskImager and rpi-imager do. Implemented in the raw
  writer kept beside the image at `D:\Source\uConsole\flash-sd.ps1`.
- **Related:** raw access to `\\.\PhysicalDriveN` needs Administrator — an unelevated shell fails
  with "Access to the path is denied" before writing anything. Opening and locking the *volume*
  (`\\.\E:`) does **not** need elevation; only the physical-drive write does. Raspberry Pi Imager
  avoids the whole problem by self-elevating, and is the easier route if you do not need a
  scripted flash.
- **Gotcha when adapting the script:** PowerShell parses an 8-digit hex literal as `Int32`, so a
  bare `0xC0000000` (`GENERIC_READ|GENERIC_WRITE`) silently becomes `-1073741824` and the P/Invoke
  fails with *"Cannot convert ... to type System.UInt32: Value was either too large or too small"*.
  Write it `[uint32]0xC0000000L` — the `L` forces `Int64` first, then the cast succeeds.
### 18650 cells marked "9900mAh" — capacity claim is not physically achievable

- **Observed:** the two cells fitted to the stock battery board on 2026-09-15 are wrapped
  `9900mAh 3.7V` / `18650 LI-ION RECHARGEABLE BATTERY`, green wrap, **no brand or model name and no
  batch code** anywhere on the wrap.
- **Why it is wrong:** the highest-capacity 18650 cells in mass production are about **3500 mAh**
  (Panasonic NCR18650GA 3450, Samsung INR18650-35E 3500, LG INR18650-MJ1 3500). A claim of
  9900 mAh is roughly **2.8× what the chemistry fits in that volume**. Cells wrapped with
  four-digit capacities in this range are a long-standing relabelling category; measured capacity
  is typically a few hundred to a couple of thousand mAh, protection circuits are often absent, and
  cell-to-cell consistency is not controlled.
- **Why it matters here specifically:** the system is **1S with the two holder positions in
  parallel**. Paralleling two cells whose capacity, internal resistance and state of charge are all
  unknown is the case this repo's own matched-pair rule exists to prevent — the stronger cell dumps
  current into the weaker one the moment they are connected. It also invalidates the ≈22 Wh
  two-18650 figure in [`../reference/power-budget.md`](../reference/power-budget.md), which assumed
  ≈3000 mAh per cell: **real pack energy is currently unknown, not 37 Wh and not 22 Wh.**
- **Checks that settle it, cheapest first:**
  - **Weigh each cell.** A genuine 3000–3500 mAh 18650 is ≈45–48 g. Substantially lighter means
    less active material, and no amount of wrapper text changes that. A kitchen scale is enough.
  - **Measure resting voltage** of each cell and compare (already a checklist item — expect
    ≈3.6–3.8 V storage charge, both within 0.05 V).
  - **Capacity test** at ≈0.2 C (≈0.6 A) down to 2.5 V on a cell analyser. That number replaces
    every runtime estimate in `power-budget.md`.
- **Until those are done:** treat pack energy as unmeasured, and do not leave the device charging
  unattended. Replacement is a matched pair from a named manufacturer with a real datasheet.
- **Status:** open as of 2026-09-16. Cells were fitted 2026-09-15, and **the device was already
  powered on and booted once, 2026-09-16, before any of these checks were done** — see
  `docs/logs/build-log.md`'s "First boot" entry. Do the checks now, before any *further* power-up.

### ~~`ANT1` carries an unmarked stub that is almost certainly the wrong band~~ — WITHDRAWN 2026-09-15

- **This entry was wrong and is retracted the same day it was written.** An edge-on photograph of
  the fitted antennas shows every stub is marked, in exactly the mapped order: **`LoRa`,
  `Bluetooth`, `Bluetooth`, `Wi-Fi`, `Wi-Fi`, `Wi-Fi`**, then the GNSS puck. `ANT1` carries a
  vendor-marked **LoRa** antenna.
- **Where the error came from:** a close-up taken during inventory showed only three of the six
  markings — the others faced away from the camera — and that partial count was written up as "no
  antenna is marked `LoRa`". It also *overturned* an earlier, correct reading of a dimmer frame
  that had noted a `LoRa` marking. A partial count was treated as a complete one.
- **The length argument was also unsound.** "Shorter than an 82 mm ¼-wave, therefore not 915 MHz"
  only holds for a straight quarter-wave radiator. These are loaded stubby/rubber-duck antennas,
  whose helical element makes them routinely **half or less** of the free-space ¼-wave physical
  length at their design frequency. Physical length implies nothing about band for this antenna
  class.
- **Standing position:** the vendor marking is the evidence, and it says LoRa. No mismatch is
  suspected. If certainty is wanted before TX, sweep 902–928 MHz on a VNA and expect better than
  2:1 — that is a confirmation step, not a suspicion.
- **What still holds from the original entry:** LoRa TX into a bad load can damage the SX1262 PA
  ([`../../hardware/specs/aio-v2.md`](../../hardware/specs/aio-v2.md)), so the antenna stays on
  `ANT1` before the rail is enabled. That was always the rule and is unchanged.

### Networking "spotty" after a hostname change — stale `127.0.1.1` line in `/etc/hosts`

- **Observed:** general networking flakiness reported 2026-09-20. System hostname was `fancy`
  (changed from `clockworkpi` at some earlier point).
- **Cause:** `/etc/hosts` still had the old `127.0.1.1 clockworkpi` line. Tailscale had already
  picked up the new name, but local hostname resolution via `/etc/hosts` was stale — anything
  resolving `hostname` through it (`sudo`, some daemons) missed the fast local match and fell
  through to a slower path.
- **Fix:** `sudo sed -i 's/127.0.1.1\t\tclockworkpi/127.0.1.1\t\tfancy/' /etc/hosts`. Confirmed
  with `getent hosts $(hostname)` → `127.0.1.1 fancy`.
- **Status:** resolved 2026-09-20, for the local-hostname-resolution symptom specifically. See
  [`build-log.md`](build-log.md#2026-09-20--linux-hostname-change-clockworkpi--fancy-fixed-a-stale-etchosts-entry)
  for the full entry, including the sudo NOPASSWD grant this required since the fixing session had
  no TTY for a password prompt.
- **Update 2026-09-22 — a second, unrelated cause of "spotty" networking, now also resolved:**
  general Wi-Fi connectivity kept being flaky even after the `/etc/hosts` fix above, which only
  ever explained slow local name resolution, not radio-level drops. Root cause was the antenna
  path: the external u.FL lead for the CM4's onboard Wi-Fi (`wlan0`/`brcmfmac`, `dtparam=ant2`,
  see [`../../hardware/specs/cm4-lite-8gb.md`](../../hardware/specs/cm4-lite-8gb.md) and the
  `ANT4` mapping in [`decisions.md`](decisions.md)) was plugged into a u.FL connector on the
  mainboard (silkscreen `CPI 3.14`), not into the u.FL connector on the CM4 module itself.
  Reseating the lead onto the CM4 module's own connector directly — bypassing the mainboard
  connector — fixed it; the device owner confirms Wi-Fi connectivity now works as expected.
  Mechanism (cold joint vs. marginal mating vs. a mainboard-side routing fault) not diagnosed —
  only the fix was verified. **Status: resolved 2026-09-22.** This also answers, in part, the
  still-open "which antenna position performs better in the shell" question in
  [`decisions.md`](decisions.md): whichever u.FL connector is used, it should be the module's own,
  not the mainboard's.

### ~~Onboard Ethernet never links~~ — RESOLVED 2026-09-23: the kit's CM4 adapter had no port for the AIO V2's Ethernet ribbon

- **Observed:** 2026-09-20, first attempt at checklist 2.2. `eth0` (`bcmgenet`, the CM4's native
  gigabit controller, whose jack is the RJ45 on the AIO V2 — *corrected 2026-09-25; this entry first
  said the mainboard's own jack* — **not** the separate HackerGadgets
  upgrade-kit RJ45+USB3 board, which isn't installed on this build; see the AIO V2/NVMe entries
  elsewhere in this log) never shows carrier: `ip link` reports `NO-CARRIER`, `ethtool` reports
  `Link detected: no`.
- **Ruled out, in order:**
  - **Not a missing/absent PHY.** The PHY is on the CM4 module itself (the CM4 datasheet lists an
    on-module gigabit Ethernet PHY), which is why it answered over MDIO. *Corrected 2026-09-25:*
    this bullet first placed the jack and PHY on the mainboard; the jack is on the AIO V2.
  - **Not a device-tree/overlay misconfiguration.** Live device tree
    (`/proc/device-tree/scb/ethernet@7d580000`) shows `status = okay`, `phy-mode = rgmii-rxid`,
    and a correctly wired `phy-handle` to `mdio@e14/ethernet-phy@0` (MDIO address 0) — exactly
    what `dtoverlay=clockworkpi-uconsole` should produce, and the driver initializes cleanly
    (`GENET 5.0 EPHY`, `Broadcom UniMAC MDIO bus`, `configuring instance for external RGMII (RX
    delay)`).
  - **Not a broken MDIO management bus.** `mii-tool -v eth0` successfully reads the PHY chip's own
    registers over MDIO — vendor OUI, model/rev, and its full capability list
    (`1000baseT-HD/FD`, `100baseTx-HD/FD`, `10baseT-HD/FD`) all come back correctly. The
    digital control path between the SoC and the PHY works.
  - **Not an autonegotiation incompatibility with the far end.** Forced `ethtool -s eth0 speed 100
    duplex full autoneg off` — a mode that only needs a valid electrical link pulse, no
    negotiated handshake — and the PHY's own status register (read by both the kernel and
    `mii-tool`) still reports no link.
  - **Not the cable or the switch port.** The same cable/port pair was confirmed working on a
    different machine.
  - **The jack's LEDs are not diagnostic on this board.** Solid green + solid amber were observed
    with a cable inserted, which looked at first like a real link the driver just wasn't
    reporting — but the same LEDs stay solid with the cable **fully unplugged**, so they are not
    wired to reflect real link state (likely just tied to a power rail). Disregard them for this
    subsystem; use `mii-tool -v eth0` or `ethtool eth0` instead.
- **Standing conclusion, revised 2026-09-22 — not a hardware fault, no RMA needed.** The
  2026-09-20 diagnosis correctly showed every software-checkable layer working (overlay, device
  tree, MDIO management, forced-mode negotiation) and pinned the gap to the physical link path,
  but read that as probable damage. Per the device owner: the CM4-to-CPI adapter **currently
  installed is the uConsole kit's own basic adapter — an older model that only supports CM4, not
  CM5 — and it has no port for the AIO V2's Ethernet ribbon** (the wording at the time said the adapter
  "lacks the ribbon"; see the 2026-09-25 correction below). The port is on the **upgraded
  HackerGadgets adapter, part of order #11953** (see
  [`../records/order-and-warranty.md`](../records/order-and-warranty.md) and
  [`../../hardware/specs/upgrade-kit-boards.md`](../../hardware/specs/upgrade-kit-boards.md)),
  which is also why the PHY answered over MDIO while there was no link — exactly the split the
  2026-09-20 session observed. This
  explanation is **not yet independently confirmed on hardware** — #11953 still hasn't arrived —
  so it stands as the working theory, not a closed fact, until the adapter is swapped in and
  Ethernet is retested.
- **Status:** open, but **downgraded from suspected hardware fault to expected behavior of the
  interim adapter** as of 2026-09-22. No RMA action needed against the mainboard. Re-test checklist
  2.2 once the HackerGadgets adapter (#11953) is installed; if Ethernet still doesn't link at that
  point, the hardware-fault hypothesis is back on the table. See
  [`build-log.md`](build-log.md#2026-09-20--onboard-ethernet-diagnosed-as-a-hardware-fault) for the
  original diagnostic session.
- **Update 2026-09-23 (later):** The HackerGadgets adapter from #11953 is **now installed**.
  `eth0` comes up and the PHY still reads over MDIO. Carrier is still absent, but **no cable was
  plugged in**, so this is not yet a retest. The next step is to plug in a live cable and run
  checklist 2.2. See
  [`build-log.md`](build-log.md#2026-09-23--hackergadgets-kit-installed-boot-migrated-to-nvme-storagenicusbpower-tests).
- **Resolved 2026-09-23 (01:35 UTC).** With a live cable plugged in, `eth0` linked at **1 Gbps
  full duplex**, got a DHCP lease and passed traffic with 0% loss. The interim adapter was the
  whole cause, as the device owner said, and no RMA is needed. See
  [`build-log.md`](build-log.md#2026-09-23--ethernet-links-at-1-gbps-charging-confirmed).
- **Correction 2026-09-25 (device owner):** the Ethernet RJ45 jack is on the **AIO V2**, and the AIO V2's Ethernet ribbon plugs into the port marked **"CM5 USB 3.0"** on the HackerGadgets CM4/5 Adapter Pro. The uConsole kit's `RPi CM4 to CPI v3.14 Adapter` has no such port, so until #11953 arrived the ribbon had nowhere to plug in. Nothing was missing from the kit: the ribbon came with the AIO V2. This fits every 2026-09-20 observation: the PHY is on the CM4 and answered over MDIO, but its line side had no path to the AIO V2's jack, and that jack's LEDs stayed lit with no cable because nothing behind them was connected. Earlier text in this entry calling it an "RGMII ribbon" on the adapter, or the mainboard's jack, is wrong. Which signals the ribbon carries is *unverified*.

### Kismet's nRF/KW41Z udev rules are rejected at every boot

- **Observed:** 2026-09-23. `systemd-udevd` logs `Invalid value "/bin/sh -c 'echo $(($(ls
  /dev/nrf51822* ...` `for PROGRAM (char 18: invalid substitution type), ignoring` for
  `99-kismet-nrf51822.rules`, `-nrf52840.rules` and `-nxp-kw41z.rules` (packages
  `kismet-capture-nrf-51822`, `-nrf-52840`, `-nxp-kw41z`).
- **Cause:** udev treats `$` as its own substitution character, so the shell's `$(` must be
  written `$$(`. The rules also lack a comma after `ACTION=="add"`. Upstream packaging bug.
- **Effect:** only the `/dev/nrf51822N`-style symlinks for those sniffer dongles are missing. None
  is attached, so nothing is broken today.
- **Fix:** corrected copies in [`../../configs/udev/`](../../configs/udev/) pass `udevadm verify`.
  Install with `sudo install -m644 configs/udev/99-kismet-*.rules /etc/udev/rules.d/ && sudo
  udevadm control --reload`. They are dpkg conffiles, so a Kismet upgrade will ask whether to keep
  them — keep the local version.
- **Status:** resolved 2026-09-23 — installed, `udevadm verify` passes on the installed files and
  udev reloaded. Confirm at next boot that the `Invalid value` lines are gone.

### `spi-bcm2835 fe204000.spi: prop pinctrl-0 index 1 invalid phandle` at boot

- **Observed:** every boot, 2026-09-23 and earlier.
- **Cause:** `fe204000` is **SPI0**, which `dtoverlay=spi0-0cs` strips of its chip-select pins,
  leaving an empty pinctrl entry. The LoRa SX1262 is on **SPI1** (`spi1-1cs`, `/dev/spidev1.0`).
- **Effect:** none on LoRa — `meshtasticd` logs `sx1262 init success` on the same boot.
- **Status:** resolved as harmless, 2026-09-23. No change made.

### RTC lost its time across the 2026-09-23 hardware swap

- **Observed:** 2026-09-23, first boot after fitting the HackerGadgets kit. `dmesg` shows
  `rtc-pcf85063 1-0051: POR issue detected, sending a SW reset`, then `rtc rtc0: Power loss
  detected, invalid time` and `hctosys: unable to read the hardware clock`. NTP resynced the system
  clock, and `timedatectl` then showed the RTC matching UTC.
- **Cause:** **confirmed 2026-09-23 — no backup cell is fitted** (owner report). A POR flag means
  the PCF85063 lost power entirely, which is expected with an empty holder.
- **Fix:** Fit the coin cell (listed as CR1220; *verify the holder size*), then run checklist 3.1:
  set the RTC, power off fully with no network, boot and compare.
- **Status:** open — waiting on the cell.

### `rtl_test` fails with `usb_claim_interface error -6` while `readsb` is enabled

- **Observed:** 2026-09-23. `aiov2_ctl SDR on` then `rtl_test` gives `usb_claim_interface error
  -6` / `Failed to open rtlsdr device #0`. The DVB modules are not loaded (`lsmod` is clean, and
  `blacklist-rtl-dvb.conf` is in place).
- **Cause:** historically `readsb` was `enabled` and grabbed the dongle as soon as the SDR rail
  powered it. This is not a USB or driver fault.
- **Fix:** As of **2026-10-03** `readsb` is `systemctl-disabled` — the SDR rail coming on no longer
  starts ADS-B. ADS-B is now one of three mutually-exclusive SDR applications chosen in the webdash
  SDR view (ADS-B / broadcast-airband hunt / listen), so the tuner is free unless you pick ADS-B.
  If ADS-B *is* running, free the dongle first: `sudo systemctl stop readsb` (or Stop ADS-B in the
  dashboard), then start your other SDR tool.
- **Status:** expected behaviour, logged so that `error -6` is not misread as the DVB-driver
  problem the checklist points to. The auto-grab-on-rail-up behaviour is resolved.

### ~~meshtasticd hears nothing~~ — RESOLVED 2026-09-23: wrong frequency (secondary vs primary channel)

- **Observed:** 2026-09-23. `num_packets_rx=0`, `num_packets_rx_bad=0` and
  `channel_utilization=0.0` over ~4 h, even with the owner's Heltec V3 on USB and an M5Stack node
  nearby.
- **Cause:** SCMesh and NCMesh were added as **secondary** channels on a LongFast primary
  (2026-09-17). With `channel_num` 0, the frequency slot is a hash of the **primary** channel
  name, so the node stayed on 906.875 MHz (slot 19). The owner's nodes use an SCMesh primary,
  which puts them on 924.125 MHz (slot 88).
- **Fix:** `meshtastic --host localhost --ch-index 0 --ch-set name SCMesh`, then
  `--ch-index 1 --ch-del` to drop the duplicate. The log now shows `name=SCMesh, ch=88`, and a
  traceroute to the Heltec went both ways. Stop the webdash container first:
  `meshtasticd` serves one API client at a time.
- **Rollback:** `--ch-index 0 --ch-set name ""` goes back to LongFast/906.875 MHz.

### meshtasticd web UI unreachable — its embedded webserver framework never starts (fixed 2026-09-25)

- **Observed:** 2026-09-22, reported as "the Meshtastic UI isn't available from webdash." The
  dashboard's "Open Meshtastic UI ↗" link (`https://fancy.<tailnet>.ts.net:9443/`) times out /
  connection-refuses. Confirmed **not a webdash bug**: `webdash`'s own Meshtastic panel (which
  talks to `meshtasticd`'s TCP API on `127.0.0.1:4403`) works fine, and `tailscale serve status`
  correctly shows the `:9443` mapping proxying to `localhost:9443` — there is just nothing local
  listening on `9443` for it to reach (`ss -tlnp` confirms only `tailscaled` itself holds `9443`,
  on the tailnet interface).
- **Cause:** `meshtasticd`'s own bundled HTTPS web UI server fails to start, every time, with
  `ERROR | 0 Error starting Web Server framework, error number: 4` immediately after `INFO | 0
  Webserver started` in the log — reproduced identically across the current boot and three
  separate manual `systemctl restart meshtasticd` runs. The framework is Ulfius +
  `libmicrohttpd12t64` (1.0.1-4) + `libgnutls30t64`, per this build's own dependency chain
  (confirmed in `dpkg.log`, installed together with `meshtasticd` 2026-09-16 and never upgraded
  since). **Ruled out:** missing/wrong cert or key (`/etc/meshtasticd/ssl/{certificate,private_key}.pem`
  exist, are owned `meshtasticd:meshtasticd`, the cert is valid until 2027 and its modulus matches
  the key); missing web root (`/usr/share/meshtasticd/web` present); a port conflict (nothing else
  bound to `9443` locally — **wrong, see Root cause below**); an IPv6 dual-stack bind edge case (IPv6 is disabled system-wide);
  AppArmor confinement (no `meshtasticd` profile loaded); a file-descriptor limit (`LimitNOFILE`
  524288); low disk space (54% free on `/`); and a dependency-version drift (no package in the
  Ulfius/libmicrohttpd/gnutls chain has changed since the 2026-09-16 install). It is **not**
  libmicrohttpd lacking TLS support either — it links `libgnutls30t64` and exports the GnuTLS
  symbols `MHD_start_daemon` needs.
- **This is a regression, not a since-day-one failure:** [`../../software/meshtastic.md`](../../software/meshtastic.md)
  recorded the webserver working on 2026-09-18 (`Create SSL Cert ... successful` in the log,
  listening on `0.0.0.0:9443`) — those are the same cert files still on disk today. Exactly what
  changed between then and now is **not identified**; `journalctl` only retains logs back to the
  current boot (2026-09-21 22:38), so there is no log evidence from the intervening days, and no
  package, config, or permission change was found that explains it.
- **External corroboration:** a Meshtastic Discourse thread ("Pie5 Unable to access meshtasticd
  while running") reports the identical `Error starting Web Server framework, error number: 4`
  message on a different Raspberry Pi 5 build — consistent with this being a real bug in
  `meshtasticd`'s Linux-native web-server startup path (this build is
  `2.7.26.61~obs54e0d8d~beta`, an OBS beta build) rather than something specific to this device.
  No fix was found in that thread or elsewhere searched.
- **Impact / workaround:** only the browser-based web UI is affected. The mesh itself, the TCP API
  (port 4403), the `meshtastic` CLI, `gtk-meshtastic-client`, and the official mobile app's Network
  connection type all still work normally — see
  [`../../software/meshtastic.md`](../../software/meshtastic.md#interacting-with-the-node). Use one
  of those instead of the web UI until this is resolved.
- **Tried 2026-09-22: `sudo apt install --reinstall meshtasticd`.** Backed up `config.yaml`,
  `config.d/`, and `ssl/` first as a precaution; `/var/lib/meshtasticd/.portduino` (the actual
  node/channel database with the joined NCMesh/SCMesh state) is outside the package and was never
  at risk. dpkg correctly detected `config.yaml` as a locally-modified conffile and left it alone
  (checksum unchanged across the reinstall). Result: **identical failure** — same
  `Error starting Web Server framework, error number: 4` on restart, byte-for-byte the same
  package reinstalled from the apt cache. This rules out a corrupted local install as the cause.
- **Root cause (found 2026-09-25): a port clash with `tailscale serve`.** The serve entry for
  `:9443` makes `tailscaled` listen on the tailnet address itself (`100.x.y.z:9443` and its
  IPv6 twin). meshtasticd binds the wildcard `0.0.0.0:9443`, and Linux refuses a wildcard bind
  while a specific address holds the port: `bind(("0.0.0.0", 9443))` returns `EADDRINUSE` with or
  without `SO_REUSEADDR`. Ulfius reports that as error 4 (`U_ERROR_LIBMHD`). The earlier "no port
  conflict" check only looked at loopback. It is a boot-order race: on 2026-09-25 meshtasticd
  started at 02:15:12, before tailscaled had brought its serve listener up, and the web server
  started normally ("Web Server framework started on port: 9443"). Every manual restart after
  boot lost the race, which is why the failure looked permanent. It also explains the "regression":
  the 2026-09-18 success came before the `:9443` serve entry was added.
- **Second fault in the same path:** the serve entry proxied `http://localhost:9443`, but
  meshtasticd serves HTTPS only (`ulfius_start_secure_framework`), so even a running web server
  would not have been reachable through it.
- **Fix (2026-09-25):** meshtasticd's `Webserver: Port` in `/etc/meshtasticd/config.yaml` moved to
  **9444**, and the serve entry now reads
  `sudo tailscale serve --bg --https=9443 https+insecure://localhost:9444` (self-signed cert, hence
  `+insecure`). The tailnet URL `https://fancy.<tailnet>.ts.net:9443/` is unchanged. webdash's
  `web_ui` probe now checks `127.0.0.1:9444`. **Verified 2026-09-25 09:40** after a restart with
  tailscaled already up: "Web Server framework started on port: 9444"; the tailnet URL returns
  `200` with the "Meshtastic Web" page, `/api/v1/fromradio` returns `200` through the proxy, and
  webdash's probe reports `web_ui: true`.
- **Unrelated, same day:** meshtasticd also exits (`No sx1262 radio`, then `free(): invalid
  pointer`) whenever the LORA rail is off, and systemd gives up after five restarts
  (`start-limit-hit`). The web app lives inside meshtasticd, so it's only up while LORA is on and
  the service is running (`sudo systemctl restart meshtasticd` after switching LORA back on).

### Kismet crash-loops on `systemctl start`, restart counter exhausts quickly (likely root cause found 2026-09-25; fix deployed, not yet re-tested)

- **Observed:** 2026-09-22, incidentally, while checking whether Kismet's HTTP response sets
  `X-Frame-Options`/CSP headers that would block embedding it in an iframe (for `webdash`'s new
  embedded-frame feature). `sudo systemctl start kismet` → `FATAL: Remote side closed read pipe`
  from multiple `kismet_cap_*` helper processes, `Start request repeated too quickly`, unit ends
  `failed`. Not investigated further — out of scope for that task. Left the service stopped and
  disabled (its normal resting state) and ran `systemctl reset-failed kismet` afterward, so no
  state was left behind.
- **Likely cause (found 2026-09-25, first LAB-15 run):** the foreground run failed at startup with
  `FATAL: Could not initialize HTTP server on 0.0.0.0:2501, could not bind socket - Address already
  in use`. `tailscale serve` holds `:2501` on the tailnet address (`100.x.y.z` and its IPv6
  twin), and Linux refuses Kismet's wildcard bind while a specific address holds the port — the same
  clash as the meshtasticd `:9443` entry above. The capture helpers' "Remote side closed read pipe"
  is what they log when the server exits under them, so the 2026-09-22 service failure is very
  likely this bind fatal followed by systemd's restarts. *Inferred, not confirmed from the service's
  own journal.*
- **Fix (deployed 2026-09-25):** `httpd_bind_address=127.0.0.1` in
  [`kismet_site.conf`](../../configs/kismet/kismet_site.conf). Loopback does not clash with the
  tailnet listener, `tailscale serve` still proxies `http://localhost:2501`, and the UI is no longer
  reachable on the LAN. The foreground run then started and surveyed normally
  ([finding](../../knowledge/wardriving/findings/2026-09-25-wifi-survey.md)).
- **Status:** likely resolved for the bind clash; **the root `kismet.service` has not been
  re-tested** and stays disabled. Superseded operationally (2026-10-01): the webdash now starts
  Kismet as a **user** systemd service
  ([`../../webdash/host-helpers/kismet-user.service`](../../webdash/host-helpers/kismet-user.service)),
  which runs reliably — start/stop verified repeatedly on Fancy, with `kismet_cap_linux_wifi` coming
  up each time. The root unit's crash-loop therefore no longer blocks running Kismet; see
  [`webdash-architecture.md`](../reference/webdash-architecture.md)'s "Kismet start/stop" for why a
  user service is used instead of the root one. If the root unit is ever wanted, re-test with
  `sudo systemctl start kismet; journalctl -u kismet -n 30` (expect no bind `FATAL`) and note that
  it would contend with the user service for `:2501` — run only one.

### `tailscale serve` exposes Kismet and the meshtasticd web UI to the tailnet without webdash's login

- **Observed:** 2026-09-24, during the learning-platform analysis
  ([`learning-platform-plan.md`](../reference/learning-platform-plan.md) §3.6).
  `tailscale serve status` lists three tailnet-only entries: `:443` → webdash `:8090`, **`:2501` →
  Kismet** and **`:9443` → meshtasticd's web UI**. The last two bypass webdash's password + TOTP.
  meshtasticd's UI has no login of its own and can transmit; Kismet has its own admin login once
  one is set.
- **Cause:** the two extra serve entries were added for direct access. It's harmless while the
  owner's devices are the only tailnet members.
- **Fix:** before sharing Fancy with anyone (node sharing or a guest account), remove the entries
  (`sudo tailscale serve --https=2501 off`, `sudo tailscale serve --https=9443 off`, *verify the
  syntax against the installed tailscale version*) or add a tailnet ACL that limits other users to
  `fancy:443`.
- **2026-09-29 — closed, then restored the same day at the owner's request.** Both serve mappings
  were removed (`sudo tailscale serve --https=2501 off` / `--https=9443 off`; tailscale 1.102.4) and
  the owner then chose to bring both UIs back — they are wanted on the tailnet, and the owner is the
  sole tailnet member (accepted risk, reaffirming the 2026-09-24 decision). Mappings re-added and
  meshtasticd's `Webserver:` re-enabled; `serve status` again lists `:443`, `:2501`, `:9443`.
  Two findings from the exercise, kept for whenever this is closed for real:
  - Removing the proxies alone is **not enough for meshtasticd** — it binds its webserver to
    `0.0.0.0:9444` (no bind-address option in the `Webserver:` block), so it stays directly
    reachable on the tailnet IP at `:9444` (`https://100.x.y.z:9444/` → `200`, no auth) even
    with the `:9443` proxy gone. Truly closing it means disabling that block in
    `/etc/meshtasticd/config.yaml` (backup `config.yaml.bak-20260929`) and restarting.
  - Kismet's `:2501` **is** fully closed by removing its proxy — it binds `127.0.0.1`
    (`httpd_bind_address` in `kismet_site.conf`) and also has its own login.
- **Separate, larger surface (open):** meshtasticd's **client API on `0.0.0.0:4403`** has no auth
  and is always tailnet-reachable. Left as-is because the dashboard's mesh collector and the
  `meshtastic` CLI use it (over loopback); revisit before sharing the device or binding it off-loopback.

### <symptom>

- Observed:
- Cause:
- Fix:
- Link:

---

## Watch-list (common gotchas to expect)

- `JP1` set wrong for the fitted battery → the jumper selects the current path: **open for 18650s,
  soldered closed for a JST LiPo pack**. Check it before first power-up; the silkscreen states it.
  **Armed since 2026-09-23:** the HackerGadgets NVMe battery board, which carries `JP1`, is
  installed. `JP1` was checked the same day and is **open**, correct for the interim 18650s now
  fitted (checklist 1.7). It must be soldered **closed** before the Meshnology LiPo goes on.
- `rpiboot` does nothing → charge-only USB-C cable; use a data cable.
- NVMe not detected / won't boot → bootloader EEPROM order or version; check `rpi-eeprom-config`.
- AIO module dead → its rail is off by default; `aiov2_ctl <FEATURE> on` or `pinctrl <GPIO> op`/`dh`.
- No GPS fix → passive antenna without clear sky, or wrong antenna type.
- No continuous GPS on CM4 → `console=serial0,115200` still in `cmdline.txt` grabbing the UART; remove it.
- `meshtastic --info` hangs indefinitely with no error → **not a hardware fault, a missing piece
  of software.** The `meshtastic` pip/pipx package is a *client* (talks to a node over
  serial/TCP/BLE); it does not drive the SX1262's SPI bus itself. This board's SX1262 has no
  onboard microcontroller running Meshtastic firmware, so there's nothing for the client to find.
  Needs **`meshtasticd`** (the native Linux build of the firmware itself) installed and running as
  the actual radio driver first — confirmed 2026-09-16 that it's not in this image's configured
  apt sources (only client packages `python3-meshtastic`/`gtk-meshtastic-client` show up); it
  ships from Meshtastic's own apt repo, not added here, and adding one needs `sudo`. See
  [`../../software/meshtastic.md`](../../software/meshtastic.md) for the pin map `meshtasticd`
  will need (already documented in `hardware/specs/aio-v2.md`) and how the CLI itself was
  installed without `sudo` via a venv. **Update 2026-09-17:** `meshtasticd` is now installed and
  running; this specific hang is resolved. It surfaced three further, separate bugs on the way to
  a working radio — see the 2026-09-17 entry in
  [`build-log.md`](build-log.md#2026-09-17--meshtasticd-installed-and-run-against-real-hardware-for-the-first-time)
  for the full chain (`spi1-0cs` vs `spi1-1cs`, the wrong `spidev4.0` bus, the `CS: 18`/hardware-CS
  conflict, and the still-open `SX126x init result -707`).
- LoRa won't TX → region/frequency not configured in Meshtastic (Config → LoRa tab), not a hardware/SKU issue. The antenna on `ANT1` is vendor-marked `LoRa`, so start with the region setting rather than the hardware.
- LoRa silent / SPI errors on Rex's Bookworm image → `devterm-printer` service holding SPI1; stop it before using LoRa.
- USB stuck at 2.0 speeds → expected on CM4; USB 3.0 needs CM5 (and the newer adapter board).
- No sound / speaker seems dead → try 100% `PCM` volume first (`amixer -c0 set PCM 100%`) before
  suspecting hardware. Confirmed 2026-09-16: the default 80% (-17.41 dB) was inaudible on this
  board's amp; 100% (+4.00 dB, the top of this control's range) was clearly audible. Not a fault —
  this board's software gain range just tops out low.
- Bluetooth HID device (mouse/keyboard) connects then immediately drops, repeating every 10–60 s,
  with `bluetoothd: profiles/input/hog-lib.c:set_report_cb() Error setting Report value: Request
  attribute has encountered an unlikely error` in the journal → known upstream BlueZ bug
  ([bluez/bluez#1911](https://github.com/bluez/bluez/issues/1911), ATT error 0x0E): a BLE HID
  peripheral waking from its own sleep needs a moment before its GATT server responds, and BlueZ
  treats a request that lands in that window as permanent failure instead of retrying. No merged
  fix as of this build's BlueZ (5.82-1.1+rpt2). Hit 2026-09-16 with a Logitech M720 Triathlon.
  Workaround: `bluetoothctl remove <mac>`, re-pair while the peripheral is actively awake/moving,
  then nudge it if a later auto-reconnect drops again — there's no permanent fix short of a BlueZ
  patch or switching to a wired/Unifying-receiver connection. Not related to this repo's AIO
  V2/GPIO work — separate subsystem (onboard CM4 Bluetooth, not the AIO board).
- `aiov2_ctl --add-apps` / `apt install hackergadgets-uconsole-aio-board` fails, **not a dpkg
  error — the package genuinely isn't published anywhere reachable from this image.** Confirmed
  2026-09-16: `clockworkpi/apt`'s `bookworm` repo (the only one configured, `main` component only)
  has no `hackergadgets-*`, `meshtastic-mui`, `sdrpp-brown`, `tar1090`, or `pygpsclient` package,
  and the `hackergadgets` GitHub org has no apt repo at all (three unrelated repos). A ClockworkPi
  forum thread (`hackergadgets-aio-board-package`, posts #832/#838) shows other users hitting the
  identical "can't find package" error; the maintainer's only reply ("it's in the repo, run apt
  update first") doesn't match what's actually published. Fall back to installing pieces
  individually from stock Debian/pip instead of the meta-package: `rtl-sdr` (confirmed working for
  SDR, 2026-09-16), `gpsd`/`gpsd-clients` for GPS, `meshtastic` via `pip`/`pipx` for LoRa.
  **Update 2026-09-18:** the ADS-B/`tar1090` piece is now resolved — `readsb` (a `dump1090` fork)
  and `tar1090` installed directly from their own upstream installers (wiedehopf's scripts), not
  from this broken meta-package, and confirmed working end-to-end. See
  [`../../software/adsb-tar1090.md`](../../software/adsb-tar1090.md). `sdrpp-brown` specifically
  is still unresolved — a plain `sdrpp` binary is present on this build with no record of how it
  got there or whether it's actually the `-brown` fork; see
  [`../../software/sdr-stack.md`](../../software/sdr-stack.md).
  **Update 2026-09-23:** `pygpsclient` resolved too — installed from PyPI into
  `~/.venvs/pygpsclient`, fed from gpsd through a TCP NMEA relay (`configs/gpsd/gpsd-nmea-relay.py`). See
  [`../../software/gps.md`](../../software/gps.md#pygpsclient).
- AIO V2 not responding after first mount → forum reports it sometimes needs reseating on the mainboard connector before it starts working.
- SDR draws power at idle even though "off by default" → **not observed, and settled 2026-09-16**:
  a post-reboot `aiov2_ctl --status`/`--boot-rails-status` confirms all four rails off after a
  cold boot, matching the boot-apply code path (defaults every rail to off absent a saved config)
  and the vendor doc. SDR/USB still boot off as of 2026-09-22; still applies to SDR specifically.
  See [`decisions.md`](decisions.md).
- ~~GPS and LoRa boot **on** silently since 2026-09-17~~ — **closed 2026-09-22, was intentional**:
  `/usr/local/share/aiov2_ctl/config.json` gained a `rails_on_boot` entry the day after the "all
  rails off" baseline was settled, via the `aiov2_ctl` GUI tray app's boot-on-toggle checkbox (no
  CLI path writes it). Confirmed by the user as a deliberate choice, to keep `meshtasticd`/`gpsd`
  fed across reboots — it had just gone unlogged for 5 days, contradicting the
  checklist/decisions-log baseline the whole time. See [`decisions.md`](decisions.md), which now
  carries GPS+LoRa-on/SDR+USB-off as this build's standing cold-boot state.
- GPS documented as `/dev/ttyAMA0` → **wrong on this build, corrected 2026-09-16**: the CM4's
  onboard Bluetooth holds the full PL011 (registers as `ttyAMA1`); GPIO14/15 falls back to the
  mini-UART (`ttyS0`). Use `/dev/serial0` (the stable symlink) in commands and configs instead —
  confirmed streaming NMEA. `configs/gpsd/gpsd.default` updated; see [`decisions.md`](decisions.md).
- `rtl_test -t` prints `[R82XX] PLL not locked!` on every run (with GPS/LoRa rails either on or
  off) → benign. It's this librtlsdr build's tuner-init path warning on a non-E4000 tuner before
  the `-t` E4000-specific PLL check aborts with "No E4000 tuner found, aborting." Plain `rtl_test`
  (no `-t`) streams samples normally afterward — confirmed 2026-09-16, ~52 bytes lost in an 8 s
  run, consistent with the earlier sample-integrity pass. Not treated as a fault.
- `vcgencmd measure_temp`/`get_throttled` fail with `Can't open device file: /dev/vcio_gencmd` when
  run without `sudo` → `/dev/vcio` is `root:root 0600` on this image. Use `sudo vcgencmd ...`, or
  cross-check with `/sys/class/thermal/thermal_zone0/temp` (no sudo needed). Confirmed 2026-09-16.
- Idle CPU temp read 62–63 °C (`throttled=0x0`, never throttled) shortly after a burst of package
  installs — above the module-bringup checklist's "< 60 °C idle" bar. Not yet re-checked after a
  longer settle or with a clean idle (nothing installing, all AIO rails off). Recorded 2026-09-16,
  not treated as a fault yet — see [`docs/checklists/module-bringup-tests.md`](../checklists/module-bringup-tests.md) item 1.4.
