---
name: hardware-project-repo
description: Scaffold and drive a documentation-first hardware project repository — directory structure, sourced spec sheets, staged configuration files, bring-up acceptance checklists, budgets, order records, and a knowledge base — then create it on GitHub. Use this whenever the user is starting, documenting, or organizing a physical build (SBC, SDR, drone, 3D printer, homelab, robot, sensor rig, cyberdeck, retro console, ham/RF gear, PCB project), when they mention parts on order or in transit, a BOM, bring-up, assembly, or wiring, when they ask how to structure a repo for hardware, or when they want work done on a build before the parts arrive. Also use it to bring an existing hardware repo up to this standard.
---

# Documentation-first hardware project repository

## The idea

The deliverable of a hardware build is not the hardware. It is the reproducible description: a
repository that lets someone else — or the user in six months — rebuild, debug, and hand off the
device. Most hardware projects fail at the seams: the part that was "included" and wasn't, the
setting that worked once on a 2023 forum post, the measurement nobody wrote down.

Two things make this work, and both are counterintuitive:

1. **Shipping time is engineering time.** Nearly everything except touching the hardware can be
   done while parts are in transit. Budgets, conflict maps, staged configs, acceptance checklists.
2. **Every claim is falsifiable or marked.** An agent (you) can produce confident, well-formatted,
   wrong specifications faster than anyone can check them. The conventions below exist to contain
   that, not for tidiness.

If you skip the second point, this skill produces a repository that looks authoritative and
quietly lies. That is worse than no documentation.

## Before you scaffold: ask four things

Do not guess these. They change the whole shape of the repo.

1. **What is the device, and what are the major components?** Names and vendors are enough to start.
2. **Where is the project?** Parts ordered / in transit / on the bench / already built. Pre-arrival
   projects get the full pre-arrival pass; a built device gets bring-up results captured first.
3. **What are the disciplines it feeds?** A build is usually for something — RF, astrophotography,
   home automation, retro gaming, network testing. This becomes `knowledge/`.
4. **Any legal or safety constraints?** Transmit licensing, lithium cells, mains voltage, lasers,
   drone airspace, data privacy. These belong in the repo as a stated posture, not an afterthought.

If the user has invoices, order confirmations, or vendor emails, ask for them. They are the single
highest-value input — see Phase 1.

## Scaffold

```bash
python3 scripts/scaffold.py --path <repo-dir> --name "<Project Name>" \
  --disciplines "rf-fundamentals,sdr" --components "board-a,board-b"
```

The script writes the tree, seeds every living document, copies templates, copies the link and
audit checkers into `scripts/`, and creates `.gitignore`, `.gitattributes`, and `CLAUDE.md`. Read `references/document-types.md` for what each
file is for. Do not hand-roll the tree; the script exists so every project starts identical and
you spend your effort on content.

```
docs/          bill-of-materials, accessories, runbooks/, checklists/, reference/, logs/, records/
hardware/      specs/, datasheets/, mechanical.md
configs/       files that get applied to the device, by subsystem
software/      per-application setup notes
firmware/      what gets flashed, with checksum discipline
knowledge/     one directory per discipline: learned/ configs/ runbooks/ findings/
```

Then create the GitHub repository (`gh repo create`, or the GitHub MCP tools if `gh` is absent),
push an initial commit, and work on a feature branch from there.

## The nine phases

Work them in order. Each produces files; each is a natural commit.

### Phase 1 — Order reality

Reconstruct what was actually bought from invoices and shipping mail, not memory, into
`docs/records/`. One file per order with line items verbatim.

**This phase pays for itself.** Read the line items literally. In the reference build, an order
read *"with dual 18650 batteries **holder**"* while the BOM recorded the battery as included — a
holder is not cells, and lithium cells are routinely excluded from international shipments. That
is two blockers found weeks early, from reading an invoice carefully.

Look for: variant strings that differ from what was intended, "pre-order" markers, items that are
accessories rather than the thing itself, and shipping methods with no tracking.

### Phase 2 — Bill of materials and accessories

`docs/bill-of-materials.md` is what was ordered. `docs/accessories.md` is everything else the build
needs, each with a status: **BLOCKER** (cannot boot/run without it), **VERIFY** (may be in the box,
confirm at inventory), **OPTIONAL** (capability add-on).

The accessories file is where projects are usually lost. Consumables, cables that must carry data,
coin cells, storage media, mounting hardware, the second device needed to test a radio link.

### Phase 3 — Sourced spec sheets

`hardware/specs/<board>.md`, one per component, plus `hardware/datasheets/README.md` as a link
index.

**Delegate this phase when there are three or more components.** Spawn one `hw-research` agent per
component, all in the same turn — the work is independent, read-heavy, and produces large
intermediate output that should not land in the main context. Each returns a filled spec sheet with
a confidence column, practical limits, conflict candidates, sources, and an unresolved list; you
commit them and assemble the conflict candidates into phase 4. With one or two components, do it
inline: an agent spawn cold-starts and re-derives context, so the hand-off costs more than the work.

Sourcing rules are in `references/research-playbook.md`; the short version:

- Silicon datasheets and upstream repositories outrank vendor marketing pages.
- **Read the vendor's own control software.** In the reference build, the GPIO map and the
  default-on power rail came from the upstream Python source, not the documentation — and the
  source disagreed with the docs.
- Forum lore is often the only source for real-world gotchas. Keep it, with the thread link and a
  verify marker.
- Every row that is not confirmed on this hardware says so in the sentence that makes the claim.

### Phase 4 — The conflict map

This is the highest-value pre-arrival artifact and the one nobody thinks to write. Enumerate every
shared resource and what contends for it, then stage the fix before first boot:

| Class | Example from the reference build |
|---|---|
| Serial/UART | kernel console vs GNSS on the same UART — "GPS works intermittently" |
| Bus (SPI/I²C) | a printer service holding SPI1 vs the LoRa radio — "LoRa is silent" |
| Kernel driver claiming a device | DVB driver vs RTL2832U — `usb_claim_interface error -6` |
| Bandwidth | USB 2.0 shared bus capping sample rates and Ethernet |
| Power rails | a rail that boots on when the docs say off |
| Pin/mechanical | headers, standoff heights, clearances |

Each conflict presents as failed hardware. Each costs an evening live and five minutes on paper.
Write them into `docs/logs/known-issues.md` as a watch-list with symptom → cause → staged fix.

### Phase 5 — Staged configuration

Every file that will be copied onto the device, written now, in `configs/<subsystem>/`, with a
header saying what it is, how to apply it, how to verify it, and how to roll it back. First boot
becomes *apply and verify*, not *research and improvise*.

Include the rollback. A boot config that bricks a boot is recovered by mounting the media
elsewhere — say so in the file.

### Phase 6 — Bring-up as an acceptance test

`docs/checklists/` — not "does it seem OK?" but rows of **command → expected output → recorded
result**. Order them so later tests depend on earlier passes.

Make **test 0** the one that settles your biggest open assumption (in the reference build: which
power rails are actually on after a cold boot). A checklist whose first row resolves the largest
unknown is worth more than one that starts with the easy stuff.

### Phase 7 — Budgets with an expiry date

Power, thermal, bandwidth, storage — whatever constrains this build. Every estimated number is
marked as an estimate, states its basis, and **names the command whose output replaces it**. Add a
note telling the future reader to delete the estimate column once measured. Documentation that
plans its own obsolescence stays true.

### Phase 8 — Knowledge base

`knowledge/<discipline>/` with `learned/` (durable understanding), `configs/`, `runbooks/`
(repeatable procedures), `findings/` (dated observations). See `references/knowledge-base.md`.

`findings/` stays **empty** until there is hardware to observe. An empty directory is honest; a
fabricated observation is not.

State the legal and safety posture in `knowledge/README.md` — what this platform is for, what is
out of scope, and why. Scope decisions belong in the repo where they can be reviewed.

### Phase 9 — Hygiene and handoff

- `CLAUDE.md` records the conventions so the next session (human or agent) follows them.
- Run `python3 scripts/audit.py .` before committing a batch of documentation. It covers what is
  deterministic: broken links, secret-shaped strings, precise coordinates, staged configs missing
  verify or rollback lines, unfilled placeholders, estimates that name no replacement.
- **For a substantial batch, spawn the `repo-audit` agent.** It runs that script, then does the
  judgment pass an author cannot do on their own prose: unmarked claims, contradictions between
  documents, unrunnable commands, and observations recorded for hardware that has not arrived. It
  reports; you decide what to fix.
- Commit messages explain *why* the documentation changed and what is still unverified.
- Update the living documents as a side effect of work, never as a cleanup pass: build log,
  known issues, decisions, firmware versions, order records, CHANGELOG, TODO.

## Conventions that make it trustworthy

Full text in `references/conventions.md`, and the scaffold writes them into the project's
`CLAUDE.md`. The four that matter most:

1. **Verify markers in the sentence that makes the claim.** Not a caveats section nobody reads.
   Otherwise a vendor claim quietly becomes a fact three documents later.
2. **Estimates name their replacement.** An estimate with a measurement path is a plan; one
   without is a guess that will be quoted back as fact.
3. **Living documents are updated as part of the work.** The decisions log answers "why is this
   jumper here" better than any comment ever will.
4. **Nothing sensitive enters the repo.** Keys, PSKs, tokens, precise private coordinates, raw
   captures containing identifiers, binaries. Enforce with `.gitignore` *and* state it in
   `CLAUDE.md`. Watch for encodings — a device config export can embed a key in a URL.

## Working with the user

- **Deliver in tiers.** Tier 1 is what blocks arrival-day work (accessories, boot configs, driver
  blacklists, bring-up checklist). Tier 2 is arrival-day speed (spec sheets, budgets, runbooks,
  per-app notes). Tier 3 is the knowledge base. Offer the tiers; do not silently do all three when
  the user asked for a survey.
- **Report what you could not source.** If a vendor page was unreachable, say so and mark the
  claims that depend on it. Silence about a gap is the failure mode this whole method exists to
  prevent.
- **Give them a gap analysis before a build-out** when the ask is open-ended ("what can we do
  before the parts arrive?"). A prioritized list with file paths and sources is usually the more
  useful deliverable, and it lets the user choose scope.

## Delegation

Two agent definitions ship with this skill, in `.claude/agents/` of a repository that carries it:

| Agent | Phase | Why it is worth a separate context |
|---|---|---|
| `hw-research` | 3 | N components are independent; fan-out is real parallelism and keeps raw source material out of the main context |
| `repo-audit` | 9 | Auditing prose you wrote yourself is the weakest kind of review; a cold reader catches laundered claims and contradictions |

Everything else in the nine phases is sequential and shares evolving state — order records inform
the BOM, which informs the accessory list, which informs the checklist. Splitting those across
agents costs more in hand-off than it saves, and produces documents in inconsistent voices with
inconsistent confidence markers. Deterministic checks belong in `scripts/`, not in an agent.

Both agents are read-only by design: they return reports, and the parent session commits. That
keeps one writer for the repository, which is what makes cross-links and conventions hold.

## When this skill does not apply

Pure software projects, one-off purchase questions, or a device the user simply wants advice about.
The overhead is only worth it when something physical will be assembled, debugged, and lived with.
