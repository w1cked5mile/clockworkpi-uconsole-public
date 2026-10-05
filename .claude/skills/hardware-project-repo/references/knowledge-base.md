# Knowledge base

A hardware build usually exists to *do* something. `knowledge/` is where the domain understanding
accumulates, separately from the device documentation, so it survives the device.

## Structure

```
knowledge/
  README.md              disciplines index, conventions, legal/safety posture
  _templates/            finding, runbook, config, session-log, and domain-specific templates
  <discipline>/
    README.md            scope + curated upstream links + index of what is here
    learned/             durable understanding — concepts, techniques, limits
    configs/             tool configuration with rationale
    runbooks/            repeatable procedures
    findings/            dated observations
```

## learned/ vs findings/ — keep them apart

- `learned/` is durable: how a thing works, what the limits are, what the arithmetic is. It stays
  true when the device changes.
- `findings/` is dated: what was observed, with equipment, settings, time, and location. It is
  evidence, not understanding.

Mixing them produces a directory that is neither a reference nor a log. When a finding generalizes,
write the generalization into `learned/` and link back to the finding as its evidence.

## findings/ starts empty

Until there is hardware and an observation, `findings/` stays empty. An empty directory is an
honest statement about the state of the project. Do not populate it with hypotheticals.

## Choosing disciplines

Ask what the build is *for* and split by domain, not by tool. Examples:

| Build | Disciplines |
|---|---|
| SDR/RF cyberdeck | rf-fundamentals, sdr, mesh-networks, aerospace, communications, ham-radio, wardriving |
| Home lab | networking, virtualization, storage, observability, backup |
| 3D printing | materials, slicing, calibration, mechanics, post-processing |
| Astrophotography | optics, mounts-and-tracking, capture, processing, targets |
| Drone | airframes, flight-control, rf-links, regulations, photogrammetry |

Four to seven disciplines is usually right. Fewer and it is just a notes folder; more and each one
starves.

## Legal and safety posture

State it once, in `knowledge/README.md`, in terms of what the platform is **for** and what is out
of scope — then let individual documents reference it. Make it specific to the domain: transmit
licensing and interception law for RF; airspace and line-of-sight rules for drones; mains,
lithium, and laser safety for benchtop work; privacy and authorization for anything that observes
other people's systems.

Scope decisions belong in the repo where they can be reviewed, not in the author's head.

## Cross-linking

Tie domain documents back to the device: a runbook that needs a rail powered names the command
that powers it; a limits document names the board that imposes the limit. That link is what makes
the knowledge base usable during a debugging session rather than after one.
