"""Unit tests for Detect (offensive-device detection): rule validation and matching, the contact
log's upsert/sighting/summary logic, Kismet alert mapping, and the exporters. stdlib unittest, no
network or device access — engine.py (the only module that talks to Kismet) is not imported, so
this runs on the host as well as in the container:

  cd webdash && PYTHONPATH=. python3 tests/test_detect.py
  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/test_detect.py

WEBDASH_DATA_DIR is redirected to a temp dir BEFORE import, so no run touches the real log.
The rules used here are made-up test patterns, not device signatures. Test MACs use the
AA:BB:CC placeholder prefix that the public-sync verifier (publish/make-public.sh) accepts.
"""
import json
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp(prefix="detect-test-")
os.environ["WEBDASH_DATA_DIR"] = os.path.join(_TMP, "data")

from app.detect import export, observe, rules, store  # noqa: E402

assert str(store.DATA_DIR).startswith(_TMP), "tests must not use the real data dir"


def _rule(**kw):
    r = {"id": "t1", "class": "other", "radio": "wifi", "field": "ssid", "match": "exact",
         "pattern": "fancy-detect-test", "confidence": "low"}
    r.update(kw)
    return r


def _dev(mac="AA:BB:CC:33:44:55", ssid="fancy-detect-test", sig=-60, t=1000):
    return {"mac": mac, "ssid": ssid, "name": ssid, "manuf": "Acme", "channel": "6",
            "signal_dbm": sig, "last_time": t}


class RulesTest(unittest.TestCase):
    def test_valid_rule_loads(self):
        got, errs = rules.parse({"rules": [_rule()]})
        self.assertEqual(errs, [])
        self.assertEqual(got[0]["id"], "t1")

    def test_bad_rules_are_reported_not_fatal(self):
        got, errs = rules.parse({"rules": [_rule(), _rule(id="bad id"), _rule(id="t2", **{"class": "x"}),
                                           _rule(id="t3", match="regex", pattern="("), _rule()]})
        self.assertEqual([r["id"] for r in got], ["t1"])
        self.assertEqual(len(errs), 4)  # bad id, bad class, bad regex, duplicate t1

    def test_wrong_shape(self):
        self.assertEqual(rules.parse([])[0], [])
        self.assertTrue(rules.parse({"rules": "x"})[1])

    def test_missing_file_is_empty_not_error(self):
        self.assertEqual(rules.load(rules.RULES_PATH.with_name("nope.json")), ([], []))

    def test_bad_json_file(self):
        p = rules.RULES_PATH.with_name("bad.json")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("{not json")
        got, errs = rules.load(p)
        self.assertEqual(got, [])
        self.assertIn("not valid JSON", errs[0])

    def test_match_modes(self):
        cases = [("exact", "Fancy-Detect-Test", True), ("exact", "fancy", False),
                 ("prefix", "fancy-", True), ("contains", "detect", True),
                 ("regex", r"^fancy-\w+-test$", True), ("regex", r"^nope", False)]
        for mode, pat, want in cases:
            rs, _ = rules.parse({"rules": [_rule(match=mode, pattern=pat)]})
            self.assertEqual(bool(rules.match(_dev(), rs, "wifi")), want, (mode, pat))

    def test_case_sensitive(self):
        rs, _ = rules.parse({"rules": [_rule(pattern="Fancy-detect-test", case_sensitive=True)]})
        self.assertIsNone(rules.match(_dev(), rs, "wifi"))

    def test_mac_ignores_separators(self):
        rs, _ = rules.parse({"rules": [_rule(field="mac", match="prefix", pattern="aabbcc")]})
        self.assertTrue(rules.match(_dev(), rs, "wifi"))

    def test_strongest_rule_wins_and_radio_filters(self):
        rs, _ = rules.parse({"rules": [_rule(), _rule(id="t2", match="contains", pattern="detect",
                                                       confidence="high"),
                                       _rule(id="t3", radio="ble", field="name", confidence="high")]})
        self.assertEqual(rules.match(_dev(), rs, "wifi")["id"], "t2")
        self.assertIsNone(rules.match({"ssid": None, "name": None}, rs, "wifi"))

    def test_describe(self):
        rs, _ = rules.parse({"rules": [_rule()]})
        self.assertEqual(rules.describe(rs[0]), "Wi-Fi ssid is “fancy-detect-test”")


class StoreTest(unittest.TestCase):
    def setUp(self):
        store.reset_cache()
        for p in (store.LOG_PATH, store.STATE_PATH):
            if p.exists():
                p.unlink()

    def _fold(self, devs, alerts=(), conf="low", grid="EM94ab"):
        rs, _ = rules.parse({"rules": [_rule(confidence=conf)]})
        return observe.fold(list(devs), list(alerts), rs, grid)

    def test_new_contact_then_sightings(self):
        new = self._fold([_dev(t=1000)])
        self.assertEqual(len(new), 1)
        self.assertEqual(new[0]["grid_first"], "EM94ab")
        self.assertEqual(new[0]["addr_type"], "local")
        # Same Kismet state re-read: not a new sighting.
        self.assertEqual(self._fold([_dev(t=1000)]), [])
        self.assertEqual(store.records()[0]["sightings"], 1)
        # Newer sighting: count, RSSI last/peak, grid last.
        self._fold([_dev(t=1010, sig=-40)], grid="EM94ac")
        r = store.records()[0]
        self.assertEqual((r["sightings"], r["rssi_first"], r["rssi_peak"], r["rssi_last"]), (2, -60, -40, -40))
        self.assertEqual((r["grid_first"], r["grid_last"]), ("EM94ab", "EM94ac"))

    def test_persists_across_reload(self):
        self._fold([_dev()])
        store.reset_cache()
        self.assertEqual(len(store.records()), 1)

    def test_no_match_no_record(self):
        self._fold([_dev(ssid="someone-else")])
        self.assertEqual(store.records(), [])

    def test_ssids_accumulate_without_duplicates(self):
        rs, _ = rules.parse({"rules": [_rule(field="mac", match="exact", pattern="AA:BB:CC:33:44:55")]})
        observe.fold([_dev(ssid="a", t=1), _dev(ssid="b", t=2), _dev(ssid="a", t=3)], [], rs, None)
        self.assertEqual(store.records()[0]["ssids"], ["a", "b"])

    def test_kismet_alerts(self):
        alerts = [{"kismet.alert.header": "DEAUTHFLOOD", "kismet.alert.transmitter_mac": "AA:BB:CC:00:00:09",
                   "kismet.alert.timestamp": 1000, "kismet.alert.channel": 6, "kismet.alert.text": "flood"},
                  {"kismet.alert.header": "SOMEOTHER", "kismet.alert.timestamp": 1000},
                  {"kismet.alert.text": "no header"}]
        new = self._fold([], alerts)
        by = {r["name"]: r for r in new}
        self.assertEqual(set(by), {"DEAUTHFLOOD", "SOMEOTHER"})
        self.assertEqual((by["DEAUTHFLOOD"]["cls"], by["DEAUTHFLOOD"]["confidence"]), ("deauth_flood", "medium"))
        self.assertEqual(by["DEAUTHFLOOD"]["addr_type"], "local")  # 0xAA has the LA bit set
        self.assertEqual((by["SOMEOTHER"]["cls"], by["SOMEOTHER"]["ident"]), ("other", None))

    def test_summary_and_seen_marker(self):
        import time
        store.mark_seen(0)
        now = time.time()
        self._fold([_dev(t=now)], conf="high")
        s = store.summary(now=now)
        self.assertEqual((s["total"], s["now_count"], s["unseen_high"]), (1, 1, 1))
        self.assertEqual(s["now_by_class"], {"other": 1})
        self.assertNotIn("ident", s["newest"])  # the status snapshot carries no addresses
        store.mark_seen(now + 1)
        self.assertEqual(store.summary(now=now)["unseen_high"], 0)
        self.assertEqual(store.summary(now=now + 600)["now_count"], 0)

    def test_place_delete_clear(self):
        self._fold([_dev()])
        rid = store.records()[0]["id"]
        self.assertEqual(store.set_place(rid, "  hall B " + "x" * 200)["record"]["place"][:6], "hall B")
        self.assertEqual(len(store.records()[0]["place"]), store.MAX_PLACE)
        self.assertFalse(store.set_place("nope", "x")["ok"])
        self.assertTrue(store.delete(rid)["ok"])
        self._fold([_dev(t=5)])
        self.assertEqual(store.clear()["deleted"], 1)
        self.assertEqual(store.records(), [])

    def test_filtered(self):
        rs, _ = rules.parse({"rules": [_rule(), _rule(id="t2", field="mac", match="exact",
                                                       pattern="AA:BB:CC:00:00:01", confidence="high",
                                                       **{"class": "pineapple"})]})
        observe.fold([_dev(t=100), _dev(mac="AA:BB:CC:00:00:01", ssid="x", t=200)], [], rs, None)
        self.assertEqual(len(store.filtered()), 2)
        self.assertEqual([r["cls"] for r in store.filtered(min_conf="high")], ["pineapple"])
        self.assertEqual([r["cls"] for r in store.filtered(cls="other")], ["other"])
        self.assertEqual(len(store.filtered(since=150)), 1)

    def test_watch_and_coverage(self):
        self.assertFalse(store.state()["armed"])
        self.assertTrue(store.set_armed(True)["armed_since"])
        store.mark_listening("wifi", 100, 30)
        store.mark_listening("wifi", 120, 30)
        store.mark_listening("wifi", 200, 30)  # gap > 30: a new interval
        c = store.coverage(0)["wifi"]
        self.assertEqual((c["seconds"], len(c["intervals"])), (20, 2))
        self.assertIsNone(store.set_armed(False)["armed_since"])


class ExportTest(unittest.TestCase):
    def setUp(self):
        self.recs = [{"cls": "other", "confidence": "low", "rule_text": "Wi-Fi ssid is “x”",
                      "name": "=HYPERLINK(\"evil\")", "ident": "AA:BB:CC:33:44:55", "addr_type": "local",
                      "ssids": ["a|b", "c"], "radio": "wifi", "channel": "6", "rssi_first": -60,
                      "rssi_peak": -40, "rssi_last": -50, "sightings": 3, "grid_first": "EM94ab",
                      "grid_last": "EM94ab", "place": "hall", "source": "kismet-device",
                      "first_seen": 0, "last_seen": 60, "detail": None}]

    def test_csv_neutralises_formulas(self):
        out = export.to_csv(self.recs)
        self.assertIn("'=HYPERLINK", out)
        self.assertIn("-40", out)  # numbers untouched

    def test_json(self):
        d = json.loads(export.to_json(self.recs))
        self.assertEqual(d["count"], 1)
        self.assertEqual(d["contacts"][0]["last_seen_utc"], "1970-01-01T00:01:00Z")
        self.assertNotIn("lat", json.dumps(d))

    def test_markdown_escapes_pipes(self):
        self.recs[0]["place"] = "hall|B"
        out = export.to_markdown(self.recs)
        self.assertIn("hall\\|B", out)
        self.assertEqual(out.count("\n| "), 2)  # header + one row (separator starts "|---")


if __name__ == "__main__":
    unittest.main(verbosity=1)
