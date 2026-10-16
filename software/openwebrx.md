# OpenWebRX — web-native SDR receiver

A browser-based SDR receiver: a live waterfall and tunable demodulators, served as a web page.
On this build it is the **fourth** SDR application behind the dashboard's **SDR → Receiver** tab,
sharing the one RTL-SDR with ADS-B, the band hunt, and listen. **Receive-only** — it decodes and
plays what the tuner hears and transmits nothing, within the posture in
[`../knowledge/README.md`](../knowledge/README.md).

Installed 2026-10-14. See the build log for that date, and
[`../docs/logs/decisions.md`](../docs/logs/decisions.md) for why it runs as its own container.

## How it runs

- A **host** Docker container (`jketterl/openwebrx:stable`, arm64 — v1.2.2 as installed), **not** in
  the webdash image, which has no `/dev` access. The RTL-SDR is passed through as raw USB.
- Compose file: [`../configs/openwebrx/docker-compose.yml`](../configs/openwebrx/docker-compose.yml).
  It binds **127.0.0.1:8073** only; the tailnet reaches it through `tailscale serve --https=8073`,
  the same posture as Kismet (its own login, tailnet-only).
- `restart: "no"` on purpose — like `readsb`, it must **not** auto-start at boot and seize the
  tuner. The webdash host bridge ([`webdash/host-helpers/sdr-bridge.py`](../webdash/host-helpers/sdr-bridge.py))
  starts and stops the container on demand from the Receiver tab, and the bridge user is in the
  `docker` group so no `sudo` is involved.

## One tuner, four applications

The single RTL-SDR can only serve one application at a time, so the bridge treats OpenWebRX as a
fourth mutually-exclusive holder (`busy = "owrx"`), the same symmetric model ADS-B uses:

- Starting the receiver needs a **free** tuner; it is refused while Hunt, Listen, or ADS-B hold it.
- It also needs the **USB rail off** (2026-10-15). The bridge reads it from the aiov2 bridge and
  refuses with 409 if it is on or unknown, after a hard power loss with the receiver running.
  Turn it off with `aiov2_ctl USB off` or the rail switch on the Overview. See
  [`../docs/logs/known-issues.md`](../docs/logs/known-issues.md).
- While the receiver runs, Hunt / Listen / ADS-B are **refused** until it is stopped — the
  dashboard's tuner banner reads "Tuner: OpenWebRX (receiver)" and each tab shows why it is blocked.
- The reservation is on the container **running**, not on a client being connected: OpenWebRX opens
  the dongle lazily (only when a browser tunes a profile), but the bridge reserves it the whole time
  the container is up so a hunt can't grab it in between. A container started outside the bridge
  (manual `docker compose up`) is still honoured — the claim paths consult the live container state.

## Using it

1. **SDR → Receiver** tab → **Start receiver** (first start pulls up the container; a few seconds).
2. **Open the receiver in a new tab ↗** — the waterfall loads. Viewing needs **no login**.
3. Stop it from the same tab to hand the tuner back to ADS-B / Hunt / Listen.

### Profiles

The seed config [`../configs/openwebrx/settings.json`](../configs/openwebrx/settings.json) defines
the RTL-SDR device with FM broadcast, airband (AM), NOAA weather (NFM), and 2 m / 70 cm ham
profiles, all at the device's known-good **2.048 MS/s** (NOAA at 250 kS/s). Each profile is a ~2 MHz
window — the R820T front end bottoms out around 24 MHz, so broadcast AM is out of reach (see
[`sdr-stack.md`](sdr-stack.md)). Apply/verify/rollback steps are in that file's `_readme` key and
the compose header.

### Admin login (only to change settings)

Viewing the receiver needs no account; the **Settings** UI does. Create the one-time admin user
with the container running (set your own password — it is stored in the container's volume, never
in this repo):

```bash
docker exec -it openwebrx openwebrx admin adduser <name>
```

## Verify

```bash
docker ps --filter name=openwebrx                         # Up while running
curl -s -o /dev/null -w '%{http_code}\n' http://127.0.0.1:8073/   # 200
curl -s http://127.0.0.1:8767/hunt/status | grep -o '"busy": "[^"]*"'   # "owrx" while running
docker logs openwebrx | grep -i "out of range"            # should print nothing
```

## Rollback

```bash
docker compose -f configs/openwebrx/docker-compose.yml down   # stop + remove the container
docker volume rm openwebrx_openwebrx-settings                 # also discard settings + admin user
```

Stopping the container releases the tuner immediately.
