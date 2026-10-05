# aircrack-ng — authorized WPA/WPA2 auditing

Upstream: https://www.aircrack-ng.org/ · installed from Debian trixie's own repos (like Kismet,
no third-party apt repo needed here — unlike Kismet, which does). Installed and verified on this
hardware 2026-09-21: `aircrack-ng` 1.7 (package `1:1.7+git20230807.4bf83f1a-2`).

> **Scope: own network, or a documented written authorization to test — nothing else.** This is
> the one deliberate exception to this repo's passive-only wardriving posture (see
> [`../CLAUDE.md`](../CLAUDE.md) and [`../knowledge/README.md`](../knowledge/README.md)'s
> responsible-use section). Deauth frames and handshake capture are active, not passive — that's
> exactly why they're gated behind ownership/authorization rather than folded into general
> wardriving. If you're not sure a target is in scope, it isn't.

## Install

```bash
sudo apt update
sudo apt install -y aircrack-ng
```

## What it writes

Nothing persistent — `aircrack-ng` is a CLI toolset (`airmon-ng`, `airodump-ng`, `aireplay-ng`,
`aircrack-ng`), no daemon, no config file, no site config the way Kismet or gpsd have one. Capture
files (`.cap`/`.pcap`) and anything derived from cracking (recovered PSKs) are created wherever
you point `airodump-ng -w <prefix>` — **never inside this repo's working tree** even though
`.gitignore` now excludes those extensions as a backstop (`*.cap`, `*.pcap`, `*.pcapng`,
`*.hccapx`, `*.hc22000`).

## Capture source on this build (same adapter as Kismet — see `kismet.md`)

The onboard CM4 Wi-Fi (`brcmfmac`, `wlan0`) has no monitor mode. `wlan1` is a Ralink RT5370 USB
dongle (`rt2800usb`), standing in for the still-pre-order AC1200 — confirmed monitor-capable via
`airmon-ng`:

```bash
sudo airmon-ng            # lists phys/interfaces + chipset; confirms wlan1 (RT5370) here
```

## Verified 2026-09-21

```bash
sudo airmon-ng check kill   # optional — stops NetworkManager/wpa_supplicant/avahi from fighting
                             # the interface; airmon-ng warns about this each run if skipped
sudo airmon-ng start wlan1  # wlan1 -> wlan1mon, monitor mode
sudo airmon-ng stop wlan1mon # back to wlan1, managed mode
```

Confirmed both directions work cleanly on this hardware. One observed quirk: the interface's MAC
address changed by one digit across the stop/restore cycle (`...c4` → `...c5`) — cosmetic, not
investigated further, doesn't affect monitor-mode function.

**Did not run `airmon-ng check kill`** during verification — this build also runs Kismet,
`aiov2_ctl`-managed rails, and Tailscale, and killing `NetworkManager`/`wpa_supplicant` wholesale
would affect those. If a real capture session needs the interface free of interference, kill only
what's actually contending for `wlan1` rather than everything `airmon-ng check` lists.

## Authorized WPA handshake capture — the actual workflow

Only against a network you own or have written authorization to test. The step-by-step version with
expected output, handshake verification and the crack paths is
[`../docs/runbooks/wifi-wpa2-handshake-audit.md`](../docs/runbooks/wifi-wpa2-handshake-audit.md);
the short version:

```bash
sudo airmon-ng start wlan1
sudo airodump-ng wlan1mon                              # survey — find the target BSSID/channel
sudo airodump-ng -c <channel> --bssid <BSSID> -w capture wlan1mon
# in a second shell, if you need to force a handshake and have authorization to deauth:
#   sudo aireplay-ng --deauth 3 -a <BSSID> -c <CLIENT-MAC> wlan1mon   # targeted at a client you own
aircrack-ng -w <wordlist> capture-01.cap                # crack, against your own wordlist
sudo airmon-ng stop wlan1mon
```

Move `capture-*.cap` files and anything cracked off the device to storage you control — they
contain the target network's real traffic and, if cracking succeeds, its actual password.

## GPU crack-offload

Fancy is CPU-only and slow; the real crack runs on a GPU host on the tailnet. The standing host is
`gpu-host-wsl` (a Kali/WSL tailnet node, RTX 3070 Ti) — one-time setup in
[`../docs/reference/gpu-crack-offload-host.md`](../docs/reference/gpu-crack-offload-host.md).
[`crack-offload.sh`](crack-offload.sh) automates the whole hop (reachability check → copy → convert
→ `hashcat -m 22000`):

```bash
CRACK_HOST=gpu-host-wsl ~/labs/wpa/crack-offload.sh ~/labs/wpa/handshake-01.cap
```

## From the webdash (authorized allowlist + capture pipeline)

Added 2026-10-01. The webdash Wi-Fi view can run the capture half of this workflow — **gated to an
authorized-equipment allowlist**, enforced on the host, not just in the browser. Full design in
[`../docs/reference/webdash-architecture.md`](../docs/reference/webdash-architecture.md)'s "WPA audit"
section; the short version:

- **Allowlist:** you type a BSSID into the Wi-Fi view with an authorization basis (own gear or an
  engagement ref). Active auditing can only ever target a BSSID on this list; keyed on BSSID
  (hardware), since SSIDs are spoofable. Stored outside git.
- **Capture:** pick an allowlisted BSSID → the host runs monitor mode, a channel scan, a **bounded,
  targeted deauth** (a few frames × a few rounds — never a continuous flood/DoS), and handshake
  detection, then restores the radio. Kismet is paused during capture. Captures land in gitignored
  `~/labs/wpa`.
- **Enforcement:** the `wpa-audit-bridge` and the root capture script **both** re-check the BSSID
  against the allowlist before any RF.

One-time host install (owner-authorized; it adds a scoped `sudoers` entry and a service):

```bash
cd ~/clockworkpi-uconsole/webdash
sudo install -m0755 -o root -g root host-helpers/wpa-capture.sh /usr/local/sbin/uconsole-wpa-capture.sh
sudo install -m0440 -o root -g root host-helpers/wpa-capture.sudoers /etc/sudoers.d/webdash-wpa-capture
sudo visudo -cf /etc/sudoers.d/webdash-wpa-capture
sudo cp host-helpers/wpa-audit-bridge.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now wpa-audit-bridge.service
```

- **Crack (2026-10-01):** once a handshake is captured, a **Send to gpu-host (crack)** button
  offloads it to the GPU host — the [crack-offload](#gpu-crack-offload) above, run by the bridge and
  streamed back as progress → result. The dashboard only lets you crack a `wpa-*.cap` it captured
  (the bridge re-validates the path). The recovered PSK is shown in the session and **never
  persisted** (held in the bridge's memory, not written to a file or the audit log). Needs
  `gpu-host-wsl` online.

## Manual fallback / troubleshooting

```bash
iw dev                                       # confirm interface names haven't shifted
iw phy | grep -A3 'Supported interface modes'  # re-confirm monitor mode support
rfkill list                                   # confirm nothing is soft/hard blocked
```
