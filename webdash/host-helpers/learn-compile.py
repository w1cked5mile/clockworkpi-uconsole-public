#!/usr/bin/env python3
"""Compile webdash/curriculum/**.md into the learning platform's JSON bundle, and lint it.

Runs on the HOST, not in the container: it needs the repo (git, the knowledge/ docs it excerpts)
and uses python3-markdown-it and python3-yaml, which Debian already ships. The container only
ever reads the finished bundle, mounted read-only. See docs/reference/learning-platform-plan.md
§3.2 (content model) and §3.4 (sync).

  learn-compile.py --check                 lint the working tree; write nothing (pre-commit)
  learn-compile.py                         compile the working tree into the output dir
  learn-compile.py --ref main              compile what is committed on main (what sync uses)
  learn-compile.py --out DIR               output dir (default ~/.local/share/uconsole-webdash/learn)

Lesson bodies become typed blocks (h, p, list, code, table, callout, ref), never HTML: raw HTML in
any curriculum file fails compilation, and the browser renders blocks with textContent only.
Exit status: 0 ok, 1 lint errors (nothing written), 2 usage/IO error.
"""
import argparse
import glob as globmod
import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tarfile
import tempfile
import time
from pathlib import Path

import yaml
from markdown_it import MarkdownIt

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
DEFAULT_OUT = Path.home() / ".local/share/uconsole-webdash/learn"

_spec = importlib.util.spec_from_file_location("schema", HERE.parent / "app/learn/schema.py")
S = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(S)

MD = MarkdownIt("commonmark", {"html": True}).enable("table")
FRONTMATTER = re.compile(r"\A---\n(.*?)\n---\n?(.*)\Z", re.S)
LIVE = re.compile(r"\{live:([a-z0-9_.]+)\}", re.I)
REF_LINE = re.compile(r"^@ref\s+(\S+)$")
# Lints on raw text. Heuristics; a hit is an error because the fix is always to reword.
LATLON = re.compile(r"-?\d{1,3}\.\d{4,}\s*,\s*-?\d{1,3}\.\d{4,}")
SECRET = re.compile(r"(?i)\b(psk|password|passwd|token|secret|api[_-]?key)\b\s*[:=]\s*[\"']?[A-Za-z0-9+/=_-]{8,}")
ALLOWED_LINK = re.compile(r"^(#/|https://)")


class Errors(list):
    def add(self, where, msg):
        self.append(f"{where}: {msg}")


# ---------------------------------------------------------------------------
# Markdown -> typed blocks
# ---------------------------------------------------------------------------


def slugify(text: str) -> str:
    """GitHub-style heading anchor."""
    s = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return s.replace(" ", "-")


def inline_spans(token, where, errors, strict=True):
    """markdown-it inline children -> [{t, b?, i?, code?, href?, live?}]. strict=False (excerpts
    from knowledge/) turns disallowed links into plain text instead of failing."""
    spans, bold, ital, href = [], False, False, None

    def push_text(text):
        pos = 0
        for m in LIVE.finditer(text):
            if m.start() > pos:
                spans.append(_span(text[pos:m.start()], bold, ital, href))
            path = m.group(1)
            if path in S.FORBIDDEN_PATHS:
                errors.add(where, f"{{live:{path}}} is not allowed — use gps.grid")
            elif path not in S.LIVE_PATHS:
                errors.add(where, f"unknown live path {{live:{path}}}")
            spans.append({"live": path})
            pos = m.end()
        if pos < len(text):
            spans.append(_span(text[pos:], bold, ital, href))

    for c in token.children or []:
        if c.type == "text":
            push_text(c.content)
        elif c.type in ("softbreak", "hardbreak"):
            spans.append(_span(" ", bold, ital, href))
        elif c.type == "strong_open":
            bold = True
        elif c.type == "strong_close":
            bold = False
        elif c.type == "em_open":
            ital = True
        elif c.type == "em_close":
            ital = False
        elif c.type == "code_inline":
            spans.append({"t": c.content, "code": True})
        elif c.type == "link_open":
            target = c.attrs.get("href", "")
            if ALLOWED_LINK.match(target):
                href = target
            elif strict:
                errors.add(where, f"link target {target!r} not allowed (use #/route or https://)")
        elif c.type == "link_close":
            href = None
        elif c.type == "html_inline":
            errors.add(where, f"raw HTML not allowed: {c.content!r}")
        elif c.type == "image":
            errors.add(where, "images are not supported in lessons")
    # merge adjacent spans with identical styling
    merged = []
    for sp in spans:
        if merged and "t" in sp and "t" in merged[-1] and {k: v for k, v in sp.items() if k != "t"} == {
            k: v for k, v in merged[-1].items() if k != "t"
        }:
            merged[-1]["t"] += sp["t"]
        else:
            merged.append(sp)
    return merged


def _span(text, bold, ital, href):
    sp = {"t": text}
    if bold:
        sp["b"] = True
    if ital:
        sp["i"] = True
    if href:
        sp["href"] = href
    return sp


def md_blocks(text, where, errors, root, strict=True, depth=0):
    tokens = MD.parse(text)
    blocks, i = [], 0
    while i < len(tokens):
        t = tokens[i]
        if t.type == "heading_open":
            level = int(t.tag[1])
            blocks.append({"type": "h", "level": level, "spans": inline_spans(tokens[i + 1], where, errors, strict)})
            i += 3
        elif t.type == "paragraph_open":
            inline = tokens[i + 1]
            m = REF_LINE.match(inline.content.strip())
            if m and strict:
                blocks.append(ref_block(m.group(1), where, errors, root, depth))
            else:
                blocks.append({"type": "p", "spans": inline_spans(inline, where, errors, strict)})
            i += 3
        elif t.type in ("bullet_list_open", "ordered_list_open"):
            ordered = t.type == "ordered_list_open"
            close = t.type.replace("_open", "_close")
            items, lvl, j = [], t.level, i + 1
            while not (tokens[j].type == close and tokens[j].level == lvl):
                if tokens[j].type == "inline" and tokens[j].level == lvl + 3:
                    items.append(inline_spans(tokens[j], where, errors, strict))
                elif strict and tokens[j].type in ("bullet_list_open", "ordered_list_open") and tokens[j].level > lvl:
                    errors.add(where, "nested lists are not supported; flatten them")
                j += 1
            blocks.append({"type": "list", "ordered": ordered, "items": items})
            i = j + 1
        elif t.type in ("fence", "code_block"):
            blocks.append({"type": "code", "lang": (t.info or "").strip(), "text": t.content.rstrip("\n")})
            i += 1
        elif t.type == "table_open":
            head, rows, row, j = [], [], None, i + 1
            in_head = False
            while tokens[j].type != "table_close":
                tt = tokens[j].type
                if tt == "thead_open":
                    in_head = True
                elif tt == "thead_close":
                    in_head = False
                elif tt == "tr_open":
                    row = []
                elif tt == "tr_close":
                    (head.extend(row) if in_head else rows.append(row))
                elif tt == "inline":
                    row.append(inline_spans(tokens[j], where, errors, strict))
                j += 1
            blocks.append({"type": "table", "head": head, "rows": rows})
            i = j + 1
        elif t.type == "blockquote_open":
            # "> **Note:** …" -> callout. Only paragraphs inside are kept.
            j, paras = i + 1, []
            while not (tokens[j].type == "blockquote_close" and tokens[j].level == t.level):
                if tokens[j].type == "inline":
                    paras.append(inline_spans(tokens[j], where, errors, strict))
                j += 1
            blocks.append({"type": "callout", "paras": paras})
            i = j + 1
        elif t.type == "html_block":
            errors.add(where, f"raw HTML not allowed: {t.content.strip()[:60]!r}")
            i += 1
        elif t.type == "hr":
            i += 1
        else:
            i += 1
    return blocks


def ref_block(target, where, errors, root, depth):
    """@ref path#anchor -> the referenced section of a repo doc, compiled to blocks. Relative repo
    links inside the excerpt become plain text (there is no doc viewer on the device)."""
    path, _, anchor = target.partition("#")
    full = (root / path).resolve()
    if depth > 0:
        errors.add(where, "nested @ref not allowed")
        return {"type": "ref", "path": path, "anchor": anchor, "blocks": []}
    if not str(full).startswith(str(root.resolve())) or not full.is_file():
        errors.add(where, f"@ref target not found: {target}")
        return {"type": "ref", "path": path, "anchor": anchor, "blocks": []}
    text = full.read_text()
    if anchor:
        section = _section(text, anchor)
        if section is None:
            errors.add(where, f"@ref anchor #{anchor} not found in {path}")
            return {"type": "ref", "path": path, "anchor": anchor, "blocks": []}
        text = section
    sub = Errors()
    blocks = md_blocks(text, f"{path}#{anchor}", sub, root, strict=False, depth=depth + 1)
    for e in sub:  # excerpts must still not smuggle in HTML or bad live paths
        errors.add(where, f"in excerpt {e}")
    return {"type": "ref", "path": path, "anchor": anchor, "blocks": blocks}


def _section(text, anchor):
    lines, out, level, fenced = text.splitlines(), None, None, False
    for line in lines:
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        m = None if fenced else re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            if out is not None and len(m.group(1)) <= level:
                break
            if out is None and slugify(m.group(2)) == anchor:
                out, level = [line], len(m.group(1))
                continue
        if out is not None:
            out.append(line)
    return "\n".join(out) if out else None


# ---------------------------------------------------------------------------
# Loading and validating each file type
# ---------------------------------------------------------------------------


def read_md(path, errors, root):
    rel = str(path.relative_to(root))
    text = path.read_text()
    m = FRONTMATTER.match(text)
    if not m:
        errors.add(rel, "missing YAML frontmatter")
        return rel, {}, ""
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        errors.add(rel, f"bad YAML: {exc}")
        return rel, {}, ""
    if LATLON.search(text):
        errors.add(rel, "decimal lat/lon found — record location as a grid square only")
    if SECRET.search(text):
        errors.add(rel, "secret-shaped string found — keys and passwords never go in the repo")
    return rel, meta, m.group(2)


def need(meta, keys, rel, errors):
    for k in keys:
        if meta.get(k) in (None, "", []):
            errors.add(rel, f"missing required field '{k}'")


def item_hash(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True).encode()).hexdigest()[:16]


def check_check(check, rel, errors, labels="check"):
    if not isinstance(check, dict):
        errors.add(rel, f"{labels} must be a mapping")
        return
    ctype = check.get("type")
    if ctype not in S.CHECK_TYPES:
        errors.add(rel, f"{labels}: unknown type {ctype!r}")
        return
    if ctype == "status":
        path, op = check.get("path"), check.get("op")
        if path in S.FORBIDDEN_PATHS:
            errors.add(rel, f"{labels}: {path} not allowed")
        elif path not in S.LIVE_PATHS:
            errors.add(rel, f"{labels}: unknown status path {path!r}")
        if op not in S.STATUS_OPS:
            errors.add(rel, f"{labels}: unknown op {op!r}")
        if op != "exists" and "value" not in check:
            errors.add(rel, f"{labels}: 'value' required for op {op}")
    elif ctype == "computed":
        fn = check.get("fn")
        if fn not in S.COMPUTED_FNS:
            errors.add(rel, f"{labels}: unknown computed fn {fn!r}")
        if fn in ("mean", "rise", "counter_rate") and check.get("path") not in S.LIVE_PATHS:
            errors.add(rel, f"{labels}: unknown status path {check.get('path')!r}")
        if fn == "delta" and not (check.get("a") and check.get("b")):
            errors.add(rel, f"{labels}: delta needs 'a' and 'b' (saved values)")
    elif ctype == "messages":
        where = check.get("where") or {}
        for k in list(where) + list(check.get("not_null") or []):
            if k not in S.MESSAGE_FIELDS:
                errors.add(rel, f"{labels}: unknown message field {k!r}")
    elif ctype == "file":
        if check.get("op") not in S.FILE_OPS:
            errors.add(rel, f"{labels}: unknown file op {check.get('op')!r}")
        if not check.get("path"):
            errors.add(rel, f"{labels}: file check needs 'path'")
        for key in ("path", "other"):
            if check.get(key) and not S.file_allowed(check[key]):
                errors.add(rel, f"{labels}: {key} {check[key]!r} is outside the allowed lab roots")
        if check.get("op") == "regex_count":
            _regex(check, "pattern", rel, errors, labels, required=True)
            # min defaults to 1, max to unbounded; `min: 0, max: 0` means "no matches".
            lo, hi = check.get("min", 1), check.get("max")
            for key, v in (("min", lo), ("max", hi)):
                if v is not None and (isinstance(v, bool) or not isinstance(v, int) or v < 0):
                    errors.add(rel, f"{labels}: regex_count {key} must be a non-negative integer")
            if (isinstance(lo, int) and isinstance(hi, int) and not isinstance(hi, bool)
                    and hi < lo):
                errors.add(rel, f"{labels}: regex_count max {hi} is below min {lo}")
    elif ctype == "paste":
        if check.get("parser") not in S.PASTE_PARSERS:
            errors.add(rel, f"{labels}: unknown paste parser {check.get('parser')!r}")
        if check.get("parser") in ("regex", "journal_set_radio", "alert_dry_run"):
            _regex(check, "pattern", rel, errors, labels, required=True)
        _regex(check, "reject", rel, errors, labels, required=False)
    elif ctype == "quiz" and not check.get("assessment"):
        errors.add(rel, f"{labels}: quiz check needs 'assessment'")


NESTED_QUANT = re.compile(r"\([^)]*[+*][^)]*\)[+*{]")


def _regex(check, key, rel, errors, labels, required):
    pat = check.get(key)
    if pat is None:
        if required:
            errors.add(rel, f"{labels}: '{key}' regex is required")
        return
    try:
        re.compile(pat)
    except re.error as exc:
        errors.add(rel, f"{labels}: bad {key} regex: {exc}")
    if NESTED_QUANT.search(pat):
        # Python's re has no timeout; a nested quantifier on pasted text can freeze the dashboard.
        errors.add(rel, f"{labels}: {key} regex has a nested quantifier — rewrite it")


# A flow-style list splits on commas: `choices: [In series, for 7.4 V]` is two choices, not one.
FLOW_CHOICES = re.compile(r"^\s*choices:\s*\[(.*)\]\s*$", re.M)


def _flow_choices_quoted(text, rel, errors):
    for m in FLOW_CHOICES.finditer(text):
        items = [x.strip() for x in re.findall(r'"[^"]*"|\'[^\']*\'|[^,]+', m.group(1))]
        if any(x and x[0] not in "\"'" for x in items):
            errors.add(rel, "flow-style choices must quote every item (commas split unquoted ones); "
                            "or write the choices as a block list")


def compile_tree(root: Path, errors: Errors) -> dict:
    cur = root / "webdash/curriculum"
    if not cur.is_dir():
        errors.add("webdash/curriculum", "not found")
        return {}
    out = {"tracks": [], "modules": {}, "lessons": {}, "labs": {}, "assessments": {}, "glossary": {},
           "endorsements": []}

    for p in sorted((cur / "glossary").glob("*.md")):
        rel, meta, body = read_md(p, errors, root)
        need(meta, ["id", "term", "tooltip"], rel, errors)
        entry = {k: meta.get(k) for k in ("id", "term", "tooltip", "good_bad", "try_this", "learn_more",
                                          "live", "live_prompt", "example")}
        if entry["learn_more"] and not ALLOWED_LINK.match(str(entry["learn_more"])):
            errors.add(rel, f"learn_more {entry['learn_more']!r} must be a #/route or https:// link")
        if entry["live"]:
            # A live-read review card: "Right now <term> is <value> — what does that tell you?"
            if entry["live"] in S.FORBIDDEN_PATHS or entry["live"] not in S.LIVE_PATHS:
                errors.add(rel, f"live path {entry['live']!r} not allowed")
            if not entry["live_prompt"] or entry["example"] is None:
                errors.add(rel, "a live card needs live_prompt and an example value (shown when the reading isn't available)")
        entry["blocks"] = md_blocks(body, rel, errors, root)
        out["glossary"][meta.get("id") or p.stem] = entry

    for mdir in sorted(p for p in (cur / "modules").glob("*") if p.is_dir()):
        mfile = mdir / "module.md"
        if not mfile.is_file():
            errors.add(str(mdir.relative_to(root)), "missing module.md")
            continue
        rel, meta, body = read_md(mfile, errors, root)
        need(meta, ["id", "title", "discipline", "objectives", "est_minutes", "today"], rel, errors)
        mid = meta.get("id") or mdir.name
        if meta.get("discipline") and meta["discipline"] not in S.DISCIPLINES:
            errors.add(rel, f"unknown discipline {meta['discipline']!r}")
        if meta.get("station") and meta["station"] not in S.STATIONS:
            errors.add(rel, f"unknown station {meta['station']!r}")
        today = meta.get("today") or {}
        if today.get("state") not in S.TODAY_STATES:
            errors.add(rel, f"today.state must be one of {sorted(S.TODAY_STATES)}")
        for g in meta.get("sources") or []:
            if not globmod.glob(str(root / g), recursive=True):
                errors.add(rel, f"source glob matches nothing: {g}")
        module = {
            "id": mid, "title": meta.get("title"), "themed_title": meta.get("themed_title"),
            "discipline": meta.get("discipline"), "station": meta.get("station"),
            "prerequisites": [p if isinstance(p, dict) else {"id": p, "soft": False}
                              for p in meta.get("prerequisites") or []],
            "sources": meta.get("sources") or [], "today": today,
            "objectives": meta.get("objectives") or [], "est_minutes": meta.get("est_minutes"),
            "blocks": md_blocks(body, rel, errors, root), "lessons": [], "labs": [], "assessment": None,
        }

        for lp in sorted((mdir / "lessons").glob("*.md")):
            lrel, lmeta, lbody = read_md(lp, errors, root)
            need(lmeta, ["id", "title"], lrel, errors)
            lid = lmeta.get("id") or f"{mid}.{lp.stem}"
            if not str(lid).startswith(f"{mid}."):
                errors.add(lrel, f"lesson id must start with '{mid}.'")
            blocks = md_blocks(lbody, lrel, errors, root)
            out["lessons"][lid] = {"id": lid, "module": mid, "title": lmeta.get("title"),
                                   "est_minutes": lmeta.get("est_minutes"), "blocks": blocks,
                                   "glossary": lmeta.get("glossary") or []}
            module["lessons"].append(lid)

        for lp in sorted((mdir / "labs").glob("*.md")):
            lrel, lmeta, lbody = read_md(lp, errors, root)
            need(lmeta, ["id", "title", "mode", "steps"], lrel, errors)
            if lmeta.get("mode") and lmeta["mode"] not in S.LAB_MODES:
                errors.add(lrel, f"unknown mode {lmeta['mode']!r}")
            if lmeta.get("transmits") and not lmeta.get("legal_basis"):
                errors.add(lrel, "transmits: true requires legal_basis")
            if lmeta.get("transmits") and not ((lmeta.get("requires") or {}).get("assessments")):
                errors.add(lrel, "transmits: true requires requires.assessments (the legal check)")
            steps = lmeta.get("steps") or []
            ids = [s.get("id") for s in steps if isinstance(s, dict)]
            if len(ids) != len(set(ids)) or None in ids:
                errors.add(lrel, "every step needs a unique id")
            for n, s in enumerate(steps):
                if isinstance(s, dict):
                    if not s.get("text"):
                        errors.add(lrel, f"step {s.get('id')}: missing text")
                    check_check(s.get("check"), lrel, errors, f"step {s.get('id')}")
                    c = s.get("check") or {}
                    if c.get("fn") == "first_true_elapsed":
                        earlier = ids[:n]
                        for key in ("step", "from_step"):
                            if c.get(key) and c[key] not in earlier:
                                errors.add(lrel, f"step {s.get('id')}: {key} {c[key]!r} must name an earlier step")
            for key in ("safety_stops", "restore"):
                for n, c in enumerate(lmeta.get(key) or []):
                    check_check(c, lrel, errors, f"{key}[{n}]")
                    if c.get("type") not in ("status", "file"):
                        errors.add(lrel, f"{key}[{n}] must be a status or file check")
            for e in lmeta.get("evidence") or []:
                if e not in S.LIVE_PATHS:
                    errors.add(lrel, f"evidence path {e!r} not allowed")
            lab = {k: lmeta.get(k) for k in ("id", "title", "themed_title", "mode", "requires", "transmits",
                                              "legal_basis", "steps", "safety_stops", "restore",
                                              "evidence", "world", "est_minutes")}
            lab["module"] = mid
            lab["blocks"] = md_blocks(lbody, lrel, errors, root)
            out["labs"][lab["id"]] = lab
            module["labs"].append(lab["id"])

        ap = mdir / "assessment.md"
        if ap.is_file():
            arel, ameta, abody = read_md(ap, errors, root)
            _flow_choices_quoted(ap.read_text(), arel, errors)
            need(ameta, ["id", "pass_threshold", "items"], arel, errors)
            for it in ameta.get("items") or []:
                w = f"{arel} item {it.get('id')}"
                if it.get("type") not in S.ITEM_TYPES:
                    errors.add(w, f"unknown type {it.get('type')!r}")
                if "answer" not in it:
                    errors.add(w, "missing answer")
                if it.get("type") in ("single", "multi", "order") and not it.get("choices"):
                    errors.add(w, "missing choices")
                if it.get("type") == "numeric" and "tolerance" not in it:
                    errors.add(w, "numeric item needs tolerance")
                for t in it.get("concept_tags") or []:
                    if not re.fullmatch(r"C\d\d", str(t)):
                        errors.add(w, f"concept tag {t!r} must look like C24 (plan §1.2 concept IDs)")
            out["assessments"][ameta.get("id")] = {
                "id": ameta.get("id"), "module": mid, "kind": ameta.get("kind", "quiz"),
                "pass_threshold": ameta.get("pass_threshold"), "items": ameta.get("items") or [],
                "blocks": md_blocks(abody, arel, errors, root),
            }
            module["assessment"] = ameta.get("id")

        out["modules"][mid] = module

    for tp in sorted((cur / "tracks").glob("*.md")):
        rel, meta, body = read_md(tp, errors, root)
        need(meta, ["id", "title", "modules"], rel, errors)
        for m in meta.get("modules") or []:
            if m not in out["modules"]:
                errors.add(rel, f"unknown module {m!r}")
        out["tracks"].append({"id": meta.get("id"), "title": meta.get("title"),
                              "themed_title": meta.get("themed_title"), "summary": meta.get("summary"),
                              "note": meta.get("note"), "modules": meta.get("modules") or [],
                              "est_minutes": meta.get("est_minutes"),
                              "blocks": md_blocks(body, rel, errors, root)})

    ep = cur / "endorsements.md"
    if ep.is_file():
        rel, meta, _ = read_md(ep, errors, root)
        for e in meta.get("endorsements") or []:
            need(e, ["id", "name", "plain", "type", "when", "rule"], f"{rel} {e.get('id')}", errors)
            out["endorsements"].append(e)

    # cross-references
    for e in out["endorsements"]:
        rule = e.get("rule") or {}
        for key, table in (("lab_pass", "labs"), ("assessment_pass", "assessments")):
            for ref in rule.get(key, []):
                if ref not in out[table]:
                    errors.add(f"endorsement {e.get('id')}", f"{key} refers to unknown {ref!r}")
        if not (rule.get("lab_pass") or rule.get("assessment_pass")):
            errors.add(f"endorsement {e.get('id')}", "rule needs lab_pass and/or assessment_pass")
    for mid, m in out["modules"].items():
        for p in m["prerequisites"]:
            if p["id"] not in out["modules"]:
                errors.add(f"module {mid}", f"unknown prerequisite {p['id']!r}")
    for lab in out["labs"].values():
        for a in (lab.get("requires") or {}).get("assessments", []):
            if a not in out["assessments"]:
                errors.add(f"lab {lab['id']}", f"requires unknown assessment {a!r}")
        for s in lab.get("steps") or []:
            c = (s or {}).get("check") or {}
            if c.get("type") == "quiz" and c.get("assessment") not in out["assessments"]:
                errors.add(f"lab {lab['id']}", f"unknown assessment {c.get('assessment')!r}")
    _cycles(out["modules"], errors)

    out["hashes"] = {}
    for kind in ("modules", "lessons", "labs", "assessments", "glossary"):
        for k, v in out[kind].items():
            v["content_hash"] = item_hash(v)
            out["hashes"][k] = v["content_hash"]
    return out


def _cycles(modules, errors):
    state = {}

    def visit(m, stack):
        if state.get(m) == 1:
            errors.add(f"module {m}", "prerequisite cycle: " + " -> ".join(stack + [m]))
            return
        if state.get(m) == 2 or m not in modules:
            return
        state[m] = 1
        for p in modules[m]["prerequisites"]:
            visit(p["id"], stack + [m])
        state[m] = 2

    for m in modules:
        visit(m, [])


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


def write_bundle(bundle, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    data = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()
    sha = hashlib.sha256(data).hexdigest()[:16]
    bundle["meta"]["bundle_sha"] = sha
    data = json.dumps(bundle, sort_keys=True, separators=(",", ":")).encode()
    target = out_dir / f"bundle-{sha}.json"
    tmp = out_dir / f".{target.name}.tmp"
    tmp.write_bytes(data)
    os.replace(tmp, target)
    link_tmp = out_dir / ".current.tmp"
    if link_tmp.is_symlink() or link_tmp.exists():
        link_tmp.unlink()
    link_tmp.symlink_to(target.name)  # relative, so it resolves inside the container mount too
    os.replace(link_tmp, out_dir / "current.json")
    # keep the newest 5 bundles
    olds = sorted(out_dir.glob("bundle-*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    for old in olds[5:]:
        old.unlink()
    return target


def export_ref(ref: str, dest: Path) -> str:
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", ref], capture_output=True,
                            text=True, check=True).stdout.strip()
    arch = subprocess.run(["git", "-C", str(REPO), "archive", "--format=tar", commit],
                          capture_output=True, check=True).stdout
    with tempfile.NamedTemporaryFile() as f:
        f.write(arch)
        f.flush()
        with tarfile.open(f.name) as tar:
            tar.extractall(dest, filter="data")
    return commit


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="lint only; write nothing")
    ap.add_argument("--ref", help="compile a git ref (e.g. main) instead of the working tree")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args(argv)

    errors = Errors()
    with tempfile.TemporaryDirectory() as td:
        if args.ref:
            try:
                commit = export_ref(args.ref, Path(td))
            except subprocess.CalledProcessError as exc:
                print(f"git failed: {exc}", file=sys.stderr)
                return 2
            root, source = Path(td), f"git:{args.ref}"
        else:
            root, source = REPO, "working-tree"
            commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                                    capture_output=True, text=True).stdout.strip() or None
        bundle = compile_tree(root, errors)

    if errors:
        print(f"learn-compile: {len(errors)} error(s)", file=sys.stderr)
        for e in errors:
            print(f"  {e}", file=sys.stderr)
        return 1
    counts = {k: len(bundle[k]) for k in ("tracks", "modules", "lessons", "labs", "assessments", "glossary",
                                          "endorsements")}
    if args.check:
        if not args.quiet:
            print("learn-compile: ok", counts)
        return 0
    bundle["meta"] = {"schema": 1, "commit": commit, "source": source,
                      "compiled_at": time.time(), "counts": counts}
    target = write_bundle(bundle, args.out)
    if not args.quiet:
        print(f"learn-compile: wrote {target} {counts}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
