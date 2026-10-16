"""Tests for the host SDR bridge's tuner ownership (host-helpers/sdr-bridge.py): a new listen or
scan takes the tuner from the live stream (latest wins) instead of getting 409 "SDR is busy".

Why: the page's listen() drops the old stream and requests the new one at once, but the bridge
only noticed the old client had gone on its next failed write (~3 s, measured 2026-10-11), so a
station switch always hit 409.

The bridge runs in-process on an ephemeral port with stub binaries first on PATH: lsusb reports an
RTL2838, sudo never reaches systemd (readsb reads as inactive), rtl_fm emits silence and logs its
start/stop, and ffmpeg is `cat`. No tuner, no radio, nothing transmits. Host only — the bridge is
a host helper, not in the container image:

  cd webdash && python3 tests/test_sdr_bridge.py
"""
import importlib.util
import json
import os
import stat
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

_BRIDGE = Path(__file__).resolve().parent.parent / "host-helpers/sdr-bridge.py"

_STUBS = {
    "lsusb": 'echo "Bus 001 Device 029: ID 0bda:2838 Realtek Semiconductor Corp. RTL2838 DVB-T"\n',
    "sudo": 'case "$*" in *is-active*) echo inactive;; esac\nexit 0\n',
    "rtl_fm": ('echo "start $$" >> "$SDR_TEST_LOG"\n'
               'trap \'echo "stop $$" >> "$SDR_TEST_LOG"; exit 0\' TERM INT\n'
               'while :; do head -c 9600 /dev/zero || exit 0; sleep 0.1; done\n'),
    "ffmpeg": "exec cat\n",
    # OpenWebRX is controlled through docker; the status poll runs `docker inspect`. The stub makes
    # the container read as not-running and compose up/stop succeed, so owrx arbitration is tested
    # off the _busy flag without a real container.
    "docker": ('case "$*" in\n'
               '  *inspect*) echo false;;\n'
               '  *) exit 0;;\n'
               'esac\n'),
}


class _Aiov2Stub(BaseHTTPRequestHandler):
    """Stands in for the aiov2 bridge's GET /status, which the SDR bridge reads before starting
    OpenWebRX. `usb` is the USB rail state it reports; None makes /status answer 503."""
    usb = False

    def log_message(self, *args):
        pass

    def do_GET(self):
        if _Aiov2Stub.usb is None:
            self.send_response(503)
            self.end_headers()
            return
        body = json.dumps({"ok": True, "rails": {"USB": {"gpio": 23, "on": _Aiov2Stub.usb}}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)


@unittest.skipUnless(_BRIDGE.exists(), "host-helpers/sdr-bridge.py not present (container run)")
class TunerOwnershipTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Never read the real aiov2 bridge: the owrx tests must not depend on Fancy's rail state.
        cls.aiov2 = ThreadingHTTPServer(("127.0.0.1", 0), _Aiov2Stub)
        threading.Thread(target=cls.aiov2.serve_forever, daemon=True).start()
        os.environ["AIOV2_STATUS_URL"] = f"http://127.0.0.1:{cls.aiov2.server_address[1]}/status"
        cls.tmp = tempfile.mkdtemp(prefix="sdr-bridge-test-")
        bindir = Path(cls.tmp, "bin")
        bindir.mkdir()
        for name, body in _STUBS.items():
            p = bindir / name
            p.write_text("#!/bin/sh\n" + body)
            p.chmod(p.stat().st_mode | stat.S_IXUSR)
        cls.log = Path(cls.tmp, "rtl.log")
        os.environ["SDR_TEST_LOG"] = str(cls.log)
        os.environ["PATH"] = f"{bindir}{os.pathsep}{os.environ['PATH']}"
        spec = importlib.util.spec_from_file_location("sdr_bridge", _BRIDGE)
        cls.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.m)
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), cls.m.Handler)
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.aiov2.shutdown()

    def setUp(self):
        self.log.write_text("")
        self.open = []
        _Aiov2Stub.usb = False

    def tearDown(self):
        for r in self.open:
            r.close()
        self._wait_busy(None)

    # --- helpers ---------------------------------------------------------------------------------

    def _listen(self, freq=100_000_000):
        r = urllib.request.urlopen(f"{self.base}/listen?mode=wbfm&freq={freq}", timeout=10)
        self.open.append(r)
        return r

    def _status(self):
        with urllib.request.urlopen(f"{self.base}/hunt/status", timeout=5) as r:
            return json.load(r)

    def _wait_busy(self, want, timeout=8.0):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if self._status()["busy"] == want:
                return True
            time.sleep(0.1)
        return False

    def _ends_within(self, resp, seconds):
        """True if the stream reaches EOF within `seconds` (the bridge closed it)."""
        resp.fp.raw._sock.settimeout(seconds)
        end = time.monotonic() + seconds
        try:
            while time.monotonic() < end:
                if not resp.read(4096):
                    return True
        except (TimeoutError, OSError):
            return False
        return False

    # --- tests -----------------------------------------------------------------------------------

    def test_second_listen_takes_the_tuner(self):
        first = self._listen()
        self.assertTrue(first.read(4096))
        second = self._listen(101_100_000)
        self.assertEqual(second.status, 200)
        self.assertTrue(second.read(4096))
        self.assertTrue(self._ends_within(first, 5), "the preempted stream should be closed")

    def test_switch_straight_after_drop(self):
        first = self._listen()
        first.read(4096)
        first.close()
        second = self._listen(101_100_000)  # what listen() does after stopListen()
        self.assertEqual(second.status, 200)
        self.assertTrue(second.read(4096))

    def test_old_stream_does_not_release_the_new_ones_claim(self):
        first = self._listen()
        first.read(4096)
        second = self._listen(101_100_000)
        self.assertTrue(self._ends_within(first, 5))
        time.sleep(0.5)  # let the old handler's cleanup run
        self.assertEqual(self._status()["busy"], "listen")
        self.assertTrue(second.read(4096))

    def test_tuner_never_shared(self):
        first = self._listen()
        first.read(4096)
        second = self._listen(101_100_000)
        second.read(4096)
        events = self.log.read_text().split()
        # Pairs of (event, pid). The first rtl_fm must stop before the second starts.
        seq = [(events[i], events[i + 1]) for i in range(0, len(events), 2)]
        running = 0
        for ev, _pid in seq:
            running += 1 if ev == "start" else -1
            self.assertLessEqual(running, 1, f"two rtl_fm on one tuner: {seq}")

    def test_listen_takes_over_from_scan(self):
        scan = urllib.request.urlopen(f"{self.base}/listen?scan=118000000&squelch=150", timeout=10)
        self.open.append(scan)
        self.assertTrue(scan.read(4096))
        self.assertTrue(self._wait_busy("scan", 2))
        listen = self._listen()
        self.assertEqual(listen.status, 200)
        self.assertTrue(listen.read(4096))
        self.assertTrue(self._ends_within(scan, 6))
        self.assertEqual(self._status()["busy"], "listen")

    def test_adsb_still_blocks_listen(self):
        req = urllib.request.Request(f"{self.base}/adsb", data=b'{"action": "start"}',
                                     headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=5).close()
        try:
            with self.assertRaises(urllib.error.HTTPError) as cm:
                self._listen()
            self.assertEqual(cm.exception.code, 409)
            self.assertIn("adsb", json.load(cm.exception)["error"])
        finally:
            req = urllib.request.Request(f"{self.base}/adsb", data=b'{"action": "stop"}',
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=5).close()

    def _owrx(self, action):
        req = urllib.request.Request(f"{self.base}/owrx",
                                     data=json.dumps({"action": action}).encode(),
                                     headers={"Content-Type": "application/json"})
        return urllib.request.urlopen(req, timeout=10)

    def test_owrx_claims_the_tuner_and_blocks_listen(self):
        self._owrx("start").close()
        self.assertEqual(self._status()["busy"], "owrx")
        try:
            with self.assertRaises(urllib.error.HTTPError) as cm:
                self._listen()
            self.assertEqual(cm.exception.code, 409)
            self.assertIn("owrx", json.load(cm.exception)["error"])
        finally:
            self._owrx("stop").close()
        self.assertIsNone(self._status()["busy"])

    def test_owrx_refused_while_a_listen_holds_the_tuner(self):
        self._listen()
        self._wait_busy("listen")
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self._owrx("start")
        self.assertEqual(cm.exception.code, 409)
        self.assertIn("listen", json.load(cm.exception)["error"])

    # Starting OpenWebRX with the USB rail on preceded a power cut (2026-10-15, cause unverified),
    # so the bridge refuses to start it unless the aiov2 bridge reports the USB rail off.
    def test_owrx_refused_while_the_usb_rail_is_on(self):
        _Aiov2Stub.usb = True
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self._owrx("start")
        self.assertEqual(cm.exception.code, 409)
        self.assertIn("USB rail is on", json.load(cm.exception)["error"])
        self.assertIsNone(self._status()["busy"])

    def test_owrx_refused_when_the_usb_rail_state_is_unknown(self):
        _Aiov2Stub.usb = None
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self._owrx("start")
        self.assertEqual(cm.exception.code, 409)
        self.assertIn("USB rail state unknown", json.load(cm.exception)["error"])
        self.assertIsNone(self._status()["busy"])

    def test_owrx_stop_is_not_gated_on_the_usb_rail(self):
        _Aiov2Stub.usb = True
        self._owrx("stop").close()


@unittest.skipUnless(_BRIDGE.exists(), "host-helpers/sdr-bridge.py not present (container run)")
class SweepTraceTest(unittest.TestCase):
    """parse_rtl_power (peaks) and sweep_trace (the whole band the webdash graphs) read the same
    rtl_power CSV; the trace must carry every bin and the floor/threshold the peak finder used."""

    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("sdr_bridge_parse", _BRIDGE)
        cls.m = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.m)

    # One rtl_power line: lo, hi, step, n, then one dB per bin. Floor ~ -30, a peak at the 3rd bin.
    CSV = "2026-10-14, 00:00:00, 88000000, 88500000, 100000, 100, -30.0, -29.5, -8.0, -31.0, -30.5\n"

    def test_trace_has_every_bin_and_floor(self):
        t = self.m.sweep_trace(self.CSV)
        self.assertEqual(len(t["points"]), 5)                 # all five bins, not just the peak
        self.assertEqual(t["lo_hz"], 88_000_000)
        self.assertEqual(t["hi_hz"], 88_400_000)              # lo + 4*step
        self.assertEqual(t["threshold_db"], round(t["floor_db"] + self.m.PEAK_MARGIN_DB, 1))
        # points are [freq_hz, dB] sorted by frequency
        self.assertEqual(t["points"][2], [88_200_000, -8.0])

    def test_peak_and_trace_agree(self):
        stations = self.m.parse_rtl_power(self.CSV, 100_000)
        t = self.m.sweep_trace(self.CSV)
        self.assertEqual(stations[0]["freq_hz"], 88_200_000)  # the -8 dB bin clears the +6 dB line
        self.assertEqual(stations[0]["snr_db"], round(stations[0]["power_db"] - t["floor_db"], 1))

    def test_empty_sweep_is_none(self):
        self.assertIsNone(self.m.sweep_trace("garbage\n\n"))
        self.assertEqual(self.m.parse_rtl_power("garbage\n\n", 100_000), [])


if __name__ == "__main__":
    unittest.main(verbosity=1)
