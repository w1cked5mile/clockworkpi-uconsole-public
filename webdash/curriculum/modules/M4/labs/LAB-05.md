---
id: LAB-05
title: Meet your node
themed_title: Sea trial · Know your own radio
mode: observe
est_minutes: 10
requires: {rails: [LORA], services: [meshtasticd]}
transmits: false
steps:
  - id: rail
    text: "The LORA rail is on."
    check: {type: status, path: aiov2.rails.LORA.on, op: eq, value: true}
  - id: running
    text: "webdash is connected to meshtasticd."
    check: {type: status, path: mesh.state, op: eq, value: running}
  - id: node
    text: "The node reports its ID."
    check: {type: status, path: mesh.node_id, op: exists}
  - id: primary
    text: "SCMesh is among the node's channels."
    check: {type: status, path: mesh.channels, op: contains, value: SCMesh}
  - id: slot
    text: 'Run journalctl -u meshtasticd | grep "Set radio" | tail -1 and paste it. It should show region US and the SCMesh slot, ch=88.'
    check: {type: paste, parser: regex, pattern: 'Set radio: region=US, name=SCMesh, .*ch=88', min_matches: 1}
restore:
  - {type: status, path: aiov2.rails.LORA.on, op: eq, value: true}
evidence: [mesh.nodes_seen]
---

Read-only. Don't use `meshtastic --info` for this: it would drop webdash's connection to
meshtasticd, which serves one client at a time.

The line ends with `power=30`. That is the US region's limit in dBm, not what the radio sends:
the SX1262 driver caps output at 22 dBm, about 160 mW (the cap is *unverified* against the
installed meshtasticd version). What actually leaves the antenna also depends on the antenna.
