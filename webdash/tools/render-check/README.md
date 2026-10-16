# webdash render-check

Headless screenshots of webdash views, for visually verifying they render without standing up
the full dashboard: the **Build log** (`#/timeline`), and the **mesh transmit control** in every
state (added 2026-10-11).

## Why

The live app is login-gated, and loading it in headless chromium hangs: `main.js` opens a
status WebSocket that reconnects forever, so the page never idles and chromium never exits.
The timeline view is **static** — [`app/static/js/timeline.js`](../../app/static/js/timeline.js)
builds it from in-file data with no API or WebSocket — so this mounts just that view against
the real `timeline.js` and `styles.css` and screenshots it.

No source is copied: [`render-timeline.sh`](render-timeline.sh) symlinks
`app/static/{js,styles.css}` next to a copy of [`timeline-harness.html`](timeline-harness.html)
in a temp dir, so the render always tracks whatever is shipping.

## Run

```bash
./render-timeline.sh                      # -> $TMPDIR/webdash-timeline.png
./render-timeline.sh /tmp/build-log.png   # custom output path
./render-timeline.sh /tmp/build-log.png 920,4200   # taller window for more entries
```

Requires `chromium` (or `chromium-browser` / `google-chrome`) on `PATH`, or `CHROMIUM=/path/to/chrome`.

## Notes

- `--allow-file-access-from-files` is required: the harness imports `timeline.js` as an ES
  module, and module imports are blocked on `file://` without it. Serving over http instead
  reintroduces the hang (Python's single-thread `http.server` stalls chromium mid-load).
- `--no-sandbox` is used because this renders our own local files on Linux/Pi, where the
  chromium sandbox often isn't available. Don't copy that flag into anything that opens
  untrusted pages.
- This checks rendering only — it does not exercise `main.js`, auth, or any live data path.

## Mesh transmit control (`render-actuator.sh`)

Renders the real `mesh.js` and `actuator.js` once per transmit-control state: ready, secondary
channel, too long, rail off, rail unknown, meshtasticd unreachable, no channels, frequency
disagreement, and still checking. Nothing is fetched or sent: `main.js` and
`pollMeshMessages` are never called.

- The status data comes from [`actuator-fixtures.py`](actuator-fixtures.py), which builds it with
  the real `app/collectors/mesh_radio.py`. The render therefore shows exactly the readiness and
  copy the server would send.
- The markup is copied out of `app/static/index.html` at render time, so it can't drift from
  what ships.

```bash
./render-actuator.sh                                  # -> $TMPDIR/webdash-actuator/*.png
./render-actuator.sh /tmp/act 1280,720 vintage        # out dir, window size, skin
./render-actuator.sh /tmp/act 640,900                 # phone-ish width
```

This shows rendering and copy only. It doesn't exercise a real send or the live status socket.

## Full views (`render-view.sh`)

Screenshots **any** dashboard view by running the **real** `main.js` — routing, rendering and tab
selection exactly as production — with the network neutralized. This is what lets QA see the
overview, the Wi-Fi tabs, the SDR tabs, and the GPS/power/system/mesh views, not just the timeline.

How it defuses the hang (see *Why* above): `main.js` opens a status WebSocket that reconnects
forever, so the page never idles. [`view-harness.html`](view-harness.html) replaces
`window.WebSocket` with a fake that opens, delivers **one** fixture snapshot and never closes (so
the reconnect/`onclose` path stays dormant), and replaces `window.fetch` with one that serves
fixtures for the boot `/api/*` calls. It sets `location.hash` and then imports the real `./js/main.js`.
[`render-view.sh`](render-view.sh) stages it like the actuator tool: `js/` and `styles.css` are
symlinks to the shipping files, and the `<header>` + `<main>` are copied out of `index.html` at
render time (so they can't drift; the `<script src=".../main.js">` tag sits after `</main>` and is
dropped). The status snapshot comes from [`fixture-status.py`](fixture-status.py) — a **fixture,
not live data** — whose `mesh.tx`/`mqtt`/`tx_copy` are built from the real `mesh_radio.py` so the
transmit copy matches the server; every other value is static and the location is invented
(grid-only policy).

```bash
./render-view.sh                       # -> $TMPDIR/webdash-view/view-overview-default-1280x480.png
./render-view.sh wifi/wpa              # the WPA-audit Wi-Fi tab
./render-view.sh sdr/adsb /tmp/a.png 1280,720 vintage   # out path, window, skin
for v in overview wifi wifi/survey wifi/capture wifi/wpa sdr/adsb mesh gps power system; do
  ./render-view.sh "$v"; done          # the core set
```

- **History:** the fetch stub also serves a synthetic 2 h `/api/history` that ends on the status
  fixture's values, so the sparklines render with a full trace. It's not live data either.
- **Views:** `overview | mesh | gps | power | system | learn | timeline`;
  `wifi` (opens Kismet) `| wifi/kismet | wifi/survey | wifi/capture | wifi/wpa`;
  `sdr` (opens ADS-B) `| sdr/adsb | sdr/hunt | sdr/listen | sdr/owrx`. The old top-level `#/survey`,
  `#/capture`, `#/wpa` still render — they redirect to the matching Wi-Fi tab, as in the app.
- **Default window is `1280,480`** (the uConsole panel area; `1280,720` is the full panel). Skins:
  `default` or `vintage` — set via the `fancy.v1.skin` key before `main.js` imports, because
  `learn.js` runs `applySkin()` at load and would otherwise clobber a `data-skin` attribute.
- A successful render shows `conn-state: live` in the strip (the fixture socket landed and one
  `tick()` ran). `#/learn` renders only the "compile the curriculum" panel: learning content is
  served from the mounted bundle, not `/static`, so the offline fixture reports it unavailable.
  Pointing the fetch stub at a dumped bundle would cover the learning pages — a follow-up.
- Same caveats as the other tools: `--allow-file-access-from-files` for ES-module `file://` imports,
  `--no-sandbox` because these are our own local files, and `--virtual-time-budget` to screenshot
  despite `main.js`'s polling intervals. Rendering only — no auth, no live data, nothing transmitted.
