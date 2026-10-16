# webdash design team: who does what, in what order, to what bar

Status: **charter, 2026-10-11.** Restructures how the webdash design and learning agents work
together. It doesn't replace the design of record:
[`webdash-design.md`](webdash-design.md) (the UI), [`learning-platform-plan.md`](learning-platform-plan.md)
(the learning layer, newer where the two disagree), [`webdash-architecture.md`](webdash-architecture.md)
(what exists and why) and [`../../software/webdash.md`](../../software/webdash.md) (how to run it).

Why this exists: the agents were written on 2026-09-23 and 2026-09-24 as one-off reviewers. Each
read a different subset of the docs, none knew the others existed, and several still described
webdash as it was then (`app.js`, `localStorage` progress, no AC1200, no RTC cell). Nobody looked at
the rendered page: every review so far has been a code or screenshot reading.

## The bar

"Best website ever" means best *for this device*: a field instrument on a 5" screen that also
teaches. Each line is a pass/fail check, and the agent named in the last column checks it.

| # | Quality | Pass when | Checked by |
|---|---|---|---|
| Q1 | Glanceable | The overview fits 1280×480 with no scroll, and each station answers its one question in under 2 s of looking | `webdash-qa` |
| Q2 | Honest | Every value has a unit and a source. Every off state says why and gives the control or command. Nothing claims what telemetry can't witness | `design-planner`, `senior-rf-engineer` |
| Q3 | Safe to touch | Anything that transmits or changes hardware says so, on what, at the control. Untrusted data (mesh text, SSIDs, callsigns) renders via `textContent` only | `web-ui-engineer`, `/security-review` |
| Q4 | Accessible | WCAG 2.1 AA: contrast ≥ 4.5:1 in **every skin**, full keyboard reach with visible focus, accessible names, status never colour-only, `prefers-reduced-motion` respected | `webdash-qa` |
| Q5 | Fast on a CM4 | Targets, *not yet measured*: first paint < 1 s and each 3 s status tick < 16 ms of main-thread work in on-device Chromium. Measure with the DevTools Performance panel, then replace these targets with numbers | `webdash-qa` |
| Q6 | Offline | No CDN, no remote font, no runtime fetch outside the device | `web-ui-engineer` |
| Q7 | Teaches | Every reading links to an explainer, every explainer to a lesson, every lesson to a lab whose checks come from live data | `syllabus-designer`, `tutor`, `guided-learning` |
| Q8 | Has a voice | Themed names are subtitles to the plain name; the voice never costs legibility or glamorizes intrusion | `creative-director` |
| Q9 | Lawful | Receive, learn, licensed transmit; the authorized-audit exception stays gated by its allowlist (a BSSID plus a written authorization basis, enforced by the server and again before any RF) | `senior-rf-engineer` |

When two of these conflict, the higher row in this order wins: **Q9 lawful → Q3 safe → Q2 honest
→ Q4 accessible → Q1 glanceable → Q5 fast → Q7 teaches → Q8 voice**.

## Roster

| Agent | Owns | Produces | Never does |
|---|---|---|---|
| [`webdash-qa`](../../.claude/agents/webdash-qa.md) *(new 2026-10-11)* | The rendered page: Q1, Q4, Q5 | As-built evidence (screenshots at three viewports in each skin, keyboard pass, contrast table, perf numbers) and a regression list | Design or write copy |
| [`creative-director`](../../.claude/agents/creative-director.md) | Concept, voice, naming, motifs, skins' character: Q8 | Direction, string rewrites, naming table | Change structure or tokens |
| [`design-planner`](../../.claude/agents/design-planner.md) | Information architecture, layout, visual system, component patterns: Q1, Q2 | The design plan, as edits proposed to `webdash-design.md` | Write code |
| [`syllabus-designer`](../../.claude/agents/syllabus-designer.md) | What is learned, in what order | Module map, objectives, lab candidates, content gaps | Write lesson prose |
| [`tutor`](../../.claude/agents/tutor.md) | Explanations | Glossary entries and lesson prose in `webdash/curriculum/` format; durable prose for `knowledge/*/learned/` | Invent values not read from the device |
| [`guided-learning`](../../.claude/agents/guided-learning.md) | Labs and missions | `LAB-nn.md` drafts using the real check types; data gaps for collectors | Write checks the lab engine can't run |
| [`senior-rf-engineer`](../../.claude/agents/senior-rf-engineer.md) | RF truth and legality: Q2 (RF numbers), Q9 | Rated findings (blocker / fix / note) | Approve anything outside the legal posture |
| [`web-ui-engineer`](../../.claude/agents/web-ui-engineer.md) | Buildability: Q3, Q6 | Component specs, data-gap → collector plan, phased build plan, code review | Merge its own work |

Also on call, and not webdash-specific: [`doc-review`](../../.claude/agents/doc-review.md) and
[`repo-audit`](../../.claude/agents/repo-audit.md) before a batch lands, and the built-in
`/security-review` for any change that touches auth, the WPA audit, or a transmit path. All agents
are read-only and report. **The main session builds, verifies and commits**.

## The pipeline

Every piece of work runs through these stages in order. A small fix can skip the stages marked
optional. Stages 2–4 can run in parallel once stage 1 is done.

| # | Stage | Who | Input | Output | Gate to the next stage |
|---|---|---|---|---|---|
| 0 | Brief | owner + main session | A goal | One paragraph: the station(s), the user moment, the bar rows it must move, and what's out of scope | Owner agrees |
| 1 | As-built evidence | `webdash-qa` | The brief | Screenshots, keyboard pass, contrast and perf baseline for the affected views | Evidence exists; no design starts from memory |
| 2 | Concept *(optional)* | `creative-director` | Brief + evidence | Voice, naming, motifs for the new surface | Plain names stay first |
| 3 | Structure | `design-planner` | Brief + evidence + stage 2 | IA, layout per viewport, component pattern, off-state copy slots | Fits Q1 on paper |
| 4 | Content *(when it teaches)* | `syllabus-designer` → `tutor` → `guided-learning` | Brief + stage 3's learning slots | Module placement, explainers and lessons, lab drafts | `learn-compile.py --check` passes on the drafts |
| 5 | Technical review | `senior-rf-engineer` | Stages 3–4 | Rated findings | No open **blocker** |
| 6 | Engineering spec | `web-ui-engineer` | Stages 3–5 | Markup/CSS/JS spec, data gaps → collectors, phased build steps with on-device verify | Every step verifiable on the device |
| 7 | Build | main session | Stage 6 | Code, one phase per commit | Tests pass (below) |
| 8 | Verify | `webdash-qa`, `web-ui-engineer` (code review), `/security-review` where Q3 applies | The build | A pass/fail table against the bar, compared with the stage 1 baseline | No bar row regresses |
| 9 | Record | main session, `doc-review` / `repo-audit` | Stage 8 | `webdash-design.md` status updated, build log, CHANGELOG, decisions | Audit clean |

The checks run in stage 7:

```bash
cd webdash && sg docker -c 'docker compose up -d --build'   # rebuild; then Chromium at 127.0.0.1:8090
cd ..
# stdlib unittest, run in the container (tests/ isn't baked into the image)
for t in test_learn test_survey; do
  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/$t.py
done
python3 webdash/host-helpers/learn-compile.py --check     # curriculum lint
python3 .claude/skills/hardware-project-repo/scripts/audit.py .
```

### How to hand work between agents

Agents don't see each other's reports. The main session passes them on. Each prompt should
include:

1. The brief (stage 0), word for word.
2. The upstream reports it depends on, pasted or saved to a scratch file and named by path.
3. The bar rows this agent owns for this piece of work.
4. Where its output goes: which section of which document of record, or which curriculum path.

## What needs to happen

The current state, with evidence, in the order the bar puts it. Each item runs through the
pipeline above. Line references are as of 2026-10-11.

| Order | Work | Evidence | Bar | First stage |
|---|---|---|---|---|
| 1 | ~~**Mesh Send doesn't say it transmits**~~ **Built 2026-10-11 (phase 1a–1h); 1i, an owner-run send, still to do.** (F7, open since 2026-09-23) | `webdash/app/static/index.html:136-139`: a plain "Send" button with no TX caption or frequency. It's disabled only when no channels are loaded (`js/mesh.js:44-45`), not with a stated reason when the LORA rail is off. The 200-byte check exists (`mesh.js:112-115`) | Q3, Q9 | 3 |
| 2 | ~~**Give QA a way to see the real page.**~~ **Done 2026-10-14:** `render-view.sh` runs the real `main.js` with a stubbed WebSocket (one fixture snapshot, never closes) and stubbed `fetch`, so every view — overview, the Wi-Fi tabs, the SDR tabs, GPS/power/system/mesh — screenshots headless at any viewport and skin. Stages 1 and 8 are unblocked; the only gap left is `#/learn` (served from the mounted bundle, not `/static`). Was: `render-check` only rendered `#/timeline` | [`../../webdash/tools/render-check/README.md`](../../webdash/tools/render-check/README.md) | Q1, Q4, Q5 | 6 |
| 3 | ~~**Set the records straight.**~~ **Done 2026-10-15:** `webdash-design.md`'s status line now points here as the live status (phases 1–3 + the 2026-09-25 learning MVP + the later redesign work), its "Progress is stored per browser" claim is corrected to server-side SQLite, and the Open-decisions "Progress storage" row is marked resolved server-side. `learning-platform-plan.md`'s status line was already accurate | [`webdash-design.md`](webdash-design.md) status line and §Open decisions; [`learning-platform-plan.md`](learning-platform-plan.md) status line | Q2 | 9 |
| 4 | ~~**Accessibility baseline.**~~ **Built 2026-10-11 (redesign phase 2a):** `prefers-reduced-motion` covers the switch transitions; contrast measured in both skins and fixed (vintage `--learn`, `--dim`, `--ok`; default `--off`; new `--edge` for control borders), with tests in `test_mesh_radio.py`. Was: no reduced-motion rule, and contrast never measured | `webdash/app/static/styles.css:301,305`; [`webdash-design.md`](webdash-design.md) §Skins | Q4 | 1 |
| 5 | **Off states that teach** (F5). `webdash-design.md` still lists it as open, but Kismet has since gained a Start/Stop control. Check every station's off state against the pattern (why it's off, the control or command, what it would show), then close F5 or narrow it | `index.html:243`, `js/kismet.js:19`; [`webdash-design.md`](webdash-design.md) §What the review found | Q2 | 1 |
| 6 | **Track A's RF review never ran.** The senior-rf-engineer review of Track A was cut off by a usage limit | [`learning-platform-plan.md`](learning-platform-plan.md) status line | Q2, Q9 | 5 |
| 7 | **Measure CM4 performance.** *(2026-10-11: hidden views no longer drawn each tick; headless per-tick estimates in the build log. On-device numbers still missing.)* No numbers exist. `learn.js` is 1162 lines and `styles.css` 718 | `wc -l webdash/app/static/js/*.js webdash/app/static/styles.css` | Q5 | 1 |
| 8 | **Detail views** (phase 5): GPS sky plot, mesh node table, aircraft table, power flow. None found in `static/js/` | [`webdash-design.md`](webdash-design.md) §Build plan | Q1, Q7 | 3 |
| 9 | **Explainer coverage.** 49 glossary terms exist; how many dashboard fields have an ⓘ is unmeasured | `webdash/curriculum/glossary/`; `ui.js` | Q7 | 4 |
