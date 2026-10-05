# Meshtastic configuration baseline

The applied configuration lives at
[`../../../configs/meshtastic/us915.yaml`](../../../configs/meshtastic/us915.yaml); this file
records *why* each choice was made and what to capture after applying it.

## Choices and rationale

| Setting | Value | Why |
|---|---|---|
| `region` | US | your location — 902–928 MHz. Software setting on this hardware. |
| `modem_preset` | LONG_FAST | Meshtastic default and what most local meshes run; interoperability beats tuning. |
| `hop_limit` | 3 | Default. Raising it multiplies airtime without reliably adding reach. |
| `role` | CLIENT | The device is portable and sleeps; advertising ROUTER would degrade the mesh. |
| `position.gps_enabled` | false | Broadcasting a home fix is a privacy decision, not a default. |
| `tx_power` | unset | Region default; the SX1262 is rated to 22 dBm. |

## After applying

```bash
meshtastic --configure ../../../configs/meshtastic/us915.yaml
meshtastic --export-config > ../../../configs/meshtastic/as-applied.yaml   # strip any PSK first
meshtastic --info
```

Record in `../findings/`:

- [ ] Firmware version reported by `--info`
- [ ] Region, preset, and hop limit as actually applied
- [ ] Node ID / short name
- [ ] Nodes visible at the baseline location

## Do not commit

PSKs, private channel URLs (`meshtastic --info` prints a channel URL that **encodes the key**),
or exported configs containing either. Scrub before saving an as-applied export.

## Interoperability checklist

Before blaming hardware when a node cannot see the mesh:

- [ ] Same region
- [ ] Same modem preset
- [ ] Same primary channel name **and** PSK
- [ ] Frequency slot not manually overridden on one node
