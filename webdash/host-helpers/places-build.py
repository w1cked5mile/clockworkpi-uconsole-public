#!/usr/bin/env python3
"""Build the offline place list the mesh view uses to label senders ("near Albany, GA").

Runs on the host, once (or whenever you want fresher data). Downloads GeoNames `cities500` —
every populated place of 500+ people, villages included — plus the admin-1 (state/province)
names, and writes a trimmed TSV into webdash's data dir, outside the repo and git:

  ~/.local/share/uconsole-webdash/data/places.tsv     (mounted in the container as /data)

webdash loads it lazily (app/places.py). Without it the feature is simply off — no lookups, no
network calls, nothing in the message header. Lookups are always local: senders' positions are
never sent to any online geocoder.

GeoNames data is CC BY 4.0 (https://www.geonames.org/) — the attribution is written into the
TSV's header line and stated in software/webdash.md.

  places-build.py                      download and build
  places-build.py --zip cities500.zip  build from an already-downloaded archive (offline)
"""
import argparse
import hashlib
import io
import os
import sys
import time
import urllib.request
import zipfile
from pathlib import Path

BASE = "https://download.geonames.org/export/dump/"
OUT = Path(os.environ.get("WEBDASH_DATA_DIR_HOST",
                          Path.home() / ".local/share/uconsole-webdash/data")) / "places.tsv"


def fetch(name: str) -> bytes:
    print(f"places-build: downloading {BASE}{name}", flush=True)
    with urllib.request.urlopen(BASE + name, timeout=120) as r:
        return r.read()


def clean(s: str) -> str:
    return s.replace("\t", " ").replace("\n", " ").strip()


def build(zip_bytes: bytes, admin1_text: str) -> list[str]:
    # admin1CodesASCII.txt: "US.GA<TAB>Georgia<TAB>Georgia<TAB>4197000"
    admin1 = {}
    for line in admin1_text.splitlines():
        parts = line.split("\t")
        if len(parts) >= 2:
            admin1[parts[0]] = parts[1]
    rows = []
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as z:
        with z.open("cities500.txt") as f:
            for raw in io.TextIOWrapper(f, encoding="utf-8"):
                c = raw.rstrip("\n").split("\t")
                if len(c) < 11:
                    continue
                name, lat, lon, cc, a1 = c[1], c[4], c[5], c[8], c[10]
                # US: the admin-1 code is the postal abbreviation ("GA"), which is what people say.
                # Elsewhere: the admin-1 name plus the country code ("Bavaria, DE").
                if cc == "US" and a1:
                    region = a1
                else:
                    region = ", ".join(x for x in (admin1.get(f"{cc}.{a1}"), cc) if x)
                try:
                    lat_f, lon_f = float(lat), float(lon)
                except ValueError:
                    continue
                rows.append(f"{clean(name)}\t{clean(region)}\t{lat_f:.4f}\t{lon_f:.4f}")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--zip", type=Path, help="use a local cities500.zip instead of downloading")
    ap.add_argument("--admin1", type=Path, help="use a local admin1CodesASCII.txt")
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    zip_bytes = args.zip.read_bytes() if args.zip else fetch("cities500.zip")
    admin1 = args.admin1.read_text("utf-8") if args.admin1 else fetch("admin1CodesASCII.txt").decode("utf-8")
    rows = build(zip_bytes, admin1)
    if len(rows) < 1000:
        print(f"places-build: only {len(rows)} places parsed — refusing to write", file=sys.stderr)
        return 1

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_suffix(".tmp")
    sha = hashlib.sha256(zip_bytes).hexdigest()
    built = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with tmp.open("w", encoding="utf-8") as f:
        f.write(f"# GeoNames cities500 (CC BY 4.0, geonames.org) built {built} zip-sha256 {sha}\n")
        f.write("\n".join(rows) + "\n")
    tmp.replace(args.out)
    print(f"places-build: wrote {len(rows)} places to {args.out} (zip sha256 {sha[:16]}…)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
