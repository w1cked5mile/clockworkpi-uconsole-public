# webdash — operator dashboard architecture & build plan

A single-container, read-only-for-v1 web dashboard unifying the status of this build's software
stack (`aiov2_ctl`, Kismet, gpsd, meshtasticd, tar1090/readsb, system vitals) behind one
authenticated page. Modeled on the proven pattern from a sibling build,
[`w1cked5mile/CyberDeck`](https://github.com/w1cked5mile/CyberDeck)'s `webdash` (Pi 5, FastAPI +
Docker, TOTP-gated) — **not a port**. That deck owns hardware directly (raw serial to a Meshtastic
node, esptool flashing five ESP32 boards, SSH to two roving Pi Zeros) because none of its
peripherals run their own daemon. This build is the opposite: `aiov2_ctl`, Kismet, gpsd,
meshtasticd, and tar1090 already run as independent services with their own state — the dashboard's
job is to **aggregate and proxy** them, not own them. That's a materially smaller, lower-privilege
container.

## Why this fits (headroom, checked 2026-09-21)

| Resource | Available | Notes |
|---|---|---|
| CPU | 4-core CM4, load average 0.4 | Idle; a FastAPI/Uvicorn process is single-digit % |
| RAM | 7.6 GiB total, 6.6 GiB available | `python:3.12-slim` + deps is tens of MB resident |
| Disk | 29 GB microSD, 16 GB free (44% used) | The constraint. `python:3.12-slim` + this app's deps ≈ 300–400 MB image — budget it, don't let it grow unbounded (see [Image budget](#image-budget)) |

**Update 2026-09-23:** the NVMe board (#11953) arrived and root now runs from NVMe (WD PC SN730,
`/dev/nvme0n1p2`, 234 GB, ~208 GB free). The microSD was removed. Disk is no longer the binding
constraint; the table above records the 2026-09-21 microSD state.

## Non-goals for v1

- ~~No control actions that touch hardware state~~ — **superseded 2026-09-21**: `aiov2_ctl` rail
  control (on/off for GPS/LORA/SDR/USB) shipped once the read path (this doc's original v1) was
  proven working. See [Rail control](#rail-control) below. Reboot and flashing remain out of
  scope — nothing on this build is analogous to CyberDeck's CYD fleet.
- **No MQTT bridge, no Prometheus/telegraf sidecar** — this build has no fleet to aggregate across;
  add only if a real need shows up.
- **No feature-parity chase with CyberDeck** — no CYD flashing, no Pwnagotchi/Porky, no five-node
  device matrix. Different hardware, different job.

## What maps to what

| CyberDeck component | uConsole equivalent | Access pattern |
|---|---|---|
| `collectors.py` device matrix (5 owned devices) | one collector per **service**, not per device | HTTP/TCP to each service's own port over `network_mode: host` — no device ownership |
| `MeshClient` owning `/dev/ttyACM0` directly | `meshtastic` Python lib, `TCPInterface(hostname="127.0.0.1")` against meshtasticd's own port `4403` | meshtasticd already owns the SX1262; the container never touches `/dev/serial0` |
| Winglet/gpsd proxy (external device) | gpsd is local (`127.0.0.1:2947`) | same gpsd JSON protocol, no proxying needed |
| esptool flashing over `/dev/ttyUSB*` | *(not applicable — no CYD-equivalent boards)* | n/a |
| `power_guard.py` (UPS-aware shutdown) | *(not applicable — no UPS on this build yet)* | n/a |
| Auth (PBKDF2 password + TOTP + signed session cookie) | same pattern, reimplemented (not copied — different repo, different secrets) | secret store outside the repo, outside git: `~/.config/uconsole-webdash/` |
| `--network=host` + `/dev` bind-mount for hot-plug serial | `--network=host` only; the one exception below | — |

**The one exception:** `aiov2_ctl` is a CLI tool, not a daemon with its own API. The collector
shells out to it. This needs the host binary bind-mounted read-only into the container
(`/usr/local/bin/aiov2_ctl:/usr/local/bin/aiov2_ctl:ro` plus its `/usr/local/share/aiov2_ctl`
assets — see [`../../software/aiov2_ctl.md`](../../software/aiov2_ctl.md) for what the installer
wrote). `aiov2_ctl --status` already runs as a non-root user on the host with no special
capabilities (checked 2026-09-21 — it reads cached rail state and sysfs power-supply paths, not a
raw GPIO device), so no extra `--device`/`cap-add` grants are expected. Verify this holds once
containerized rather than assuming it — if `--status` fails inside the container, the fallback is
running `aiov2_ctl` as a tiny host-side systemd-managed helper the container polls over localhost,
same shape as gpsd/meshtasticd.

## Collectors (v1)

| Collector | Source | What it reads | Failure mode if the service is down |
|---|---|---|---|
| `system.py` | `psutil`, `/sys/class/thermal` (bind-mounted read-only), `/hostfs` (host `/` bind-mounted read-only for real disk usage) | CPU%, mem, disk, temp, uptime, load | n/a — always available |
| `aiov2.py` | HTTP GET to the host-side `aiov2-bridge` (`127.0.0.1:8765`) — see [Resolved](#resolved-during-the-build-2026-09-21) | Rail on/off (GPS/LORA/SDR/USB), PMIC voltage | Reports `unavailable`, does not crash the API |
| `kismet.py` | Kismet REST, `http://127.0.0.1:2501/system/status.json` | Whether Kismet is running, source active/inactive, device count | Kismet is off by default on this build — must report `stopped`, not error |
| `gps.py` | gpsd JSON protocol, `127.0.0.1:2947` (same approach as manual `gpspipe` checks in [`../logs/build-log.md`](../logs/build-log.md)'s 2026-09-21 entry) | Fix mode, satellite count, lat/lon (see [Privacy](#privacy)) | `gpsd` inactive → reports `stopped` |
| `mesh.py` | `meshtastic` Python lib, `TCPInterface(hostname="127.0.0.1")` (default port `4403`) | Node info, channel list, last-seen mesh nodes; text message buffer and send (see [Mesh text messaging](#mesh-text-messaging)) | meshtasticd down → reports `unreachable`, short connect timeout |
| `adsb.py` | HTTP GET `http://127.0.0.1/tar1090/data/aircraft.json` | Aircraft count, receiver uptime | `readsb` crash-loops when the SDR rail is off (confirmed 2026-09-21, `journalctl -u readsb`: `FATAL: rtlsdr: no supported devices found`) — **this is a normal, expected state on this build**, not a bug; the collector must report `receiver offline` cleanly, not surface the crash-loop as an error |
| `net.py` (added 2026-09-25) | `/sys/class/net/*/type` — the host's, since the container uses `network_mode: host` | `monitor_ifaces` (count of ARPHRD 803 interfaces); `wlan0`/`wlan1` `present` and `mode` (`managed`/`monitor`/`other`/null). Never reads `address` — no MACs. Kismet's `wlan1mon` is a separate vif next to `wlan1` (2026-09-25) and counts toward `monitor_ifaces`; it stands in for wlan1 only if `wlan1` is absent | Reads sysfs, no service to be down; any failure reports `state: error` with null values |

Every collector gets a short timeout (≤2 s) and a `try`/`except` that turns any failure into a
structured "unavailable" status — mirrors CyberDeck's own stated design rule ("a dead peer can't
stall the API response") and matters more here, since several of these services are *deliberately*
off most of the time (Kismet, on-demand; SDR rail, off by default per
[`../../software/aiov2_ctl.md`](../../software/aiov2_ctl.md)).

## Rail control

Added 2026-09-21, past v1's original read-only scope (see [Non-goals](#non-goals-for-v1)). The
`aiov2-bridge` host service (already needed for `aiov2.py`'s reads) gained `POST /rail`
(`{"feature": "GPS"|"LORA"|"SDR"|"USB", "state": "on"|"off"}`), which shells out to
`aiov2_ctl <FEATURE> <on|off>` — the exact command a person would type by hand
([`../../software/aiov2_ctl.md`](../../software/aiov2_ctl.md)). `POST /api/aiov2/rail` on the app
side validates the request (`Literal` types — FastAPI rejects anything else with `422` before it
ever reaches the bridge) and forwards it. This was the only write path in the app until mesh text
messaging (next section) added a second one, and Kismet start/stop (below) a third. Every other
route is read-only.

## Kismet start/stop

Added 2026-10-01. The Wi-Fi view has a Start/Stop button → `POST /api/kismet/control`
(`{"action": "start"|"stop"}`, `Literal`-validated) → the bridge's `POST /kismet`, which runs
`systemctl --user start|stop kismet.service`. That user unit is
[`kismet-user.service`](../../webdash/host-helpers/kismet-user.service), **not** the packaged root
`kismet.service`. The reasons are specific to how Kismet gains its privileges on this build:
`kismet_cap_linux_wifi` carries file capabilities (`cap_net_admin,cap_net_raw=eip`) and
`wicked5mile` is in the `kismet` group, so Kismet needs no root — only a *clean* exec. Launched
under the user manager it keeps those caps and can write `~/kismet-logs`; spawned as a child of the
hardened `aiov2-bridge` unit (`NoNewPrivileges=true`, `ProtectHome=read-only`) it would get
neither, and the root `kismet.service` crash-loops (see
[`../logs/known-issues.md`](../logs/known-issues.md)). The bridge reaches the user manager via
`XDG_RUNTIME_DIR=/run/user/1000` (set in its unit); `loginctl enable-linger wicked5mile` keeps that
manager running headless. No `sudo`, and the bridge's own sandbox is unchanged. Kismet is
passive/receive-only, within the repo's [legal posture](../../knowledge/README.md). The button's
label tracks the `kismet.py` collector's live state (`running`/`locked` → "Stop", `stopped` →
"Start"), not systemd — the REST API is the honest signal for "is it actually up."

Access control for it is the same session gate as everything else, not a separate permission
tier. That's a deliberate simplification for a single-operator device: whoever can see the
dashboard can already see live GPS position and RF-survey state, which is arguably more sensitive
than "can turn the LoRa radio off." Verified end-to-end on real hardware (toggled the USB rail
on/off via the bridge and the FastAPI route both) before shipping; UI-side, each rail is a
toggle switch that disables itself and reverts on a failed request rather than trusting an
optimistic update.

**Front end (2026-09-23, redesign phase 3).** One page, hash-routed: an overview of six station
tiles and one detail view per station. ES modules under `app/static/js/`, no build step. The only
remaining frame, tar1090, loads only while `#/sdr` is the current route and the SDR rail is on.

**Collection model (2026-09-23).** A single startup task runs `build_status()` every 3 s and
caches the result; `/api/status` and every `/ws/status` client read the cache. It also samples a
2 h in-memory history (30 s interval) served at `GET /api/history`. Before this, each WebSocket
client ran its own collection every 3 s.

A proposed redesign, with explainers, a syllabus and guided missions, is in
[`webdash-design.md`](webdash-design.md). It is not built yet.

## SDR broadcast/airband (hunt & listen)

Added 2026-10-01. Expands the SDR rail beyond ADS-B with receive-only broadcast/airband use, through
a third host bridge, `sdr-bridge.py` (`127.0.0.1:8767`), built like the aiov2 one but able to
`sudo` — only `systemctl stop|start readsb`, which is already in sudoers (no new grant). The one
RTL-SDR tuner is shared with ADS-B, so every operation **brackets readsb** (stop → use → restart)
and requires the SDR rail already on; a single-tuner lock makes hunt and listen mutually exclusive.

- **Hunt** (`POST /api/sdr/hunt`, `GET …/status`): a one-shot `rtl_power` sweep of FM (88–108 MHz)
  or airband (118–137 MHz AM), parsed into a station list (freq / power / SNR). Background job,
  polled from the SDR view.
- **Listen** (`GET /api/sdr/listen?mode=&freq=`): `rtl_fm` → `ffmpeg` MP3, relayed to an `<audio>`
  element. The same-origin **session cookie** authenticates the `<audio>` request. The stream lives
  as long as the browser stays connected; on disconnect the proxy closes upstream, and the bridge
  kills the pipeline and restores readsb. Because a `/listen` stream is long-lived, the bridge uses
  a threaded server so it doesn't block `/hunt/status` polls.

Broadcast AM is out of reach here (R860 floor ~24 MHz; see
[`../../knowledge/sdr/learned/rtl-sdr-limits.md`](../../knowledge/sdr/learned/rtl-sdr-limits.md)) —
airband replaces it. Captures/audio are ephemeral; nothing is written to the repo.

## WPA audit (authorized equipment only)

Added 2026-10-01. The one deliberate active/offensive capability in the dashboard, kept narrow by an
**authorization gate** rather than trusted to the operator's judgement at click time — in keeping with
the repo's aircrack posture (own gear or documented authorization; see
[`../../software/aircrack-ng.md`](../../software/aircrack-ng.md) and
[`../../knowledge/README.md`](../../knowledge/README.md)).

- **The gate:** a BSSID allowlist the operator fills in from the Wi-Fi view, each entry with an
  authorization basis. Stored in the read-write data dir, outside git. Keyed on BSSID (hardware),
  because SSIDs are spoofable and shared. `app/wpa/allowlist.py` is the store; routes
  `GET/POST /api/wpa/allowlist` and `DELETE …/{bssid}`.
- **The capture path:** `POST /api/wpa/capture` → a third host bridge, `wpa-audit-bridge.py`
  (`127.0.0.1:8766`), built like the aiov2 one but *able to `sudo`* (not NoNewPrivileges), scoped to
  exactly one root-owned script (`/usr/local/sbin/uconsole-wpa-capture.sh`, via
  `/etc/sudoers.d/webdash-wpa-capture`). The bridge brackets Kismet (shared `wlan1`), tracks one job,
  and exposes start/status/cancel.
- **The script** re-checks the BSSID against the allowlist **before any RF**, then monitor mode →
  channel scan → **bounded, targeted deauth** (a few frames × a few rounds, never a continuous
  flood — that would be a DoS, which is out of scope) → handshake detection → cleanup. Captures go to
  gitignored `~/labs/wpa`; a per-run audit log records target + time.
- **Enforcement in depth:** the app checks the allowlist, the bridge re-checks it, and the root
  script re-checks it — so the gate holds where the privileged commands actually run.
- **Crack offload** (`POST /api/wpa/crack`, `GET …/status`): the bridge runs the existing
  `crack-offload.sh` (SSH to `gpu-host-wsl` → `hcxpcapngtool` → `hashcat -m 22000`) as a
  background job, parsing its `[n/4]` steps and final result. The job only accepts a `wpa-*.cap`
  directly under `~/labs/wpa` (so the route can't be pointed at arbitrary host paths). **The
  recovered PSK lives only in the bridge process's memory** — served to the authenticated UI, never
  written to a statefile or the audit log (the log records success/no-result, not the key).

Installing the host pieces and running a live capture or crack are owner-authorized steps, separate
from deploying the app.

## Mesh text messaging

Added 2026-09-23. It follows [CyberDeck](https://github.com/w1cked5mile/CyberDeck)'s `MeshClient`
design, but talks to `meshtasticd` over the TCP API instead of owning a serial port:

| Piece | What it does |
|---|---|
| Receive | `mesh.py` subscribes once to the library's `meshtastic.receive.text` pubsub topic and appends each text packet to an in-memory `deque` of 200 |
| Keepalive | A startup task in `main.py` calls `mesh.collect()` every 15 s, so the TCP interface stays connected (and receives) with no dashboard open |
| `GET /api/mesh/messages` | Returns the buffer plus the enabled channels (`index`, `name`); the page polls it every 4 s |
| `POST /api/mesh/send` | `{"text", "channel"}`: `text` 1–200 bytes UTF-8, `channel` 0–7. Broadcasts with `sendText(channelIndex=…)` and echoes the sent message into the buffer as `mine` |

Limits, stated rather than implied:

- **The buffer is not persisted.** A container restart empties it, and anything received while the
  interface is disconnected is not seen. `meshtasticd` does not replay missed text to a new API
  client.
- **Sending transmits for real** on the selected channel, including public ones such as LongFast.
  It is behind the same session gate as the rail toggle, for the same single-operator reason.
- **Broadcast only.** Direct messages are received and labelled `direct`, but the UI cannot send
  one.
- Message text and sender names come from anyone on the channel. The page inserts them with
  `textContent` only, never `innerHTML`.

## Other apps: proxied vs. linked

Kismet, tar1090, and meshtasticd's own web UI all have real, richer interfaces of their own
beyond this dashboard's status panels. Rather than one approach for all three:

| App | Approach | Why |
|---|---|---|
| tar1090 (ADS-B map) | Reverse-proxied *through* this app, at `/apps/tar1090/` (`app/proxy.py`) | Its shipped HTML/JS already uses paths relative to whatever prefix it's served under — confirmed by grepping for absolute `href`s, and by the fact it's already deployed at `/tar1090/` on this same host. A straight passthrough proxy (headers minus `content-encoding`, since `httpx` already decompresses the body) works with no rewriting. It also has **no auth of its own** — lighttpd serves it to anyone who can reach `:80` — so putting it behind this app's TOTP session is a real access-control improvement, not just convenience. |
| Kismet | Own `tailscale serve` mapping, `https://<device>.ts.net:2501/`, linked from the Kismet panel | Kismet's web UI assumes it owns the URL root; proxying it under a subpath the way tar1090 gets away with would very likely break asset loading. It has its own login (set on first run — see [`../../software/kismet.md`](../../software/kismet.md)), so this is still gated, just by a second, independent credential rather than this app's session. |
| meshtasticd web UI | Same approach, `https://<device>.ts.net:9443/`, linked from the Mesh panel | Same root-path assumption as Kismet. **Unlike Kismet, this has no login of its own** (confirmed 2026-09-21 — a plain `GET` returned `200` with no redirect to any auth page) — anyone on the tailnet can reach it once this mapping exists. Accepted as consistent with this build's existing trust boundary (Tailscale membership already gates everything else exposed this way), but called out here rather than left implicit. **As of 2026-09-22 this is moot in practice** — `meshtasticd`'s embedded webserver fails to start (see [`../logs/known-issues.md`](../logs/known-issues.md)), so the mapping proxies to nothing; the login-boundary reasoning still applies whenever it's working again. |

`GET /api/links` returns the Kismet/meshtasticd URLs (built from `WEBDASH_TAILNET_FQDN`, see
`main.py`) for the frontend to populate; it's session-gated like every other API route, even
though the links it returns lead to services with their own (or no) separate gate.

## Embedded frames

Added 2026-09-22: the three sub-pages above ([Other apps](#other-apps-proxied-vs-linked)) also
render inline as an `<iframe>` in their panel, alongside the existing "Open ↗" link rather than
instead of it — the request was to make them available *in* the dashboard, gated by the same
radio that gates the panel's own status.

| Frame | `src` | Gate | Why this gate, not something else |
|---|---|---|---|
| ADS-B map | `/apps/tar1090/` (same-origin, proxied — reuses this app's own session gate) | `aiov2.rails.SDR.on` | Literal rail dependency: readsb needs the RTL-SDR the SDR rail powers. Gated on the rail itself, not `adsb.state` — `state` briefly reads `"stopped"` for a few seconds after the rail flips on while `readsb` restarts, and the rail is what the operator actually just toggled. tar1090's own page (lighttpd) stays up regardless of the rail either way; only the aircraft data goes stale, so the map still loads, just empty. |
| ~~Meshtastic UI~~ | removed 2026-09-23 | — | meshtasticd's web server never starts (known issue), so the frame was always a blank box. The panel shows a note, and links to `:9443` only while the mesh collector's `web_ui` TCP probe succeeds. |
| ~~Kismet~~ | removed 2026-09-23 (phase 3) | — | Cross-origin framing was never confirmed, and the design keeps only the same-origin tar1090 frame. The Wi-Fi view links to Kismet instead. The original gate was `kismet.state === "running" \|\| "locked"` | **Not gated by any aiov2 rail** — Kismet's capture adapter (a Ralink RT5370 USB dongle, see `software/kismet.md`) isn't one of the AIO V2's GPIO-switched radios on this build, so there's no rail whose state would mean anything here. Its own running/locked state is the only "on" signal it has. *Superseded 2026-09-25: the USB rail powers the internal USB-C port for the Wi-Fi radio, and the Wi-Fi station's status is now gated on it.* |

GPS was deliberately left without a frame: gpsd has no web UI in this stack (`cgps`/PyGPSClient
are terminal/desktop, not web), so there's no sub-page to embed.

**Teardown, not just hiding.** `app.js`'s `setEmbed()` resets a hidden frame's `src` to
`about:blank` rather than only `display:none`-ing it — otherwise a Kismet or Meshtastic session
left open behind a flipped-off rail keeps polling/rendering in the background for no reason. It
also only touches `.src` on an actual on→off/off→on transition (tracked via a `dataset.src`
marker), not on every ~3s WebSocket status tick, so a frame the operator is actively using doesn't
get reloaded out from under them.

**Cross-origin framing is unconfirmed.** The Meshtastic and Kismet frames load a different
origin/port (their own `tailscale serve` mappings) inside this app's page. If either target ever
sends `X-Frame-Options` or a CSP `frame-ancestors` directive that blocks being framed, the iframe
just renders blank — cross-origin means this app's JS can't inspect why or detect it via
`onerror`. Neither could be checked at build time: Kismet was crash-looping
([`../logs/known-issues.md`](../logs/known-issues.md) — a pre-existing, separate bug, not caused
by this change) and meshtasticd's webserver doesn't start at all. tar1090 (same-origin, proxied)
was confirmed to send neither header. The "Open ↗" link next to each frame is the fallback if
framing ever turns out to be blocked. **Not click-tested in an actual browser** — verified that
the container builds, starts clean, and serves the updated static files; this session has no
browser attached to the device's display to confirm the frames render and toggle visually.

## Auth

Session cookie (signed, `itsdangerous`) gated by password + TOTP (`pyotp`), same shape as
CyberDeck's `auth.py`. Secret store (`password_hash`, `totp_secret`) lives at
`~/.config/uconsole-webdash/auth.json`, bind-mounted into the container, **outside the repo** —
this build's own convention already forbids committing secrets (see [`../../CLAUDE.md`](../../CLAUDE.md)).
First-run enrollment page generates a QR code (`segno`), same as CyberDeck.

This matters more here than it might elsewhere: this box does passive RF survey (Kismet) and its
dashboard would otherwise expose live GPS position — see [Privacy](#privacy).

## Privacy

`gps.py`'s collector reads the live fix. Per this repo's convention (general location only, no
precise coordinates in anything committed — [`../../knowledge/README.md`](../../knowledge/README.md)),
the **dashboard UI is allowed to show a precise fix** (it's a live operator tool behind auth, not a
committed document), but:

- No collector output is ever logged to a file that could land in git.
- The `/api/mesh/gps` style "exempt from login for internal consumers" pattern CyberDeck uses is
  **not** carried over — every route requires the session, no exceptions, since Kismet on this box
  can be mid-survey and the dashboard would be showing more than just this node's position.

## Image budget

`python:3.12-slim` (~130 MB) + `fastapi`, `uvicorn[standard]`, `psutil`, `meshtastic` (pulls
`protobuf`, `pyserial`), `pyotp`, `segno`, `itsdangerous`, `python-multipart` ≈ 300–400 MB total,
based on CyberDeck's own `requirements.txt` minus `esptool`/`docker`/`paho-mqtt` (not needed here).
Against ~208 GB free on the NVMe root (since 2026-09-23), this is not a meaningful bite. Track it
anyway (`docker system df`) as other images accumulate.

## Deployment

```
webdash/
├── Dockerfile              # python:3.12-slim, aarch64
├── docker-compose.yml      # network_mode: host; bind-mounts: aiov2_ctl binary+assets,
│                            #   /sys/class/thermal:ro, host / at /hostfs:ro, auth secret dir
├── requirements.txt
└── app/
    ├── main.py              # FastAPI app, REST + WebSocket (/ws/status, 3s push — same cadence as CyberDeck)
    ├── auth.py               # session + TOTP
    ├── collectors/
    │   ├── system.py
    │   ├── aiov2.py
    │   ├── kismet.py
    │   ├── gps.py
    │   ├── mesh.py
    │   ├── adsb.py
    │   └── net.py           # added 2026-09-25: Wi-Fi interface modes from sysfs
    └── static/
        ├── index.html
        ├── app.js
        └── styles.css
```

Setup/operational runbook (install Docker, build, verify): [`../../software/webdash.md`](../../software/webdash.md).

## Build order

1. `system.py` + `main.py` skeleton + auth — get one real panel behind login, end to end, in a
   running container on this hardware. Proves the container/auth/WebSocket plumbing before adding
   anything hardware-adjacent.
2. `aiov2.py` — the one collector needing a non-default bind-mount; proves that pattern early.
3. `gps.py`, `adsb.py`, `kismet.py` — same shape (HTTP/TCP over host network, no bind-mounts),
   done together.
4. `mesh.py` — last, since it's the only collector with a real client library and connection
   lifecycle (not just a one-shot HTTP GET).
5. Verify every collector's down-state on this actual hardware (Kismet stopped, SDR rail off so
   readsb is crash-looping, gpsd with no fix) — these are the *normal* states on this build most of
   the time, not edge cases to defer.

## Resolved during the build (2026-09-21)

- **`aiov2_ctl --status` does *not* work bind-mounted into the container as originally hoped.**
  Traced it (`strace -f -e trace=execve,openat`): it shells out to `pinctrl get <N>` per rail,
  a compiled binary that needs GPIO device access — bind-mounting the script plus `pinctrl` plus
  its device nodes into a `python:3.12-slim` image was judged more fragile than the documented
  fallback, so v1 goes straight there: [`../../webdash/host-helpers/aiov2-bridge.py`](../../webdash/host-helpers/aiov2-bridge.py),
  a ~60-line stdlib `http.server` on `127.0.0.1:8765`, run as a host-side systemd unit
  (`uconsole-aiov2-bridge.service`). `aiov2.py` just does an HTTP GET, same shape as every other
  collector. See [`../../software/webdash.md`](../../software/webdash.md).
- **`meshtastic`'s `TCPInterface(hostname="127.0.0.1")` confirmed working** against this build's
  `meshtasticd` — real node info, battery, channel list. No serial port involved.
- **`mesh.py` reconnected every ~15s (its cache TTL) until 2026-09-21, when that turned out to
  race the library's own teardown.** Closing a `TCPInterface` right after its initial handshake
  races its background reader thread, which reacts to the just-arrived "config complete" message
  by firing an immediate heartbeat send — on a socket our own code had, by then, already closed.
  The library caught its own `BrokenPipeError` and kept going (never broke `collect()`'s return
  value), but it logged the full traceback every cycle, `docker logs` spam that would only grow
  with the dashboard's own use. Fixed by keeping one persistent `TCPInterface` for the app's
  lifetime instead of reconnecting per poll — confirmed clean logs across repeated `/api/status`
  calls afterward.
- **HTTP, bound to `127.0.0.1` only, not `0.0.0.0`** — chosen over TLS/wider exposure for v1.
  With `network_mode: host`, `127.0.0.1` means reachable from this device alone, not the LAN, even
  though the network namespace is shared. Deliberately conservative: v1's login has no rate
  limiting or lockout, and the panels include live GPS position and RF-survey state.
  **Widened via `tailscale serve`, 2026-09-21** — see [`../../software/webdash.md`](../../software/webdash.md#tailscale-access).
  It reverse-proxies from this device's tailnet HTTPS endpoint (`https://fancy.example-tailnet.ts.net/`,
  a real Let's Encrypt cert issued through Tailscale) to the still-loopback-only Uvicorn — the
  127.0.0.1 bind above didn't change, Tailscale is just the only thing that can now reach it from
  outside the device. Confirmed tailnet-only (`tailscale serve status`, not `funnel`) — not exposed
  to the public internet.
- **Runs as uid/gid 1000, not root** — an addition beyond the original plan. Root was the
  `python:3.12-slim` default; first-run testing found it left `/auth`'s files root-owned on the
  host (unreadable to the normal user without `sudo`). Fixed by adding a non-root user to the
  image matching the host build user, which this app's access pattern (no device, no privileged
  path) doesn't need root for anyway.
- **A WebSocket-close bug, found and fixed during testing:** closing an unauthenticated connection
  *before* calling `accept()` rejects the opening handshake itself (client sees a bare HTTP 403,
  never an `onclose` event with a code) — so the intended "session expired, reload the page" path
  (`close(code=4401)`) silently never fired. Fixed by accepting first, then immediately closing
  with `4401` — confirmed client-side afterward (`websockets` client in the running container saw
  `ConnectionClosed` with `code: 4401`, not a handshake `InvalidStatus`).

Verified end-to-end against real services on this hardware: image builds to 205 MB (well under
the 300–400 MB estimate above); `/setup` → `/login` → authenticated `/` and `/api/status` →
`/ws/status` (both the live-data path and the 4401 rejection path) all confirmed working. All
five service-backed collectors returned correct output against this build's actual state — Kismet
`stopped`, gpsd `running` with no fix, `readsb` `stopped` (SDR rail off), meshtasticd `running`
with real node data, `aiov2_ctl` rails matching `aiov2_ctl --status` run directly on the host.
