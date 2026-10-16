"""Unit tests for the phone-widget summary and its token. stdlib unittest, no fastapi, network or
device, so it runs on the host as well as in the container:

  cd webdash && PYTHONPATH=. python3 tests/test_widget.py
  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/test_widget.py
"""
import os
import stat
import tempfile
import unittest
from pathlib import Path

from app import widget

STATUS = {
    "generated_at": 1_760_000_000.0,
    "system": {"cpu_percent": 12.5, "temp_c": 51.2, "temp_avg_1h_c": 49.9,
               "disk": {"percent": 31.0}, "mem": {"percent": 40.1}, "uptime_s": 7200,
               "undervoltage": False},
    "aiov2": {"state": "ok",
              "rails": {"GPS": {"on": True}, "LORA": {"on": True}, "SDR": {"on": False},
                        "USB": {"on": True}},
              "power_num": {"voltage_v": 3.92, "current_a": -0.95, "power_w": 3.7,
                            "capacity_pct": 41.0, "on_battery": True}},
    "gps": {"state": "running", "fix": "3D", "lat": 34.1234, "lon": -81.5678, "grid": "EM94ab",
            "satellites_used": 12, "satellites_visible": 18, "hdop": 0.7},
    "kismet": {"state": "running", "devices": 314},
    "mesh": {"state": "running", "nodes_seen": 27, "rx_nodes": 5},
    "adsb": {"state": "running", "aircraft_count": 9},
}

HISTORY = [{"ts": 1_760_000_000.0 - 30 * i, "voltage_v": 4.0 - 0.001 * i} for i in range(240)][::-1]


class SummaryTest(unittest.TestCase):
    def test_no_coordinates_anywhere(self):
        s = widget.summary(STATUS, HISTORY)
        flat = repr(s)
        self.assertNotIn("34.1234", flat)
        self.assertNotIn("-81.5678", flat)
        self.assertNotIn("lat", s["gps"])
        self.assertNotIn("lon", s["gps"])

    def test_grid_truncated_to_four_characters(self):
        self.assertEqual(widget.summary(STATUS, [])["gps"]["grid"], "EM94")

    def test_fields(self):
        s = widget.summary(STATUS, HISTORY)
        self.assertEqual(s["host"], "fancy")
        self.assertEqual(s["power"]["voltage_v"], 3.92)
        self.assertTrue(s["power"]["on_battery"])
        self.assertEqual(s["power"]["level"], "ok")
        self.assertEqual(s["gps"]["fix"], "3D")
        self.assertEqual(s["gps"]["sats"], 12)
        self.assertEqual(s["system"]["temp_c"], 51.2)
        self.assertEqual(s["rails"], {"GPS": True, "LORA": True, "SDR": False, "USB": True})
        self.assertEqual(s["kismet"], {"state": "running", "devices": 314})
        self.assertEqual(s["mesh"], {"state": "running", "nodes": 27})
        self.assertEqual(s["adsb"], {"state": "running", "aircraft": 9})
        self.assertEqual(s["generated_at"], 1_760_000_000.0)

    def test_voltage_levels(self):
        # Thresholds from docs/reference/power-budget.md: plug in by 3.60 V; cut-out seen ~3.5 V.
        for v, level in ((3.95, "ok"), (3.70, "ok"), (3.69, "low"), (3.60, "low"),
                         (3.59, "plug_in"), (3.40, "plug_in")):
            st = {**STATUS, "aiov2": {**STATUS["aiov2"],
                                      "power_num": {"voltage_v": v, "on_battery": True}}}
            self.assertEqual(widget.summary(st, [])["power"]["level"], level, v)

    def test_charging_is_never_a_warning(self):
        st = {**STATUS, "aiov2": {**STATUS["aiov2"],
                                  "power_num": {"voltage_v": 3.50, "on_battery": False}}}
        self.assertEqual(widget.summary(st, [])["power"]["level"], "charging")

    def test_voltage_history_downsampled(self):
        hist = widget.summary(STATUS, HISTORY)["power"]["history_v"]
        self.assertEqual(len(hist), widget.HISTORY_POINTS)
        self.assertEqual(hist[-1], 4.0)  # newest sample kept as the last point
        self.assertTrue(all(isinstance(v, float) for v in hist))

    def test_history_skips_missing_samples(self):
        hist = [{"ts": 1, "voltage_v": None}, {"ts": 2, "voltage_v": 3.9}]
        self.assertEqual(widget.summary(STATUS, hist)["power"]["history_v"], [3.9])

    def test_degraded_status(self):
        st = {"generated_at": 1.0, "system": {}, "aiov2": {"state": "unavailable"},
              "gps": {"state": "stopped"}, "kismet": {"state": "stopped"},
              "mesh": {}, "adsb": None}
        s = widget.summary(st, [])
        self.assertIsNone(s["power"]["voltage_v"])
        self.assertEqual(s["power"]["level"], "unknown")
        self.assertEqual(s["gps"]["fix"], "none")
        self.assertIsNone(s["gps"]["grid"])
        self.assertEqual(s["rails"], {})
        self.assertEqual(s["mesh"]["state"], "unavailable")
        self.assertEqual(s["adsb"]["state"], "unavailable")


class TokenTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "widget_token.sha256"

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_token_file_rejects_everything(self):
        self.assertFalse(widget.token_ok("anything", self.path))
        self.assertFalse(widget.token_ok("", self.path))

    def test_rotate_then_verify(self):
        tok = widget.rotate_token(self.path)
        self.assertGreaterEqual(len(tok), 40)
        self.assertTrue(widget.token_ok(tok, self.path))
        self.assertFalse(widget.token_ok(tok + "x", self.path))
        self.assertFalse(widget.token_ok(None, self.path))

    def test_only_hash_is_stored(self):
        tok = widget.rotate_token(self.path)
        self.assertNotIn(tok, self.path.read_text())
        self.assertEqual(stat.S_IMODE(os.stat(self.path).st_mode), 0o600)

    def test_rotate_invalidates_old_token(self):
        old = widget.rotate_token(self.path)
        new = widget.rotate_token(self.path)
        self.assertFalse(widget.token_ok(old, self.path))
        self.assertTrue(widget.token_ok(new, self.path))

    def test_bearer_parsing(self):
        self.assertEqual(widget.bearer("Bearer abc"), "abc")
        self.assertEqual(widget.bearer("bearer  abc "), "abc")
        self.assertIsNone(widget.bearer("Basic abc"))
        self.assertIsNone(widget.bearer(None))


if __name__ == "__main__":
    unittest.main()
