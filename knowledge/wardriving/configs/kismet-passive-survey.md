# Kismet configuration for passive survey

Applied file: [`../../../configs/kismet/kismet_site.conf`](../../../configs/kismet/kismet_site.conf).
This file records the reasoning and the operational checks around it.

## Why `kismet_site.conf`

Kismet reads it last, and package upgrades do not overwrite it. Everything site-specific belongs
here rather than in the shipped defaults.

## Choices and rationale

| Setting | Value | Why |
|---|---|---|
| `source` | Monitor-capable adapter, 5 hops/sec | Onboard CM4 Wi-Fi (`brcmfmac`) has no monitor mode; 5/sec is a balanced default. The adapter is the **AC1200** (MT7921AUN, `wlan1`, `mt7921u`) — arrived 2026-09-30, monitor mode verified on 2.4/5/6 GHz; the RT5370 that previously stood in has been removed. See [`../../../software/kismet.md`](../../../software/kismet.md) |
| `gps` | `gpsd:host=localhost,port=2947` | Position tags every observation; gpsd shares the receiver with other tools |
| `log_types` | `kismet` | One self-contained log; convert later if needed |
| `log_prefix` | outside the repo | Logs hold MACs and precise coordinates — they must not land in git |
| `dot11_fingerprint_devices` | false | Reduces stored device detail; passive survey does not need it |
| `kis_log_data_packets` | false | Overrides the shipped `true`. Data frames can carry unencrypted payloads, which courts have held are not "readily accessible" (*Joffe v. Google*, 729 F.3d 1262, 9th Cir. 2013) |
| `kis_log_packets` | true | With data frames off, keeps the management frames (beacons, probes) for later analysis. Verified 2026-09-25: a 1,400-packet log held 651 management and 749 control frames, 0 data, 0 EAPOL ([finding](../findings/2026-09-25-wifi-survey.md)) |
| `dot11_keep_eapol` | false | Overrides the shipped `true`; EAPOL frames are handshakes. None reached the 2026-09-25 log |
| `httpd_bind_address` | `127.0.0.1` | `tailscale serve` holds `:2501` on the tailnet address, so Kismet's default wildcard bind failed (`Address already in use`) and it exited at startup (2026-09-25). Loopback doesn't clash, `tailscale serve` proxies `http://localhost:2501`, and the web UI is no longer on the LAN. Very likely also the cause of the service's crash loop (service start not yet re-tested — [`known-issues.md`](../../../docs/logs/known-issues.md)) |
| Bluetooth source | none | Kismet's Bluetooth capture scans actively. Never add an `hci` source or enable `hci0` in the UI — see [`../learned/ble-passive-observation.md`](../learned/ble-passive-observation.md) |

## Pre-session checks

```bash
iw dev                                     # confirm the interface name matches the config
iw phy | grep -A3 'Supported interface modes'   # monitor supported
systemctl status gpsd && cgps -s           # a real 3D fix before starting
df -h ~                                    # log space
```

## Running

```bash
sg kismet -c 'kismet --no-ncurses-wrapper'   # web UI on http://localhost:2501; no sudo needed
                                              # once you're in the kismet group (usermod, re-login)
```

Kismet puts the adapter into monitor mode itself; do not pre-configure it. It does this by
creating a separate monitor interface, `wlan1mon`, alongside `wlan1` (which stays managed), and on
2026-09-25 it **left `wlan1mon` up after a clean exit** (still present 55 s later). Remove it
after every run with `sudo iw dev wlan1mon del`, or unplug and replug the adapter.

## Verifying the capture is useful

- [ ] GPS shows a fix inside Kismet, not just in `cgps`
- [ ] Networks appear on multiple channels (hopping is working)
- [ ] Log file is growing

## Post-session handling

- [ ] Move logs off the device to storage you control
- [ ] Summarize in a finding: counts, channels, general area, equipment — **not** device lists
- [ ] Confirm no `.kismet` file, GPS track, or coordinate-bearing export was staged for commit

## Out of scope

No `--deauth`, no handshake capture, no association with networks you do not own, no cracking.
Kismet can be configured for behavior beyond passive observation; this build's configuration
deliberately is not.
