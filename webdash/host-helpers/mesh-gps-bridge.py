#!/usr/bin/env python3
"""Feed gpsd's live position into meshtasticd so this node shares its location on the mesh.

WHY A BRIDGE (and not meshtasticd's own GPS):
    meshtasticd's native GPS support opens a *raw* serial port and cannot talk to gpsd
    (confirmed by grepping the binary — see software/meshtastic.md). gpsd owns /dev/serial0
    exclusively so Kismet, PyGPSClient and the webdash can all share one receiver, and so chrony
    can discipline the clock from it (configs/chrony/chrony-gps.conf). Handing the port back to
    meshtasticd would evict all of that. Instead this bridge keeps gpsd as the sole owner of the
    receiver and *pushes* position into meshtasticd over its TCP API (127.0.0.1:4403), exactly
    the same localhost trust boundary the webdash already uses.

HOW:
    The bridge calls the node's setFixedPosition() over the admin API. The node *adopts* that
    position as its own (it shows in NodeInfo and on the node's map) and rebroadcasts it on the
    firmware's normal position schedule (position.position_broadcast_secs + smart broadcast), so
    peers see us while we message. sendPosition() was tried first but only transmits a one-shot
    packet without the node adopting it (getMyNodeInfo stayed empty), which isn't verifiable or
    locally usable — setFixedPosition is the canonical "external GPS into meshtasticd" path.

    Each update is a small config write. On this build meshtasticd runs on Linux (the CM4), so
    that is a file write on eMMC/SD, not embedded-flash wear as on an ESP32/nRF node — and the
    movement/interval gate below keeps updates infrequent regardless.

    Prerequisite, set once (not by this bridge):
        meshtastic --host localhost --set position.gps_mode NOT_PRESENT
    so the firmware does not keep trying to drive a serial GPS it can't reach (gpsd owns it) and
    instead uses the fixed position this bridge maintains.

AIRTIME:
    Mirrors the node's own smart-broadcast intent rather than spamming the mesh: a new position
    goes out only when the fix has moved >= MIN_DIST_M or MIN_INTERVAL_S has passed, and never
    more often than MIN_INTERVAL_S. Defaults match the node's position.broadcast_smart_* values
    (100 m / 300 s). A keepalive goes out at most every MAX_INTERVAL_S.

PRIVACY:
    Logs grid square + metres moved, never raw lat/lon — the repo records location as a Maidenhead
    grid only (knowledge/README.md). Raw coordinates are sent over RF (that is the point) but are
    not written to any file.

Env overrides: MESH_HOST, GPSD_HOST, GPSD_PORT, MIN_INTERVAL_S, MAX_INTERVAL_S, MIN_DIST_M,
FIX_MAX_AGE_S. Run with --once to push a single current fix and exit (used by the
doc's verify step).
"""
import json
import math
import os
import socket
import sys
import time

GPSD_HOST = os.environ.get("GPSD_HOST", "127.0.0.1")
GPSD_PORT = int(os.environ.get("GPSD_PORT", "2947"))
MESH_HOST = os.environ.get("MESH_HOST", "127.0.0.1")

MIN_INTERVAL_S = float(os.environ.get("MIN_INTERVAL_S", "300"))   # airtime floor between sends
MAX_INTERVAL_S = float(os.environ.get("MAX_INTERVAL_S", "900"))   # keepalive ceiling
MIN_DIST_M = float(os.environ.get("MIN_DIST_M", "100"))           # resend if moved this far
FIX_MAX_AGE_S = float(os.environ.get("FIX_MAX_AGE_S", "30"))      # ignore stale TPV
POLL_S = 5.0                                                      # gpsd read cadence

WATCH_CMD = b'?WATCH={"enable":true,"json":true};\n'


def log(msg: str) -> None:
    print(f"mesh-gps-bridge: {msg}", flush=True)


def maidenhead(lat: float, lon: float) -> str:
    """6-char locator — same algorithm as webdash/app/collectors/gps.py, kept in sync by hand."""
    lon += 180.0
    lat += 90.0
    a = ord("A")
    field = chr(a + int(lon // 20)) + chr(a + int(lat // 10))
    square = str(int((lon % 20) // 2)) + str(int(lat % 10))
    sub = chr(ord("a") + int((lon % 2) * 12)) + chr(ord("a") + int((lat % 1) * 24))
    return field + square + sub


def haversine_m(lat1, lon1, lat2, lon2) -> float:
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lon2 - lon1)
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def read_fix(timeout=4.0):
    """One fresh fix from gpsd, or None. Returns (lat, lon, alt_or_None, mode)."""
    try:
        s = socket.create_connection((GPSD_HOST, GPSD_PORT), timeout=2.0)
    except OSError as exc:
        log(f"gpsd unreachable: {exc}")
        return None
    s.settimeout(timeout)
    best = None
    try:
        s.sendall(WATCH_CMD)
        buf = b""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                chunk = s.recv(4096)
            except socket.timeout:
                break
            if not chunk:
                break
            buf += chunk
            while b"\n" in buf:
                line, buf = buf.split(b"\n", 1)
                try:
                    msg = json.loads(line)
                except ValueError:
                    continue
                if msg.get("class") != "TPV":
                    continue
                mode = msg.get("mode", 0)
                if mode < 2 or msg.get("lat") is None or msg.get("lon") is None:
                    continue
                # Freshness: gpsd stamps TPV with the receiver's time; needs a sane clock, which
                # chrony now keeps even offline. If the stamp can't be parsed, accept the fix.
                age = _age_s(msg.get("time"))
                if age is not None and age > FIX_MAX_AGE_S:
                    continue
                best = (msg["lat"], msg["lon"], msg.get("alt") if mode == 3 else None, mode)
                break
            if best:
                break
    finally:
        s.close()
    return best


def _age_s(iso):
    if not iso:
        return None
    try:
        from datetime import datetime
        t = datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None
    return time.time() - t


class Mesh:
    """Persistent meshtasticd TCP API client, reconnecting once on failure (cf. collectors/mesh.py)."""

    def __init__(self, host):
        self.host = host
        self.iface = None

    def _connect(self):
        import meshtastic.tcp_interface  # lazy: protobuf/pypubsub init is not free
        self.iface = meshtastic.tcp_interface.TCPInterface(hostname=self.host)

    def send_position(self, lat, lon, alt):
        if self.iface is None:
            self._connect()
        alt_i = int(alt) if alt is not None else 0
        try:
            self.iface.localNode.setFixedPosition(lat, lon, alt_i)
        except Exception:
            # Stale/dead socket (meshtasticd restarted etc.): drop and reconnect once.
            try:
                self.iface.close()
            except Exception:
                pass
            self.iface = None
            self._connect()
            self.iface.localNode.setFixedPosition(lat, lon, alt_i)


def run_once(mesh):
    fix = read_fix()
    if not fix:
        log("no usable fix (need 2D/3D and a fresh TPV) — nothing sent")
        return False
    lat, lon, alt, mode = fix
    mesh.send_position(lat, lon, alt)
    log(f"sent position: grid={maidenhead(lat, lon)} fix={mode}D "
        f"alt={'%.0fm' % alt if alt is not None else 'n/a'}")
    return True


def run_loop(mesh):
    last = None   # (lat, lon, t) of the last position actually sent
    log(f"started: min_interval={MIN_INTERVAL_S}s max_interval={MAX_INTERVAL_S}s "
        f"min_dist={MIN_DIST_M}m")
    while True:
        fix = read_fix()
        if fix:
            lat, lon, alt, mode = fix
            now = time.time()
            send = False
            if last is None:
                send = True
            else:
                moved = haversine_m(last[0], last[1], lat, lon)
                since = now - last[2]
                if since >= MAX_INTERVAL_S:
                    send = True                       # keepalive
                elif since >= MIN_INTERVAL_S and moved >= MIN_DIST_M:
                    send = True                       # moved enough, and past the airtime floor
            if send:
                try:
                    mesh.send_position(lat, lon, alt)
                    moved_s = "first" if last is None else f"{haversine_m(last[0], last[1], lat, lon):.0f}m"
                    log(f"sent position: grid={maidenhead(lat, lon)} fix={mode}D moved={moved_s}")
                    last = (lat, lon, now)
                except Exception as exc:
                    log(f"send failed: {exc}")
        time.sleep(POLL_S)


def main():
    once = "--once" in sys.argv[1:]
    mesh = Mesh(MESH_HOST)
    if once:
        ok = run_once(mesh)
        try:
            if mesh.iface:
                mesh.iface.close()
        except Exception:
            pass
        sys.exit(0 if ok else 1)
    try:
        run_loop(mesh)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
