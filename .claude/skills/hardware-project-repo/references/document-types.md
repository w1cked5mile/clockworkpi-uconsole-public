# Document types — what each file is for

Templates for these live in `../assets/templates/`; the scaffold copies them in.

| Document | Answers | Required elements |
|---|---|---|
| `README.md` | What is this and where is everything? | Component table, layout table, links to every index |
| `CLAUDE.md` | How does work happen here? | Where-things-belong table, conventions, living docs, checks |
| `docs/bill-of-materials.md` | What was ordered? | Line items, quantities, prices, vendor, source links |
| `docs/accessories.md` | What else does it need? | Status per item: BLOCKER / VERIFY / OPTIONAL, with specs |
| `docs/records/<vendor>-<order>.md` | What did the invoice actually say? | Verbatim line items, totals, dates, RMA contacts |
| `docs/records/order-and-warranty.md` | Shipping and warranty state | One row per item, serials, tracking, links to invoices |
| `hardware/specs/<board>.md` | What is this board? | Attribute table with a confidence column, consequences section |
| `hardware/datasheets/README.md` | Where are the primary sources? | Link index, grouped by vendor and by silicon |
| `hardware/mechanical.md` | Will it physically fit? | Stack-up, clearances to measure, fastener map, routing |
| `docs/reference/<topic>.md` | Cross-cutting facts | Pin maps, budgets, interconnect — tables, not prose |
| `docs/runbooks/<procedure>.md` | How do I do X, repeatably? | Preconditions, numbered steps with commands, verification, rollback |
| `docs/checklists/<milestone>.md` | Did it pass? | Command → expected output → recorded result rows, sign-off |
| `configs/<subsystem>/<file>` | What gets applied to the device? | Header: purpose, apply, verify, roll back |
| `software/<app>.md` | How is this app set up and driven? | Install, full command surface, what it writes, first-run sequence |
| `firmware/README.md` | What gets flashed and how? | Sources, checksum discipline, version-of-record pointer |
| `docs/logs/build-log.md` | What happened, when? | Dated entries: what / result / photos / next |
| `docs/logs/known-issues.md` | What broke and why? | Symptom → cause → fix → link; plus a pre-arrival watch-list |
| `docs/logs/decisions.md` | Why is it like this? | Date, decision, rationale, alternatives; open questions section |
| `docs/logs/firmware-versions.md` | What is running? | Target versions, as-flashed table, capture commands |
| `knowledge/<discipline>/…` | What did we learn, generally? | See `knowledge-base.md` |

## Runbook vs checklist

A **runbook** is followed many times and describes a procedure. A **checklist** is run once at a
milestone and produces a pass/fail record. Assembly is a runbook; inventory and bring-up are
checklists. Mixing them produces documents that are too heavy to follow and too vague to sign off.

## The spec sheet confidence column

Every spec-sheet table carries a confidence column: `from datasheet`, `from BOM`, `inferred from
source`, `*unverified*`. Reviewers can then see at a glance which rows are load-bearing and which
are waiting on hardware.

## Config file headers

Every staged config starts with a comment block:

```
# What this is
# Prerequisites
# Apply:   <command>
# Verify:  <command and expected output>
# Roll back: <how>
```

Without the verify line the file is a suggestion. Without the rollback line it is a hazard.
