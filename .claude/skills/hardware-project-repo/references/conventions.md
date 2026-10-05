# Conventions

These are the rules that make an agent-written hardware repository trustworthy. The scaffold copies
a project-specific version of them into `CLAUDE.md`; this file is the reasoning behind each one.

## 1. Verify markers

Any claim not confirmed on the actual hardware says so **in the sentence that makes the claim**.

> The SDR rail is documented as default-on at boot. Forum reports attribute this to CM5. Confirm on
> CM4 with `aiov2_ctl --status` after a cold boot.

Not a footnote, not a "caveats" section. The failure mode being prevented is documentation
laundering: a vendor claim is quoted in a spec sheet, the spec sheet is quoted in a runbook, and by
the third document it reads as measured fact.

Acceptable markers: *unverified*, "verify before running", or — best — the command that settles it.

## 2. Estimates name their replacement

Every derived number states its basis and the command whose output replaces it.

| State | Est. current | Basis |
|---|---|---|
| SDR streaming | +250–350 mA | RTL2832U class typical |

> Replace with `aiov2_ctl --power` — bring-up test 4.

Add an instruction to delete the estimate column once measured. Numbers that cannot expire become
folklore.

## 3. Living documents, updated as a side effect

| File | Updated when |
|---|---|
| `docs/logs/build-log.md` | any hands-on session |
| `docs/logs/known-issues.md` | a symptom is hit or resolved |
| `docs/logs/decisions.md` | a choice is made or an open question closes |
| `docs/logs/firmware-versions.md` | anything is flashed |
| `docs/records/` | shipping, serial, or RMA state changes |
| `CHANGELOG.md` / `TODO.md` | a batch of work lands / a blocker appears |

The decisions log is the one people skip and later wish they had. Record the alternatives
considered — that is what makes it useful a year later.

## 4. Nothing sensitive enters the repo

- No keys, PSKs, tokens, passwords, captured credentials.
- No precise private coordinates. City or grid square only.
- No raw captures containing identifiers (MAC addresses, message contents).
- No binaries or images — reference them by location and checksum.

Enforce in `.gitignore` **and** state it in `CLAUDE.md`, because `.gitignore` cannot catch a secret
pasted into prose. Watch for encodings: device configuration exports and share URLs often embed a
key.

## 5. Commands are runnable

Prefer a shell block a person can paste over a description of what they should do. State the
expected output when the output is the point of the step. A runbook step whose result is
unspecified cannot be failed, which means it cannot be trusted.

## 6. Structure

- Tables for anything enumerable; checkbox lists for anything performed once.
- Relative links between documents; every document reachable from the README or a documentation
  index.
- Markdown only. No HTML (deck sources are the reasonable exception).
- UTC timestamps.

## 7. Git

- Feature branches, not direct commits to the default branch.
- Commit messages: imperative subject, body explaining *why* the documentation changed and what
  remains unverified.
- Run the link checker before committing.
