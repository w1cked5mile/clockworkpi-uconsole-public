# systemd — services, states and restart loops

Every radio on Fancy is fronted by a service: gpsd, meshtasticd, readsb, Kismet, and webdash's
aiov2 bridge. systemd starts and watches them. Written 2026-09-24 (gap P1). Reference: the
`systemd.unit(5)`, `systemctl(1)` and `journalctl(1)` man pages.

## Units, enabled and active

A **unit** is a file describing something systemd manages; a `.service` unit describes a
program. Two independent questions apply to each:

| Question | Command | Answers |
|---|---|---|
| Will it start at boot? | `systemctl is-enabled readsb` | `enabled`, `disabled`, `masked` |
| Is it running now? | `systemctl is-active readsb` | `active`, `inactive`, `activating`, `failed` |

`systemctl start` changes only the second; `systemctl enable` only the first (`enable --now`
does both). **Masked** means linked to `/dev/null` so nothing can start it, even by hand.

## Reading `systemctl status`

```bash
systemctl status readsb
```

The `Active:` line is the one that matters. With the SDR rail off it reads something like
`activating (auto-restart) (Result: exit-code)`: readsb started, found no SDR, exited, and
systemd is waiting to try again.

## Restart loops

A unit with `Restart=` in it is restarted when it exits. If the cause doesn't go away, it fails
again, and `NRestarts` climbs:

```bash
systemctl show readsb -p ActiveState,SubState,NRestarts
```

| ActiveState / SubState | Meaning | On Fancy |
|---|---|---|
| `active` / `running` | running normally | readsb with the SDR rail on |
| `activating` / `auto-restart` | crashed; waiting to retry — a **crash loop** | readsb with the SDR rail off: **normal here** |
| `inactive` / `dead` | stopped, not trying | Kismet, normally (started by hand when needed) |
| `failed` | gave up — too many restarts too quickly | Kismet, if `systemctl start kismet` hits the known issue |

webdash reads these same fields, which is how the SDR station tells "stopped" from
"crash-looping".

## The journal

Services log to the systemd journal:

```bash
journalctl -u readsb -b -n 30        # this boot, last 30 lines
journalctl -u meshtasticd | grep "Set radio"
journalctl -u gpsd -f                # follow live; Ctrl-C to stop
```

`-b` limits to the current boot, `-n` to the last N lines, `-f` follows. With readsb
crash-looping, the reason is in the journal: `rtlsdr: no supported devices found`.

## User units

Some units run as the logged-in user rather than root — the first-packet alert
([`../../../configs/meshtastic/first-packet-alert.service`](../../../configs/meshtastic/first-packet-alert.service))
and learn-sync. They take `--user` and need no sudo:

```bash
systemctl --user status learn-sync.timer
journalctl --user -u learn-sync -n 20
```
