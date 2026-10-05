# Knowledge base — RF exploration platform

Reference indexes and a documenting structure for exploring radio-frequency signals across seven disciplines, using this uConsole build (RTL-SDR / LoRa / GPS / RTC via the AIO V2, plus Wi-Fi/BT).

## Disciplines

| Discipline | Scope | Index |
|---|---|---|
| RF fundamentals | Cross-cutting theory, DSP, antennas, signal ID, safety, regs | [rf-fundamentals/](rf-fundamentals/README.md) |
| SDR | Software-defined radio: software, hardware, workflows | [sdr/](sdr/README.md) |
| Mesh networks | LoRa mesh — Meshtastic, Reticulum, MeshCore | [mesh-networks/](mesh-networks/README.md) |
| Wardriving | Wi-Fi/BT survey + geolocation (observe, don't intrude) | [wardriving/](wardriving/README.md) |
| Aerospace | ADS-B, ACARS/VDL/HFDL, weather sats, satellites | [aerospace/](aerospace/README.md) |
| Communications | Digital voice/data, paging, AIS, trunking, broadcast | [communications/](communications/README.md) |
| Ham radio | Licensing, band plans, digital modes, APRS, sat | [ham-radio/](ham-radio/README.md) |

## How each discipline folder is organized

```
<discipline>/
  README.md     reference index + scope (curated links)
  learned/      concepts/techniques/lessons (durable understanding)
  configs/      tool configs + notes (tool, version, device path)
  runbooks/     repeatable step-by-step procedures
  findings/     logged observations, captures, signal IDs
```

Populated so far (see each discipline index for the full list):

| Discipline | learned | configs | runbooks | findings |
|---|---|---|---|---|
| RF fundamentals | 7 | 1 | 1 | — |
| SDR | 2 | 1 | 1 | — |
| Mesh networks | 2 | 1 | 1 | — |
| Wardriving | 2 | 1 | 2 | — |
| Aerospace | 2 | 1 | 2 | — |
| Communications | 2 | 1 | 1 | — |
| Ham radio | 3 | 1 | 1 | — |

`findings/` stays empty until the hardware is in hand — findings are dated observations, and there
is nothing to observe yet. Everything above is hardware-independent or explicitly marked as
unverified against this build.

Capture templates live in [`_templates/`](_templates/): `finding.md`, `runbook.md`, `config.md`, `session-log.md`, `signal-id.md`. Copy one rather than starting blank so entries stay consistent and searchable.

## Conventions

- Timestamps in **UTC**. Record **general** location only (city / Maidenhead grid) — never precise home coordinates.
- Cite upstream docs in runbooks and mark version-dependent steps "verify before running."
- Never commit secrets, keys, captured credentials, or precise private locations. `.gitignore` excludes raw IQ (`*.iq`, `*.cf32`, `*.cs8`, `*.cu8`, `*.sigmf-data`) and Kismet logs (`*.kismet`, `*.kismetdb`), and lab outputs (`*.wav`, `*.csv`, `*.raw`, `*.kismet-journal`, added 2026-09-24) — still write those outside the repo (e.g. `~/labs/`) or use LFS.
- Cross-link related entries with relative links; tie hardware specifics back to [`../docs/`](../docs/).

## Platform references (Linux, access, power)

Not an RF discipline, so kept here. Added 2026-09-24 for the learning platform's platform gap
modules (P1…P8) — see [`../docs/reference/learning-platform-plan.md`](../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| systemd man pages (man7 mirror): `systemd.unit(5)`, `systemctl(1)`, `journalctl(1)` | Unit states, enable vs mask, restart loops (P1) | https://man7.org/linux/man-pages/man5/systemd.unit.5.html | 200 on 2026-09-24 |
| man7: `udev(7)`, `modprobe.d(5)` | Rule syntax, driver blacklisting (P2) | https://man7.org/linux/man-pages/man7/udev.7.html | 200 on 2026-09-24 |
| Raspberry Pi — `config.txt` | `dtparam`/`dtoverlay`, UART and serial console (P3, P4) | https://www.raspberrypi.com/documentation/computers/config_txt.html | blocks scripted checks; confirm in a browser |
| Raspberry Pi — configuration (device trees, overlays) | What an overlay adds (P3) | https://www.raspberrypi.com/documentation/computers/configuration.html | blocks scripted checks; confirm in a browser |
| Raspberry Pi — OS docs (`vcgencmd get_throttled`) | Throttle bit meanings (P8) | https://www.raspberrypi.com/documentation/computers/os.html | blocks scripted checks; confirm in a browser |
| Linux kernel — spidev | What `/dev/spidev1.0` is (P4) | https://www.kernel.org/doc/html/latest/spi/spidev.html | 200 on 2026-09-24 |
| Docker — overview; Compose | Image, container, bind mount, host networking (P5) | https://docs.docker.com/get-started/docker-overview/ | 200 on 2026-09-24 |
| Tailscale — `tailscale serve` | Tailnet-only serving vs Funnel (P6) | https://tailscale.com/kb/1312/serve | 200 on 2026-09-24 |
| WireGuard whitepaper | Key-based peer identity under Tailscale (P6) | https://www.wireguard.com/papers/wireguard.pdf | 200 on 2026-09-24 |
| IETF RFC 6238 (TOTP) | 30 s step, clock-skew tolerance (P7) | https://datatracker.ietf.org/doc/html/rfc6238 | 200 on 2026-09-24 |
| NIST SP 800-63B | Authenticator guidance (P7) | https://pages.nist.gov/800-63-4/sp800-63b.html | 200 on 2026-09-24 |
| linux-sunxi — AXP PMICs | AXP family and sysfs `power_supply` readings (P8) | https://linux-sunxi.org/AXP_PMICs | 200 on 2026-09-24 |
| Battery University (secondary, educational) | Li-ion series/parallel, capacity, safety basics (P8) | https://batteryuniversity.com/ | 200 on 2026-09-24 |

## Responsible / legal use

This platform is for **receiving, learning, and licensed transmitting**. Rules vary by country — confirm your local regulations.

- **Receive-only is broadly legal** (ADS-B, weather sats, broadcast). Some jurisdictions restrict decoding/divulging certain communications (e.g. US ECPA); do not decode or share protected/private/encrypted traffic.
- **Transmitting** (ham bands, some experiments) requires the appropriate license and band/power/duty-cycle compliance. LoRa/ISM (US 902–928 MHz) is license-free within its limits; **amateur bands require an amateur license**.
- **Wardriving** here means **passive observation** of broadcast Wi-Fi/BT beacons and their positions (WiGLE-style). Do not associate with, deauth, capture handshakes from, or crack networks you don't own or lack written authorization to test.
- **WPA/WPA2 auditing** (`aircrack-ng`, installed 2026-09-21 — [`../software/aircrack-ng.md`](../software/aircrack-ng.md)) is the one deliberate exception to passive-only, and it's narrow: **own network or documented written authorization, nothing else.** Deauth frames and handshake capture are active/intrusive by nature — that's exactly why they're gated behind ownership/authorization rather than folded into general wardriving. Captured handshakes (`.cap`/`.pcap`) and anything derived from cracking (recovered PSKs) are secrets — never commit them; see [`../.gitignore`](../.gitignore).
- Respect privacy; don't target individuals.

## Platform tie-in

- SDR RX: AIO V2 RTL-SDR (RTL2832U + R860, 100 kHz–1.74 GHz) — `aiov2_ctl SDR on`.
- LoRa mesh: AIO V2 SX1262 (860–960 MHz) — `aiov2_ctl LORA on`.
- GPS/RTC: AIO V2 (timestamping, wardriving geotags) — `aiov2_ctl GPS on`.
- Wi-Fi/BT: onboard + optional AC1200 (MT7921, monitor mode).
- See [`../docs/runbooks/software-install.md`](../docs/runbooks/software-install.md) and [`../docs/documentation-index.md`](../docs/documentation-index.md).
