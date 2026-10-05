# ADS-B — decoder + tar1090 map

`tar1090` is a **web map**; it renders data from a decoder (`dump1090-fa` / `readsb`). Installing
tar1090 without a running decoder produces an empty map — the most common "it doesn't work".

## Install

**Corrected 2026-09-18** — `sudo aiov2_ctl --add-apps` does **not** work on this image (confirmed
2026-09-16, see [`../docs/logs/known-issues.md`](../docs/logs/known-issues.md)); it would never
have provided a decoder here. Installed `readsb` (a maintained `dump1090` fork) and `tar1090`
directly from their own upstream installers instead, confirmed working 2026-09-18:

```bash
sudo bash -c "$(wget -nv -O - https://github.com/wiedehopf/adsb-scripts/raw/master/readsb-install.sh)"
sudo bash -c "$(wget -nv -O - https://raw.githubusercontent.com/wiedehopf/tar1090/master/install.sh)"
```

Both scripts were read in full before running (build readsb from source + a systemd service
reading the RTL-SDR directly via `--device-type rtlsdr`; tar1090 as a lighttpd-served map).
Nothing unusual found.

**readsb is `systemctl-disabled` (2026-10-03).** It was originally `enable`d (active on boot), which
made ADS-B the implicit owner of the single tuner — it crash-looped until the SDR rail powered the
dongle, then grabbed it. Per the owner's decision ([`../docs/logs/decisions.md`](../docs/logs/decisions.md))
the SDR rail is now power-only and ADS-B is one of three mutually-exclusive SDR applications you
choose in the webdash SDR view (ADS-B / broadcast-airband hunt / listen). tar1090 stays enabled —
it is just a web server and serves an empty map until a decoder runs. To apply or confirm:

```bash
sudo systemctl disable --now readsb     # once; stops auto-grab on rail-up
systemctl is-enabled readsb             # -> disabled
```

## Bring-up

Turn the SDR rail on (power only — nothing starts), then pick ADS-B:

```bash
aiov2_ctl SDR on
sdr-swap.sh adsb   # or: sudo systemctl start readsb — only one process can hold the dongle,
                   # see "Single tuner" in ../software/sdr-stack.md. In the dashboard: SDR view -> Start ADS-B.
systemctl status readsb tar1090
```

Open the map: `http://<device-IP>/tar1090` (works over LAN or Tailscale — this build has both).

## Swapping the SDR for other use

`readsb` holds the RTL-SDR continuously once running — `rtl_fm`/`gqrx`/`sdrpp` (see
[`sdr-stack.md`](sdr-stack.md)) can't open it at the same time. Toggle with
[`../configs/sdr/sdr-swap.sh`](../configs/sdr/sdr-swap.sh):

```bash
sdr-swap.sh            # toggle
sdr-swap.sh free        # force SDR freed for rtl_fm/gqrx/sdrpp
sdr-swap.sh adsb        # force ADS-B tracking back on
sdr-swap.sh status      # report only
```

Needs `sudo` unless this scoped rule is installed (matches the same pattern used for
`meshtasticd`, not a blanket sudo grant):

```bash
echo 'wicked5mile ALL=(root) NOPASSWD: /usr/bin/systemctl start readsb, /usr/bin/systemctl stop readsb, /usr/bin/systemctl status readsb' \
  | sudo tee /etc/sudoers.d/020-readsb-wicked5mile
sudo chmod 440 /etc/sudoers.d/020-readsb-wicked5mile
sudo visudo -c
```

Installed on this build, 2026-09-18.

## Antenna is the whole game

RTL-SDR on this board has its own dedicated **bulkhead SMA** port (separate from the `ANT1`–`ANT7`
strip) with a **telescopic whip fitted** (confirmed 2026-09-15) and a 5V bias tee — see
[`../docs/reference/antennas-and-rf-connectors.md`](../docs/reference/antennas-and-rf-connectors.md).
Do not attach a DC-shorted antenna while the bias tee is enabled.

- 1090 MHz ¼-wave ≈ 69 mm; a purpose-built collinear does markedly better.
- Height and line-of-sight beat gain and preamps.
- Indoors near a window is a valid first test; expect tens of km, not hundreds.

## Verification

| Check | Command / place | Expect |
|---|---|---|
| Decoder receiving | `sudo journalctl -u readsb -f` | `Found Rafael Micro R820T tuner` at startup, no repeated errors |
| Aircraft present | `sudo cat /run/readsb/aircraft.json \| python3 -c "import json,sys; print(len(json.load(sys.stdin)['aircraft']))"` | count > 0 when traffic is in range — 0 is not itself a fault, depends on live traffic |
| Map | `http://<device-IP>/tar1090` | targets rendered when present |

Confirmed working end-to-end 2026-09-18: `readsb` claims the same RTL2832U `rtl_test` identifies
(`HackerGadgets, AIO_V2 Ext, SN 25120901`), tar1090 serves correctly.

Log first-light results as a finding under `knowledge/aerospace/findings/`. Not yet done.
