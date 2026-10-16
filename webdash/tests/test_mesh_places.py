"""Unit tests for the mesh sender-place label: the offline nearest-place lookup (app/places.py),
the GeoNames TSV builder (host-helpers/places-build.py) and the mesh collector's use of a node's
NodeDB position. stdlib unittest, no network, no meshtasticd — runs on the host or in the container:

  cd webdash && PYTHONPATH=. python3 tests/test_mesh_places.py
  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/test_mesh_places.py

WEBDASH_DATA_DIR is redirected to a temp dir holding a tiny synthetic places.tsv BEFORE import, so
no run reads the real place list. The coordinates below are made-up test points, not locations.
"""
import importlib.util
import io
import os
import tempfile
import time
import unittest
import zipfile
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="places-test-")
os.environ["WEBDASH_DATA_DIR"] = _TMP
Path(_TMP, "places.tsv").write_text(
    "# test fixture\n"
    "Alpha\tGA\t31.5000\t-84.1000\n"
    "Bravo\tGA\t31.9900\t-84.0100\n"   # just inside a cell edge
    "Charlie\tBavaria, DE\t48.1000\t11.5000\n"
    "Wrap\tFJ\t-17.0000\t179.9500\n",
    encoding="utf-8")

from app import places  # noqa: E402
from app.collectors import mesh  # noqa: E402

assert str(places.PLACES_PATH).startswith(_TMP), "tests must not use the real place list"


class NearestTest(unittest.TestCase):
    def test_near_label_within_threshold(self):
        self.assertEqual(places.describe(31.51, -84.11), "near Alpha, GA")

    def test_distance_label_beyond_threshold(self):
        label = places.describe(31.70, -84.10)  # ~22 km north of Alpha
        self.assertRegex(label, r"^~\d+ km from (Alpha|Bravo), GA$")

    def test_finds_nearer_place_across_cell_edge(self):
        # Query in cell (32, -84); Bravo sits in cell (31, -84) a few hundred metres away.
        label, km = places.nearest(32.001, -84.01)
        self.assertEqual(label, "Bravo, GA")
        self.assertLess(km, 2)

    def test_antimeridian_wrap(self):
        label, km = places.nearest(-17.0, -179.99)
        self.assertEqual(label, "Wrap, FJ")
        self.assertLess(km, 10)

    def test_nothing_nearby(self):
        self.assertIsNone(places.describe(-60.0, -30.0))  # southern ocean, far from any fixture

    def test_region_with_country(self):
        self.assertEqual(places.describe(48.1, 11.5), "near Charlie, Bavaria, DE")


class _Iface:
    def __init__(self, nodes):
        self.nodes = nodes


class SenderPlaceTest(unittest.TestCase):
    def test_float_position(self):
        iface = _Iface({"!a": {"position": {"latitude": 31.5, "longitude": -84.1}}})
        self.assertEqual(mesh._sender_place(iface, "!a"), "near Alpha, GA")

    def test_integer_position(self):
        iface = _Iface({"!a": {"position": {"latitudeI": 315000000, "longitudeI": -841000000}}})
        self.assertEqual(mesh._sender_place(iface, "!a"), "near Alpha, GA")

    def test_no_position_or_null_island(self):
        iface = _Iface({"!a": {}, "!b": {"position": {"latitude": 0, "longitude": 0}}})
        self.assertIsNone(mesh._sender_place(iface, "!a"))
        self.assertIsNone(mesh._sender_place(iface, "!b"))
        self.assertIsNone(mesh._sender_place(iface, "!missing"))
        self.assertIsNone(mesh._sender_place(iface, None))

    def test_stale_position_says_age(self):
        old = time.time() - 3 * 86400
        iface = _Iface({"!a": {"position": {"latitude": 31.5, "longitude": -84.1, "time": old}}})
        self.assertEqual(mesh._sender_place(iface, "!a"), "near Alpha, GA (pos 3d old)")

    def test_label_never_contains_coordinates(self):
        iface = _Iface({"!a": {"position": {"latitude": 31.51234, "longitude": -84.10987}}})
        self.assertNotIn("31.5", mesh._sender_place(iface, "!a"))

    def test_fill_places_retries_recent_only(self):
        self.assertTrue(places.available())  # load synchronously; the app does this on a thread
        iface = _Iface({"!a": {"position": {"latitude": 31.5, "longitude": -84.1}}})
        now = time.time()
        recent = {"ts": now, "from_id": "!a", "mine": False, "place": None}
        old = {"ts": now - mesh.PLACE_RETRY_S - 5, "from_id": "!a", "mine": False, "place": None}
        mine = {"ts": now, "from_id": None, "mine": True, "place": None}
        mesh._MESSAGES.clear()
        mesh._MESSAGES.extend([recent, old, mine])
        mesh._fill_places(iface)
        self.assertEqual(recent["place"], "near Alpha, GA")
        self.assertIsNone(old["place"])
        self.assertIsNone(mine["place"])
        mesh._MESSAGES.clear()


# The builder is a host helper, not in the container image (and a script piped in over stdin has
# no __file__ directory), so this runs on the host only.
_BUILDER = Path(__file__).resolve().parent.parent / "host-helpers/places-build.py"


@unittest.skipUnless(_BUILDER.exists(), "host-helpers/places-build.py not present (container run)")
class BuilderTest(unittest.TestCase):
    def test_build_rows(self):
        spec = importlib.util.spec_from_file_location("places_build", _BUILDER)
        pb = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pb)
        cols = lambda name, lat, lon, cc, a1: "\t".join(
            ["1", name, name, "", lat, lon, "P", "PPL", cc, "", a1, "", "", "", "600"])
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as z:
            z.writestr("cities500.txt", "\n".join([
                cols("Alpha", "31.5", "-84.1", "US", "GA"),
                cols("Charlie", "48.1", "11.5", "DE", "02"),
                cols("Broken", "not-a-number", "1", "XX", ""),
            ]) + "\n")
        rows = pb.build(buf.getvalue(), "DE.02\tBavaria\tBavaria\t1\n")
        self.assertEqual(rows[0], "Alpha\tGA\t31.5000\t-84.1000")
        self.assertEqual(rows[1], "Charlie\tBavaria, DE\t48.1000\t11.5000")
        self.assertEqual(len(rows), 2)  # the malformed row is skipped, not fatal


class MissingFileTest(unittest.TestCase):
    def test_missing_file_disables_quietly(self):
        saved = (places.PLACES_PATH, places._INDEX, places._LOADED)
        try:
            places.PLACES_PATH = Path(_TMP, "nope.tsv")
            places._INDEX, places._LOADED = None, False
            self.assertFalse(places.available())
            self.assertIsNone(places.describe(31.5, -84.1))
        finally:
            places.PLACES_PATH, places._INDEX, places._LOADED = saved


if __name__ == "__main__":
    unittest.main(verbosity=1)
