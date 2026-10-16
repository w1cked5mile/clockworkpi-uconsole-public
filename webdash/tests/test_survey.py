"""Unit tests for the Claude-assisted Wi-Fi survey: the store's session/waypoint lifecycle, the
analysis aggregation, and the three report renderers. stdlib unittest, no network or device
access — the survey store, analysis and report modules are pure stdlib (only snapshot.py talks to
Kismet, and it is not imported here), so this runs on the host as well as in the container:

  cd webdash && PYTHONPATH=. python3 tests/test_survey.py
  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/test_survey.py

WEBDASH_DATA_DIR is redirected to a temp dir BEFORE import, so no run touches real survey data.
"""
import os
import tempfile
import unittest

_TMP = tempfile.mkdtemp(prefix="survey-test-")
os.environ["WEBDASH_DATA_DIR"] = os.path.join(_TMP, "data")

from app.survey import analysis, report, rf, sitemap, store  # noqa: E402

assert str(store.DATA_DIR).startswith(_TMP), "tests must not use the real data dir"


def _snap(devices):
    return {"ok": True, "devices": devices, "device_count": len(devices)}


def _ap(mac, ssid, ch, freq, sig, crypt, manuf="Acme", typ="Wi-Fi AP"):
    return {"mac": mac, "phy": "IEEE802.11", "type": typ, "name": ssid, "ssid": ssid,
            "channel": ch, "freq_khz": freq, "manuf": manuf, "crypt": crypt,
            "signal_dbm": sig, "max_signal_dbm": sig + 5, "last_time": 1}


def _client(mac, sig):
    return {"mac": mac, "phy": "IEEE802.11", "type": "Wi-Fi Client", "name": None, "ssid": None,
            "channel": "6", "freq_khz": 2437000, "manuf": "Dev", "crypt": "",
            "signal_dbm": sig, "max_signal_dbm": sig, "last_time": 1}


class StoreTest(unittest.TestCase):
    def setUp(self):
        # Clean slate: remove any surveys/state a prior test left.
        for p in store.SURVEY_DIR.glob("*.json"):
            p.unlink()
        if store.STATE_PATH.exists():
            store.STATE_PATH.unlink()

    def test_start_is_exclusive(self):
        self.assertTrue(store.start("A")["ok"])
        r = store.start("B")
        self.assertFalse(r["ok"])
        self.assertIn("already active", r["error"])
        store.stop()

    def test_waypoint_requires_active(self):
        r = store.add_waypoint("X", {}, _snap([]))
        self.assertFalse(r["ok"])

    def test_lifecycle_and_undo(self):
        store.start("Walk")
        store.add_waypoint("WP1", {"grid": "EM94", "fix": "3D"},
                           _snap([_ap("AA:BB:CC:00:00:01", "N", "6", 2437000, -50, "WPA2-PSK")]))
        r = store.add_waypoint("WP2", {"grid": "EM94", "fix": "3D"}, _snap([]))
        self.assertEqual(r["waypoint_count"], 2)
        self.assertTrue(store.delete_last_waypoint()["ok"])
        self.assertEqual(len(store.get_active()["waypoints"]), 1)
        stopped = store.stop()
        self.assertTrue(stopped["ok"])
        self.assertIsNone(store.active_id())
        # Still readable after stop, and listed as completed.
        self.assertEqual(store.get(stopped["survey_id"])["status"], "completed")
        self.assertEqual(store.list_surveys()[0]["status"], "completed")

    def test_failed_snapshot_still_records_position(self):
        store.start("Walk")
        store.add_waypoint("WP1", {"grid": "EM94", "fix": "3D"},
                           {"ok": False, "error": "Kismet is not running"})
        wp = store.get_active()["waypoints"][0]
        self.assertEqual(wp["grid"], "EM94")
        self.assertEqual(wp["snapshot_error"], "Kismet is not running")
        self.assertEqual(wp["devices"], [])
        store.stop()

    def test_survey_id_cannot_escape_dir(self):
        # A path-traversal id must miss, never resolve outside the survey dir.
        self.assertIsNone(store.get("../../etc/passwd"))
        self.assertFalse(store.delete("../../etc/passwd")["ok"])


class AnalysisTest(unittest.TestCase):
    def _survey(self):
        return {
            "name": "Acme", "id": "x", "created": "t0", "stopped": "t1", "status": "completed",
            "waypoints": [
                {"seq": 1, "label": "Lobby", "grid": "EM94", "fix": "3D", "note": "", "device_count": 5,
                 "snapshot_error": None, "devices": [
                     _ap("AA:BB:CC:00:00:01", "Acme-Corp", "6", 2437000, -45, "WPA2-PSK"),
                     _ap("AA:BB:CC:00:00:02", "Acme-Guest", "6", 2437000, -52, "Open"),
                     _ap("AA:BB:CC:00:00:03", "OldAP", "3", 2422000, -60, "WEP"),
                     _ap("AA:BB:CC:00:00:04", "Acme-5G", "36", 5180000, -55, "WPA3-SAE"),
                     _client("AA:BB:CC:44:55:66", -50)]},
                {"seq": 2, "label": "Back", "grid": "EM94", "fix": "3D", "note": "", "device_count": 2,
                 "snapshot_error": None, "devices": [
                     _ap("AA:BB:CC:00:00:01", "Acme-Corp", "6", 2437000, -74, "WPA2-PSK"),
                     _ap("AA:BB:CC:00:00:05", None, "11", 2462000, -78, "WPA2-PSK")]},
                {"seq": 3, "label": "Server", "grid": "EM94", "fix": "3D", "note": "", "device_count": None,
                 "snapshot_error": "Kismet is not running", "devices": []},
            ],
        }

    def test_totals_and_dedup(self):
        a = analysis.analyze(self._survey())
        self.assertEqual(a["totals"]["unique_aps"], 5)      # 00:01 seen twice, counted once
        self.assertEqual(a["totals"]["unique_clients"], 1)
        self.assertEqual(a["totals"]["hidden_ssids"], 1)    # 00:05 has no SSID
        self.assertEqual(a["totals"]["waypoints_with_data"], 2)
        self.assertEqual(a["totals"]["waypoints_failed"], 1)

    def test_best_signal_is_strongest_seen(self):
        a = analysis.analyze(self._survey())
        corp = next(x for x in a["access_points"] if x["mac"] == "AA:BB:CC:00:00:01")
        self.assertEqual(corp["best_signal_dbm"], -45)      # not the -74 from the Back waypoint
        self.assertEqual(corp["seen_at"], ["Lobby", "Back"])

    def test_bands_security_channels(self):
        a = analysis.analyze(self._survey())
        self.assertEqual(a["bands"], {"2.4 GHz": 4, "5 GHz": 1})
        self.assertEqual(a["security"], {"WPA3": 1, "WPA2": 2, "WEP": 1, "Open": 1})
        self.assertEqual(a["channels"]["2.4 GHz"]["6"], 2)

    def test_findings_flag_weak_and_failures(self):
        titles = [f["title"] for f in analysis.analyze(self._survey())["findings"]]
        self.assertTrue(any("WEP" in t for t in titles))
        self.assertTrue(any("open network" in t for t in titles))
        self.assertTrue(any("captured no data" in t for t in titles))

    def test_zero_signal_is_not_counted_as_strongest(self):
        # Kismet reports 0 dBm for a device with no real signal measurement; it must not become
        # the "best" reading (that would show a bogus 0 dBm best signal).
        self.assertFalse(analysis.valid_signal(0))
        self.assertFalse(analysis.valid_signal(5))
        self.assertTrue(analysis.valid_signal(-57))
        survey = {"name": "z", "id": "z", "created": "t0", "stopped": "t1", "status": "completed",
                  "waypoints": [{"seq": 1, "label": "A", "grid": None, "fix": "none", "note": "",
                                 "device_count": 2, "snapshot_error": None, "devices": [
                                     _ap("AA:BB:CC:00:00:01", "N", "6", 2437000, 0, "WPA2-PSK"),
                                     _ap("AA:BB:CC:00:00:02", "M", "6", 2437000, -63, "WPA2-PSK")]}]}
        a = analysis.analyze(survey)
        self.assertEqual(a["waypoints"][0]["best_signal_dbm"], -63)  # not 0
        n = next(x for x in a["access_points"] if x["mac"] == "AA:BB:CC:00:00:01")
        self.assertIsNone(n["best_signal_dbm"])  # 0 dropped, no valid reading

    def test_band_and_bucket_helpers(self):
        self.assertEqual(analysis.band_of(2437000), "2.4 GHz")
        self.assertEqual(analysis.band_of(5180000), "5 GHz")
        self.assertEqual(analysis.band_of(6135000), "6 GHz")
        self.assertIsNone(analysis.band_of(None))
        self.assertEqual(analysis.signal_bucket(-45), "excellent")
        self.assertEqual(analysis.signal_bucket(-90), "poor")
        self.assertIsNone(analysis.signal_bucket(None))


class ReportTest(unittest.TestCase):
    def _a(self):
        return analysis.analyze(AnalysisTest()._survey())

    def test_all_three_render_without_error(self):
        a = self._a()
        for text in (report.comprehensive(a), report.executive(a), report.claude_brief(a)):
            self.assertIsInstance(text, str)
            self.assertGreater(len(text), 100)

    def test_executive_has_no_dangling_fragments(self):
        # The exec "What matters" lines must be complete sentences, not truncated at a colon.
        exec_md = report.executive(self._a())
        for line in exec_md.splitlines():
            if line.startswith("- **") and line.rstrip().endswith(("at.", "these.", "following.")):
                self.fail(f"dangling executive fragment: {line!r}")

    def test_comprehensive_lists_inventory_and_method(self):
        md = report.comprehensive(self._a())
        self.assertIn("Access point inventory", md)
        self.assertIn("receive-only", md.lower())
        self.assertIn("Acme-Corp", md)

    def test_brief_is_bounded_and_oui_only(self):
        md = report.claude_brief(self._a())
        # OUI redaction: the brief must not carry full 6-octet BSSIDs.
        self.assertNotIn("AA:BB:CC:00:00:01", md)
        self.assertIn("AA:BB:CC", md)


class RfTest(unittest.TestCase):
    def test_width_from_htmode(self):
        self.assertEqual(rf.width_mhz("HT20"), 20)
        self.assertEqual(rf.width_mhz("HT40+"), 40)
        self.assertEqual(rf.width_mhz("VHT80"), 80)
        self.assertEqual(rf.width_mhz("HT80"), 80)      # Kismet labels VHT80 "HT80" on this build
        self.assertEqual(rf.width_mhz("VHT160"), 160)
        self.assertEqual(rf.width_mhz("VHT80+80"), 80)  # first segment
        self.assertIsNone(rf.width_mhz(None))
        self.assertIsNone(rf.width_mhz("weird"))

    def test_channel_center(self):
        self.assertEqual(rf.channel_center_mhz("6", None), 2437)
        self.assertEqual(rf.channel_center_mhz("36", None), 5180)
        self.assertEqual(rf.channel_center_mhz(None, 5180000), 5180.0)  # prefers freq

    def test_span_uses_advertised_center(self):
        # ch36 HT80, Kismet center 5210 MHz -> block 5170..5250.
        lo, hi, center, w, src = rf.occupied_span_mhz(5180, 80, 5210, "HT80")
        self.assertEqual((lo, hi, center, w, src), (5170, 5250, 5210, 80, "beacon"))

    def test_span_assumed_when_no_width(self):
        lo, hi, center, w, src = rf.occupied_span_mhz(5955, None, None, None)
        self.assertEqual((w, src), (20, "assumed"))

    def test_overlap_and_relation(self):
        # ch1 (2402..2422) vs ch3 (2412..2432): overlap 10 MHz, different primary -> adjacent/harmful.
        a = rf.occupied_span_mhz(2412, 20, None, "HT20")[:2]
        b = rf.occupied_span_mhz(2422, 20, None, "HT20")[:2]
        ov = rf.overlap_mhz(a, b)
        self.assertAlmostEqual(ov, 10.0)
        self.assertEqual(rf.relation("1", "3", ov), "adjacent")
        self.assertEqual(rf.relation("6", "6", 20), "co-channel")
        self.assertEqual(rf.relation("1", "11", 0), "clear")


def _apfull(mac, ssid, ch, center, width, sig, **kw):
    lo, hi, c, w, src = rf.occupied_span_mhz(center, width, None, f"HT{width}")
    d = {"mac": mac, "phy": "IEEE802.11", "type": "Wi-Fi AP", "name": ssid, "ssid": ssid,
         "channel": ch, "freq_khz": int(center * 1000), "manuf": "Acme", "crypt": "WPA2-PSK",
         "signal_dbm": sig, "max_signal_dbm": sig, "min_signal_dbm": sig - 3, "noise_dbm": None,
         "width_mhz": w, "span_lo_mhz": lo, "span_hi_mhz": hi, "center_mhz": c, "width_source": src,
         "ht_mode": f"HT{width}", "num_clients": None, "qbss_present": False, "qbss_util_pct": None,
         "qbss_stations": None, "maxrate": None, "mobility_domain": None, "last_time": 1}
    d.update(kw)
    return d


class FocusTest(unittest.TestCase):
    def _survey(self):
        # Target ESS "Acme" on ch6 (2.4) and ch36 (5). A neighbour "Other" on ch36 (co-channel to
        # the 5 GHz member) and a rogue on ch4 (adjacent to the 2.4 member).
        wp1 = {"seq": 1, "label": "Lobby", "grid": "EM94", "fix": "3D", "lat": 32.1, "lon": -84.2,
               "note": "", "device_count": 4, "snapshot_error": None, "devices": [
                   _apfull("AA:BB:CC:10:00:01", "Acme", "6", 2437, 20, -45, num_clients=3,
                           qbss_util_pct=12.0, qbss_stations=5),
                   _apfull("AA:BB:CC:10:00:02", "Acme", "36", 5180, 80, -50),
                   _apfull("AA:BB:CC:20:00:01", "Other", "36", 5180, 80, -60),
                   _apfull("AA:BB:CC:30:00:01", "Rogue", "4", 2427, 20, -70)]}
        wp2 = {"seq": 2, "label": "Hall", "grid": "EM94", "fix": "3D", "lat": 32.11, "lon": -84.21,
               "note": "", "device_count": 2, "snapshot_error": None, "devices": [
                   _apfull("AA:BB:CC:10:00:01", "Acme", "6", 2437, 20, -66),
                   _apfull("AA:BB:CC:10:00:03", "Acme", "6", 2437, 20, -58)]}  # 2nd 2.4 AP, self co-ch
        return {"name": "F", "id": "f", "created": "t0", "stopped": "t1", "status": "completed",
                "waypoints": [wp1, wp2]}

    def test_list_ssids(self):
        ssids = {s["ssid"]: s for s in analysis.list_ssids(self._survey())}
        self.assertEqual(ssids["Acme"]["bssid_count"], 3)
        self.assertEqual(set(ssids["Acme"]["bands"]), {"2.4 GHz", "5 GHz"})

    def test_focus_membership_and_overlap(self):
        f = analysis.focus_analysis(self._survey(), "Acme")
        self.assertEqual({m["mac"] for m in f["ess_bssids"]},
                         {"AA:BB:CC:10:00:01", "AA:BB:CC:10:00:02", "AA:BB:CC:10:00:03"})
        # Lobby: the 5 GHz Acme member is co-channel with "Other" (both ch36).
        lobby = f["waypoints"][0]
        acme5 = next(o for o in lobby["observations"] if o["bssid"] == "AA:BB:CC:10:00:02")
        self.assertIn("AA:BB:CC:20:00:01", acme5["overlap"]["co_channel"])
        # The 2.4 Acme member sees the Rogue on ch4 as adjacent overlap.
        acme24 = next(o for o in lobby["observations"] if o["bssid"] == "AA:BB:CC:10:00:01")
        self.assertTrue(any(x["bssid"] == "AA:BB:CC:30:00:01" for x in acme24["overlap"]["adjacent"]))
        self.assertEqual(acme24["contention"]["qbss_util_pct"], 12.0)
        # Per-waypoint no longer carries cumulative clients; they live in the footprint.
        self.assertNotIn("observed_clients", acme24["contention"])
        fp = next(x for x in f["roaming"]["per_bssid_footprint"] if x["bssid"] == "AA:BB:CC:10:00:01")
        self.assertEqual(fp["clients_cumulative"], 3)

    def test_co_channel_radios_groups_virtual_bssids(self):
        # Two BSSIDs sharing the lower 5 octets are one physical radio. Fixture MACs use the
        # AA:BB:CC placeholder the public-sync verifier accepts, so the sibling is derived from it
        # by swapping only the top octet (the case under test).
        base = "AA:BB:CC:33:44:55"
        sibling = "02" + base[2:]
        self.assertEqual(analysis._radio_key(base), "BB:CC:33:44:55")
        self.assertEqual(analysis._radio_key(base), analysis._radio_key(sibling))
        self.assertNotEqual(analysis._radio_key(base), analysis._radio_key("AA:BB:CC:33:44:56"))

    def test_focus_self_co_channel_gated(self):
        f = analysis.focus_analysis(self._survey(), "Acme")
        pairs = f["roaming"]["self_co_channel_pairs"]
        pair = next(p for p in pairs if {p["bssid_a"], p["bssid_b"]} ==
                    {"AA:BB:CC:10:00:01", "AA:BB:CC:10:00:03"})
        # Hall: both ch6 siblings are -66/-58 (both >= -70) -> genuine contention there.
        self.assertIn("Hall", pair["contending_waypoints"])
        self.assertFalse(pair["healthy_reuse"])

    def test_focus_findings_present(self):
        f = analysis.focus_analysis(self._survey(), "Acme")
        titles = " | ".join(x["title"] for x in f["findings"])
        self.assertIn("self co-channel", titles.lower())

    def test_focus_reports_render(self):
        f = analysis.focus_analysis(self._survey(), "Acme")
        md = report.focus_markdown(f)
        self.assertIn("Acme", md)
        self.assertIn("Roaming footprint", md)
        self.assertIn("Findings", md)
        self.assertIn("Best server per band", md)

    def test_sitemap_available_with_coords(self):
        f = analysis.focus_analysis(self._survey(), "Acme")
        self.assertTrue(sitemap.available(f["waypoints"]))
        svg = sitemap.build(f["waypoints"], "strongest_signal_dbm", "t")
        self.assertIsNotNone(svg)
        self.assertTrue(svg.startswith("<svg"))

    def test_sitemap_unavailable_without_coords(self):
        wps = [{"seq": 1, "label": "A", "lat": None, "lon": None, "strongest_signal_dbm": -50}]
        self.assertFalse(sitemap.available(wps))
        self.assertIsNone(sitemap.build(wps))


if __name__ == "__main__":
    unittest.main(verbosity=2)
