# webdash — operator dashboard

Locally-authored software (not a vendor app) — see [`../docs/reference/webdash-architecture.md`](../docs/reference/webdash-architecture.md)
for why it exists and what it does. This doc is the setup/operational runbook. Code lives in
[`../webdash/`](../webdash/). `webdash` is the repo/component name throughout this doc and the
architecture doc; the on-screen name is **Fancy Dashboard**, after `fancy` (this device's
hostname), itself named for *The Fancy*, Henry Every's frigate (1695) — the tagline under the
title on every page.

Installed and verified end-to-end on this hardware 2026-09-21: Docker, the image build, first-run
setup, login, the authenticated dashboard page, `/api/status`, and the `/ws/status` WebSocket
(including its session-expiry close code) all confirmed working against the real `aiov2_ctl`,
gpsd, and meshtasticd on this device.

## Install Docker

```bash
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker "$USER"   # log out/in (or `sg docker -c '...'`) for it to take effect
```

Debian trixie carries Docker directly in its own repos (26.1.5 as of 2026-09-21) — no need for
Docker's official third-party apt repo, unlike Kismet. `docker.service` is enabled at boot by the
package install; confirm with `systemctl is-enabled docker`.

## The aiov2_ctl host bridge (install this first)

`aiov2_ctl` shells out to `pinctrl`, which needs GPIO device access — simpler to run it as a tiny
host-side systemd service than to bind-mount a compiled binary and device nodes into the
container. See [`../docs/reference/webdash-architecture.md`](../docs/reference/webdash-architecture.md#the-one-exception).
As of 2026-09-21 it also handles rail *control* (`POST /rail`), not just status — see
[Rail control](#rail-control) below.

```bash
sudo cp ../webdash/host-helpers/uconsole-aiov2-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now uconsole-aiov2-bridge
curl -s http://127.0.0.1:8765/status   # sanity check before starting the container
```

## Build and run

```bash
cd ../webdash
mkdir -p ~/.config/uconsole-webdash   # auth secret store — outside the repo, outside git
sg docker -c 'docker compose up -d --build'
```

`docker-compose.yml` runs with `network_mode: host` (reaches gpsd/Kismet/meshtasticd/tar1090/the
aiov2_ctl bridge on localhost, no port mapping needed) and bind-mounts `/` read-only at `/hostfs`
(for real disk-usage numbers — the container's own `/` is its overlay filesystem, not useful for
this) and `/sys/class/thermal` read-only (CPU temperature). No `/dev` bind-mount, no `cap_add` —
this app never owns hardware directly.

The container runs as uid/gid 1000 (matching the default build user), not root — files it writes
into the bind-mounted `/auth` volume are host-readable, not root-owned. **Verify this if your
host user isn't uid 1000**, or the container won't be able to write its auth store.

The app binds Uvicorn to **127.0.0.1 only** (see the Dockerfile) — reachable from this device
alone, not the LAN, even though `network_mode: host` is in play. This is deliberate: v1's login
has no rate limiting or lockout, and the dashboard shows live GPS position and RF-survey state.
Wider access goes through Tailscale Serve (below), not a direct LAN bind.

## Tailscale access

Exposed via `tailscale serve` — it reverse-proxies from this device's tailnet HTTPS endpoint to
the loopback-only Uvicorn above, so the "127.0.0.1 only" binding above doesn't change; Tailscale
is the only thing that can reach it from outside the device. Same shape as CyberDeck's own
Tailscale-cert-terminated access, but via `tailscale serve` instead of handing Uvicorn a cert
file directly — one fewer thing to keep in sync when the cert renews (Tailscale does that itself).

```bash
sudo tailscale serve --bg --https=443 localhost:8090
tailscale serve status   # confirm: "(tailnet only)" — not funnel, not exposed to the public internet
```

Reachable, tailnet-only, at `https://<this device's MagicDNS name>.<tailnet>.ts.net/` — confirmed
2026-09-21 at `https://fancy.example-tailnet.ts.net/` with a valid Let's Encrypt cert issued
through Tailscale. `tailscale serve` config is stored in `tailscaled`'s own state and re-applied
automatically when `tailscaled` (re)starts — no extra systemd unit needed, same as CyberDeck's
`tailscaled` restart self-heal note in its own README, just without a container to re-touch since
Tailscale itself is doing the proxying rather than app-owned code.

To remove: `sudo tailscale serve --https=443 off`.

**Never run `tailscale funnel`** for this — that would expose it to the public internet, not just
the tailnet. `tailscale serve` alone keeps it tailnet-only.

### Kismet and the meshtasticd web UI get their own mapping

Added 2026-09-21, alongside the dashboard's own proxy for tar1090 (see
[Other apps](#other-apps-proxied-vs-linked) below and the architecture doc's section of the same
name for the full reasoning):

```bash
sudo tailscale serve --bg --https=2501 localhost:2501    # Kismet's own web UI
sudo tailscale serve --bg --https=9443 https+insecure://localhost:9444    # meshtasticd's own web UI (HTTPS, self-signed)
tailscale serve status   # should list all three (443, 2501, 9443), each "(tailnet only)"
```

**meshtasticd's web UI has no login of its own** — confirmed 2026-09-21, a plain `GET` to `:9443`
returned `200` with no redirect to any auth page, and the UI can control/transmit on the radio.
Exposing it this way relies on tailnet membership as the only gate. Kismet does have its own login
(set on Kismet's first run, separate from this app's account), and binds `127.0.0.1` locally
(`httpd_bind_address=127.0.0.1` in `/etc/kismet/kismet_site.conf`), so only the serve proxy reaches
it from the tailnet.

meshtasticd listens on **9444** locally, not 9443. The serve entry above makes `tailscaled` hold
`:9443` on the tailnet address, and that blocks meshtasticd's `0.0.0.0:9443` bind. From
2026-09-22 until the move on 2026-09-25, that clash was why the web UI wouldn't start. See
[`../docs/logs/known-issues.md`](../docs/logs/known-issues.md).

**These mappings were removed 2026-09-29 and restored the same day** at the owner's request — the
UIs are wanted on the tailnet, and the owner is the sole tailnet member (accepted risk, see
[`known-issues.md`](../docs/logs/known-issues.md)). Two things to know if closing them again:
Kismet's loopback bind means removing its proxy fully closes `:2501`, but meshtasticd binds
`0.0.0.0:9444`, so removing only the `:9443` proxy leaves it **directly reachable on the tailnet IP
at `:9444`** — to truly close it, disable the `Webserver:` block in `/etc/meshtasticd/config.yaml`
(there is no bind-address option) and restart. Separately, meshtasticd's **client API on
`0.0.0.0:4403`** is always tailnet-reachable with no auth of its own — a larger surface the
dashboard's mesh collector and the `meshtastic` CLI use over loopback; flagged in `known-issues.md`.

## First-run setup

```bash
curl -s http://127.0.0.1:8090/api/health   # {"ok":true,...} confirms the container is up
```

Visit `https://<device>.<tailnet>.ts.net/` from any device on your tailnet (or
`http://127.0.0.1:8090/` on the box itself). First visit redirects to `/setup`: pick a username
and password (≥8 characters), then **scan the TOTP QR code shown once** — it is not recoverable.
After that, `/login` takes username + password + 6-digit code.

**No default credentials are shipped or committed anywhere** — `/setup` only works once, before
`~/.config/uconsole-webdash/auth.json` exists. To reset (lost the TOTP device, starting over):

```bash
rm ~/.config/uconsole-webdash/auth.json ~/.config/uconsole-webdash/session_secret
```

## What it shows

Grouped into two sections on the page, matching how the panels are actually used rather than a
flat grid: **Platform** (this device itself — System, aiov2_ctl rails) and **Services** (Kismet,
GPS, ADS-B, Meshtastic).

| Panel | Group | Source | Normal-but-idle state on this build |
|---|---|---|---|
| System | Platform | `psutil`, in-container | always available |
| aiov2_ctl rails | Platform | the host bridge above | rail switches — see [Rail control](#rail-control) |
| Kismet | Services | `127.0.0.1:2501` | `stopped` — Kismet is off by default ([`kismet.md`](kismet.md)) |
| GPS (gpsd) | Services | `127.0.0.1:2947` | `running`, `fix: none` until there's sky view ([`gps.md`](gps.md)) |
| ADS-B (readsb) | Services | `127.0.0.1/tar1090/data/aircraft.json` | `stopped` — `readsb` crash-loops when the SDR rail is off, which is the default |
| Meshtastic | Services | meshtasticd's TCP API, `127.0.0.1:4403` | `running`, real node/channel info — meshtasticd is enabled at boot |

Every collector has a short timeout and never lets a downstream service being off surface as a
crash — confirmed by testing against this build's actual resting state, where three of the five
service-backed panels are normally idle/off.

## Layout and navigation

Since 2026-09-23 (redesign phase 3) the page is one overview plus a detail view per station,
switched by the URL hash. There is no framework and no build step: ES modules in
`app/static/js/` (`main.js` router and WebSocket, `views.js` rendering, `rails.js`, `mesh.js`,
`ui.js` helpers).

| Route | Shows |
|---|---|
| `#/` | Six tiles: System and Power on the top row; Meshtastic, GPS, ADS-B, Wi-Fi survey below. Each has a status, one headline figure, two facts, and its rail switch |
| `#/mesh` | Node details, message log and send box, LORA switch |
| `#/gps` | Fix and satellites. Position shows as a **Maidenhead grid square**; *Show coordinates* reveals latitude/longitude for this page load only |
| `#/sdr` | ADS-B counts, SDR switch, and the embedded tar1090 map (loaded only while this view is open and the SDR rail is on) |
| `#/wifi` | Kismet state, the passive-only note, the verified start command, and the Kismet UI link. No embedded frame |
| `#/power` | All four rail switches with what each powers, and every field the bridge reports |
| `#/system` | CPU, load, memory, disk, temperature, uptime |

The status strip at the top stays visible on every view: power source and voltage, CPU temperature,
and a chip per rail that links to the station it powers. On a 1280×480 viewport (the uConsole in
landscape with browser chrome) the overview fits with no scrolling. Verified 2026-09-23 in
headless Chromium at 1280×480, 1440×900 and 390×844.

## Rail control

The aiov2_ctl rails panel shows each rail (GPS/LORA/SDR/USB) as a toggle switch, not just a
status dot — past this app's original read-only v1 scope, added 2026-09-21 once that read path
was proven (see the architecture doc's [Rail control](../docs/reference/webdash-architecture.md#rail-control)
section for the full design/security reasoning). Flipping one calls `POST /api/aiov2/rail`, which
the aiov2-bridge turns into the exact `aiov2_ctl <FEATURE> on|off` command you'd type by hand.
Verified end-to-end on this hardware (toggled the USB rail through the real HTTP stack, confirmed
against `aiov2_ctl --status`).

No separate confirmation dialog — the switch disables itself while the request is in flight and
reverts if it fails, same as flipping the switch in the terminal. Turning off SDR mid-capture or
LORA while relying on the mesh has the same real consequences it would from the CLI; this doesn't
add a safety net the CLI doesn't already lack.

## Mesh messages

The Meshtastic panel has a message log and a send box. Pick a channel, type up to 200 bytes, and
press **Send**. The message is broadcast over LoRa from this node, the same as
`meshtastic --host 127.0.0.1 --sendtext "…" --ch-index N`. Incoming text on any enabled channel
shows in the log within about 4 s, with sender, channel and SNR. This replaces the broken
Meshtastic web UI for messaging. Design and limits:
[Mesh text messaging](../docs/reference/webdash-architecture.md#mesh-text-messaging).

- The log is in memory only. Restarting the container clears it.
- **Sending transmits for real**, including on public channels such as LongFast.
- Send and receive over the air are **unverified** as of 2026-09-23. The API, validation and login
  gate were tested, but no message was sent and the node had received 0 packets that day. To
  verify, send from the dashboard and confirm a second node hears it, then reply.

## Panel status

Each service panel shows its state as a colour, a glyph **and** a word. It combines the service
with the rail that powers it, so a service whose rail is off reads "rail off", not "running" or
"error". (Added 2026-09-23. Before that, Meshtastic stayed green with the LORA rail off, because
meshtasticd keeps running without the radio.)

| Word | Glyph | Meaning | Examples |
|---|---|---|---|
| live, 3D fix | ● green | working and producing data | Meshtastic reachable with LORA on; GPS fixed |
| searching, listening, starting | ◐ blue | up, waiting on the world | GPS without sky view; readsb with no aircraft yet |
| off, rail off | ○ grey | deliberately off; normal on this build | SDR rail off; Kismet not started |
| login needed, gpsd stopped | ▲ amber | something for you to do | Kismet admin login not set |
| error | ✕ red | unreachable or failing unexpectedly | collector error |

If the aiov2 bridge is unavailable, rail state is unknown, and panels fall back to the service's
own state rather than guessing "off".

Rail switches are `<button role="switch">` elements: Tab to one, Space or Enter toggles it, and a
failed switch reverts and shows the error under the rail grid.

## Status collection and history

One background task collects every source every 3 s. `/api/status` and each `/ws/status` client
get that cached snapshot, so opening more tabs doesn't multiply gpsd, Kismet or bridge queries.
Verified 2026-09-23: gpsd saw 18 connections per minute with no dashboard clients, and 16 with
three extra WebSocket clients attached. The same loop keeps meshtasticd's TCP interface connected
while nobody has the page open.

Fields added 2026-09-24 for the learning platform (build step S2): `aiov2.power_num` (voltage,
current, power, capacity as numbers; `on_battery`), `gps.hdop`/`pdop`/`eph_m`/`tpv_age_s`/`grid`,
`adsb.messages_per_s` (from the delta of readsb's cumulative `messages` counter),
`mesh.rx_packets`/`rx_nodes`/`last_rx_ts`/`last_rx_snr`/`last_rx_rssi` (any packet from another
node since webdash started — counts only, no payloads), and `services.<name>.{active, sub,
n_restarts, crash_looping}` for readsb, gpsd, meshtasticd and Kismet, from the bridge's read-only
`GET /services`. **After pulling this change, restart the bridge**
(`sudo systemctl restart uconsole-aiov2-bridge`) — it runs from the repo checkout.

Added 2026-09-25 for M7 (passive Wi-Fi): a `net` block from the `net.py` collector, which reads
`/sys/class/net/*/type` (the host's interfaces, through host networking) — `net.state`,
`net.monitor_ifaces` (how many interfaces are in monitor mode) and `net.wlan0`/`net.wlan1`, each
`{present, mode}` with mode `managed`, `monitor`, `other` or null. Kismet adds a separate
`wlan1mon` monitor interface next to `wlan1` (seen 2026-09-25), so during a survey
`net.monitor_ifaces` is 1 and `net.wlan1` stays `managed`; only if `wlan1` were absent would
`wlan1mon` be reported as `net.wlan1` in monitor mode. Booleans, counts and mode
names only: the collector never reads an interface's MAC address. Needs a container rebuild, not a
bridge restart.

`GET /api/history` returns the last 2 h of vitals at one sample per 30 s: CPU %, CPU temperature,
pack voltage, bridge power reading, GPS satellites used and mesh nodes seen. It is held in memory
and empties when the container restarts. Nothing in the UI draws it yet; it is there for the
redesign's sparklines ([`../docs/reference/webdash-design.md`](../docs/reference/webdash-design.md)).

## Other apps: proxied vs. linked

- **ADS-B map (tar1090)** — proxied *through* this app: `Open map ↗` in the ADS-B panel, or
  `https://<device>.<tailnet>.ts.net/apps/tar1090/` directly. No separate Tailscale mapping
  needed; it's this app's own session gating it, and tar1090 has none of its own.
- **Kismet** and **meshtasticd's web UI** — linked (`Open Kismet UI ↗` / `Open Meshtastic UI ↗`),
  not proxied: each gets its own `tailscale serve` port mapping (above) and opens in a new tab.
  `GET /api/links` (session-gated) is what the page fetches to populate those hrefs.

Why the split, and the meshtasticd-has-no-login-of-its-own caveat, are in the architecture doc's
[Other apps](../docs/reference/webdash-architecture.md#other-apps-proxied-vs-linked) section —
don't re-derive it here if it drifts, fix it there and this section's summary.

### Embedded frames, on/off with the radios

Added 2026-09-22: each of the three sub-pages above also renders inline as an `<iframe>` in its
panel, not just as an "Open ↗" link — full detail and the code-level rationale (why `.src` is
only touched on a state *transition*, not every status tick) is in the architecture doc's
[Embedded frames](../docs/reference/webdash-architecture.md#embedded-frames) section. In short:

| Frame | Shown when | Why that gate |
|---|---|---|
| ADS-B map | SDR rail is on | readsb (behind tar1090) needs the RTL-SDR the SDR rail powers |

The Meshtastic frame was **removed 2026-09-23**: meshtasticd's web server wasn't starting at the
time (a port clash, fixed 2026-09-25), so it only ever showed an empty 440 px box. The panel shows a
note instead, and the "Open Meshtastic UI ↗" link appears only while `mesh.web_ui` reports
meshtasticd's local port 9444 answering. That
check is a TCP connect made each time the mesh collector refreshes.

When the gating condition is off, the frame is torn down (`src` reset to `about:blank`, not just
hidden) so it isn't polling or holding a session in the background, and a short placeholder
explains why. GPS has no web sub-page in this stack (gpsd/`cgps`/PyGPSClient are all
non-web), so it wasn't given a frame. Kismet and the Meshtastic UI are cross-origin iframes
(their own `tailscale serve` ports, not this app's origin) — if either ever sets
`X-Frame-Options`/CSP `frame-ancestors` against being framed, the iframe will just render blank
with no error this app can detect; the "Open ↗" link stays as a guaranteed-working fallback for
exactly that case. **Not yet confirmed against a real browser** — verified server-side (files
serve correctly, container starts clean) but not click-tested, since this session has no browser
tooling attached to the device's display. As of 2026-09-22 the Meshtastic frame will show a
connection error regardless of the LoRa rail — that's the known `meshtasticd` webserver bug
([`../docs/logs/known-issues.md`](../docs/logs/known-issues.md)), not this feature.

## Learning platform (the Chart Table)

Being built on branch `claude/learning-mvp-20260924` from
[`../docs/reference/learning-platform-plan.md`](../docs/reference/learning-platform-plan.md).
Curriculum source is in [`../webdash/curriculum/`](../webdash/curriculum/README.md); it is
compiled on the host and mounted read-only into the container:

```bash
python3 webdash/host-helpers/learn-compile.py            # writes ~/.local/share/uconsole-webdash/learn/
python3 webdash/host-helpers/learn-compile.py --check    # lint only
```

The container picks up a new bundle on the next request; no restart is needed. Learner state
goes in `~/.local/share/uconsole-webdash/data/` (mounted at `/data`). Neither directory is in the
repo, and nothing learning-related is served from `/static` (which needs no login). The pages
live at `#/learn` (Learn in the status strip); the API is `/api/learn/*`, behind the login.

## Verify

```bash
curl -s http://127.0.0.1:8090/api/health
sg docker -c 'docker logs uconsole-webdash'
sg docker -c 'docker images uconsole-webdash'   # 205 MB as built 2026-09-21
sudo systemctl status uconsole-aiov2-bridge
```

## Rebuilding after a code change

```bash
cd ../webdash
sg docker -c 'docker compose up -d --build'
```

No source bind-mount — like CyberDeck's webdash, `app/` is baked into the image at build time.
Editing files on disk has no effect on the running container until this is re-run.
