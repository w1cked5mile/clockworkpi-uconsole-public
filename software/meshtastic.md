# Meshtastic — LoRa mesh + GPS on the AIO V2 (SX1262, GP-02)

Working, verified configuration as of 2026-09-18. For the trial-and-error that got here (wrong
SPI bus, a CS/hardware-CS conflict, a TCXO mismatch, a gpsd/meshtasticd port conflict), see
[`../docs/logs/build-log.md`](../docs/logs/build-log.md)'s 2026-09-17 and 2026-09-18 entries — this
file is the reproducible end state, not the journal.

## Prerequisites

1. `dtparam=spi=on` + `dtoverlay=spi1-1cs` in `config.txt`
   ([`../configs/boot/config-cm4.txt`](../configs/boot/config-cm4.txt)). **Must be `-1cs`, not
   `-0cs`** — `-0cs` registers zero chip-select lines, so the kernel never creates `/dev/spidev1.0`
   at all (confirmed 2026-09-17, see build-log). Overlay changes need a reboot.
2. `devterm-printer` masked if present — it holds SPI1 on ClockworkPi's DevTerm image. **Not
   applicable on this build**: confirmed 2026-09-17 the service doesn't exist on this image.
3. **915 MHz antenna attached to `ANT1`** before enabling the rail or transmitting — LoRa TX
   without one can damage the SX1262 PA.
4. `aiov2_ctl LORA on` (and, for GPS, `aiov2_ctl GPS on`) — both rails default off at boot;
   persist with `aiov2_ctl --boot-rail LORA on` / `--boot-rail GPS on`.

Confirm the bus exists before blaming the radio: `ls /dev/spidev1.*` → `spidev1.0`.

## Install

```bash
sudo apt install meshtasticd            # native Linux firmware — drives the SPI radio directly
sudo apt install gtk-meshtastic-client  # optional native GUI (GTK4/Libadwaita, unofficial)
python3 -m venv ~/.venvs/meshtastic && ~/.venvs/meshtastic/bin/pip install meshtastic
ln -s ~/.venvs/meshtastic/bin/meshtastic ~/.local/bin/meshtastic   # CLI, already on PATH
```

`meshtastic` (pip/CLI) is a **client only** — it talks to a running Meshtastic node over
serial/TCP/BLE, it does not drive SPI itself. **`meshtasticd`** is the native Linux build of the
firmware itself; it's what actually owns the radio, and the CLI/GUI just connect to it locally
(default: TCP `localhost:4403`). Without `meshtasticd` running, `meshtastic --info` hangs
indefinitely with no error — it's waiting for a node that doesn't exist, not failing.
`sudo aiov2_ctl --add-apps` (which would install `meshtastic-mui`) does **not** work on this
image — confirmed 2026-09-16, the `hackergadgets-*` packages aren't published anywhere reachable
from this repo's apt sources (see [`../docs/logs/known-issues.md`](../docs/logs/known-issues.md)).
`gtk-meshtastic-client` (plain Debian package, unrelated to that meta-package) works fine instead.

## Configure

Base config, then join the regional community meshes:

```bash
meshtastic --host localhost --info                            # confirm meshtasticd + SX1262 up
meshtastic --host localhost --configure ../configs/meshtastic/us915.yaml
meshtastic --host localhost --ch-index 0 --ch-set name SCMesh    # primary: sets the frequency
meshtastic --host localhost --ch-add NCMesh
meshtastic --host localhost --ch-set psk default --ch-index 1
meshtastic --host localhost --set position.gps_mode ENABLED   # see GPS section — needs a restart
```

**The primary channel's name sets the frequency.** With `channel_num` unset, Meshtastic hashes the
primary channel name to pick a slot: unnamed or `LongFast` gives slot 19 (906.875 MHz), `SCMesh`
gives slot 88 (924.125 MHz), and `NCMesh` gives slot 59 (916.875 MHz). Secondary channels share
the primary's frequency. Until 2026-09-23 this node joined SCMesh and NCMesh only as
**secondaries** on a LongFast primary, so it sat on 906.875 MHz and couldn't hear the owner's
SCMesh-primary Heltec V3 or M5Stack. Check the live frequency with
`journalctl -u meshtasticd | grep "Set radio"`. The SCMesh-primary layout matches the owner's other
nodes. Whether it's what scmesh.us recommends is *unverified*.

Region for your location is **US** (902–928 MHz). Region is a software setting on this hardware —
the SX1262 covers the whole 860–960 MHz range, so there was no SKU choice to make (see
[`../docs/logs/decisions.md`](../docs/logs/decisions.md)).

`meshtastic --export-config` (to capture the live state as `as-applied.yaml`, normally the
convention for staged configs in this repo) **hangs indefinitely with no output** against this
node — confirmed 2026-09-17, not investigated further. Don't rely on it; this file is the current
record instead.

### `/etc/meshtasticd/config.d/lora-aio-v2.yaml` (LoRa radio — final, working)

```yaml
Lora:
  Module: sx1262
  DIO2_AS_RF_SWITCH: true
  DIO3_TCXO_VOLTAGE: 1.8   # module has a TCXO (see hardware/specs/aio-v2.md); without this,
                           # RadioLib fails chip detection/commands with -2 or -706/-707
  IRQ: 26
  Busy: 24
  Reset: 25
  spidev: spidev1.0
  # No "CS:" line. With dtoverlay=spi1-1cs the kernel owns GPIO18 as hardware CS0
  # (confirm: `cat /sys/kernel/debug/gpio | grep GPIO18` → "spi1 CS0 ... ACTIVE LOW"). Setting
  # "CS: 18" here makes Portduino try to also claim it via libgpiod, which fails with
  # "gpiod_line_request_reconfigure_lines: Assertion 'request' failed" and aborts meshtasticd.
```

### `/etc/meshtasticd/config.d/gps-aio-v2.yaml` (GNSS)

> **Currently disabled, 2026-09-21** — renamed to `gps-aio-v2.yaml.disabled` so `gpsd` could take
> `/dev/serial0` instead (Kismet and other tools need it; see
> [`gps.md`](gps.md#gps--gnss--gpsd-and-clients)). `meshtasticd` itself is still running normally
> for LoRa mesh — only GPS-sourced position is off. Content below is what to restore it with.

```yaml
GPS:
  SerialPath: /dev/serial0
```

**`gpsd` and `meshtasticd` cannot share `/dev/serial0`.** meshtasticd's GPS support only opens a
raw serial device itself (no gpsd/network client — confirmed by grepping strings in the
`meshtasticd` binary); `gpsd` holds the port exclusively while running. This file (`gpsd` disabled,
meshtasticd owning GPS directly) was the working setup from 2026-09-18 to 2026-09-21; flipped back
to `gpsd` owning the port on 2026-09-21. They don't coexist as configured — re-enabling one means
disabling the other.

`SerialPath` alone does nothing: `position.gps_mode` (a device config field, separate from the
daemon's serial config) has to be set to `ENABLED` too — that's the actual on/off switch — and
it only takes effect on the next `meshtasticd` restart, not live.

### Position from gpsd, without giving up the port (current setup, 2026-10-02)

The node gets position **without** `meshtasticd` owning `/dev/serial0`: `gpsd` stays the sole
owner of the receiver (so Kismet, PyGPSClient, the webdash and chrony's clock discipline all keep
working — see [`gps.md`](gps.md)), and a small host bridge reads gpsd and pushes the fix into
`meshtasticd` over its localhost admin API. This resolves the long-standing either/or above — you
no longer have to choose between gpsd and Meshtastic position.

Set the node once so the firmware stops trying to drive a serial GPS it can't reach, and uses the
externally supplied fixed position instead:

```bash
meshtastic --host localhost --set position.gps_mode NOT_PRESENT
```

Then install the bridge (host service; uses the `meshtastic` library from `~/.venvs/meshtastic`):

```bash
sudo cp ../webdash/host-helpers/mesh-gps-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now mesh-gps-bridge.service
journalctl -u mesh-gps-bridge -f        # "sent position: grid=... fix=3D ..."
```

How it works: the bridge calls `setFixedPosition()`, so the node **adopts** the position (it shows
in `getMyNodeInfo` and rebroadcasts on the firmware's normal position schedule, so peers see us
while we message) rather than a one-shot `sendPosition()` the node ignores. It only updates on a
move of ≥100 m or every ≤900 s (airtime/write gate); all tunable by env var — see the header of
[`../webdash/host-helpers/mesh-gps-bridge.py`](../webdash/host-helpers/mesh-gps-bridge.py).
Verified end to end 2026-10-02: a live 3D fix (grid `FM03cv`, eph ~13 m, HDOP 0.7) pushed through
and read back as the node's own fixed position. **Position is only as good as the fix** — indoors,
multipath can give a confident but wrong fix (an early send landed a grid field away before the fix
settled), so trust it outdoors with low HDOP.

Roll back: `sudo systemctl disable --now mesh-gps-bridge.service`, then
`meshtastic --host localhost --remove-position` (clears the fixed position and its flag).

## Verify

| Check | Command | Expect |
|---|---|---|
| `meshtasticd` running | `sudo systemctl status meshtasticd` | active, no SPI/GPIO errors, no restart-looping |
| Radio detected | look for in the log | `SX126x init result 0` and `sx1262 init success` |
| GPS detected | look for in the log | `[GPS] L76K detected` |
| Client connects | `meshtastic --host localhost --info` | node info, region US, `gpsMode: ENABLED` |
| Local nodes | `meshtastic --host localhost --nodes` | own node; others if any are in range |
| Round trip | second node on the same channel/preset | message delivered both directions |

Confirmed working end-to-end 2026-09-17/18: `meshtasticd` active with no crash-loop, SX1262
detected, GPS chip detected and polling (no satellite fix yet — needs clear sky, not a fault),
and three channels live at the time: PRIMARY `LongFast` (region US, `LONG_FAST` preset), SECONDARY
`SCMesh`, SECONDARY `NCMesh` (both using Meshtastic's public default key `AQ==`, sourced from
[ncmesh.net/join](https://ncmesh.net/join/) and [scmesh.us](https://www.scmesh.us/)). **Since
2026-09-23 the layout is PRIMARY `SCMesh` (924.125 MHz) and SECONDARY `NCMesh`, with `LongFast`
dropped.** See "Configure" above for why.

LoRa mesh itself (radio, channels) is unaffected by the 2026-09-21 GPS-ownership swap above; only
the "GPS detected"/position-broadcast row currently doesn't apply, since `meshtasticd` no longer
has a `SerialPath` to read.

A single node in isolation cannot prove RF works. The LoRa acceptance test needs a second node
([`../docs/checklists/module-bringup-tests.md`](../docs/checklists/module-bringup-tests.md) 3.10). It
**passed 2026-09-23** with the owner's Heltec V3: traceroute and acknowledged direct messages both
ways.

## Interacting with the node

- **CLI**: `meshtastic --host localhost --sendtext "hi"` (primary), sends on the primary channel
  (SCMesh); add `--ch-index 1` for NCMesh.
- **Native GUI**: `gtk-meshtastic-client` (installed above) — connect via **TCP/IP** to
  `localhost`. No CLI flags or config file to pre-seed the connection; it has to be entered in
  the app's connection screen each time (confirmed 2026-09-17 — no `--host` option, no relevant
  `gsettings` key beyond UI preferences).
- **Official mobile app** (Android/iOS): this node has `hasBluetooth: false`, so use the app's
  **Network** connection type (not Bluetooth pairing) pointed at the device's LAN IP — it talks to
  the same TCP port 4403 API as the CLI/GUI, independent of the Webserver module below.
- **Browser** (a local page, or [client.meshtastic.org](https://client.meshtastic.org)): needs
  meshtasticd's `Webserver` module enabled. **Done 2026-09-18** — uncommented `Port: 9443` and
  `RootPath: /usr/share/meshtasticd/web` in `/etc/meshtasticd/config.yaml`. On restart it
  self-generated a self-signed cert/key at `/etc/meshtasticd/ssl/` (confirmed:
  `Create SSL Cert /etc/meshtasticd/ssl/certificate.pem successful` in the log) and listened on
  `0.0.0.0:9443`, not just localhost. **Moved to port 9444 on 2026-09-25**: the `tailscale serve`
  entry for `:9443` blocks meshtasticd's `0.0.0.0:9443` bind, which caused the
  `Error starting Web Server framework, error number: 4` failures from 2026-09-22 on. The tailnet
  still reaches it at `https://fancy.<tailnet>.ts.net:9443/`. On the LAN it's now
  `https://<device-ip>:9444/`. See [`../docs/logs/known-issues.md`](../docs/logs/known-issues.md).

**One API client at a time.** `meshtasticd` serves port 4403 to a single client. While the webdash
host bridge (`uvicorn` on `127.0.0.1:8090`) is connected, the CLI and GUI get kicked off
(`Broken pipe` on the first heartbeat). Stop the bridge before using them.

## Receive activity and the first-packet alert

> **Superseded 2026-09-23, later the same evening:** the silence below was a **frequency
> mismatch**, not a quiet area and not a receive fault. The node was on LongFast (906.875 MHz)
> while the owner's nodes were on SCMesh (924.125 MHz); see "Configure" above. After moving the
> primary to SCMesh, a traceroute to the owner's Heltec V3 went both ways (6.5 / 6.25 dB SNR), and
> acknowledged direct messages went both ways (checklist 3.10).
> The SDR scan below only covered 905.6–908.2 MHz, so it never looked at 924.125 MHz.

As of 2026-09-23 the node had **heard nothing**. Across ~4 h of uptime on US LongFast
(906.875 MHz, slot 19), the LocalStats line showed `num_packets_rx=0`, `num_packets_rx_bad=0`
and `channel_utilization=0.0`, with the noise floor at -93 dBm. `num_total_nodes=2` suggests one
other node was heard at some point. A 3-minute `rtl_power` scan of 905.6–908.2 MHz on the AIO SDR
showed the LongFast channel more than 10 dB above its neighbours in only 2 of 180 seconds, while
915 MHz ISM activity turned up across the whole span. Most likely there's no mesh within range of
an indoor stub antenna. A receive fault isn't ruled out until a second node (checklist 3.10) or
an outdoor test is heard.

A one-shot user service alerts on the first packet. It follows meshtasticd's journal, and on the
first LocalStats line with `num_packets_rx > 0` (decoded) or `num_packets_rx_bad > 0` (heard,
not decoded) it sends a critical desktop notification. It also appends a line to
`~/meshtastic-first-packet.log` and disables itself. The stats line is logged every ~15 min, so
the alert fires within 15 min of the first packet.

```bash
install -m 755 ../configs/meshtastic/first-packet-alert.sh ~/.local/bin/meshtastic-first-packet-alert
install -m 644 ../configs/meshtastic/first-packet-alert.service ~/.config/systemd/user/
systemctl --user daemon-reload && systemctl --user enable --now first-packet-alert
```

Files: [`../configs/meshtastic/first-packet-alert.sh`](../configs/meshtastic/first-packet-alert.sh)
(install, verify and rollback in its header) and
[`../configs/meshtastic/first-packet-alert.service`](../configs/meshtastic/first-packet-alert.service).
Installed and running 2026-09-23. The parsing was tested with dry-run lines (decoded, bad, none,
and a real stats line), and a notification sent from a user-service context reached the desktop.
**It fired for real at 2026-09-24T01:39:29Z** (`num_packets_rx=2`, after the SCMesh fix below) and
disabled itself as designed. To re-arm it: `systemctl --user enable --now first-packet-alert`. It
runs only while the desktop session is logged in, because lingering is off for this user.

## MQTT internet-bridging (not configured)

Both NCMesh and SCMesh publish public MQTT broker credentials on their own sites for
internet-bridging local RF traffic to their wider networks, but meshtasticd's MQTT module only
holds one broker connection at a time — bridging both simultaneously isn't possible without
picking one. Deliberately left unconfigured on 2026-09-17 (both channels' `uplinkEnabled`/
`downlinkEnabled` are `false`); revisit and pick a single broker (`mqtt.ncmesh.net` or
`mqtt.scmesh.us`) if internet-bridging is wanted. Credentials intentionally not copied into this
repo even though they're public-by-design — see each site for current values.

## Cautions

- Do not enable the rail or transmit without an antenna.
- The default `LongFast` channel is public and unencrypted by design. Generate a PSK for private
  use (`meshtastic --ch-set psk random --ch-index 0`) and **never commit it**. `SCMesh`/`NCMesh`'s
  shared default key (`AQ==`) is not a real secret — see Configure above — but a real generated
  PSK for a private channel is, and stays off this repo per this repo's no-secrets convention.
- Position broadcast is on: since 2026-10-02 `position.gps_mode` is `NOT_PRESENT` and the
  `mesh-gps-bridge` service supplies the fix from gpsd (see "Position from gpsd" above). This
  publishes location to the mesh over RF whenever it moves ≥100 m. To stop sharing location,
  `sudo systemctl disable --now mesh-gps-bridge.service` and
  `meshtastic --host localhost --remove-position`. Precise coordinates are transmitted by design
  but are never written to this repo (grid square only) — see [`gps.md`](gps.md#privacy).
