# WatchDogsGo — hacking-RPG frontend over the AIO recon stack

[WatchDogsGo](https://github.com/LOCOSP/WatchDogsGo) (LOCOSP, MIT) is a Pyxel game that wraps
real recon tooling behind a 640×360 "open-world hacking RPG" UI. It is written for an ESP32-C5
running *projectZero* firmware, **but ships a no-ESP32 bridge** (`wdg_wifi_bridge.py`) that
emulates the projectZero serial protocol over a PTY and drives the uConsole's own AIO radios
instead. That bridge path is the one this build uses — Fancy already has every radio the game
expects.

**Scope on this build (read first).** WatchDogsGo also ships active-attack features — deauth
("Dragon Drain"), Evil Twin, MITM, BlueDucky, RACE. Those are **out of scope** under this build's
legal posture (receiving/learning/licensed TX; passive wardriving only — see
[`../knowledge/README.md`](../knowledge/README.md) and `CLAUDE.md`) and are **not enabled or
documented here**. On Fancy the tool is used for its **passive** layer: Wi-Fi/BLE survey, GPS
wardrive logging, and the RPG/learning frontend over that data. Handshake capture is the one
exception, allowed **only** inside the existing authorized-audit carve-out (own gear or a documented
engagement) — see "Handshake capture" below and [`aircrack-ng.md`](aircrack-ng.md).

Installed and verified on Fancy **2026-10-06**, WatchDogsGo **0.9.13** (git `6412603`). This file
is the reproducible end state; what is *not* yet exercised on hardware carries a verify marker.

## What it maps onto, on Fancy

| Game role | Hardware on Fancy | State |
|---|---|---|
| Wi-Fi survey (wardrive) | AC1200 MT7921 Wi-Fi → `wlan1` | ✅ present, monitor-capable ([`../hardware/specs/ac1200-mt7921.md`](../hardware/specs/ac1200-mt7921.md)) |
| Passive BLE | AC1200 Bluetooth → `hci1` (USB) | ✅ present |
| Internet / game uplink | CM4 onboard `brcmfmac` → `wlan0` | ✅ present |
| GPS | AIO GPS → gpsd → PTY | ✅ gpsd working ([`gps.md`](gps.md)) |
| Handshake capture | **external AWUS036ACM → `wlan2`** | ⚠️ **not fitted**; authorized-audit only — see "One radio, one Wi-Fi role" |
| ADS-B radar | AIO RTL-SDR (RTL2832U) via `dump1090` | ⛔ **held off** — see "SDR / stability" |
| LoRa / MeshCore | AIO SX1262 (SPI) | ⛔ **conflicts with `meshtasticd`** — see "LoRa" |
| Active attacks (deauth/EvilTwin/MITM/BlueDucky) | — | ⛔ **out of scope** under this build's legal posture; not enabled |

## One radio, one Wi-Fi role (why `wlan2` matters)

The AC1200 (MT7921AUN) is **two radios — Wi-Fi *and* Bluetooth — but only one Wi-Fi radio**: a
single phy (`wlan1`), tri-band 2.4/5/6 GHz (Wi-Fi 6E). Its valid interface combination is
`total ≤ 2, #channels ≤ 2` over `{managed, AP, P2P}`, and **monitor is not concurrent with
managed**. So the Wi-Fi side does one role at a time.

- **Concurrent today, AC1200 alone:** `wlan1` survey + `hci1` BLE + `wlan0` uplink — three roles,
  three radios. The core wardrive loop works with no extra hardware.
- **Handshake capture needs a second Wi-Fi adapter.** The game runs a monitor-mode capture on
  `wlan2` *while* `wlan1` keeps surveying — two simultaneous Wi-Fi roles one radio cannot do. The
  AWUS036ACM (MT7612U) is **not plugged in** (`wlan2` absent, 2026-10-06). Without it: run
  survey+BLE and skip in-game handshake capture, or stop survey and capture on `wlan1` by hand
  (see [`aircrack-ng.md`](aircrack-ng.md) / [`../docs/runbooks/wifi-wpa2-handshake-audit.md`](../docs/runbooks/wifi-wpa2-handshake-audit.md)).

## SDR / stability — ADS-B radar stays off

WatchDogsGo's ADS-B radar uses the RTL-SDR via `dump1090` (built from source to
`/usr/local/bin/dump1090` by `setup.sh`). On Fancy the SDR rail is deliberately **power-only with
`readsb` disabled** while the hang/drop + undervoltage question is open
([`../docs/logs/known-issues.md`](../docs/logs/known-issues.md); see also [`adsb-tar1090.md`](adsb-tar1090.md)
and [`sdr-stack.md`](sdr-stack.md)). **Do not enable the in-game ADS-B radar** until that is
closed — re-activating SDR RX under load is exactly the kind of draw that could trip it. `dump1090`
is installed but nothing starts it.

## LoRa — mutually exclusive with meshtasticd

The game's LoRa/MeshCore feature wants the SX1262 on SPI. `run.sh` **`pkill`s `meshtasticd` and
stops the service** at launch to take the radio ([`meshtastic.md`](meshtastic.md) owns it the rest
of the time). The two cannot hold the SX1262 at once. Leave LoRa out of WatchDogsGo unless you
intend to hand it the mesh radio for that session.

## Install (done 2026-10-06)

Cloned to `~/WatchDogsGo`; `bash setup.sh` completed with no errors.

```bash
git clone https://github.com/LOCOSP/WatchDogsGo.git ~/WatchDogsGo
cd ~/WatchDogsGo && bash setup.sh        # venv + apt build deps + pip + builds dump1090
```

`setup.sh` detects the ClockworkPi/RPi model and additionally: links apt `rpi-lgpio` + `python3-gi`
into the venv (LoRa GPIO, BlueZ pairing), builds FlightAware `dump1090` from source, confirms
`aiov2_ctl` (already present on this build — [`aiov2_ctl.md`](aiov2_ctl.md)), and creates
`loot/ maps/ firmware_cache/ secrets.conf`. `secrets.conf` holds API keys (wdgwars.pl / WiGLE) —
**keep it off-repo** (it's `chmod 600`, outside this repo tree).

### Verified on Fancy 2026-10-06

venv Python 3.13.5, all imports load — required (`pyxel 2.9.9`, `pyserial 3.5`, `Pillow 12.3.0`)
and optional (`scapy 2.8.0`, `bleak 3.0.2`, `netifaces 0.11.0`, `dbus-python 1.5.0`, `python3-gi`,
`LoRaRF 1.4.0`, `PyNaCl 1.6.2`, `cryptography 50.0.2`). `dump1090` built to `/usr/local/bin`. The
`python -m watchdogs` pre-flight dependency check is satisfied. **The game itself has not been
launched** — `run.sh` runs it as root and kills `meshtasticd`, so a launch is a deliberate act, not
part of install.

## Launch (bridge mode) — not yet applied

The bridge + supporting services are **not installed yet** (owner's call pending — they reconfigure
`wlan1`, which is the live Kismet survey adapter, [`kismet.md`](kismet.md)). The project's guide is
`~/WatchDogsGo/docs/uconsole-setup.md`; adapted to this build:

1. **Unmanage `wlan1` from NetworkManager** — already `unmanaged` on Fancy (verified 2026-10-06),
   so the project's step 2 is a no-op here. Keep it that way; `iw scan` and NM fight over a managed
   interface.
2. **BLE adapter pinning** (project step 1): on Fancy BT enumeration is already stable — `hci0`
   onboard UART, `hci1` AC1200 USB (verified, [`../hardware/specs/ac1200-mt7921.md`](../hardware/specs/ac1200-mt7921.md)).
   The bridge wants the *recon* controller; on Fancy that is **`hci1`**, not the `hci0` the generic
   guide assumes. Pass `--bt-iface hci1`. Fill BD addresses from `hciconfig` if you add udev rules —
   do not copy them from the upstream example.
3. **GPS PTY** (project step 5): `gpspipe -r | socat - PTY,link=/tmp/gps-pty,...`. gpsd already runs
   ([`gps.md`](gps.md)); only the socat PTY bridge is new.
4. **Bridge**, surveying on the AC1200, BLE on `hci1`, no `wlan2`:
   ```bash
   ~/WatchDogsGo/.venv/bin/python3 ~/WatchDogsGo/wdg_wifi_bridge.py \
       --iface wlan1 --bt-iface hci1 --no-monitor --loot-dir ~/WatchDogsGo/loot
   ```
   (Omit `--sniffer-iface wlan2` until the AWUS036ACM is fitted.)
5. **Run the game** against the bridge PTY:
   ```bash
   cd ~/WatchDogsGo && sudo ./run.sh /tmp/esp32-pty
   ```

> First launch builds a cluster index over all scanned networks; the project notes 142k+ records
> takes 2–3 min on a CM4. Fancy's Kismet loot is large, so expect a slow first load.
> *(Not yet timed on this build — verify.)*

## Handshake capture (authorized audit only)

The game can trigger WPA handshake capture via `hs_capture.py` on a monitor-mode `wlan2`. On this
build that is permitted **only** within the existing authorized-audit carve-out — own gear or a
written engagement, nothing else — exactly as scoped in [`aircrack-ng.md`](aircrack-ng.md) and
[`../docs/runbooks/wifi-wpa2-handshake-audit.md`](../docs/runbooks/wifi-wpa2-handshake-audit.md).
It also needs the AWUS036ACM fitted as `wlan2` (not present, 2026-10-06). It is **not** part of the
default survey loop; leave it disabled unless you are running a sanctioned audit. The RPG framing
does not change the posture in [`../knowledge/README.md`](../knowledge/README.md) — passive
observation only against anything you do not own or are not authorized to test.

## Upstream

Repo <https://github.com/LOCOSP/WatchDogsGo> · community portal `wdgwars.pl`. Pull updates with
`git -C ~/WatchDogsGo pull && bash ~/WatchDogsGo/setup.sh` (setup is idempotent — skips present
packages). Bridge compatibility notes live in the project's `docs/uconsole-setup.md`.
