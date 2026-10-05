---
id: M4.channels
title: Channels, keys and frequency slots
est_minutes: 25
---

@ref knowledge/mesh-networks/learned/meshtastic-architecture.md#channels-and-encryption

> **Don't run the `--ch-set psk` command above on Fancy.** It would change the primary channel's
> pre-shared key (PSK) and cut Fancy off from the owner's nodes — and the meshtastic CLI also
> drops webdash's connection while it runs.

Fancy's SCMesh primary uses the public default key, `AQ==`, so anyone on SCMesh can read what
Fancy sends. Never put location or anything private in a message.

In the US band, Meshtastic hashes the **primary channel's name** to pick a frequency slot. The
journal counts slots from 0; the Meshtastic app shows them one higher. Unnamed or `LongFast` is
index 19 (the app's slot 20), 906.875 MHz; `SCMesh` is index 88 (slot 89), 924.125 MHz; `NCMesh`
is index 59 (slot 60), 916.875 MHz. Secondary channels share the primary's frequency. Nodes on
different slots can't hear each other at all, whatever their keys.

That is exactly why this node heard nothing until 2026-09-23: its primary was LongFast while the
owner's nodes used SCMesh. The journal line that settles it:

```bash
journalctl -u meshtasticd | grep "Set radio"
```

Fancy's channels right now: {live:mesh.channels}.
