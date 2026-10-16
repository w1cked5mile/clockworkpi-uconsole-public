"""Offline nearest-place lookup: a position -> "near Albany, GA" / "~18 km from Albany, GA".

Used by the mesh collector to label received messages with roughly where the sender is, from
their last position in meshtasticd's NodeDB. Entirely local: the place list is GeoNames cities500,
built once on the host by host-helpers/places-build.py into WEBDASH_DATA_DIR/places.tsv. No
sender position ever goes to an online geocoder, and only the place label (never lat/lon) leaves
this module — the browser and the logs see the town name, not coordinates.

If places.tsv is missing or unreadable, available() is False and describe() returns None; the
mesh view just shows no place. The file is loaded once, on its own background thread started by
preload() (measured 2026-10-09 on the CM4: 1.4 s and ~48 MB for 236k places), so neither the event
loop nor the mesh collector's lock ever waits on it; callers check loaded() first.

Index: places bucketed into 1°x1° cells; a lookup searches rings of cells outward from the query
cell and stops one ring after the first hit, so a nearer place just over a cell edge isn't missed.
Nothing within MAX_RING cells (several hundred km) means open ocean or wilderness -> None.
"""
import math
import os
import threading
from pathlib import Path

DATA_DIR = Path(os.environ.get("WEBDASH_DATA_DIR", "/data"))
PLACES_PATH = DATA_DIR / "places.tsv"

NEAR_KM = 5.0  # within this: "near X"; beyond: "~N km from X"
MAX_RING = 4

_LOCK = threading.Lock()
_INDEX: dict | None = None  # (lat_cell, lon_cell) -> [(lat, lon, label)]
_LOADED = False  # set only once the load attempt has finished, so loaded() never means "busy"
_STARTED = False


def preload() -> None:
    """Start the one-time load on a daemon thread; later calls do nothing."""
    global _STARTED
    with _LOCK:
        if _STARTED:
            return
        _STARTED = True
    threading.Thread(target=_load, name="places-load", daemon=True).start()


def _load() -> dict | None:
    global _INDEX, _LOADED
    with _LOCK:
        if _LOADED:
            return _INDEX
        try:
            index: dict = {}
            with PLACES_PATH.open(encoding="utf-8") as f:
                for line in f:
                    if line.startswith("#"):
                        continue
                    parts = line.rstrip("\n").split("\t")
                    if len(parts) != 4:
                        continue
                    name, region, lat_s, lon_s = parts
                    lat, lon = float(lat_s), float(lon_s)
                    label = f"{name}, {region}" if region else name
                    index.setdefault((math.floor(lat), math.floor(lon)), []).append((lat, lon, label))
            _INDEX = index or None
        except (OSError, ValueError):
            _INDEX = None
        _LOADED = True  # one attempt per process; a missing file is not retried every message
        return _INDEX


def loaded() -> bool:
    """True once the load attempt has finished — lookups from then on never touch the disk."""
    return _LOADED


def available() -> bool:
    return _load() is not None


def _km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 6371.0 * 2 * math.asin(math.sqrt(min(1.0, a)))


def nearest(lat: float, lon: float) -> tuple[str, float] | None:
    """(label, distance_km) of the closest place, or None."""
    index = _load()
    if index is None:
        return None
    clat, clon = math.floor(lat), math.floor(lon)
    best = None
    found_at = None
    for ring in range(MAX_RING + 1):
        for dy in range(-ring, ring + 1):
            for dx in range(-ring, ring + 1):
                if max(abs(dy), abs(dx)) != ring:
                    continue  # only the ring's perimeter; the inside was searched already
                cell_lon = (clon + dx + 180) % 360 - 180  # wrap across the antimeridian
                for plat, plon, label in index.get((clat + dy, cell_lon), ()):
                    d = _km(lat, lon, plat, plon)
                    if best is None or d < best[1]:
                        best = (label, d)
        if best is not None:
            if found_at is None:
                found_at = ring
            elif ring > found_at:
                break  # searched one ring past the first hit
    return best


def describe(lat: float, lon: float) -> str | None:
    """Short human label for the header: "near Albany, GA" or "~18 km from Albany, GA"."""
    hit = nearest(lat, lon)
    if hit is None:
        return None
    label, km = hit
    return f"near {label}" if km <= NEAR_KM else f"~{km:.0f} km from {label}"
