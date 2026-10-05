# Runbook — passive Wi-Fi survey session

A repeatable mobile survey: observe broadcast beacons and probe frames with position tagging,
then produce a finding that contains no personal data.

**Passive only.** No association, deauth, handshake capture, or cracking.

## Preconditions

- [ ] A monitor-capable adapter recognized: the **AC1200** (MediaTek MT7921AUN, `mt7921u`) on the
      AIO V2's internal USB-C port, which needs the USB rail on (`aiov2_ctl USB on`). Verified
      2026-09-30 as `wlan1` with monitor mode on 2.4/5/6 GHz. (The **RT5370**, 2.4 GHz only, was the
      external-USB stand-in before it arrived; removed.) Never `wlan0`: it has no monitor mode and
      is Fancy's network link
- [ ] NetworkManager manages only the onboard radio, so it never joins networks or scans
      actively (sends probe requests) with a survey adapter. Deployed 2026-09-25 as
      `/etc/NetworkManager/conf.d/wifi-onboard-only.conf`
      ([`../../../configs/networkmanager/wifi-onboard-only.conf`](../../../configs/networkmanager/wifi-onboard-only.conf);
      matches every Wi-Fi driver except `brcmfmac`). With the adapter in,
      `nmcli -t dev | grep wlan1` shows `unmanaged` — the survey adapter (now the AC1200, `mt7921u`) shows `wlan1:wifi:unmanaged:` and `wlan0` keeps the only default route (rule verified 2026-09-25)
- [ ] `iw dev` shows the adapter's interface (`wlan1` for the AC1200; if the RT5370 is ever refitted
      alongside it the names may differ) and it matches `source=` in `/etc/kismet/kismet_site.conf`
- [ ] Before state recorded: `iw dev` lists no monitor interface; `wlan0` is `type managed`
- [ ] gpsd running with a 3D fix ([`../../../software/gps.md`](../../../software/gps.md))
- [ ] Kismet configured ([`../configs/kismet-passive-survey.md`](../configs/kismet-passive-survey.md))
- [ ] Log destination outside the repo, with free space
- [ ] Battery charged — this is one of the heaviest power profiles on the device
      ([`../../../docs/reference/power-budget.md`](../../../docs/reference/power-budget.md))

## Procedure

### 1. Pre-flight (stationary, 5 minutes)

```bash
aiov2_ctl GPS on
cgps -s                      # wait for a 3D fix before moving
iw dev                       # confirm interface name
sg kismet -c 'kismet --no-ncurses-wrapper'   # foreground; web UI http://localhost:2501
```

Run Kismet in the foreground as above, not as the service (it crash-looped until 2026-09-25;
a start after the fix is not yet re-tested — see
[`../../../software/kismet.md`](../../../software/kismet.md#running)). Kismet adds a separate
monitor interface, `wlan1mon`, next to `wlan1`; `wlan1` itself stays managed. Use `localhost:2501`, not
the tailnet address. In Kismet's Data Sources page, **do not enable `hci0`** — Bluetooth
discovery scans actively.

- [ ] Fix acquired, satellites ≥ 4
- [ ] Kismet shows the GPS as connected and networks appearing

### 2. Survey

- Move at a steady pace; slower gives more frames per location.
- Do not change channel configuration mid-session — it makes the data incomparable.
- Note start/end UTC times and the general area covered (neighbourhood, not addresses).

### 3. Close out

- [ ] Stop Kismet cleanly (Ctrl-C in its terminal) so the log finalizes
- [ ] `aiov2_ctl GPS off` and radios off to save battery
- [ ] Leave the log in `~/kismet-logs/` until the finding is written, then delete it (below)

### 4. Verify the restore

Kismet leaves `wlan1mon` behind even after a clean exit (seen 2026-09-25), so remove it first:

```bash
sudo iw dev wlan1mon del              # "No such device" is fine: it's already gone
iw dev | grep -E 'Interface|type'     # wlan1 (or your adapter) "type managed"; no *mon interface
iw dev | grep -c 'type monitor'       # expect 0
iw dev wlan0 info | grep type         # expect "type managed" — wlan0 was never touched
systemctl is-active kismet            # expect "inactive" (or "failed"); if not: sudo systemctl stop kismet
```

- [ ] Adapter back in managed mode, no monitor interface left
- [ ] `wlan0` still managed and connected
- [ ] `kismet.service` not running

## Record a finding

Copy [`../../_templates/finding.md`](../../_templates/finding.md) into `../findings/` as
`<YYYY-MM-DD>-wifi-survey.md` (UTC date) with:

| Field | Example |
|---|---|
| Date / time (UTC) | 2026-09-20T18:00Z – 19:15Z |
| General area | grid square (or city), e.g. EM95 |
| Equipment | AC1200 (MT7921AUN, `mt7921u`), its IPEX antennas, AIO GNSS |
| Channels | the bands/channels you hopped, 5 hops/sec (the AC1200 covers 2.4/5/6 GHz) |
| Networks observed | count |
| Security mix | WPA3 / WPA2 / open counts |
| Notable technical observations | channel congestion, unusual beacon intervals, 5/6 GHz utilization |

**Do not include** SSID/MAC lists, device tracks, precise coordinates, or anything identifying a
household or person, and never upload the log to WiGLE or any map — that publishes BSSIDs, SSIDs
and coordinates. Once the finding is written, delete this run's log; it holds every address heard
and, with a GPS fix, where:

```bash
rm ~/kismet-logs/uconsole-*.kismet*
```

## Interpretation

- Congestion on 1/6/11 versus 5 GHz utilization is the most useful practical output.
- Open networks are an observation, not an invitation — do not connect.
- Probe-request counts overstate unique devices because of MAC randomization
  ([`../learned/wifi-capture-fundamentals.md`](../learned/wifi-capture-fundamentals.md)).

## Legal

Passive reception of broadcast frames. Do not attempt access, interference, or decryption of any
network you do not own or have written authorization to test.
