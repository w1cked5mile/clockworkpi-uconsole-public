# Ham radio — reference index

Amateur radio: licensing, band plans, digital modes, APRS, and amateur satellites.

> **Transmitting on amateur bands requires a license.** Receive freely; transmit only within your license class, band plan, and power limits. LoRa/ISM experiments (see mesh-networks) are separate and license-free within their limits.

## Licensing & band plans

| Resource | Link |
|---|---|
| ARRL (US national association) | https://www.arrl.org/ |
| ARRL band plan | https://www.arrl.org/band-plan |
| HamStudy (exam prep) | https://hamstudy.org/ |
| Awesome-hamradio (curated) | https://github.com/DD5HT/awesome-hamradio |

## Digital modes & software

| Mode / tool | Role | Link |
|---|---|---|
| WSJT-X | FT8/FT4/JT65 weak-signal | https://wsjt.sourceforge.io/ |
| JS8Call | Keyboard messaging over FT8-like | http://js8call.com/ |
| fldigi | Multi-mode digital (PSK31, RTTY, …) | http://www.w1hkj.com/ |
| Direwolf | Software TNC — APRS / packet | https://github.com/wb2osz/direwolf |

## APRS, propagation, logging

| Resource | Use | Link |
|---|---|---|
| APRS.fi | Live APRS map | https://aprs.fi/ |
| PSK Reporter | Who's hearing whom (propagation) | https://pskreporter.info/ |
| QRZ.com | Callsign lookup / logbook | https://www.qrz.com/ |
| CQRLOG / Cloudlog | Logging | https://www.cqrlog.com/ |

## Amateur satellites

| Resource | Link |
|---|---|
| AMSAT | https://www.amsat.org/ |
| Gpredict (pass prediction) | https://github.com/csete/gpredict |
| SatNOGS | https://satnogs.org/ |

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| ARRL — Grid squares | Maidenhead locator structure; the only location format this repo commits (B9) | https://www.arrl.org/grid-squares | 200 on 2026-09-24 |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/licensing-path-us.md`](learned/licensing-path-us.md) | Technician/General/Extra, exams, what a license adds here |
| [`learned/band-plans-and-privileges.md`](learned/band-plans-and-privileges.md) | 2 m / 70 cm segments, repeater offsets, HF out of scope |
| [`learned/digital-modes-and-aprs.md`](learned/digital-modes-and-aprs.md) | APRS, FT8/WSPR, satellites — receive-only participation |
| [`configs/local-repeaters-and-memories.md`](configs/local-repeaters-and-memories.md) | Repeater and fixed-memory working list |
| [`runbooks/vhf-uhf-monitoring-and-satellite-pass.md`](runbooks/vhf-uhf-monitoring-and-satellite-pass.md) | Repeaters + APRS, then a satellite pass |

## Capture here

`learned/` mode/propagation notes + license progress, `configs/` WSJT-X/Direwolf/rig configs, `runbooks/` "decode FT8 with the RTL-SDR", "run an APRS iGate", `findings/` contacts, propagation observations, satellite passes.
