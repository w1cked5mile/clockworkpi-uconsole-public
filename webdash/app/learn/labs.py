"""The lab engine: runs labs step by step and validates each step on the server.

A lab is a list of steps, each with one check (plan §2.3 validator API). Checks that read the
device — status, computed, messages, file — are evaluated here on every tick of main.py's
collection loop against the same cached snapshot the stations use, so a lab adds no polling of
its own. Checks only a person can satisfy — attest, paste — arrive via the API; quiz checks read
the attempt table. The browser only displays results, so a passed step is something the server
saw, not something a client claimed.

Labs never switch rails or start services. They check that the learner did, and at the end check
the `restore` list, reporting "device left in a changed state" with the fix until it holds.
"""
import csv
import glob
import hashlib
import json
import os
import re
import statistics
import time
from pathlib import Path

from ..collectors import mesh
from . import bundle, db, extras, sync
from . import schema
from .schema import get_path, num

HOSTFS = Path(os.environ.get("WEBDASH_HOSTFS", "/hostfs"))
HOME = schema.HOME
FILE_ROOTS = schema.FILE_ROOTS
REPO = f"{HOME}/clockworkpi-uconsole"
MAX_READ = 2 * 1024 * 1024
MAX_PASTE = 64 * 1024

_RUNS: dict[int, dict] = {}  # open runs, by run id (also persisted in lab_run)
SAFETY_MISSING_TICKS = 3  # a safety reading absent this many ticks in a row stops the run
_FILE_CACHE: dict = {}  # (op, path, mtime, size, extra) -> result, so a file is read once per change


class NoRun(LookupError):
    """No open run with that id (distinct from KeyErrors raised by bugs)."""


# ---------------------------------------------------------------------------
# Check evaluation. Each returns (state, value, detail):
#   state "true" | "false" | "missing" (can't evaluate — a field the collectors don't send)
# ---------------------------------------------------------------------------


def _cmp(op, have, want):
    if op == "exists":
        return have is not None
    if op == "eq":
        return have == want
    if op == "ne":
        return have != want
    if op == "in":
        return have in (want or [])
    if op == "contains":
        return isinstance(have, (list, tuple, str)) and want in have
    a, b = num(have), num(want)
    if a is None or b is None:
        return False
    return {"gte": a >= b, "lte": a <= b, "gt": a > b, "lt": a < b}.get(op, False)


def eval_status(c, st):
    try:
        v = get_path(st, c["path"])
    except KeyError:
        if c["op"] == "exists":
            return "false", None, f"{c['path']} not reported"
        return "missing", None, f"{c['path']} not reported"
    return ("true" if _cmp(c["op"], v, c.get("value")) else "false"), v, None


def _host(path: str) -> Path:
    p = path.replace("~", HOME, 1) if path.startswith("~") else path
    return HOSTFS / p.lstrip("/"), p


def _allowed(p: str) -> bool:
    return schema.file_allowed(p)


def _contained(host_path: str) -> bool:
    """Resolve symlinks and require the target to still be under an allowed root, so a symlink in
    a learner-writable folder can't point a check at ~/.ssh or the auth store."""
    rp = os.path.realpath(host_path)
    root = str(HOSTFS.resolve())
    return rp.startswith(root + "/") and _allowed("/" + os.path.relpath(rp, root))


def eval_file(c, run, step_started):
    # "fresh" means written during this lab run, so a finding saved earlier in the run still counts.
    try:
        return _eval_file(c, step_started, run.get("started", step_started) if run else step_started)
    except (OSError, UnicodeError, re.error) as exc:
        return "false", None, f"can't read: {exc.__class__.__name__}"


def _cached(key, fn):
    if key not in _FILE_CACHE:
        if len(_FILE_CACHE) > 256:
            _FILE_CACHE.clear()
        _FILE_CACHE[key] = fn()
    return _FILE_CACHE[key]


def _sha(path: Path, stt) -> str | None:
    if stt.st_size > MAX_READ:
        return None
    return _cached(("sha", str(path), stt.st_mtime, stt.st_size),
                   lambda: hashlib.sha256(path.read_bytes()).hexdigest())


def _eval_file(c, step_started, run_started):
    host_glob, logical = _host(c["path"])
    if not _allowed(logical):
        return "false", None, "path outside the allowed lab roots"
    matches = sorted(m for m in glob.glob(str(host_glob)) if _contained(m))
    op = c["op"]
    if op == "absent":
        return ("true" if not matches else "false"), len(matches), None
    if op == "not_under_repo":
        return ("true" if not logical.startswith(REPO) else "false"), None, None
    if not matches:
        return "false", 0, "no matching file yet"
    def mtime(m):
        try:
            return os.stat(m).st_mtime
        except OSError:
            return 0
    f = Path(max(matches, key=mtime))  # the newest match, e.g. the finding just written
    try:
        stt = f.stat()
    except OSError:
        return "false", None, "can't stat"
    if op == "exists":
        return "true", len(matches), None
    if op == "mtime_after_step":
        return ("true" if stt.st_mtime >= step_started else "false"), None, None
    if op == "size_range":
        ok = c.get("min", 0) <= stt.st_size <= c.get("max", float("inf"))
        fresh = stt.st_mtime >= step_started if c.get("fresh") else True
        return ("true" if ok and fresh else "false"), stt.st_size, None
    if op == "regex_count":
        # With `fresh`, any file written since the run started may satisfy it — not just the newest,
        # so rewriting a README afterwards can't hide the finding. The count must fall in
        # [min, max] (min defaults to 1, max to unbounded), so `min: 0, max: 0` means "this file
        # has no matches" — for a glob, that is the newest file, or with `fresh` any fresh one. A
        # missing file is still "false": zero matches needs a file to have zero matches in.
        lo, hi = c.get("min", 1), c.get("max")
        cands = [Path(m) for m in matches] if c.get("fresh") else [f]
        stale, newest_n = None, None
        for cand in sorted(cands, key=lambda x: mtime(str(x)), reverse=True):
            st2 = cand.stat()
            if st2.st_size > MAX_READ:
                continue
            n = _cached(("rx", str(cand), st2.st_mtime, st2.st_size, c["pattern"]),
                        lambda cand=cand: len(re.findall(c["pattern"], cand.read_text(errors="replace"), re.M)))
            if n < lo or (hi is not None and n > hi):
                newest_n = n if newest_n is None else newest_n
                continue
            if c.get("fresh") and st2.st_mtime < run_started:
                stale = stale or cand.name
                continue
            return "true", n, None
        if newest_n is not None and hi is not None and newest_n > hi:
            return "false", newest_n, f"{newest_n} matches — at most {hi} allowed"
        if stale:
            return "false", 0, f"found {stale} but it was saved before this lab started — save it again"
        return "false", 0, "no matching file yet"
    if op == "csv_shape":
        if stt.st_size > MAX_READ * 10:
            return "false", None, "file too large"
        def count():
            with open(f, newline="", errors="replace") as fh:
                return sum(1 for _ in csv.reader(fh))
        rows = _cached(("csv", str(f), stt.st_mtime, stt.st_size), count)
        return ("true" if rows >= c.get("min_rows", 1) else "false"), rows, None
    if op == "sha256_equal":
        other_glob, other_logical = _host(c["other"])
        if not _allowed(other_logical):
            return "false", None, "path outside the allowed lab roots"
        if not _contained(str(other_glob)):
            return "false", None, "path outside the allowed lab roots"
        other = Path(other_glob)
        a, b = _sha(f, stt), _sha(other, other.stat())
        if a is None or b is None:
            return "false", None, "file too large to compare"
        return ("true" if a == b else "false"), None, None
    return "false", None, f"unknown op {op}"


def eval_messages(c, run):
    since = run["saved"].get("_msg_since", 0)
    where = c.get("where") or {}
    need = c.get("not_null") or []
    for m in mesh.messages().get("messages", []):
        if m.get("id", 0) <= since:
            continue
        if all(m.get(k) == v for k, v in where.items()) and all(m.get(k) is not None for k in need):
            return "true", {k: m.get(k) for k in ("snr", "rssi", "channel", "mine")}, None
    return "false", None, None


def eval_computed(c, run, sid, st):
    fn, samples = c["fn"], run["samples"].setdefault(sid, [])
    now = time.time()
    if fn in ("mean", "rise", "counter_rate"):
        try:
            v = num(get_path(st, c["path"]))
        except KeyError:
            return "missing", None, f"{c['path']} not reported"
        if v is not None:
            if fn == "counter_rate" and samples and v < samples[-1][1]:
                samples.clear()  # counter reset (service restarted): start the window again
            samples.append((now, v))
            if fn == "counter_rate":
                keep = c.get("window_s", 30) * 2
                samples[:] = [x for x in samples if now - x[0] <= keep]
    if fn == "mean":
        if not samples or now - samples[0][0] < c.get("window_s", 60):
            left = c.get("window_s", 60) - (now - samples[0][0]) if samples else c.get("window_s", 60)
            return "false", None, f"measuring… {max(0, int(left))} s left"
        vals = [v for t, v in samples if now - t <= c.get("window_s", 60)]
        if not vals:
            return "false", None, "no recent readings"
        m = round(statistics.fmean(vals), 3)
        if c.get("save_as"):
            run["saved"][c["save_as"]] = m
        ok = _cmp(c["op"], m, c["value"]) if c.get("op") else True
        return ("true" if ok else "false"), m, None
    if fn == "rise":
        if not samples:
            return "false", None, None
        rise = round(samples[-1][1] - samples[0][1], 3)
        return ("true" if _cmp(c["op"], rise, c["value"]) else "false"), rise, None
    if fn == "counter_rate":
        if len(samples) < 2 or samples[-1][0] - samples[0][0] < c.get("window_s", 30):
            return "false", None, "measuring…"
        rate = round((samples[-1][1] - samples[0][1]) / (samples[-1][0] - samples[0][0]), 3)
        return ("true" if _cmp(c["op"], rate, c["value"]) else "false"), rate, None
    if fn == "delta":
        a, b = run["saved"].get(c["a"]), run["saved"].get(c["b"])
        if a is None or b is None:
            return "false", None, "waiting for earlier measurements"
        d = round(a - b, 3)
        if c.get("save_as"):
            run["saved"][c["save_as"]] = d
        ok = _cmp(c["op"], d, c["value"])
        # The saved means never change, so a failed delta can't recover by waiting.
        return ("true" if ok else "false"), d, (None if ok else
                f"{d} doesn't meet {c['op']} {c['value']}: stop the lab and start again to re-measure")
    if fn == "first_true_elapsed":
        # Time from `from_step` passing (or the run start) to `step` first being true — first
        # true, not passed, so the 2-reading hold doesn't inflate e.g. a time to first fix.
        other = run["steps"].get(c["step"], {})
        if other.get("state") != "passed":
            return "false", None, None
        t_end = other.get("first_true_at") or other["passed_at"]
        t0 = run["steps"].get(c["from_step"], {}).get("passed_at") if c.get("from_step") else run["started"]
        if t0 is None:
            return "false", None, "waiting for the starting step"
        el = round(t_end - t0, 1)
        if c.get("save_as"):
            run["saved"][c["save_as"]] = el
        return "true", el, None
    return "false", None, f"unknown fn {fn}"


def eval_quiz(c):
    rows = db.q("SELECT 1 FROM attempt WHERE user_id=? AND assessment_id=? AND passed=1 LIMIT 1",
                (db.OWNER, c["assessment"]))
    return ("true" if rows else "false"), None, None


# Paste parsers: the learner pastes command output; nothing pasted is stored, only the result.
def parse_paste(c, text: str):
    p = c["parser"]
    if p in ("regex", "journal_set_radio", "alert_dry_run"):
        n = len(re.findall(c["pattern"], text, re.M))
        bad = c.get("reject") and re.search(c["reject"], text, re.M)
        return (n >= c.get("min_matches", 1) and not bad), {"matches": n}, ("rejected pattern found" if bad else None)
    if p == "rtl_test_t":
        found = re.search(r"Found \d+ device", text)
        tuner = re.search(r"R8(20T|60)", text)
        claim = "usb_claim_interface error -6" in text
        want_claim = c.get("expect_claim_error", False)
        ok = (claim if want_claim else (bool(found) and bool(tuner) and not claim))
        return ok, {"device": bool(found), "tuner": tuner.group(0) if tuner else None, "claim_error": claim}, None
    if p == "rtl_test_loss":
        m = re.findall(r"Samples per million lost \(minimum\):\s*([\d.]+)", text)
        if not m:
            return False, None, "no 'Samples per million lost' line found"
        v = float(m[-1])
        return v <= c.get("max", 1), {"lost_per_million": v}, None
    if p == "rtl_test_ppm":
        vals = [int(x) for x in re.findall(r"cumulative PPM:\s*(-?\d+)", text)][-20:]
        if len(vals) < 5:
            return False, None, "need at least 5 'cumulative PPM' lines"
        med = statistics.median(vals)
        return abs(med - c.get("expect", 1)) <= c.get("tolerance", 2), {"median_ppm": med, "n": len(vals)}, None
    if p == "vcgencmd_throttled":
        m = re.search(r"throttled=(0x[0-9a-fA-F]+)", text)
        if not m:
            return False, None, "no throttled=0x… line"
        return True, {"throttled": m.group(1)}, None
    if p == "rtl_ais_count":
        n = len(re.findall(r"^!AIVDM", text, re.M))
        return True, {"ais_messages": n}, None
    return False, None, f"unknown parser {p}"


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


def _lab(lab_id):
    """The lab as currently compiled. A run keeps its own copy from start(), so a recompile while
    it's open (learn-sync, every 15 min) can't change its steps under it."""
    return ((bundle.get() or {}).get("labs") or {}).get(lab_id)


def _persist(run):
    db.x("UPDATE lab_run SET ended=?, outcome=?, step_results=?, evidence=?, saved=? WHERE id=?",
         (run.get("ended"), run.get("outcome"), db.dumps(run["steps"]), db.dumps(run.get("evidence", {})),
          db.dumps({k: v for k, v in run["saved"].items() if not k.startswith("_")}), run["id"]))


def _snapshot(st, paths):
    out = {}
    for p in paths or []:
        try:
            out[p] = get_path(st, p)
        except KeyError:
            out[p] = None
    return out


def start(lab_id: str, st: dict | None) -> dict:
    lab = _lab(lab_id)
    if lab is None:
        raise KeyError(lab_id)
    for r in list(_RUNS.values()):  # one open run per lab: starting again abandons the old one
        if r["lab_id"] == lab_id:
            _finish(r, "abandoned")
    baseline = _snapshot(st or {}, [f"aiov2.rails.{x}.on" for x in ("GPS", "LORA", "SDR", "USB")]
                         + [f"services.{s}.active" for s in ("readsb", "gpsd", "meshtasticd", "kismet")])
    now = time.time()
    rid = db.x("INSERT INTO lab_run (user_id, lab_id, content_hash, started, baseline) VALUES (?,?,?,?,?)",
               (db.OWNER, lab_id, lab.get("content_hash"), now, db.dumps(baseline)))
    first = lab["steps"][0]["id"]
    run = {"id": rid, "lab_id": lab_id, "lab": lab, "started": now, "ended": None, "outcome": None,
           "baseline": baseline, "saved": {}, "samples": {}, "restore": [], "safety": None,
           "steps": {s["id"]: {"state": "pending"} for s in lab["steps"]}}
    run["steps"][first].update(state="active", started=now)
    msgs = mesh.messages().get("messages", [])
    run["saved"]["_msg_since"] = max((m.get("id", 0) for m in msgs), default=0)
    _RUNS[rid] = run
    db.set_progress("lab", lab_id, "in_progress", lab.get("content_hash"))
    db.add_event("lab_start", lab_id, None)
    if st:
        _tick_run(run, st)
    return view(run)


def _current(run, lab):
    for s in lab["steps"]:
        if run["steps"][s["id"]]["state"] != "passed":
            return s
    return None


def _pass(run, lab, step, value, st):
    now = time.time()
    rs = run["steps"][step["id"]]
    rs.update(state="passed", passed_at=now, value=value, detail=None)
    nxt = _current(run, lab)
    if nxt is not None:
        run["steps"][nxt["id"]].update(state="active", started=now, ticks=0)
        msgs = mesh.messages().get("messages", [])
        run["saved"]["_msg_since"] = max((m.get("id", 0) for m in msgs), default=0)
    _persist(run)


def _restore_needed(run, lab, st) -> list[dict]:
    out = []
    for c in lab.get("restore") or []:
        state, v, _ = eval_status(c, st) if c["type"] == "status" else eval_file(c, run, run["started"])
        if state != "true":
            out.append({"path": c.get("path"), "op": c.get("op"), "value": c.get("value"), "now": v})
    return out


def _finish(run, outcome, st=None):
    lab = run.get("lab") or {}
    run["ended"], run["outcome"] = time.time(), outcome
    if outcome in ("safety_stop", "abandoned") and st:
        # Tell the learner what to put back, even though the run didn't reach its restore step.
        run["saved"]["restore_needed"] = _restore_needed(run, lab, st)
    if outcome == "pass":
        # Evidence is the last non-null reading seen during the run — not a snapshot at the end,
        # when the lab has usually made the learner switch the radio back off.
        run["evidence"] = dict(run.get("seen", {}))
        run["evidence"].update({k: v for k, v in run["saved"].items() if not k.startswith("_")})
        db.set_progress("lab", run["lab_id"], "done", lab.get("content_hash"))
    if run.get("safety"):
        run["saved"]["safety"] = run["safety"]  # survives in lab_run.saved for latest()
    db.add_event(f"lab_{outcome}", run["lab_id"], {"run": run["id"]})
    _persist(run)
    if outcome == "pass":
        run["endorsed"] = extras.award_due()
    _RUNS.pop(run["id"], None)


def tick(st: dict):
    """Called by main.py's collection loop with each fresh snapshot. Each run is isolated: an
    error in one closes that run as platform_error instead of stopping every lab every 3 s."""
    try:
        sync.ingest()
    except Exception as exc:  # noqa: BLE001
        print(f"learn: sync ingest failed: {exc!r}", flush=True)
    for run in list(_RUNS.values()):
        if run.get("last_gen") == st.get("generated_at"):
            continue  # already evaluated this snapshot (start/submit tick their own run)
        try:
            _tick_run(run, st)
        except Exception as exc:  # noqa: BLE001
            print(f"learn: lab run {run['id']} failed: {exc!r}", flush=True)
            _finish(run, "platform_error")


def _safety(run, lab, st) -> bool:
    """Safety stops fire when their check is true — and also when the reading has been missing for
    a few ticks, because a battery stop that silently disarms when the bridge drops is no stop."""
    for n, c in enumerate(lab.get("safety_stops") or []):
        state, v, _ = eval_status(c, st) if c["type"] == "status" else eval_file(c, run, run["started"])
        key = f"_safety_missing_{n}"
        missing = c["type"] == "status" and (state == "missing" or v is None)
        run["saved"][key] = run["saved"].get(key, 0) + 1 if missing else 0
        if state == "true":
            run["safety"] = f"Stopped for safety: {c.get('path')} is {v}. Put the device back as listed and start again when it's safe."
        elif run["saved"][key] >= SAFETY_MISSING_TICKS:
            run["safety"] = f"Stopped for safety: can't read {c.get('path')}, so the safety limit can't be checked. Check the Power station, then start again."
        else:
            continue
        _finish(run, "safety_stop", st)
        return True
    return False


def _tick_run(run, st):
    run["last_gen"] = st.get("generated_at")
    lab = run["lab"]
    if _safety(run, lab, st):
        return
    for p, v in _snapshot(st, lab.get("evidence")).items():
        if v is not None:
            run.setdefault("seen", {})[p] = v
    step = _current(run, lab)
    if step is None:
        _check_restore(run, lab, st)
        return
    rs, c = run["steps"][step["id"]], step["check"]
    if c["type"] in ("attest", "paste"):
        return  # waits for the learner via submit()
    if c["type"] == "status":
        state, v, detail = eval_status(c, st)
    elif c["type"] == "computed":
        state, v, detail = eval_computed(c, run, step["id"], st)
    elif c["type"] == "messages":
        state, v, detail = eval_messages(c, run)
    elif c["type"] == "file":
        state, v, detail = eval_file(c, run, rs.get("started", run["started"]))
    elif c["type"] == "quiz":
        state, v, detail = eval_quiz(c)
    else:
        state, v, detail = "missing", None, f"unknown check {c['type']}"
    need = step.get("hold_ticks", 2 if c["type"] == "status" else 1)
    if state == "true":
        if "first_true_at" not in rs:  # the very first true reading, even if a flicker resets the hold
            rs["first_true_at"] = time.time()
        rs["ticks"] = rs.get("ticks", 0) + 1
        rs.update(state="holding" if rs["ticks"] < need else rs["state"], value=v, detail=None)
        if rs["ticks"] >= need:
            _pass(run, lab, step, v, st)
    else:
        rs.update(ticks=0, value=v, detail=detail,
                  state="missing" if state == "missing" else "active")
        timeout = step.get("timeout_s")
        rs["overdue"] = bool(timeout and time.time() - rs.get("started", run["started"]) > timeout)


def _check_restore(run, lab, st):
    results = []
    for c in lab.get("restore") or []:
        if c["type"] == "status":
            state, v, _ = eval_status(c, st)
        else:
            state, v, _ = eval_file(c, run, run["started"])
        results.append({"check": c, "ok": state == "true", "value": v})
    run["restore"] = results
    if all(r["ok"] for r in results):
        _finish(run, "pass", st)


def submit(run_id: int, step_id: str, text: str | None, st: dict | None) -> dict:
    run = _RUNS.get(run_id)
    if run is None:
        raise NoRun(run_id)
    lab = run["lab"]
    step = _current(run, lab)
    if step is None or step["id"] != step_id:
        return {**view(run), "error": "that step isn't the current one"}
    c = step["check"]
    if c["type"] == "attest":
        _pass(run, lab, step, "attested", st)
    elif c["type"] == "paste":
        if not text or len(text) > MAX_PASTE:
            return {**view(run), "error": "paste the command output (up to 64 KB)"}
        ok, value, detail = parse_paste(c, text)
        if ok:
            if c.get("save_as") and value:
                run["saved"][c["save_as"]] = value
            _pass(run, lab, step, value, st)
        else:
            run["steps"][step_id].update(detail=detail or "that output doesn't show the expected result",
                                         value=value)
    else:
        return {**view(run), "error": "this step is checked automatically"}
    if st:
        _tick_run(run, st)
    return view(run) if run["id"] in _RUNS else latest(run["lab_id"])


def stop(run_id: int, st: dict | None = None) -> dict:
    run = _RUNS.get(run_id)
    if run is None:
        raise NoRun(run_id)
    _finish(run, "abandoned", st)
    return latest(run["lab_id"])


def view(run: dict) -> dict:
    return {k: run.get(k) for k in ("id", "lab_id", "started", "ended", "outcome", "baseline",
                                    "steps", "restore", "safety", "evidence")} | {
        "saved": {k: v for k, v in run["saved"].items() if not k.startswith("_")}, "open": run["id"] in _RUNS,
        "step_count": len(run["lab"]["steps"]),
        "steps_passed": sum(1 for x in run["steps"].values() if x.get("state") == "passed")}


def latest(lab_id: str) -> dict | None:
    for r in _RUNS.values():
        if r["lab_id"] == lab_id:
            return view(r)
    rows = db.q("SELECT * FROM lab_run WHERE user_id=? AND lab_id=? ORDER BY id DESC LIMIT 1",
                (db.OWNER, lab_id))
    if not rows:
        return None
    r = rows[0]
    saved = json.loads(r["saved"])
    return {"id": r["id"], "lab_id": lab_id, "started": r["started"], "ended": r["ended"],
            "outcome": r["outcome"], "steps": json.loads(r["step_results"]),
            "evidence": json.loads(r["evidence"]), "baseline": json.loads(r["baseline"]),
            "saved": saved, "restore": [], "safety": saved.get("safety"), "open": False}


def recover():
    """After a container restart, runs left open can't be resumed (their in-memory samples are
    gone): close them as abandoned so the learner starts fresh."""
    db.x("UPDATE lab_run SET ended=?, outcome='abandoned' WHERE ended IS NULL", (time.time(),))
    if bundle.get():
        extras.award_due()  # e.g. after endorsements were added to content that was already passed
