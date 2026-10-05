# Mesh networks — reference index

Long-range, low-power mesh over LoRa and related stacks. On this build: AIO V2 SX1262 (860–960 MHz), `aiov2_ctl LORA on`, with `meshtastic-mui` installed by `aiov2_ctl --add-apps`.

## Stacks

| Stack | What it is | Link |
|---|---|---|
| Meshtastic | LoRa mesh text/position; large ecosystem; SX1262 | https://meshtastic.org/ · docs: https://meshtastic.org/docs/ |
| Reticulum (RNS) | Cryptographic networking stack over any medium (LoRa, packet, TCP) | https://reticulum.network/ |
| Nomad Network / Sideband | Reticulum apps (messaging, pages) | https://github.com/markqvist/NomadNet |
| MeshCore | Lightweight LoRa mesh firmware alternative | https://github.com/meshcore-dev/MeshCore |
| LoRaWAN / The Things Network | Star-of-stars IoT (contrast to peer mesh) | https://www.thethingsnetwork.org/ |

## Underlying tech

- LoRa PHY: Semtech SX126x — https://www.semtech.com/products/wireless-rf/lora-connect
- Modulation: CSS (chirp spread spectrum); spreading factor vs. range/airtime trade-off.
- Regional params + **duty-cycle / band rules** (US 902–928 ISM, EU 868): https://meshtastic.org/docs/configuration/region-by-country/

## Meshtastic on this build

- Set the correct **region** before TX. Firmware/clients: https://meshtastic.org/docs/software/
- `meshtastic` CLI / `meshtastic-mui` GUI for config and messaging.

## Learning-platform references

Added 2026-09-24 to cover concepts the repo uses but does not yet explain; the gap IDs (B1…) are
defined in [`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md).
"Checked" is an HTTP reachability check only, not a review of the content.

| Resource | Supports | Link | Checked |
|---|---|---|---|
| Meshtastic — mesh broadcast algorithm | SNR-based rebroadcast delay, hops, channel utilisation behaviour (B5) | https://meshtastic.org/docs/overview/mesh-algo/ | 200 on 2026-09-24 |
| Meshtastic — LoRa configuration | Presets, hop limit, region (B5) | https://meshtastic.org/docs/configuration/radio/lora/ | 200 on 2026-09-24 |
| Semtech AN1200.22 — LoRa Modulation Basics | Processing gain; why SNR can be negative (B5) | — | title only; URL not confirmed |

## In this discipline

| Document | Contents |
|---|---|
| [`learned/lora-modulation-and-airtime.md`](learned/lora-modulation-and-airtime.md) | CSS, spreading factors, airtime, range expectations |
| [`learned/meshtastic-architecture.md`](learned/meshtastic-architecture.md) | Roles, channels/PSKs, flooding, MQTT, privacy |
| [`configs/meshtastic-baseline.md`](configs/meshtastic-baseline.md) | Why each setting in the staged US915 config |
| [`runbooks/node-bringup-and-range-test.md`](runbooks/node-bringup-and-range-test.md) | Bring-up, then a two-node range measurement |

## Capture here

`learned/` LoRa/mesh concepts, `configs/` node/channel/region configs (no PSKs in git), `runbooks/` bring-up + range tests, `findings/` range/coverage results and node logs.
