"""Unit tests for the learning platform: check evaluation, paste parsers, grading, the lab state
machine, answer stripping, and the net collector. stdlib unittest, no network or device access.
Run inside the container (it has the app's dependencies; tests/ is not baked into the image, so
pipe the file in):

  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/test_learn.py

The database and bundle are redirected to a temporary directory BEFORE the app is imported, so a
test run never touches the real learn.db.
"""
import json
import os
import tempfile
import unittest
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="learn-test-")
os.environ["WEBDASH_DATA_DIR"] = os.path.join(_TMP, "data")
os.environ["WEBDASH_LEARN_DIR"] = os.path.join(_TMP, "learn")
os.makedirs(os.environ["WEBDASH_LEARN_DIR"])

LAB = {
    "id": "LAB-T", "title": "Test lab", "module": "MT", "content_hash": "h1",
    "steps": [
        {"id": "on", "text": "rail on", "check": {"type": "status", "path": "aiov2.rails.SDR.on", "op": "eq", "value": True}},
        {"id": "ok", "text": "attest", "check": {"type": "attest", "prompt": "done"}},
    ],
    "restore": [{"type": "status", "path": "aiov2.rails.SDR.on", "op": "eq", "value": False}],
    "safety_stops": [{"type": "status", "path": "aiov2.power_num.voltage_v", "op": "lte", "value": 3.5}],
    "evidence": [],
}
BUNDLE = {"meta": {"bundle_sha": "t"}, "labs": {"LAB-T": LAB}, "modules": {}, "lessons": {},
          "assessments": {"Q": {"id": "Q", "module": "MT", "pass_threshold": 1.0, "items": [
              {"id": "a1", "type": "single", "choices": ["x", "y"], "answer": 1},
              {"id": "a10", "type": "single", "choices": ["x", "y"], "answer": 1}]}},
          "glossary": {}, "endorsements": [], "tracks": [], "hashes": {}}
with open(os.path.join(os.environ["WEBDASH_LEARN_DIR"], "current.json"), "w") as _f:
    json.dump(BUNDLE, _f)

from app.learn import bundle, db, grading, labs  # noqa: E402
from app.learn.schema import num  # noqa: E402

assert str(db.DB_PATH).startswith(_TMP), "tests must not use the real learn.db"

ST = {
    "aiov2": {"state": "ok", "rails": {"SDR": {"on": True}}, "power_num": {"power_w": 0.84}},
    "adsb": {"state": "running", "aircraft_count": 3, "with_position": 0},
    "mesh": {"channels": ["NCMesh", "SCMesh"]},
}


class StatusChecks(unittest.TestCase):
    def ev(self, **c):
        return labs.eval_status(c, ST)[0]

    def test_ops(self):
        self.assertEqual(self.ev(path="aiov2.rails.SDR.on", op="eq", value=True), "true")
        self.assertEqual(self.ev(path="adsb.aircraft_count", op="gte", value=1), "true")
        self.assertEqual(self.ev(path="adsb.with_position", op="gte", value=1), "false")
        self.assertEqual(self.ev(path="adsb.state", op="in", value=["running", "locked"]), "true")
        self.assertEqual(self.ev(path="mesh.channels", op="contains", value="SCMesh"), "true")
        self.assertEqual(self.ev(path="aiov2.power_num.power_w", op="lt", value=1), "true")

    def test_missing_is_not_false(self):
        # A field the collectors don't send is "can't evaluate", not a failed check.
        self.assertEqual(self.ev(path="adsb.messages_per_s", op="gt", value=0), "missing")
        self.assertEqual(self.ev(path="adsb.messages_per_s", op="exists"), "false")

    def test_num(self):
        self.assertEqual(num("4.2 V"), 4.2)
        self.assertEqual(num("100%"), 100.0)
        self.assertIsNone(num(True))
        self.assertIsNone(num("n/a"))


class PasteParsers(unittest.TestCase):
    def test_rtl_test_t(self):
        good = "Found 1 device(s):\n  0:  Realtek, RTL2838UHIDIR\nFound Rafael Micro R820T tuner\n"
        self.assertTrue(labs.parse_paste({"parser": "rtl_test_t"}, good)[0])
        busy = "usb_claim_interface error -6\nFailed to open rtlsdr device #0.\n"
        self.assertFalse(labs.parse_paste({"parser": "rtl_test_t"}, busy)[0])
        self.assertTrue(labs.parse_paste({"parser": "rtl_test_t", "expect_claim_error": True}, busy)[0])

    def test_loss(self):
        out = "Samples per million lost (minimum): 0\n"
        ok, v, _ = labs.parse_paste({"parser": "rtl_test_loss", "max": 1}, out)
        self.assertTrue(ok)
        self.assertEqual(v["lost_per_million"], 0)
        self.assertFalse(labs.parse_paste({"parser": "rtl_test_loss", "max": 1},
                                          "Samples per million lost (minimum): 3\n")[0])

    def test_ppm_median_ignores_outliers(self):
        lines = "\n".join(f"real sample rate: 2048002 current PPM: 1 cumulative PPM: {v}"
                          for v in [1, 1, 2, 1, -17, 1, 0, 2, 1, -5, 1])
        ok, v, _ = labs.parse_paste({"parser": "rtl_test_ppm", "expect": 1, "tolerance": 2}, lines)
        self.assertTrue(ok)
        self.assertEqual(v["median_ppm"], 1)

    def test_regex_with_reject(self):
        c = {"parser": "regex", "pattern": r"^\$G[NP](RMC|GGA),", "min_matches": 2}
        self.assertTrue(labs.parse_paste(c, "$GNRMC,1\n$GNGGA,2\n")[0])
        self.assertFalse(labs.parse_paste(c, "$GNRMC,1\n")[0])


class FileChecks(unittest.TestCase):
    def test_prefix_is_not_a_root(self):
        self.assertFalse(labs._allowed("/home/user/labsX/secret"))

    def test_symlink_escape(self):
        root = labs.HOSTFS
        self.assertFalse(labs._contained("/tmp"))  # outside /hostfs entirely

    def test_outside_roots_refused(self):
        state, _, detail = labs.eval_file({"op": "exists", "path": "/etc/../root/x"}, {}, 0)
        self.assertEqual(state, "false")
        self.assertIn("outside", detail)
        self.assertFalse(labs._allowed("/home/user/.config/uconsole-webdash/auth.json"))
        self.assertTrue(labs._allowed("/home/user/labs/x.csv"))


class RegexCount(unittest.TestCase):
    """regex_count against a fake /hostfs: min defaults to 1, optional max, min 0 + max 0 = none."""

    def setUp(self):
        self._hostfs = labs.HOSTFS
        self.root = tempfile.mkdtemp(prefix="hostfs-", dir=_TMP)
        labs.HOSTFS = Path(self.root)
        self.dir = os.path.join(self.root, "home/wicked5mile/labs")
        os.makedirs(self.dir)

    def tearDown(self):
        labs.HOSTFS = self._hostfs

    def put(self, name, text, mtime):
        p = os.path.join(self.dir, name)
        with open(p, "w") as f:
            f.write(text)
        os.utime(p, (mtime, mtime))

    def ev(self, **c):
        c = {"op": "regex_count", "path": "~/labs/*.md", "pattern": r"^MAC ", **c}
        return labs._eval_file(c, 0, 1000)

    def test_min_default_and_max(self):
        self.put("a.md", "MAC 1\nMAC 2\n", 2000)
        self.assertEqual(self.ev()[:2], ("true", 2))
        self.assertEqual(self.ev(max=2)[0], "true")
        state, n, detail = self.ev(max=1)
        self.assertEqual((state, n), ("false", 2))
        self.assertIn("at most 1", detail)

    def test_zero_means_none(self):
        self.put("a.md", "clean\n", 2000)
        self.assertEqual(self.ev(min=0, max=0)[:2], ("true", 0))
        self.assertEqual(self.ev()[0], "false")  # default min 1 still needs a match
        self.put("b.md", "MAC 1\n", 3000)  # newest file now has one: non-fresh reads the newest
        self.assertEqual(self.ev(min=0, max=0)[0], "false")

    def test_zero_needs_a_file(self):
        self.assertEqual(self.ev(min=0, max=0)[0], "false")

    def test_fresh_any_file_in_range(self):
        self.put("old.md", "clean\n", 500)  # before the run: doesn't count
        self.put("new.md", "MAC 1\n", 2000)
        self.assertEqual(self.ev(min=0, max=0, fresh=True)[0], "false")
        self.put("new2.md", "clean\n", 3000)
        self.assertEqual(self.ev(min=0, max=0, fresh=True)[0], "true")


class NetCollector(unittest.TestCase):
    """net.collect against a fake /sys/class/net: types, wireless marker, wlan1mon rename."""

    def fake(self, ifaces):
        root = tempfile.mkdtemp(prefix="sysnet-", dir=_TMP)
        for name, (t, wireless) in ifaces.items():
            os.makedirs(os.path.join(root, name))
            if t is not None:
                with open(os.path.join(root, name, "type"), "w") as f:
                    f.write(f"{t}\n")
            if wireless:
                os.makedirs(os.path.join(root, name, "wireless"))
        return root

    def test_managed_and_absent(self):
        from app.collectors import net
        r = net.collect(self.fake({"lo": (772, False), "eth0": (1, False), "wlan0": (1, True)}))
        self.assertEqual(r, {"state": "ok", "monitor_ifaces": 0,
                             "wlan0": {"present": True, "mode": "managed"},
                             "wlan1": {"present": False, "mode": None}})

    def test_monitor_and_rename(self):
        from app.collectors import net
        r = net.collect(self.fake({"wlan0": (1, True), "wlan1mon": (803, False)}))
        self.assertEqual(r["monitor_ifaces"], 1)
        self.assertEqual(r["wlan1"], {"present": True, "mode": "monitor"})
        r = net.collect(self.fake({"wlan1": (1, True), "wlan1mon": (803, False), "mon0": (803, False)}))
        self.assertEqual((r["monitor_ifaces"], r["wlan1"]["mode"]), (2, "managed"))

    def test_other_and_unreadable(self):
        from app.collectors import net
        r = net.collect(self.fake({"wlan0": (1, False), "wlan1": (None, False)}))
        self.assertEqual(r["wlan0"], {"present": True, "mode": "other"})  # type 1 but not wireless
        self.assertEqual(r["wlan1"], {"present": False, "mode": None})  # no type file: skipped

    def test_error_never_raises(self):
        from app.collectors import net
        r = net.collect(os.path.join(_TMP, "does-not-exist"))
        self.assertEqual(r["state"], "error")
        self.assertIsNone(r["wlan0"]["mode"])


class Grading(unittest.TestCase):
    def test_item_types(self):
        from app.learn.grading import _correct
        self.assertTrue(_correct({"type": "single", "answer": 1}, 1))
        self.assertFalse(_correct({"type": "single", "answer": 1}, 0))
        self.assertTrue(_correct({"type": "multi", "answer": [0, 3]}, [3, 0]))
        self.assertFalse(_correct({"type": "multi", "answer": [0, 3]}, [0]))
        self.assertTrue(_correct({"type": "numeric", "answer": 417, "tolerance": 10}, 425))
        self.assertFalse(_correct({"type": "numeric", "answer": 417, "tolerance": 10}, 430))
        self.assertFalse(_correct({"type": "numeric", "answer": 1, "tolerance": 0}, "x"))


def snap(sdr, volts=4.0, gen=None):
    snap.n = getattr(snap, "n", 0) + 1
    return {"generated_at": gen or snap.n, "aiov2": {"rails": {"SDR": {"on": sdr}},
                                                      "power_num": {"voltage_v": volts}}}


class LabStateMachine(unittest.TestCase):
    def test_hold_attest_restore_pass(self):
        run = labs.start("LAB-T", snap(False))
        rid = run["id"]
        labs.tick(snap(True))
        self.assertEqual(labs._RUNS[rid]["steps"]["on"]["state"], "holding")  # 1 of 2 ticks
        labs.tick(snap(True))
        self.assertEqual(labs._RUNS[rid]["steps"]["on"]["state"], "passed")
        v = labs.submit(rid, "ok", None, snap(True))
        self.assertTrue(v["open"])  # restore not met: SDR still on
        labs.tick(snap(False))
        self.assertNotIn(rid, labs._RUNS)
        self.assertEqual(labs.latest("LAB-T")["outcome"], "pass")

    def test_submit_wrong_step(self):
        run = labs.start("LAB-T", snap(False))
        v = labs.submit(run["id"], "ok", None, snap(False))
        self.assertIn("error", v)
        labs.stop(run["id"])

    def test_no_run(self):
        with self.assertRaises(labs.NoRun):
            labs.submit(999999, "on", None, None)

    def test_safety_stop_reason_survives(self):
        run = labs.start("LAB-T", snap(False))
        labs.tick(snap(True, volts=3.4))
        latest = labs.latest("LAB-T")
        self.assertEqual(latest["outcome"], "safety_stop")
        self.assertIn("3.4", latest["safety"])
        self.assertTrue(latest["saved"]["restore_needed"])  # SDR was left on

    def test_safety_stop_when_reading_missing(self):
        run = labs.start("LAB-T", snap(False))
        for _ in range(labs.SAFETY_MISSING_TICKS):
            labs.tick({"generated_at": snap.n + 100 + _, "aiov2": {"rails": {"SDR": {"on": False}}}})
            snap.n += 1
        self.assertEqual(labs.latest("LAB-T")["outcome"], "safety_stop")

    def test_bundle_change_mid_run_is_harmless(self):
        run = labs.start("LAB-T", snap(False))
        labs._RUNS[run["id"]]["lab"]  # the run keeps its own copy
        BUNDLE["labs"]["LAB-T"] = {**LAB, "steps": [LAB["steps"][1]]}
        try:
            labs.tick(snap(True))
            labs.tick(snap(True))
            self.assertEqual(labs._RUNS[run["id"]]["steps"]["on"]["state"], "passed")
        finally:
            BUNDLE["labs"]["LAB-T"] = LAB
            labs.stop(run["id"])

    def test_first_true_elapsed_from_step(self):
        run = {"started": 0, "saved": {}, "samples": {}, "steps": {
            "rail-on": {"state": "passed", "passed_at": 100.0},
            "fix": {"state": "passed", "passed_at": 160.0, "first_true_at": 157.0}}}
        c = {"type": "computed", "fn": "first_true_elapsed", "step": "fix", "from_step": "rail-on", "save_as": "ttff_s"}
        state, v, _ = labs.eval_computed(c, run, "t", {})
        self.assertEqual((state, v, run["saved"]["ttff_s"]), ("true", 57.0, 57.0))  # first true, not passed

    def test_mean_empty_window(self):
        run = {"samples": {}, "saved": {}, "steps": {}, "started": 0}
        c = {"type": "computed", "fn": "mean", "path": "x", "window_s": 0, "op": "gte", "value": 0}
        state, _, detail = labs.eval_computed(c, run, "s", {"x": None})
        self.assertEqual(state, "false")


class GradingEdges(unittest.TestCase):
    def test_float_is_not_a_choice(self):
        from app.learn.grading import _correct
        self.assertFalse(_correct({"type": "single", "answer": 1}, 1.7))
        self.assertFalse(_correct({"type": "single", "answer": 1}, True))

    def test_blank_submit_hides_explanations(self):
        g = grading.grade("Q", {})
        self.assertTrue(all(r["explanation"] is None for r in g["results"]))

    def test_hotspot_a1_vs_a10(self):
        for _ in range(3):
            grading.grade("Q", {"a1": 1, "a10": 0})  # a10 wrong every time, a1 right
        reasons = [r["reason"] for r in db.q("SELECT reason FROM review_item WHERE state='open'")]
        self.assertTrue(any("item a10 —" in x for x in reasons))
        self.assertFalse(any("item a1 —" in x for x in reasons))


class AnswersStripped(unittest.TestCase):
    def test_public_assessment(self):
        a = {"id": "q", "items": [{"id": "1", "prompt": "p", "choices": ["a"], "answer": 0,
                                   "explanation": "e", "tolerance": 1}]}
        pub = bundle.public_assessment(a)
        self.assertNotIn("answer", pub["items"][0])
        self.assertNotIn("explanation", pub["items"][0])
        self.assertIn("prompt", pub["items"][0])


if __name__ == "__main__":
    unittest.main(verbosity=2)
