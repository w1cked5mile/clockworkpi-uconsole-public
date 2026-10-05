# Repository skills

Skills committed here load automatically for any Claude Code session working in this repository.

| Skill | Purpose |
|---|---|
| [`hardware-project-repo/`](hardware-project-repo/SKILL.md) | Scaffold and drive a documentation-first hardware project repo — structure, sourced spec sheets, staged configs, bring-up acceptance checklists, budgets, order records, knowledge base |

## Using it outside this repo

Repository skills are scoped to the repository. To use this one on a new project:

```bash
# personal skill — available in every Claude Code session on this machine
cp -r .claude/skills/hardware-project-repo ~/.claude/skills/

# or scaffold a new project directly, from a clone of this repo
python3 .claude/skills/hardware-project-repo/scripts/scaffold.py \
  --path ~/projects/<new-build> --name "<Project Name>" \
  --components "<board a>,<board b>" --disciplines "<domain-a>,<domain-b>"
```

Skills authored in other Claude surfaces (Cowork, claude.ai) do not appear in Claude Code sessions
and vice versa — committing a skill to the repository is what makes it travel with the project.

## Agents

Two subagent definitions live in [`../agents/`](../agents/) and are referenced by the skill's
phases. Both are read-only — they report, the parent session commits.

| Agent | Used in | Purpose |
|---|---|---|
| [`hw-research`](../agents/hw-research.md) | Phase 3 | One agent per component, spawned in parallel: datasheets, upstream source, and the vendor's own control software → a spec sheet with a confidence column, practical limits, conflict candidates, and an unresolved list |
| [`repo-audit`](../agents/repo-audit.md) | Phase 9 | Runs `scripts/audit.py`, then the judgment pass: unmarked claims, contradictions between documents, unrunnable commands, observations recorded for hardware that has not arrived |

Everything else in the method is sequential and shares evolving state, so it stays in one context.
Deterministic checks live in `scripts/`, not in an agent.

## Structure

```
hardware-project-repo/
├── SKILL.md                    method: four questions, scaffold, nine phases, conventions
├── scripts/scaffold.py         creates the tree and seeds every living document
├── scripts/check_links.py      relative-link checker for the generated repo
├── scripts/audit.py            mechanical audit: links, secrets, coordinates, config headers
├── references/                 conventions, research playbook, document types, knowledge base
└── assets/templates/           23 document templates the scaffold renders
```
