# Research playbook

How to source facts for a hardware repository, in priority order, and how to record what you could
not source.

## Source hierarchy

1. **Silicon datasheets** — the chip vendor's PDF. Authoritative for electrical, thermal,
   mechanical, and interface facts.
2. **Upstream source code and repositories** — schematics, device-tree overlays, and the vendor's
   own control software. Often *more* accurate than the vendor's documentation.
3. **Official documentation and wikis** — good for procedures, weaker for exact values.
4. **Vendor product pages** — marketing copy. Useful for what is in the box and which variant was
   ordered; treat specifications as claims.
5. **Community forums** — frequently the only source for real-world gotchas (board revisions
   needing a reseat, packages that fail to install, undocumented conflicts). Keep them, always with
   the thread link and a verify marker.

## Read the vendor's control software

This is the highest-yield move in the whole method and it is routinely skipped.

If a board ships a CLI, tray app, or install script, read its source. In the reference build, the
GPIO map, the boot defaults, and the complete command surface all came from the upstream Python —
and one boot default contradicted both the vendor guide and the repo's own scaffold assumption.

Look for: pin maps, boot defaults, the files an installer writes (systemd units, config paths),
undocumented subcommands, and the sysfs paths it reads for telemetry.

## When a source is unreachable

Network egress is often restricted. This is a fact to record, not to work around:

- Say which sources were reachable and which were not.
- Mark every claim that depends on an unreachable source as *verify at inventory*.
- Never let an unreachable page become an implied confirmation.

A constrained environment tends to improve sourcing discipline, because nothing can be silently
"confirmed" by a page that might have changed.

## What to extract per component

| Extract | Into |
|---|---|
| Chipset, interfaces, rated ranges | `hardware/specs/<board>.md` |
| Pin maps, overlays, boot defaults | `docs/reference/pinout-gpio.md` (or equivalent) |
| Dimensions, clearances, fasteners | `hardware/mechanical.md` |
| Datasheet and schematic links | `hardware/datasheets/README.md` |
| Known failure modes and workarounds | `docs/logs/known-issues.md` |
| Exact commands, install paths, unit files | `software/<app>.md` |

## Practical limits are as valuable as specifications

A specification says what the part can do. A practical limit says what it will do in this build:
shared-bus bandwidth caps, ADC dynamic range, thermal throttling under a sealed shell, a tuner's
usable low-frequency end. Write the limit next to the specification — it is what prevents a
support session six months later.

## Agent-specific caution

You will be tempted to fill a gap with a plausible number. Do not. An empty cell marked
*unverified* is more useful than a confident wrong one, because the empty cell gets measured and
the wrong one gets quoted.
