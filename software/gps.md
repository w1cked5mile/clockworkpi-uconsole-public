# GPS / GNSS — gpsd and clients

**Correction, 2026-09-21 — `gpsd` owns `/dev/serial0` again.** Between 2026-09-18 and
2026-09-21, `meshtasticd` held the port directly (see the superseded note below); switched back
so Kismet, PyGPSClient, etc. can share the receiver. `meshtasticd`'s GPS config,
`/etc/meshtasticd/config.d/gps-aio-v2.yaml`, was renamed to `.disabled` (not deleted — trivial to
revert) and `meshtasticd` restarted to release the port; Meshtastic keeps running LoRa mesh
normally but no longer gets a GPS-sourced position. `gpsd` was re-enabled with the exact steps in
the "gpsd" section below — no drift from what's staged in
[`../configs/gpsd/gpsd.default`](../configs/gpsd/gpsd.default). Confirmed working: `gpsd` opens
`/dev/serial0` (`NMEA0183` driver, 9600 8N1) and NMEA sentences (`$GNGGA`, `$GNRMC`) flow
correctly. **No satellite fix after ~5 minutes** (`mode:1`, empty `SKY` report throughout) — the
antenna itself was already confirmed healthy 2026-09-16 (`ANTENNA OK`, see
[`../docs/logs/decisions.md`](../docs/logs/decisions.md)), so this reads as no sky view rather
than a hardware fault; per the fix-expectations table below, indoors may never fix. Re-test
outdoors or near a window before treating this as a problem.

If Meshtastic needs GPS-sourced position: **you no longer have to give the port back.** Since
2026-10-02 the `mesh-gps-bridge` service reads gpsd and pushes the fix into `meshtasticd` over its
API, so `gpsd` keeps `/dev/serial0` (and Kismet, PyGPSClient and the clock discipline keep working)
while Meshtastic still gets position — see [`meshtastic.md`](meshtastic.md#position-from-gpsd-without-giving-up-the-port-current-setup-2026-10-02).
The old either/or (stop `gpsd`, restore `gps-aio-v2.yaml`, let `meshtasticd` own the raw port) is
only needed if you specifically want the firmware driving the GPS directly.

<details>
<summary>Superseded 2026-09-18 note (meshtasticd owned the port)</summary>

`gpsd` was stopped and disabled in favor of `meshtasticd` owning `/dev/serial0` directly, because
`meshtasticd`'s GPS support only opens a raw serial device itself (no gpsd/network client) and the
two can't share the port. See [`../docs/logs/build-log.md`](../docs/logs/build-log.md)'s
2026-09-18 entry for why that was done, and its 2026-09-21 entry for why it was switched back.

</details>

## Prerequisites (CM4-specific)

1. `enable_uart=1` in `config.txt`
2. `console=serial0,115200` **removed** from `cmdline.txt` — otherwise the kernel console holds
   the UART and GPS works intermittently or not at all
   ([`../configs/boot/cmdline-notes.md`](../configs/boot/cmdline-notes.md))
3. `aiov2_ctl GPS on`

## Raw check first (before installing anything)

```bash
stty -F /dev/serial0 9600
timeout 10 cat /dev/serial0
```

Expect NMEA sentences: `$GNRMC`, `$GNGGA`, `$GPGSV`. Garbage characters usually mean the wrong
baud rate (try 38400, 115200). Silence means the rail is off, the UART is held, or the overlay
is missing.

`/dev/serial0` is the stable symlink to whichever tty is actually the GPIO14/15 header UART.
**Not `/dev/ttyAMA0`** on this build: the CM4's onboard Bluetooth holds the full PL011 (it
registers as `ttyAMA1`), so the header UART falls back to the mini-UART (`ttyS0`). Confirmed
2026-09-16 reading live NMEA off `/dev/serial0` — see
[`../docs/logs/decisions.md`](../docs/logs/decisions.md).

## gpsd

```bash
sudo apt install -y gpsd gpsd-clients
sudo cp ../configs/gpsd/gpsd.default /etc/default/gpsd
sudo systemctl enable --now gpsd
cgps -s                 # live fix view
gpspipe -r -n 10        # raw sentences through gpsd
```

gpsd is what lets Kismet, PyGPSClient, and anything else share one receiver — run it rather than
having each tool open `/dev/serial0` directly.

## Time sync — GPS disciplines the system clock (chrony)

**Done 2026-10-02.** This build's RTC does not survive a power-off, so with no network the clock
comes up wrong and anything time-dependent breaks — most visibly **TOTP 2FA** (codes are an HMAC
over a 30 s time-step; a clock even minutes off is rejected), and also TLS validity and log
timestamps. gpsd already has GPS time; it just needed a disciplinarian that can read a refclock.

**Verified root cause of the bad offline clock.** The board *does* carry a PCF85063A RTC with a
CR1220 backup (`../configs/boot/config-cm4.txt`), and `/dev/rtc0` is the `rtc-pcf85063` device — but
the kernel logs `rtc rtc0: Power loss detected, invalid time` at boot (`dmesg | grep rtc`, confirmed
2026-10-02). The backup cell is dead or unseated, so the RTC boots with no valid time. Replacing the
CR1220 is the hardware fix for *warm* GPS starts (see the fix-expectations table); until then, and
whenever truly offline, GPS is what sets the clock.

The image default, **systemd-timesyncd, cannot do this** — it is an SNTP *client* only and cannot
consume a refclock. So **chrony** replaces it: online it uses the Debian NTP pool as before; offline
it disciplines the clock from GPS via gpsd's shared-memory refclocks. The config and full
apply/verify/rollback steps live in [`../configs/chrony/chrony-gps.conf`](../configs/chrony/chrony-gps.conf).

```bash
sudo apt install -y chrony
sudo install -m 644 ../configs/chrony/chrony-gps.conf /etc/chrony/conf.d/gps.conf
sudo systemctl disable --now systemd-timesyncd      # chrony install usually does this already
sudo systemctl enable --now gpsd chrony
sudo systemctl restart chrony
```

How it works: gpsd writes GPS time into SysV shared memory; chrony reads NMEA from SHM unit 0 and
(when present) PPS from unit 1. NMEA alone is accurate to a fraction of a second — far inside TOTP's
30 s step. `/etc/chrony/chrony.conf`'s `makestep 1 3` lets chrony *step* the clock on the first few
updates, which is essential here since the RTC can boot years off.

Verify (GPS refclocks only become reachable **with a satellite fix** — test outdoors / near a
window, per the table below):

```bash
chronyc sources -v     # NMEA (and PPS) listed; '#?' seen-not-locked, '#*' current source
chronyc tracking       # Reference ID / Stratum reflect the live source
timedatectl            # 'System clock synchronized: yes'
```

Verified 2026-10-02 (indoors, with a 3D fix at the window): chrony recognised both refclocks and the
**`NMEA` refclock became reachable** (`chronyc sources` showed `Reach` advancing, sample within
~0.1 s). It stayed `#?` rather than selected only because the online NTP pool was more accurate at
the time and won; **offline, NMEA is the only reachable source and chrony disciplines from it** — the
intended behaviour. **PPS was not exported by gpsd** in that test (`Reach 0`) even though
`/dev/pps0` and `pps_ldisc` are present; the config deliberately puts no `prefer` on PPS, so a silent
PPS never blocks sync, and NMEA is sufficient on its own. Wiring gpsd to the PPS source for
sub-microsecond time is *unverified* and left as a future improvement.

To roll back to the image default time daemon, see the rollback block in the config file header.

## PyGPSClient

GUI view of satellites, signal levels, and fix quality — useful for judging antenna placement
(active vs passive, indoors vs sky view). **Installed 2026-09-23 (v1.7.6)** in a no-`sudo` venv,
the same pattern as the `meshtastic` CLI — not via `aiov2_ctl --add-apps`, whose `pygpsclient`
package isn't published anywhere reachable (see
[`../docs/logs/known-issues.md`](../docs/logs/known-issues.md)):

```bash
python3 -m venv ~/.venvs/pygpsclient
~/.venvs/pygpsclient/bin/pip install pygpsclient
ln -sf ~/.venvs/pygpsclient/bin/pygpsclient ~/.local/bin/pygpsclient
```

Needs `tkinter` (present on this image: Tk 8.6).

**PyGPSClient can't talk to gpsd directly.** It reads raw NMEA/UBX from a serial port or from a
socket it *connects to*; gpsd's port 2947 speaks JSON until a client asks for NMEA. Opening
`/dev/serial0` directly would fight gpsd for the port. So a small relay,
[`../configs/gpsd/gpsd-nmea-relay.py`](../configs/gpsd/gpsd-nmea-relay.py) (Python stdlib only),
listens on TCP `127.0.0.1:50010`, which is PyGPSClient's default socket port. It opens a gpsd
session per client with `?WATCH={"nmea":true}` and forwards only the NMEA sentences.

```bash
install -m 755 ../configs/gpsd/gpsd-nmea-relay.py ~/.local/bin/gpsd-nmea-relay
```

A wrapper, `~/.local/bin/pygpsclient-gpsd`, starts the relay, runs PyGPSClient, and stops the relay
on exit:

```sh
#!/bin/sh
"$HOME/.local/bin/gpsd-nmea-relay" &
relay=$!
trap 'kill $relay 2>/dev/null' EXIT INT TERM
"$HOME/.local/bin/pygpsclient" "$@"
```

The menu entry `~/.local/share/applications/pygpsclient.desktop` (Science category) runs that
wrapper. In PyGPSClient, click the **socket connect** button. The defaults (TCP IPv4, `localhost`,
`50010`) are already right, so no config file is needed.

Verified 2026-09-23: PyGPSClient, launched on `:0` and connected through its own socket-connect
handler, reported a **3D fix, 11 of 12 satellites used, HDOP 1.0** within 20 s.

> **Correction, 2026-09-23 — the first version of this section (UDP via `gps2udp`) could not
> work.** PyGPSClient's "UDP" mode is a UDP *client*: it `connect()`s to the server port and sends
> an empty datagram (`stream_handler.py`), and never listens on 50010. `gps2udp` sends to that
> port, so nothing received it. The relay above replaces it.

## Fix expectations

| Condition | Time to first fix |
|---|---|
| Cold start, passive antenna, indoors | may never fix |
| Cold start, clear sky | typically 30 s – several minutes |
| Warm start with RTC set and recent almanac | seconds |

The RTC matters here: a correct clock speeds acquisition. Sync it after NTP with
`aiov2_ctl --sync-rtc`.

## Privacy

GPS logs and Kismet captures contain precise coordinates. Repo convention is **general location
only** (city / Maidenhead grid) in anything committed — see
[`../knowledge/README.md`](../knowledge/README.md).
