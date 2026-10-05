# Communications — reference index

Terrestrial and maritime voice/data signals: digital voice, trunking, paging, AIS, and broadcast. Mostly receive/decode.

> **Legal note.** Receiving is broadly permitted, but some jurisdictions (e.g. US, under ECPA) restrict **decoding or divulging** certain private/encrypted communications. Do not decode or share protected traffic. Encrypted public-safety systems are off-limits to decode regardless.

## Digital voice & trunking

| System | Tool | Link |
|---|---|---|
| P25 | OP25 | https://github.com/boatbod/op25 |
| DMR / dPMR / NXDN / others | DSD-FME | https://github.com/lwvmobile/dsd-fme |
| Trunk following + recording | trunk-recorder | https://github.com/robotastic/trunk-recorder |
| TETRA | tetra-kit | https://github.com/larryth/tetra-kit |
| System/frequency lookup | RadioReference | https://www.radioreference.com/ |

## Paging, marine, broadcast

| Signal | Tool | Link |
|---|---|---|
| POCSAG / FLEX paging | multimon-ng | https://github.com/EliasOenal/multimon-ng |
| AIS (marine, 161.975/162.025 MHz) | rtl-ais / AIS-catcher | https://github.com/jvde-github/AIS-catcher |
| FM broadcast + RDS | redsea | https://github.com/windytan/redsea |
| DAB/DAB+ | welle.io | https://www.welle.io/ |
| Signal identification | sigidwiki | https://www.sigidwiki.com/ |

## Workflow

- Find frequency (RadioReference) → confirm mode (sigidwiki) → decode with the matching tool.
- Note which systems in your area are encrypted (do not attempt to decode).

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| ITU-R M.1371 — AIS technical characteristics | GMSK 9600 bit/s and SOTDMA access (B8) | https://www.itu.int/rec/R-REC-M.1371 | 200 on 2026-09-24 |
| ETSI TS 102 361-1 — DMR air interface | Two-slot TDMA structure (B8) | — | title only; URL not confirmed |
| TAPR — APRS / AX.25 references | AX.25 framing, 1200-baud Bell 202 AFSK (B8) | https://www.tapr.org/ | 200 on 2026-09-24 |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/digital-voice-and-trunking.md`](learned/digital-voice-and-trunking.md) | DMR/P25/NXDN, control channels, legal boundaries |
| [`learned/ais-and-maritime.md`](learned/ais-and-maritime.md) | AIS channels, message types, receiving (coastal only) |
| [`configs/monitoring-frequency-list.md`](configs/monitoring-frequency-list.md) | Local active-frequency list and reference frequencies |
| [`runbooks/scanner-monitoring-session.md`](runbooks/scanner-monitoring-session.md) | Sweep, classify, log without capturing content |

## Capture here

`learned/` mode/protocol notes, `configs/` decoder configs + local frequency lists, `runbooks/` "decode POCSAG", "receive AIS", `findings/` logs (respect the legal note — aggregate/technical, not personal content).
