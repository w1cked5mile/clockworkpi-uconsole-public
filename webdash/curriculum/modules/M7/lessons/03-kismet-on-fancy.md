---
id: M7.kismet
title: Kismet on Fancy
est_minutes: 20
glossary: [monitor-mode, channel-hopping, crash-loop]
---

**Kismet** listens on a monitor-mode adapter, hops across channels, and keeps a table of every
network and device it hears. It puts the adapter into monitor mode itself by adding a second
interface on the same radio, `wlan1mon`, in monitor mode; `wlan1` stays in managed mode beside it.
On Fancy, Kismet leaves `wlan1mon` behind when it exits (seen 2026-09-25), so you remove it
yourself.

Fancy's site config points Kismet at `wlan1`, which is now the AC1200 (MediaTek MT7921AUN,
`mt7921u`); the RT5370 that previously stood in has been removed.

One more thing keeps the adapter quiet. NetworkManager, which runs Fancy's own Wi-Fi, scans
actively on any Wi-Fi interface it manages — before Kismet takes the adapter and after Kismet
hands it back. A small config file tells it to leave the survey adapter (`wlan1`) alone; LAB-15
installs it and checks that `nmcli` reports `wlan1` as `unmanaged`.

## Running it in the foreground

Kismet's systemd service crash-looped until 2026-09-25 — its web server couldn't bind port 2501
while `tailscale serve` held it. The site config now binds the web UI to loopback, which very
likely fixes it, but a service start hasn't been re-tested, so the foreground run is still what
the lab uses. Stop the service and run Kismet in a terminal, as a member of the `kismet` group
(no `sudo`):

```bash
sudo systemctl stop kismet
sg kismet -c 'kismet --no-ncurses-wrapper'
```

Ctrl-C in that terminal stops it cleanly and finishes the log. Even after a clean stop,
`wlan1mon` stays up (on 2026-09-25 it was still there 55 s later), so delete it:

```bash
sudo iw dev wlan1mon del
iw dev | grep -c 'type monitor'   # expect 0
```

Cycling the AC1200's USB rail (`aiov2_ctl USB off` then `on`) does the same: the driver re-binds and
`wlan1` comes back in managed mode, with no monitor interface.

## Where the logs go

Kismet writes one `uconsole-*.kismet` file per run to `~/kismet-logs/` — outside the repo, and
never committed. It is an SQLite database holding every address heard and, with a GPS fix, where
it was heard, so it is deleted once the finding is written. Fancy's site config turns
**data-frame logging off** (`kis_log_data_packets=false`): Kismet's packaged default would store
the frames that carry people's traffic, and those are exactly what Joffe v. Google says is not
"readily accessible". Management frames — beacons and probes — are still logged. The first survey
on Fancy (2026-09-25) proved it: 1,400 packets, 651 management and 749 control, no data frames and
no EAPOL (handshake) frames.

## What webdash shows

The Wi-Fi station reads Kismet's API on port 2501. Right now Kismet is **{live:kismet.state}**.

| State | Means |
|---|---|
| `stopped` | Kismet isn't running. The normal resting state |
| `locked` | Kismet is running, but webdash has no API token, so it can't read the device count. Normal here |
| `running` | Running and readable; the device count ({live:kismet.devices}) is filled in |

`locked` is not a fault — the lab accepts it.

> **Open Kismet's web UI at `http://localhost:2501` on Fancy itself.** `tailscale serve` also
> exposes port 2501 to the tailnet, and that path skips webdash's login entirely. The first run
> asks you to set a Kismet admin login; keep it out of the repo.

> **Don't enable any Bluetooth adapter in Kismet's Data Sources list** — the onboard `hci0` now,
> the AC1200's controller later. Kismet detects each one and offers it; its Bluetooth source
> scans actively, which transmits. Bluetooth is observed passively in lessons 5 and 6, on the
> AC1200's controller and without Kismet.

## Reading the counts afterwards

After Kismet stops, count devices by type straight from the log — counts only, no addresses:

```bash
sudo apt install sqlite3      # installed on Fancy since 2026-09-25
sqlite3 "$(ls -t ~/kismet-logs/uconsole-*.kismet | head -1)" \
  'SELECT phyname, type, COUNT(*) FROM devices GROUP BY phyname, type;'
```

Each row is `phy|type|count`, for example `IEEE802.11|Wi-Fi AP|4` (verified on Fancy
2026-09-25).
