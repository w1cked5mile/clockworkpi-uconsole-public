# Curriculum source

Source for the learning platform ("the Chart Table"). Compiled by
[`../host-helpers/learn-compile.py`](../host-helpers/learn-compile.py) into a JSON bundle that
webdash serves; design in
[`../../docs/reference/learning-platform-plan.md`](../../docs/reference/learning-platform-plan.md)
§3.2. Every file is Markdown with YAML frontmatter. Raw HTML fails compilation.

| Path | Holds |
|---|---|
| `tracks/<id>.md` | A learning path: ordered module IDs |
| `modules/<Mxx>/module.md` | Module metadata (prerequisites, sources, objectives, "Today" status) and overview |
| `modules/<Mxx>/lessons/NN-*.md` | One lesson each |
| `modules/<Mxx>/labs/LAB-nn.md` | A lab: steps and the checks that validate them |
| `modules/<Mxx>/assessment.md` | Quiz items with answers (graded server-side, never sent to the browser) |
| `glossary/<term>.md` | One term for ⓘ popovers and review cards |

Lesson body syntax, beyond ordinary Markdown:

- `{live:gps.hdop}` — the current value from `/api/status`. Allowed paths are listed in
  [`../app/learn/schema.py`](../app/learn/schema.py); `gps.lat`/`gps.lon` are never allowed.
- `@ref path/to/doc.md#heading-anchor` on its own line — excerpts that section of a repo doc at
  compile time, so durable prose stays in `knowledge/` and is not copied here.
- Links: only `#/route` (inside webdash) and `https://`.

Before committing:

```bash
python3 webdash/host-helpers/learn-compile.py --check
```
