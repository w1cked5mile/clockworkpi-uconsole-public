# Kismet — passive Wi-Fi survey

Upstream: https://www.kismetwireless.net/ · installed from Kismet's own apt repo (Debian's default
repos do not carry it). Installed and verified on this hardware 2026-09-21: `kismet-core` and the
full `kismet-capture-*` helper set, package version `2025-09-R1` (`Kismet 2025.09.0-b5d5a2d04`).

> Scope: **passive observation only** — no association, no deauth, no handshake capture. See the
> responsible-use section in [`../knowledge/README.md`](../knowledge/README.md) and the rationale
> in [`../knowledge/wardriving/configs/kismet-passive-survey.md`](../knowledge/wardriving/configs/kismet-passive-survey.md).
>
> **Wi-Fi only on this build.** Kismet's Bluetooth capture (`kismet_cap_linux_bluetooth`, the
> `linuxbluetooth` source) runs discovery, which scans actively and so transmits. Never add an
> `hci` source to the config, and never enable a Bluetooth adapter (`hci0`, or the AC1200's
> controller once fitted) in the web UI's Data Sources page — Kismet auto-detects each one and
> lists it there. Passive BLE observation is done with `hcitool`/`btmon` on the AC1200's
> controller instead: [`../knowledge/wardriving/learned/ble-passive-observation.md`](../knowledge/wardriving/learned/ble-passive-observation.md).

## Install

```bash
wget -O - https://www.kismetwireless.net/repos/kismet-release.gpg.key --quiet \
  | gpg --dearmor | sudo tee /usr/share/keyrings/kismet-archive-keyring.gpg >/dev/null
echo 'deb [signed-by=/usr/share/keyrings/kismet-archive-keyring.gpg] https://www.kismetwireless.net/repos/apt/release/trixie trixie main' \
  | sudo tee /etc/apt/sources.list.d/kismet.list
sudo apt update
sudo apt install -y kismet
```

During install, `kismet-capture-linux-bluetooth`'s postinst asks (via debconf/whiptail)
**"Should Kismet be installed with suid-root helpers?"** — answer yes (the default). This grants
`cap_net_admin`/`cap_net_raw` to the capture helpers instead of running Kismet itself as root. In a
non-interactive shell this prompt blocks forever waiting for input; preseed it first:

```bash
echo "kismet-common kismet-common/install-setuid boolean true" | sudo debconf-set-selections
sudo DEBIAN_FRONTEND=noninteractive apt install -y kismet
```

Add yourself to the `kismet` group so you can run `kismet` without `sudo` (log out/in, or use
`sg kismet -c '...'`, for the new group membership to take effect in an existing session):

```bash
sudo usermod -aG kismet "$USER"
```

## What it writes

| Path | Contents |
|---|---|
| `/usr/bin/kismet`, `/usr/bin/kismet_cap_*` | server binary + per-source capture helpers |
| `/etc/kismet/*.conf` | shipped defaults (`kismet.conf`, `kismet_80211.conf`, etc.) — do not edit |
| `/etc/kismet/kismet_site.conf` | **site overrides go here** — read last, survives package upgrades |
| `/lib/systemd/system/kismet.service` | runs as `root`; not enabled by default (confirmed 2026-09-21) |
| `~/.kismet/` | per-user runtime state: server UUID, device tracker cache, web UI session/auth |

`kismet_cap_linux_wifi` and `kismet_cap_linux_bluetooth` carry `cap_net_admin,cap_net_raw=eip`
(confirmed via `getcap`) — this is what lets a `kismet`-group member capture without full root.

## Applying the staged config

```bash
sudo cp ../configs/kismet/kismet_site.conf /etc/kismet/kismet_site.conf
```

Config notes and interface-selection rationale live in
[`../configs/kismet/`](../configs/kismet/) and
[`../knowledge/wardriving/configs/kismet-passive-survey.md`](../knowledge/wardriving/configs/kismet-passive-survey.md).
`log_prefix` in the staged config points at `/home/user/kismet-logs` — create it if it
doesn't exist (`mkdir -p ~/kismet-logs`); Kismet does not create its log directory itself.

The staged config overrides three shipped defaults on purpose (the first two confirmed in
`/etc/kismet/*.conf` on 2026-09-25):

| Setting | Shipped | Staged | Why |
|---|---|---|---|
| `kis_log_data_packets` | `true` (`kismet_logging.conf`) | **`false`** | data frames can carry unencrypted payloads, which are not readily accessible broadcasts (*Joffe v. Google*, 9th Cir. 2013) |
| `dot11_keep_eapol` | `true` (`kismet_80211.conf`) | **`false`** | EAPOL frames are handshakes; handshake capture is out of scope |
| `httpd_bind_address` | all addresses (`0.0.0.0`) | **`127.0.0.1`** | `tailscale serve` holds `:2501` on the tailnet address, so the wildcard bind fails with `Address already in use` and Kismet exits (2026-09-25); loopback doesn't clash, `tailscale serve` proxies `http://localhost:2501`, and the UI is off the LAN |

`kis_log_packets` stays `true` so beacons and probes are kept for later analysis. **Verified
2026-09-25** (first LAB-15 run): the 1,400-packet log held 651 management and 749 control frames,
**0 data frames and 0 EAPOL frames**, with `kis_log_data_packets=false` and
`dot11_keep_eapol=false` ([finding](../knowledge/wardriving/findings/2026-09-25-wifi-survey.md)).
`sqlite3` is installed on Fancy (2026-09-25) for reading the log's tables.

## Running it (from the webdash, or by hand)

Since 2026-10-01 the webdash Wi-Fi view has a **Start/Stop Kismet** button — the documented way to
run it on Fancy. It starts Kismet as a **user** systemd service
([`../webdash/host-helpers/kismet-user.service`](../webdash/host-helpers/kismet-user.service)), not
the root `kismet.service`: the capture helpers' file capabilities and `kismet`-group membership mean
Kismet needs a clean user exec, not root. The button posts to the webdash, which goes through the
`aiov2-bridge` to `systemctl --user start|stop kismet.service`; the rationale and the one-time host
setup (install the unit, `loginctl enable-linger wicked5mile`, add `XDG_RUNTIME_DIR` to the bridge
unit) are in [`../docs/reference/webdash-architecture.md`](../docs/reference/webdash-architecture.md)'s
"Kismet start/stop" section. No `sudo`.

By hand (equivalent, e.g. from a terminal): `systemctl --user start kismet` / `... stop kismet`, or
a one-off foreground run `kismet --no-ncurses-wrapper` (`wicked5mile` is already in the `kismet`
group, so no `sg` wrapper is needed). The root `kismet.service` stays disabled; see the crash-loop
entry in [`../docs/logs/known-issues.md`](../docs/logs/known-issues.md).

**After changing the Kismet login, restart the webdash.** The webdash's Kismet panel reads the
login from `~/.kismet/kismet_httpd.conf`, bind-mounted read-only into the container as a single
file. In-place password edits are picked up automatically, but **recreating** the file (e.g.
Kismet's "set up login" flow, which rewrites it with a new inode) leaves the container reading the
old credentials — the panel shows Kismet as *locked* until the container is restarted and the mount
re-resolves:

```bash
docker restart uconsole-webdash
```

(This is the single-file-bind-mount inode pin; the alternative — mounting the whole `~/.kismet`
directory — was declined to keep the container's view minimal. 2026-10-01.)

## Capture source on this build (verify before trusting — hardware changes)

**Radio roles** (owner decision, 2026-09-25):

| Radio | Role |
|---|---|
| Onboard combo chip: `wlan0` (`brcmfmac`) and `hci0` (UART) | Fancy's own use only — its network link and its paired Bluetooth devices. Never used for recon. |
| AC1200 on the USB rail: `wlan1` (`mt7921u`) and its own Bluetooth controller `hci1` (Bus: USB) — **verified 2026-09-30** | All recon — Kismet's Wi-Fi source and passive BLE observation |
| ~~RT5370 USB dongle~~ (was `wlan1`, 2.4 GHz, no Bluetooth) | Interim stand-in **until the AC1200 arrived**; **removed 2026-09-30** (no longer in `lsusb`). `wlan1` is now the AC1200. |

The AC1200 (HackerGadgets #12253; MediaTek **MT7921AUN**) **arrived and was installed on 2026-09-30**
and is verified on Fancy — see [`../hardware/specs/ac1200-mt7921.md`](../hardware/specs/ac1200-mt7921.md)
and [`../TODO.md`](../TODO.md). It sits on the AIO V2's internal USB-C port, which the USB rail powers
(GPIO23, `aiov2_ctl USB on`). On-device checks (2026-09-30): `lsusb` → `0e8d:7961`, driver `mt7921u`;
`iw dev` → `wlan1`, MAC `aa:bb:cc:dd:ee:32`; monitor mode present (incl. active monitor) across
2.4 / 5 / 6 GHz; Bluetooth on `hci1` (`Bus: USB`). The interim **Ralink RT5370** (`rt2800usb`,
`148f:5370`) that previously held `wlan1` has been removed. The onboard CM4 Wi-Fi (`brcmfmac`,
`wlan0`) still does **not** offer monitor mode — its `Supported interface modes` list has no
`monitor` entry (re-confirmed 2026-09-30). `configs/kismet/kismet_site.conf` binds `source=wlan1`,
which is now the AC1200; its `name=` label was corrected from `rt5370` to `mt7921`. Re-run `iw dev`
after any replug — the MT7921's `phyN` index renumbers across re-enumeration, though `wlan1` has been
stable.

```bash
iw dev                                           # list interfaces + driver-assigned names
iw list | grep -B3 -A15 'Supported interface modes'   # confirm which phy offers monitor mode
lsusb                                            # identify a USB adapter by vendor:product ID
```

**NetworkManager stays off the survey adapter.** The onboard radio (`wlan0`, `brcmfmac`) is for
Fancy's network link only; survey work uses the AC1200 on the USB rail (`wlan1`, `mt7921u`; the
RT5370 was the interim stand-in before it arrived). A Wi-Fi interface NetworkManager manages gets scanned actively — it
sends probe requests — and can join a saved network: on 2026-09-25 the plugged-in RT5370 had been
joined to the home network through an auto-created "EvilLair 1" profile, giving Fancy two default
routes. [`../configs/networkmanager/wifi-onboard-only.conf`](../configs/networkmanager/wifi-onboard-only.conf)
leaves every Wi-Fi driver except `brcmfmac` unmanaged. It must sort after `wgpia.conf` in
`conf.d/`, because that file sets the same key with `=` and NetworkManager reads the directory in
name order. Deployed 2026-09-25:

```bash
sudo cp ~/clockworkpi-uconsole/configs/networkmanager/wifi-onboard-only.conf /etc/NetworkManager/conf.d/
sudo nmcli general reload
NetworkManager --print-config | grep -A1 '^\[keyfile\]'   # ...wgpia*,type:wifi,except:driver:brcmfmac
nmcli -t dev | grep wlan      # wlan0:wifi:connected:...  wlan1:wifi:unmanaged:
```

A second NetworkManager drop-in,
[`../configs/networkmanager/wifi-powersave-off.conf`](../configs/networkmanager/wifi-powersave-off.conf)
(`[connection] wifi.powersave = 2`, deployed 2026-09-30), disables Wi-Fi power save on the managed
`wlan0` — a weak 2.4 GHz link to the AP was turning into 20–30% packet loss until it was turned off.
It is a connectivity mitigation, not a survey setting; details and the root-cause follow-ups are in
[`../docs/logs/known-issues.md`](../docs/logs/known-issues.md).

*Unverified on this build* — not yet re-run with the AC1200 in. `wlan0` stays managed: it is Fancy's
own network link and probes routinely, like any laptop; it is never the survey adapter. The AC1200's
driver is `mt7921u`, so the `except:driver:brcmfmac` rule already leaves `wlan1` unmanaged; confirm
with `nmcli -t dev | grep wlan1` (expect `wlan1:wifi:unmanaged:`).

## Running

```bash
sg kismet -c 'kismet --no-ncurses-wrapper'   # foreground, as a kismet-group member (no sudo)
# or, once logged out/in after usermod:
kismet --no-ncurses-wrapper
```

Use the foreground run, not `systemctl start kismet`. The service crash-looped until 2026-09-25;
the likely cause (the web UI's `:2501` bind clashing with `tailscale serve`) is fixed by
`httpd_bind_address=127.0.0.1`, but a service start has not been re-tested
([`../docs/logs/known-issues.md`](../docs/logs/known-issues.md)), so the foreground run is still
the documented path. If the service was started, stop it with `sudo systemctl stop kismet`.

Web UI: http://localhost:2501/ on Fancy (loopback only; the tailnet reaches it through
`tailscale serve`) — first run prompts to set an admin username/password before most features are
usable.

**Monitor interface.** Kismet does not rename the adapter: it creates a separate monitor VIF,
`wlan1mon`, alongside `wlan1`, which stays in managed mode. On 2026-09-25 it **left `wlan1mon` up
after a clean Ctrl-C exit** (still present 55 s later). Remove it after every run:

```bash
iw dev                       # wlan1mon listed, type monitor?
sudo iw dev wlan1mon del     # wlan1 (managed) is unaffected
```

Unplugging and replugging the adapter also clears it. (The 2026-09-21 note below read this as a
rename and a restore; the 2026-09-25 run showed both interfaces present during capture.)

## Verified 2026-09-21 (no GPS — gpsd not yet running, see `gps.md`)

- Group-based capture (`sg kismet`, no `sudo`) started the `wlan1` source successfully.
- Monitor interface `wlan1mon` came up, channel-hopped, logged 802.11 APs/devices to
  `~/kismet-logs/*.kismet` (kismetdb format).
- GPS connection to `gpsd:localhost:2947` failed **non-fatally** (`Connection refused` —
  gpsd is installed but `inactive`/`disabled`, matches [`../TODO.md`](../TODO.md)); Kismet kept
  running without a position source.
- `iw dev` showed plain `wlan1` after the `timeout`-bounded run. This did not hold on
  2026-09-25, when `wlan1mon` stayed after a clean exit — see Running.
- The test capture (real neighboring SSIDs/MACs) was deleted immediately after — do not commit
  `.kismet`/`.kismetdb` files, now blocked by [`../.gitignore`](../.gitignore).

## Verified 2026-09-25 (first LAB-15 run, RT5370, no GPS fix)

- 10-minute foreground survey on 2.4 GHz; monitor mode held throughout. Counts only in the
  [finding](../knowledge/wardriving/findings/2026-09-25-wifi-survey.md): 4 APs, 23 clients,
  4 bridged.
- `wlan1` stayed managed alongside `wlan1mon`; webdash counted one monitor interface.
- The device-type query in LAB-15 returns sqlite3 list rows like `IEEE802.11|Wi-Fi AP|4`.
- Packet log: management and control frames only — no data, no EAPOL (see above).

Not yet verified: a root `systemctl start kismet` after the bind fix. (GPS-tagged capture, WiGLE
CSV export and the AC1200 were verified 2026-10-04 — see WiGLE export below.)

## WiGLE export (verified 2026-10-04)

The staged config sets `log_types=kismet,wiglecsv`, so every run also writes
`~/kismet-logs/uconsole-<timestamp>.wiglecsv` (`WigleWifi-1.4` format), ready for wigle.net.
First run: 90 s, AC1200 on `wlan1`, gpsd 3D fix → 215 `WIFI` rows, all with coordinates.

Before a drive:

```bash
aiov2_ctl USB on                                   # AC1200 → wlan1 (USB rail boots off)
aiov2_ctl GPS on                                   # already on at boot on this build
gpspipe -w -n 6 | grep -o '"mode":[0-9]' | tail -1 # expect "mode":3 (or 2)
systemctl --user start kismet                      # or the webdash Start Kismet button
```

Kismet writes a row only once it has a fix; a no-fix run leaves a header-only file.

Upload by hand at https://wigle.net/uploads, or with the API name/token from the WiGLE account
page (keep them out of the repo — e.g. in `~/.config/wigle/env`, mode 600):

```bash
curl -u "$WIGLE_API_NAME:$WIGLE_API_TOKEN" -F file=@<file>.wiglecsv \
  https://api.wigle.net/api/v2/file/upload
```

The file holds precise coordinates and MACs, including the home network. Uploading publishes them;
trim rows near home first if that matters. Never commit `.wiglecsv` files.

### Automatic upload (installed 2026-10-04)

[`../webdash/host-helpers/wigle-upload.py`](../webdash/host-helpers/wigle-upload.py), run hourly by
the user timer `wigle-upload.timer`, uploads each finished `.wiglecsv` once. It skips the file
Kismet is still writing and any file touched in the last 10 min. Before sending, it drops every row
within `WIGLE_HOME_RADIUS_M` (default 500 m) of home and every row without a fix. It keeps a record
of what it sent in `~/.local/state/wigle-upload/state.json`. **Fails closed:** with no home position
set, it uploads nothing.

One-time setup. The credentials and home position live only in `~/.config/wigle/env` (mode 600,
directory 700). They never go in the repo:

```bash
# 1. At home, with a GPS fix — stores home in ~/.config/wigle/env
~/clockworkpi-uconsole/webdash/host-helpers/wigle-upload.py --set-home-from-gps
# 2. Add the API name and token from wigle.net -> Account -> API Token
nano ~/.config/wigle/env          # WIGLE_API_NAME=AID...   WIGLE_API_TOKEN=...
# 3. Check what would go up
~/clockworkpi-uconsole/webdash/host-helpers/wigle-upload.py --dry-run
```

Timer install, verify and rollback are in the header of
[`../webdash/host-helpers/wigle-upload.service`](../webdash/host-helpers/wigle-upload.service).
Run log: `journalctl --user -u wigle-upload -n 20`.

Home is set to the town-centre of the owner's home town with an **8 km radius** (owner gave the
home as a town, not an address), so every row anywhere in or around the town is held back, home
or not. Survey there is never uploaded; narrow the radius in the env file to change that.

Verified 2026-10-04: refuses with no home set; the home filter dropped synthetic rows at 0.5 km and
7 km, kept one at 26 km, and dropped a no-fix row; **first real upload** of the drive capture
(229 rows, 0 dropped — taken far from home) accepted as WiGLE transaction `20261004-01348`; a second
run sent nothing. The transaction id is read by searching the response for `transid`/`transId`
(the first upload's response shape wasn't recorded, so the id was filled in from
`/api/v2/file/transactions`).

## Manual interface check (tool not installed / debugging)

```bash
iw dev                          # interfaces + phy mapping
iw <phy> info | grep -A10 'Supported interface modes'   # monitor mode support per radio
rfkill list                     # confirm nothing is soft/hard blocked
```
