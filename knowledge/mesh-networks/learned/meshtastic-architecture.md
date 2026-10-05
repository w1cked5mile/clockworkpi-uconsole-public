# Meshtastic architecture

What the pieces are, so configuration choices are deliberate rather than copied.

## Nodes and roles

Each node is a radio plus a small controller that participates in a flooding mesh. Roles change
how a node forwards traffic:

| Role | Behavior | Use |
|---|---|---|
| CLIENT | Normal participant; relays | Default — what this build uses |
| CLIENT_MUTE | Participates but does not relay | Dense areas where extra relays add noise |
| ROUTER | Prioritizes relaying, sleeps less | Fixed, well-sited nodes only |
| TRACKER / SENSOR | Periodic position/telemetry | Battery-focused deployments |

Choosing ROUTER for a handheld device that moves and sleeps degrades the mesh — it advertises
relay capability it cannot honor.

## Channels and encryption

- A **channel** is a name plus a pre-shared key plus radio settings.
- The default `LongFast` channel uses a **publicly known key**: traffic on it is effectively public.
- A private mesh needs a generated PSK shared out-of-band with the other operators:
  `meshtastic --ch-set psk random --ch-index 0`
- Primary channel settings must match across all nodes; secondary channels can differ.

**Never commit a PSK to this repo** (see [`../../../CLAUDE.md`](../../../CLAUDE.md)).

### How the channel name picks the frequency

Meshtastic doesn't let you choose a frequency directly. It divides the region's band into slots
one preset-bandwidth wide and picks one by hashing the **primary channel's name** (the djb2 string
hash, modulo the number of slots). In the US band with a 250 kHz preset:

```text
slot      = (channel_num set by hand ? channel_num − 1 : djb2(name)) mod 104
frequency = 902.0 MHz + frequency_offset + bw/2 + slot × bw
```

104 slots and the 0.125 MHz half-width hold for the 250 kHz presets such as LONG_FAST.

| Primary name | Slot (journal, from 0) | App's "frequency slot" (from 1) | Frequency |
|---|---|---|---|
| unnamed / `LongFast` | 19 | 20 | 906.875 MHz |
| `NCMesh` | 59 | 60 | 916.875 MHz |
| `SCMesh` | 88 | 89 | 924.125 MHz |

Recomputed 2026-09-25 (senior-rf-engineer review) and matching the `ch=` value meshtasticd logs.
The formula is as in upstream firmware (`RadioInterface.cpp`); it has not been diffed against the
installed meshtasticd version. Two nodes whose primary names differ usually land on different
slots (about 1 in 104 pairs collide) and then never hear each other, whatever their keys.

## Routing

Meshtastic floods with a hop limit (default 3). Each node rebroadcasts once, with delays to reduce
collisions. There is no route discovery and no guaranteed delivery — it is a best-effort mesh, and
raising the hop limit multiplies airtime rather than reliably extending reach.

## Position and privacy

Position sharing broadcasts coordinates to every node in range, including nodes you do not
control, and — if any node bridges to MQTT — potentially to a public map.

The staged config in [`../../../configs/meshtastic/us915.yaml`](../../../configs/meshtastic/us915.yaml)
keeps `gps_enabled: false` deliberately. Enable it as a conscious choice when mobile, not as a default
at home.

## MQTT bridging

Nodes can bridge mesh traffic to an MQTT broker, which extends reach over the internet and, on the
public broker, publishes your traffic and position. Treat enabling it as publishing, not as a
connectivity tweak.

## Interfaces on this build

| Interface | Notes |
|---|---|
| `meshtastic` CLI | Configuration, info, message send/receive; scriptable |
| `meshtastic-mui` | GUI installed by `aiov2_ctl --add-apps` |
| SPI to SX1262 | `/dev/spidev1.0` — needs `dtoverlay=spi1-1cs` and no `devterm-printer` holding SPI1 |

Setup: [`../../../software/meshtastic.md`](../../../software/meshtastic.md).
