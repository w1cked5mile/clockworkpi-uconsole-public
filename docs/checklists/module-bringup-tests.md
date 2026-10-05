# Module bring-up & test checklist

Pass/fail acceptance test for each subsystem, with the exact command and the output that counts
as a pass. Power the relevant rail first (`aiov2_ctl <FEATURE> on`). Record results and date in
the [build log](../logs/build-log.md); log failures in [`../logs/known-issues.md`](../logs/known-issues.md).

Run in order — later tests assume the earlier ones passed.

## 0. Baseline state

```bash
uname -a; cat /etc/os-release          # image and kernel
aiov2_ctl --status                     # rail states + battery/AC from the AXP PMIC
aiov2_ctl --boot-rails-status          # what the boot service will apply
```

- [x] Record which rails are on immediately after a **cold** boot. Upstream `BOOT_DEFAULTS` sets
      SDR (BCM 7) on; forum reports call that CM5-specific. **This test settles it for CM4** —
      write the answer into [`../reference/pinout-gpio.md`](../reference/pinout-gpio.md) and
      [`../logs/decisions.md`](../logs/decisions.md).
      **Settled 2026-09-16, superseded 2026-09-17, re-settled 2026-09-22**: post-reboot
      `aiov2_ctl --status` confirmed all four rails off after a cold boot on 2026-09-16. A
      `rails_on_boot` block appeared in `/usr/local/share/aiov2_ctl/config.json` the very next day
      (file mtime 2026-09-17 23:42, undocumented until found 2026-09-22) setting **GPS and LoRa to
      boot on**, via the `aiov2_ctl` GUI tray app's per-rail "start on boot" checkbox (no CLI flag
      writes this key). Confirmed 2026-09-22 as a deliberate, standing choice — keeps
      `meshtasticd`/`gpsd` fed across reboots. **Current cold-boot baseline for this build: GPS +
      LoRa on, SDR + USB off** — see `decisions.md`. Not yet re-verified against an actual power
      cycle (this check ran on an already-up system, uptime since 2026-09-21 22:38); the config
      read and `--boot-rails-status`'s prediction agree, but a real reboot would close that gap.

## 1. Core platform

| # | Subsystem | Command | Pass criterion | Pass | Notes |
|---|---|---|---|---|---|
| 1.1 | Display | power on | Backlight on at boot; `Fn` brightness keys change level | [x] | pass 2026-09-22 — backlight-on-at-boot confirmed from software: `/sys/class/backlight/backlight@0` reads `brightness=3` (of `max_brightness=9`), `bl_power=0` (unblanked); `card1-DSI-1` DRM connector reports `status=connected`; framebuffer is `720×1280`, matching the panel spec. `Fn` brightness-key behavior confirmed in person by the device owner. |
| 1.2 | Keyboard | type in a terminal; `showkey -a` | Every key and the `Fn` layer register | [ ] | **Partial, 2026-09-22** — device enumeration confirmed from software: `ClockworkPI uConsole Keyboard` (event6, `sysrq`/`kbd`/`leds` handlers) and the separate `Consumer Control` interface (event5, carries the `Fn` media/brightness layer) both bound with stable `/dev/input/by-id/` symlinks; `showkey`/`dumpkeys` installed. **Per-key and `Fn`-layer registration not yet confirmed** — that needs someone at the keyboard running `showkey -a` and watching every key (including `Fn` combos) register, which this shell-only session can't do. Leave unchecked until observed. |
| 1.3 | Audio | `speaker-test -c2 -twav -l1`; plug headphones | Tone on speaker; auto-switch to 3.5 mm | [x] | pass 2026-09-16 (speaker only) — `speaker-test -D plughw:0,0 -c2 -twav -l1` on the `bcm2835 Headphones` card; front-L/R tones confirmed audible by the builder. **Default `PCM` volume (80%, -17.41 dB) was inaudible; raised to 100% (+4.00 dB, top of this control's range) to hear it** — worth knowing before assuming the board is silent. `clockworkpi-audio-patch.service` (amp/jack-sense) and `clockworkpi-audio-shutdown.service` both active since boot, no GPIO workaround needed. Headphone-jack auto-switch not yet tried. |
| 1.4 | Thermals | `sudo vcgencmd measure_temp`; `sudo vcgencmd get_throttled` | Idle < 60 °C; `throttled=0x0` | [ ] | needs `sudo` — `/dev/vcio` is root-only. 2026-09-16: 62–63 °C idle (over bar), `throttled=0x0`; re-check after longer settle + 10 min load. **Re-checked 2026-09-22** (uptime 1 h 04 m, load avg 0.64/0.38/0.26): 62.8 °C, `throttled=0x0` — essentially unchanged, still over the < 60 °C bar, never throttled. Not a clean idle: GPS + LoRa rails are on (the standing boot config, see `decisions.md`) and this checking session itself was running, so a couple of watts of real load are baked into this number, not a true floor. Still not treated as a fault — no 10-minute deliberate-load run has been done yet to see the delta from here. |
| 1.5 | Storage (NVMe) | `lsblk -o NAME,SIZE,MODEL,MOUNTPOINT` | `nvme0n1` present; root on it once NVMe boot is set | [x] | pass 2026-09-23 — `nvme0n1` = WD PC SN730 256 GB (SN `<ssd-serial-redacted>`, FW `11130101`); `findmnt /` → `/dev/nvme0n1p2`, `/boot/firmware` → `nvme0n1p1`, both by NVMe PARTUUID. SMART `PASSED`, 0 media errors; drive is second-hand (25,560 h, 47.48 TB written, 21% used). `fio` direct I/O: seq read 398 MiB/s, seq write 365 MiB/s, 4K rand read 55k IOPS. microSD still inserted as fallback at the time. *Superseded later on 2026-09-23:* the card was removed and NVMe-only boot passed. See build log 2026-09-23. |
| 1.6 | NVMe link | `sudo lspci -vv \| grep -A3 'Non-Volatile'` | Device enumerates; `LnkSta` shows the negotiated width/speed | [x] | pass 2026-09-23 — `LnkSta: Speed 5GT/s (downgraded), Width x1 (downgraded)` against the drive's `LnkCap 8GT/s x4`: the CM4's Gen2 ×1 ceiling, as expected. No AER/NVMe errors in `dmesg`. |
| 1.7 | Battery | `aiov2_ctl --power`; unplug and run | Discharge current reported; no reverse-polarity LED; charges when re-plugged | [x] 2026-09-23 | record idle and SDR-on draw. 2026-09-16: ran on AC only (not unplugged) — reported 100%, charging, ~0.3 W; a genuine discharge reading is still needed **2026-09-23 (after NVMe battery board fitted):** genuine discharge reading — on battery, `axp22x-ac online=0`, 71–73%, 3.63–3.68 V, **1.44–1.46 A / ~5.3 W** with screen on, GPS+LoRa rails on. Charging on re-plug not yet tested; which pack/`JP1` state is fitted not confirmed. **2026-09-23 (01:37 UTC), charger re-plugged:** `axp22x-ac online=1`, battery `Charging` at a steady **1.96 A** into the pack, 3.96 V, 66%. System and battery together drew 7.78 W from the charger, `throttled=0x0`. Discharge and charge are both confirmed. **2026-09-23, owner at the board: reverse-polarity LED not lit, `JP1` open — PASS.** Charging ~2 A into the unverified `9900mAh` pair: watch cell temperature. |

## 2. Connectivity

| # | Subsystem | Command | Pass criterion | Pass | Notes |
|---|---|---|---|---|---|
| 2.1 | Wi-Fi (onboard) | `nmcli device wifi list`; connect; `ping -c3 1.1.1.1` | Associates, DNS + ping work | [x] | pass 2026-09-22 — connectivity had been spotty; traced to the external u.FL antenna lead being plugged into a connector on the mainboard (`CPI 3.14`) instead of the CM4 module's own u.FL connector. Reseated directly onto the module's connector; works as expected since. See `known-issues.md`. |
| 2.2 | Ethernet (RJ45 on the AIO V2, ribbon to the Adapter Pro) | plug cable; `ip -br a`; `ethtool eth0 \| grep Speed` | Link up, IP acquired | [x] | **FAIL, 2026-09-20** — this is the CM4's native `bcmgenet` gigabit controller, whose jack is the AIO V2's RJ45 (*corrected 2026-09-25*: first recorded as the mainboard's jack; the AIO V2's ribbon had no port on the kit's adapter), not the separate HackerGadgets upgrade-kit board (that one isn't installed — see `known-issues.md`), so it is not USB-bottlenecked. `ethtool`/`mii-tool` read the PHY correctly over MDIO (vendor/model/capabilities all identify), device tree is correctly configured (`phy-mode=rgmii-rxid`, `phy-handle`→`ethernet-phy@0`, `status=okay`), but the PHY's own link-status register reports no link — confirmed with a cable verified good on another machine, and unchanged when forced to 100M/full/no-autoneg. Jack LEDs are not diagnostic here: confirmed solid on both colors even fully unplugged. **Revised 2026-09-22 — not believed to be a mainboard fault**: the CM4-to-CPI adapter currently fitted is the uConsole kit's basic, CM4-only adapter, which per the device owner has no port for the AIO V2's Ethernet ribbon — the HackerGadgets adapter has one (order #11953, not yet arrived). Re-test once that adapter is installed. See `known-issues.md`. **2026-09-23:** HackerGadgets adapter now installed; `eth0` up, PHY reads over MDIO, but **no cable was plugged in** — link test still to do. **PASS 2026-09-23 (01:35 UTC)** with the HackerGadgets adapter fitted and the AIO V2's Ethernet ribbon plugged into it: `Link is Up - 1Gbps/Full - flow control rx/tx`, `mii-tool` reports `negotiated 1000baseT-FD`, DHCP gave it `192.168.x.y/24`, and it took the default route (metric 100, ahead of `wlan0`). 0% loss to the gateway (avg 1.4 ms) and to `1.1.1.1` (avg 13.6 ms). A 100 MB HTTPS download peaked at 10.3 MB/s (~82 Mbit/s), probably limited by the internet connection. The LAN rate was not measured because there was no `iperf3` peer. 0 RX errors, 11 TX drops over ~82k packets. This confirms the adapter-ribbon diagnosis; the mainboard is fine. |
| 2.3 | USB hub | `aiov2_ctl USB on`; `lsusb -t` | Hub and attached devices enumerate | [x] | pass 2026-09-16 — 4-port hub + RTL-SDR enumerate correctly. Re-verified 2026-09-23 after the kit install: Genesys `05e3:0608` hub, keyboard, RTL2838 (SDR rail on) and a new QinHeng `1a86:8091` hub (presumed RJ45+USB3 board — *unverified*, no device plugged into it) all enumerate at 480M; no USB errors in `dmesg`. **RJ45 + USB3 board ports, 2026-09-23 (01:40 UTC):** a USB device (Baochip Baosec-lite, `1d50:6198`) plugged into the board enumerated at **480M** behind the QinHeng `1a86:8091` hub, and `usbhid` and `cdc_acm` (`ttyACM1`) bound. That confirms the hub belongs to this board. It works with the AIO `USB` rail (GPIO23) **off**, so the hub doesn't depend on that rail. The first two full-speed attempts logged `device descriptor read/64, error -32` before it enumerated as high-speed, most likely contact bounce during insertion. No over-current events. |
| 2.4 | AC1200 card (if fitted) | `iw dev`; `sudo iw phy phyN info \| grep -A3 'Supported interface modes'` | `monitor` listed | [ ] | needed for wardriving |
| 2.5 | SSH / Tailscale | from another host: `ssh user@fancy` over the tailnet (Tailscale SSH); `tailscale status` | Reachable over the tailnet (**tailnet-only by design since 2026-09-24**; no LAN `sshd`) | [x] | pass 2026-09-24 — owner logged in over **Tailscale SSH** from `gpu-host` (Windows); `RunSSH: true`, `tailscaled be-child ssh` holds the login shell. Criterion changed from "LAN and tailnet" by owner decision: no `sshd` runs, so nothing listens on :22 on the LAN (see [`../logs/decisions.md`](../logs/decisions.md)). 2026-09-16: node online in `tailscale status` |

## 3. AIO V2 radios

| # | Subsystem | Command | Pass criterion | Pass | Notes |
|---|---|---|---|---|---|
| 3.1 | RTC | `sudo hwclock -r`; `timedatectl`; power off fully, remove network, boot, re-check | Time survives a full power cycle within a few seconds | [ ] | CR1220 fitted; `aiov2_ctl --sync-rtc` writes system→RTC. 2026-09-16: `pcf85063a` enumerates on I2C (`i2c-1`, address `0x51`) and `/dev/rtc0` exists after the overlay reboot; `timedatectl` shows RTC time within 1 s of system time. Full power-cycle-without-network test still not run (needs `sudo`, not available this session) |
| 3.2 | GPS rail | `aiov2_ctl GPS on`; `stty -F /dev/serial0 9600; timeout 10 cat /dev/serial0` | NMEA sentences (`$GNRMC`, `$GNGGA`) stream | [x] | pass 2026-09-16 — full NMEA sentence set streaming (`$GNGGA`, `$GNGLL`, `$GNGSA`, `$GPGSV`, `$GLGSV`, `$GNRMC`, `$GNVTG`, `$GNZDA`) plus `$GPTXT,...,ANTENNA OK`, confirming `ANT7` continuity to the GPS module. **Device is `/dev/serial0` (`ttyS0`), not `/dev/ttyAMA0`** — onboard CM4 Bluetooth holds the PL011 as `ttyAMA1`; see `pinout-gpio.md`. `console=serial0` already absent from `cmdline.txt`. |
| 3.3 | GPS fix | `cgps` or PyGPSClient, clear sky | 3D fix; ≥4 satellites; plausible lat/lon | [x] | pass 2026-09-23 — 30 s `gpspipe -w` sample through gpsd: 150/150 TPV reports `mode 3`; 12 satellites visible, **9 used** (8 GPS + 1 GLONASS, SNR 15–33 dB-Hz); HDOP 0.9, PDOP 1.9; eph ≈17 m, epv ≈37 m; position steady to <1 m over the run, grid **EM95**, altitude ~189 m MSL. Time to first fix not measured (the receiver was already warm). Cold fix can take minutes; active antenna helps. 2026-09-16: 0 satellites indoors, as expected |
| 3.4 | SDR rail | `aiov2_ctl SDR on`; `rtl_test -t` | `Found 1 device(s): 0: Realtek, RTL2838...`; tuner `R860`; no "usb_claim_interface error -6" | [x] | pass 2026-09-16 — `HackerGadgets, AIO_V2 Ext, SN: 25120901`; tuner identifies as `R820T` not `R860` (see `hardware/specs/aio-v2.md`), no error -6. error -6 → apply [`../../configs/modprobe.d/blacklist-rtl-dvb.conf`](../../configs/modprobe.d/blacklist-rtl-dvb.conf). Re-verified 2026-09-16 after the RTC/LoRa overlay reboot — still passes, GPS/LoRa rails on or off makes no difference. `rtl_test -t` prints `[R82XX] PLL not locked!` every run; benign — plain `rtl_test` streams normally after it (see `known-issues.md`) |
| 3.5 | SDR sample integrity | `rtl_test -s 2400000 -d0` for 30 s | Zero or near-zero dropped samples | [x] | pass 2026-09-16 — ~20 s run, ~132 bytes lost, ~1 sample/million. USB 2.0 shared bus; back off to 2.048 MS/s if lossy Re-verified 2026-09-23 after the kit install: ~25 s at 2.4 MS/s, 0 samples/million lost. Stop `readsb` first — it holds the dongle (`error -6`) whenever the SDR rail is on. |
| 3.6 | SDR PPM | `rtl_test -p` (10+ min, warm) | Stable PPM figure; record it | [x] | pass 2026-09-24 — **≈ +1 ppm**, cumulative settled 0 to +2 over 12.5 min warm with `readsb` stopped; brief −5/−17 outliers are USB timing jitter. Recorded in [`../../knowledge/sdr/configs/gain-and-sample-rate-profiles.md`](../../knowledge/sdr/configs/gain-and-sample-rate-profiles.md) |
| 3.7 | ADS-B end-to-end | 1090 MHz antenna; tar1090 web UI | Aircraft appear on the map | [ ] | see [`../runbooks/first-rf-checkout.md`](../runbooks/first-rf-checkout.md) |
| 3.8 | LoRa rail | `aiov2_ctl LORA on`; `ls /dev/spidev1.*` | `spidev1.0` present | [x] | pass 2026-09-16 — `spidev1.0` present after the overlay reboot; `devterm-printer` never present on this image |
| 3.9 | LoRa radio | `meshtastic --info` | Node info returns; region set to **US915**; SX1262 detected | [x] | pass 2026-09-23 — `meshtastic --host localhost --info` returns node info against `meshtasticd`: region `US`, preset `LONG_FAST`; log shows `SX126x init result 0` / `sx1262 init success`. Earlier note (CLI hung with no node, 2026-09-16) predates `meshtasticd`. |
| 3.10 | LoRa link | second node powered on same channel | Bidirectional message TX/RX | [x] | pass 2026-09-23 — with a Heltec V3 on the same channel (SCMesh, 924.125 MHz): traceroute both ways (6.5 dB out, 6.25 dB back), then acknowledged direct messages both ways: uConsole → Heltec `Received an ACK`; Heltec → uConsole `Received an ACK`, and meshtasticd logged `Received text msg from=0x433ef4a8`. A first DM before node-info exchange NAKed `PKI_SEND_FAIL_PUBLIC_KEY` |

## 4. Power characterization (do once, it feeds the power budget)

Record measured draw with `aiov2_ctl --power` in each state, then update
[`../reference/power-budget.md`](../reference/power-budget.md):

| State | Measured current | Notes |
|---|---|---|
| Idle, screen on, all rails off | ~5.0 W at cell (derived: 5.33 W − GPS Δ) | 2026-09-23, battery, NVMe root, 3.68 V. Not a clean floor: session shells running |
| + SDR rail on, `rtl_test` running | Δ +0.64 W (rail only, `rtl_test` not running during measure) | 2026-09-23 `aiov2_ctl --measure SDR`; 7.3 W / 2.01 A peak seen with SDR+USB on and `rtl_test` starting |
| + GPS rail on, acquiring | Δ +0.29 W | 2026-09-23 `aiov2_ctl --measure GPS`, indoors (no fix) |
| + LoRa rail on, idle listen | Δ ≈ 0 (−0.11 W, within noise) | 2026-09-23 `aiov2_ctl --measure LORA`, `meshtasticd` idle |
| + USB rail on, nothing attached | Δ ≈ 0 (+0.03 W) | 2026-09-23 `aiov2_ctl --measure USB` |
| LoRa TX burst (22 dBm) | | short duty cycle |
| Screen off / suspended | | |

## Sign-off

- [ ] All required subsystems pass.
- [ ] Failures logged in [`../logs/known-issues.md`](../logs/known-issues.md) with symptoms and links.
- [ ] Measured values written back into the power budget and firmware-version logs.
- [ ] Baseline image backed up per [`../runbooks/backup-and-restore.md`](../runbooks/backup-and-restore.md).
