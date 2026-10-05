#!/usr/bin/env python3
"""Upload finished Kismet WiGLE CSVs to wigle.net, dropping every row near home first.

Runs on the host from the systemd user timer wigle-upload.timer (hourly), or by hand. Reads
~/kismet-logs/*.wiglecsv (Kismet's log_types=wiglecsv output), skips any file Kismet may still be
writing, removes rows within WIGLE_HOME_RADIUS_M of home, and uploads the rest. Each file is sent
once; what was sent is recorded in ~/.local/state/wigle-upload/state.json.

Credentials and the home position live only in ~/.config/wigle/env (mode 600, never in the repo):
  WIGLE_API_NAME=AID...            # wigle.net -> Account -> API Token ("API Name")
  WIGLE_API_TOKEN=...              # the matching token
  WIGLE_HOME_LAT=..                # written by --set-home-from-gps
  WIGLE_HOME_LON=..
  WIGLE_HOME_RADIUS_M=500          # optional, default 500

Fails closed: with no home position set it uploads nothing.

  wigle-upload.py                      upload anything new
  wigle-upload.py --dry-run            show what would be sent, send nothing
  wigle-upload.py --set-home-from-gps  store the current gpsd fix as home (run it at home)
"""
import argparse
import base64
import csv
import io
import json
import math
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

LOGS = Path.home() / "kismet-logs"
ENV = Path.home() / ".config/wigle/env"
STATE = Path.home() / ".local/state/wigle-upload/state.json"
URL = "https://api.wigle.net/api/v2/file/upload"
SETTLE_S = 600          # a file untouched this long is finished
HEADER_LINES = 2        # WigleWifi-1.4 pre-header + column header


def log(msg: str) -> None:
    print(msg, flush=True)


def load_env() -> dict:
    env = {}
    if not ENV.exists():
        return env
    for line in ENV.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def write_env(updates: dict) -> None:
    """Set keys in the env file in place, keeping comments and other lines; a commented-out
    `#KEY=` placeholder is replaced, anything else is appended."""
    ENV.parent.mkdir(parents=True, exist_ok=True)
    ENV.parent.chmod(0o700)
    lines = ENV.read_text().splitlines() if ENV.exists() else []
    todo = dict(updates)
    for i, line in enumerate(lines):
        k = line.lstrip("#").split("=", 1)[0].strip()
        if "=" in line and k in todo:
            lines[i] = f"{k}={todo.pop(k)}"
    lines += [f"{k}={v}" for k, v in todo.items()]
    fd = os.open(ENV, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write("\n".join(lines) + "\n")
    ENV.chmod(0o600)


def gpsd_fix(timeout: float = 15.0):
    """Return (lat, lon) from gpsd's first 2D/3D TPV, or None."""
    deadline = time.time() + timeout
    with socket.create_connection(("localhost", 2947), timeout=timeout) as s:
        s.sendall(b'?WATCH={"enable":true,"json":true}\n')
        buf = b""
        while time.time() < deadline:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    msg = json.loads(line)
                except ValueError:
                    continue
                if msg.get("class") == "TPV" and msg.get("mode", 0) >= 2 and "lat" in msg:
                    return msg["lat"], msg["lon"]
    return None


def metres(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def kismet_running() -> bool:
    r = subprocess.run(["systemctl", "--user", "is-active", "--quiet", "kismet"])
    return r.returncode == 0


def finished_files() -> list:
    files = sorted(LOGS.glob("*.wiglecsv"), key=lambda p: p.stat().st_mtime)
    if files and kismet_running():
        files = files[:-1]                          # the newest is Kismet's open log
    now = time.time()
    return [p for p in files if now - p.stat().st_mtime > SETTLE_S]


def filter_rows(path: Path, home, radius: float):
    """Return (csv_bytes, kept, dropped_home, dropped_nofix)."""
    lines = path.read_text(errors="replace").splitlines(keepends=True)
    head, body = lines[:HEADER_LINES], lines[HEADER_LINES:]
    out = io.StringIO()
    out.writelines(head)
    kept = d_home = d_nofix = 0
    cols = next(csv.reader([head[1]])) if len(head) > 1 else []
    try:
        ilat, ilon = cols.index("CurrentLatitude"), cols.index("CurrentLongitude")
    except ValueError:
        raise SystemExit(f"{path.name}: unexpected header {cols}")
    w = csv.writer(out, lineterminator="\n")
    for row in csv.reader(body):
        try:
            lat, lon = float(row[ilat]), float(row[ilon])
        except (IndexError, ValueError):
            d_nofix += 1
            continue
        if lat == 0 and lon == 0:
            d_nofix += 1
            continue
        if metres(lat, lon, *home) <= radius:
            d_home += 1
            continue
        w.writerow(row)
        kept += 1
    return out.getvalue().encode(), kept, d_home, d_nofix


def upload(name: str, data: bytes, api_name: str, api_token: str) -> dict:
    boundary = uuid.uuid4().hex
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
        "Content-Type: text/csv\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    auth = base64.b64encode(f"{api_name}:{api_token}".encode()).decode()
    req = urllib.request.Request(URL, data=body, method="POST", headers={
        "Authorization": f"Basic {auth}",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read() or b"{}")


def find_transid(obj):
    """WiGLE's upload response nests the id (seen as transid/transId, alone or in a list); find it
    wherever it is rather than depend on one shape."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k.lower() == "transid" and isinstance(v, str):
                return v
            found = find_transid(v)
            if found:
                return found
    elif isinstance(obj, list):
        for v in obj:
            found = find_transid(v)
            if found:
                return found
    return None


def load_state() -> dict:
    try:
        return json.loads(STATE.read_text())
    except (FileNotFoundError, ValueError):
        return {}


def save_state(state: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, sort_keys=True))
    tmp.replace(STATE)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--set-home-from-gps", action="store_true")
    a = ap.parse_args()
    env = load_env()

    if a.set_home_from_gps:
        fix = gpsd_fix()
        if not fix:
            log("no gpsd fix within 15 s; home not set")
            return 1
        updates = {"WIGLE_HOME_LAT": f"{fix[0]:.6f}", "WIGLE_HOME_LON": f"{fix[1]:.6f}"}
        if "WIGLE_HOME_RADIUS_M" not in env:
            updates["WIGLE_HOME_RADIUS_M"] = "500"
        write_env(updates)
        log(f"home set from gpsd fix; radius {env.get('WIGLE_HOME_RADIUS_M', '500')} m ({ENV})")
        return 0

    try:
        home = (float(env["WIGLE_HOME_LAT"]), float(env["WIGLE_HOME_LON"]))
    except (KeyError, ValueError):
        log(f"no home position in {ENV}; refusing to upload (run --set-home-from-gps at home)")
        return 0
    radius = float(env.get("WIGLE_HOME_RADIUS_M", 500))
    creds = env.get("WIGLE_API_NAME"), env.get("WIGLE_API_TOKEN")
    if not all(creds) and not a.dry_run:
        log(f"WIGLE_API_NAME / WIGLE_API_TOKEN not set in {ENV}; nothing uploaded")
        return 0

    state = load_state()
    failed = 0
    for p in finished_files():
        if p.name in state:
            continue
        data, kept, d_home, d_nofix = filter_rows(p, home, radius)
        summary = f"{p.name}: {kept} rows to send, {d_home} near home dropped, {d_nofix} no-fix dropped"
        if a.dry_run:
            log("[dry-run] " + summary)
            continue
        if kept == 0:
            log(summary + " — nothing to send, marked done")
            state[p.name] = {"at": int(time.time()), "rows": 0, "result": "empty"}
            save_state(state)
            continue
        try:
            resp = upload(p.with_suffix(".csv").name, data, *creds)
        except (urllib.error.URLError, OSError, ValueError) as e:
            log(f"{summary} — upload failed: {e}; will retry next run")
            failed += 1
            continue
        if not resp.get("success"):
            log(f"{summary} — WiGLE rejected it: {resp}; will retry next run")
            failed += 1
            continue
        trans = find_transid(resp)
        state[p.name] = {"at": int(time.time()), "rows": kept, "result": "uploaded", "transid": trans}
        save_state(state)
        log(f"{summary} — uploaded (transid {trans})")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
