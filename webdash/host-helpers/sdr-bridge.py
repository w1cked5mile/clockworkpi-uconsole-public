#!/usr/bin/env python3
"""Localhost SDR control bridge for the webdash — broadcast/NOAA/airband RX on the AIO V2 RTL-SDR.

Runs on the HOST (the webdash container has no /dev access) as wicked5mile on 127.0.0.1:8767, the
same localhost trust boundary as the aiov2/kismet bridges. Receive-only, broadly legal (see the
repo's knowledge/README.md). The RTL-SDR is a single tuner, so the four SDR applications —
ADS-B (readsb), band hunt, listen, and OpenWebRX (the web receiver) — are mutually exclusive: at
most one owns the tuner at a time, tracked by `_busy`. Between the two streaming applications the
latest request wins: a new listen or scan ends the live one and takes the tuner (see
`_claim_stream`), so switching stations never collides with the stream being dropped. The SDR rail
must already be on (the dashboard's rail toggle); we don't force it, and turning the rail on no
longer starts anything by itself — readsb is systemctl-disabled on this build (see
software/adsb-tar1090.md), so the operator picks an application here rather than ADS-B grabbing the
tuner on rail-up.

ADS-B is just another selectable application now: POST /adsb {action: start|stop} runs
`sudo -n systemctl start|stop readsb` (already allowed NOPASSWD) and claims/releases the tuner.
Starting a hunt or listen while ADS-B holds the tuner is refused — stop ADS-B first.

OpenWebRX is a fourth selectable application: POST /owrx {action: start|stop} runs the host
container (configs/openwebrx/docker-compose.yml, no sudo — the bridge user is in the docker group)
and reserves the tuner the whole time it is up, since it opens the dongle lazily when a browser
tunes. It is symmetric with ADS-B: it needs a free tuner to start, and blocks hunt/listen/ADS-B
while running. A container started outside the bridge is still honoured — the claim paths check the
live container state via `_owrx_active()`. It also refuses to start unless the aiov2 bridge reports
the USB rail off (`_usb_rail_on()`, fails closed): a start with the rail on preceded a power cut on
2026-10-15.
"""
import json
import os
import select
import subprocess
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

BIND = ("127.0.0.1", 8767)

# band -> (low Hz, high Hz, rtl_power step, snap grid Hz, demod). Airband replaces broadcast AM,
# which this front end can't tune (R860 bottoms out ~24 MHz; see knowledge/sdr/learned/rtl-sdr-limits.md).
BANDS = {
    "fm":      {"lo": 88_000_000, "hi": 108_000_000, "step": 100_000, "snap": 100_000, "demod": "wbfm"},
    "airband": {"lo": 118_000_000, "hi": 137_000_000, "step": 25_000, "snap": 25_000, "demod": "am"},
}
PEAK_MARGIN_DB = 6.0   # a bin must clear the sweep's median noise floor by this much to be a station
MAX_STATIONS = 40

# listen: rtl_fm demod params per mode. Output is always s16le mono 48 kHz, piped into ffmpeg -> MP3.
RTLFM_MODES = {
    "nfm":  ["-M", "fm", "-s", "48000", "-r", "48000", "-E", "deemp", "-l", "0"],   # NOAA / NBFM voice
    "wbfm": ["-M", "wbfm", "-s", "200000", "-r", "48000"],                           # broadcast FM
    "am":   ["-M", "am", "-s", "48000", "-r", "48000", "-l", "0"],                   # airband
}
RTL_MIN_HZ, RTL_MAX_HZ = 24_000_000, 1_766_000_000

_lock = threading.Lock()
_job = {"thread": None, "running": False}
_state = {"stage": "idle", "band": None, "stations": [], "trace": None, "message": "", "updated": None}
# Single tuner: the SDR applications are mutually exclusive. None | "hunt" | "listen" | "scan".
# "scan" is the airband scanner — rtl_fm with multiple -f and a squelch cycles the channels and
# pauses on any that breaks squelch (see _handle_listen).
_busy = {"what": None, "info": None}
# The live listen or scan stream. A new one takes the tuner from it (latest wins) rather than
# getting 409: the page drops the old stream and requests the next at once, but a handler only
# notices its client has gone on its next failed write (~3 s, measured 2026-10-11), so a station
# switch always collided. gen names the owner; stop ends that stream; done is set once its rtl_fm
# has exited and the tuner is free. Hunt and ADS-B are not preempted: they still refuse with 409.
_stream = {"gen": 0, "stop": None, "done": None}
MAX_SCAN = 48  # cap on explicit scan channels passed in the URL

# Airband scanner live state, polled by the webdash at /scan/status. `active` is the frequency Hz
# currently being listened to (squelch open), or None while sweeping between channels.
_scan_state = {"stage": "idle", "active": None, "channels": [], "updated": None}
SCAN_DETECT_S = 0.9   # probe window per channel (covers rtl_fm device-init ~0.3 s + a listen slice)
SCAN_HANG_S = 1.5     # silence to tolerate on an active channel before moving on


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


_UNSET = object()


def _set_state(stage, message="", stations=None, band=None, trace=_UNSET):
    _state.update(stage=stage, message=message, updated=_now())
    if stations is not None:
        _state["stations"] = stations
    if band is not None:
        _state["band"] = band
    if trace is not _UNSET:         # explicit None clears a stale trace; _UNSET leaves it be
        _state["trace"] = trace


def _rtl_power_bins(csv_text: str) -> list[tuple[int, float]]:
    """Parse rtl_power CSV into (freq_hz, dB) bins sorted by frequency. Each line is:
        date, time, Hz_low, Hz_high, Hz_step, n_samples, dB, dB, ...
    Shared by the station finder and the spectrum trace so both read the same bins."""
    bins: list[tuple[int, float]] = []
    for line in csv_text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 7:
            continue
        try:
            lo, step = int(parts[2]), int(float(parts[4]))
            dbs = [float(x) for x in parts[6:] if x not in ("", "-nan", "nan", "inf", "-inf")]
        except ValueError:
            continue
        for i, db in enumerate(dbs):
            bins.append((lo + i * step, db))
    bins.sort(key=lambda b: b[0])
    return bins


def sweep_trace(csv_text: str) -> dict | None:
    """The whole swept band for the webdash to draw: every bin, plus the median noise floor and the
    PEAK_MARGIN_DB detection threshold the station finder uses. Receive-only display data; the peak
    list in parse_rtl_power is the same sweep reduced to stations. Returns None on an empty sweep."""
    bins = _rtl_power_bins(csv_text)
    if not bins:
        return None
    floor = sorted(d for _, d in bins)[len(bins) // 2]  # median
    return {
        "lo_hz": bins[0][0],
        "hi_hz": bins[-1][0],
        "floor_db": round(floor, 1),
        "threshold_db": round(floor + PEAK_MARGIN_DB, 1),
        "points": [[f, round(db, 1)] for f, db in bins],
    }


def parse_rtl_power(csv_text: str, snap: int) -> list[dict]:
    """Turn rtl_power CSV into a station list. Collect every bin's (freq, dB), take the median as
    the noise floor, keep contiguous runs that clear it by PEAK_MARGIN_DB, and report each run's
    strongest bin snapped to the band grid."""
    bins = _rtl_power_bins(csv_text)
    if not bins:
        return []
    floor = sorted(d for _, d in bins)[len(bins) // 2]  # median
    threshold = floor + PEAK_MARGIN_DB

    stations, run = [], []
    for freq, db in bins:
        if db >= threshold:
            run.append((freq, db))
        elif run:
            stations.append(max(run, key=lambda b: b[1]))
            run = []
    if run:
        stations.append(max(run, key=lambda b: b[1]))

    seen, out = set(), []
    for freq, db in stations:
        snapped = round(freq / snap) * snap
        if snapped in seen:
            continue
        seen.add(snapped)
        out.append({"freq_hz": snapped, "freq_mhz": round(snapped / 1e6, 3),
                    "power_db": round(db, 1), "snr_db": round(db - floor, 1)})
    out.sort(key=lambda s: s["power_db"], reverse=True)
    return out[:MAX_STATIONS]


# OpenWebRX runs as its own host container (configs/openwebrx/docker-compose.yml) and owns the
# tuner continuously while up, so it is a fourth mutually-exclusive SDR application. The bridge user
# is in the `docker` group, so these need no sudo. Path is resolved from this file so it survives a
# move of the checkout.
_REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OWRX_COMPOSE = os.path.join(_REPO_ROOT, "configs", "openwebrx", "docker-compose.yml")
OWRX_CONTAINER = "openwebrx"
# The aiov2 bridge (uconsole-aiov2-bridge.service) reports the AIO V2 rails; overridable for tests.
AIOV2_STATUS_URL = os.environ.get("AIOV2_STATUS_URL", "http://127.0.0.1:8765/status")


def _owrx(action):
    """Start or stop the OpenWebRX container. `up -d` (not `start`) so a missing container is
    created from the compose file; `stop` leaves it created for a fast next start."""
    cmd = ["docker", "compose", "-f", OWRX_COMPOSE, "up", "-d"] if action == "start" \
        else ["docker", "compose", "-f", OWRX_COMPOSE, "stop"]
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def _owrx_active() -> bool:
    out = subprocess.run(["docker", "inspect", "-f", "{{.State.Running}}", OWRX_CONTAINER],
                         capture_output=True, text=True, timeout=10)
    return out.stdout.strip() == "true"


def _usb_rail_on() -> bool | None:
    """The USB rail's state from the aiov2 bridge, or None when it can't say. Starting OpenWebRX
    with the USB rail on preceded a power cut on 2026-10-15 (cause unverified), so the receiver
    only starts with the rail known to be off."""
    try:
        with urllib.request.urlopen(AIOV2_STATUS_URL, timeout=3) as r:
            usb = (json.load(r).get("rails") or {}).get("USB")
    except (OSError, ValueError):
        return None
    return None if usb is None else bool(usb.get("on"))


def set_owrx(action: str) -> dict:
    """OpenWebRX as a chosen SDR application. Start claims the single tuner (ADS-B/hunt/listen are
    then refused until it's stopped); stop releases it. Like readsb it never auto-starts, so only
    this path brings it up."""
    if action not in ("start", "stop"):
        return {"ok": False, "error": "action must be start or stop"}
    with _lock:
        if action == "start":
            if _busy["what"] in ("hunt", "listen", "scan", "adsb"):
                return {"ok": False, "error": f"SDR is busy ({_busy['what']})"}
            usb = _usb_rail_on()
            if usb is None:
                return {"ok": False, "error": "USB rail state unknown (aiov2 bridge not answering) "
                        "— not starting the receiver"}
            if usb:
                return {"ok": False, "error": "USB rail is on — turn it off before starting the "
                        "receiver (aiov2_ctl USB off)"}
            if not _device_present():
                return {"ok": False, "error": "SDR device not found — turn the SDR rail on first"}
        _busy["what"] = "owrx" if action == "start" else None
        _busy["info"] = None
    r = _owrx(action)
    if r.returncode != 0:
        with _lock:
            if _busy["what"] == "owrx" and action == "start":
                _busy["what"] = None   # the container never came up; don't hold the tuner on paper
        return {"ok": False, "error": f"docker compose {action} failed: {r.stderr.strip()[:160]}"}
    return {"ok": True, "owrx_active": action == "start"}


def _readsb(action):
    subprocess.run(["sudo", "-n", "systemctl", action, "readsb"],
                   capture_output=True, text=True, timeout=20)


def _adsb_active() -> bool:
    out = subprocess.run(["sudo", "-n", "systemctl", "is-active", "readsb"],
                         capture_output=True, text=True)
    return out.stdout.strip() == "active"


def set_adsb(action: str) -> dict:
    """ADS-B (readsb) as a chosen SDR application. Start claims the single tuner (hunt/listen are
    then refused until it's stopped); stop releases it. readsb is systemctl-disabled on this build,
    so nothing starts it but this path and configs/sdr/sdr-swap.sh."""
    if action not in ("start", "stop"):
        return {"ok": False, "error": "action must be start or stop"}
    with _lock:
        if action == "start":
            if _busy["what"] in ("hunt", "listen", "scan", "owrx") or _owrx_active():
                return {"ok": False, "error": f"SDR is busy ({_busy['what'] or 'owrx'})"}
            if not _device_present():
                return {"ok": False, "error": "SDR device not found — turn the SDR rail on first"}
        _busy["what"] = "adsb" if action == "start" else None
        _busy["info"] = None
    _readsb(action)
    return {"ok": True, "adsb_active": action == "start"}


def _claim_stream(what: str, info: dict):
    """Take the tuner for a listen or scan. Returns (gen, stop, done), or an error string when a
    hunt or ADS-B holds it. A live listen/scan is told to stop, and this waits until its rtl_fm has
    exited, since two rtl_fm can't open one dongle."""
    with _lock:
        if _busy["what"] in ("hunt", "adsb", "owrx") or _owrx_active():
            return f"SDR is busy ({_busy['what'] or 'owrx'})"
        prev = (_stream["stop"], _stream["done"]) if _busy["what"] in ("listen", "scan") else None
        _stream["gen"] += 1
        mine = (_stream["gen"], threading.Event(), threading.Event())
        _stream["stop"], _stream["done"] = mine[1], mine[2]
        _busy["what"], _busy["info"] = what, info
    if prev:
        prev[0].set()
        # Usually well under a second. The long bound covers a scan caught in its seed sweep: one
        # rtl_power run that can't be interrupted and holds the dongle until it finishes.
        prev[1].wait(timeout=20)
    return mine


def _release_stream(gen: int, done: threading.Event) -> None:
    """Called last by a listen/scan handler, after its processes are reaped. Frees the tuner only
    if no newer stream has claimed it, then signals that this stream's rtl_fm is gone."""
    with _lock:
        if _stream["gen"] == gen:
            _busy["what"] = _busy["info"] = None
            _stream["stop"] = _stream["done"] = None
    done.set()


def _kill(procs) -> None:
    for p in procs:
        if p and p.poll() is None:
            p.terminate()
            try:
                p.wait(timeout=3)
            except subprocess.TimeoutExpired:
                p.kill()


def _device_present() -> bool:
    out = subprocess.run(["lsusb"], capture_output=True, text=True, timeout=5).stdout.lower()
    return "rtl" in out or "2832" in out or "realtek" in out


def _run_hunt(band: str):
    cfg = BANDS[band]
    readsb_was_up = subprocess.run(["sudo", "-n", "systemctl", "is-active", "readsb"],
                                   capture_output=True, text=True).stdout.strip() == "active"
    try:
        if not _device_present():
            _set_state("error", "SDR device not found — turn the SDR rail on first", [], band, trace=None)
            return
        # Clear the previous band's trace as the sweep starts, so the graph never shows stale bins.
        _set_state("scanning", f"sweeping {band} ({cfg['lo']//10**6}–{cfg['hi']//10**6} MHz)", band=band, trace=None)
        if readsb_was_up:
            _readsb("stop")
            time.sleep(1.5)  # let readsb release the tuner
        with tempfile.NamedTemporaryFile("r", suffix=".csv", delete=False) as tf:
            csv_path = tf.name
        try:
            r = subprocess.run(
                ["rtl_power", "-f", f"{cfg['lo']}:{cfg['hi']}:{cfg['step']}", "-i", "1", "-1", csv_path],
                capture_output=True, text=True, timeout=120)
            csv_text = open(csv_path).read()
        finally:
            try:
                os.remove(csv_path)
            except OSError:
                pass
        if not csv_text.strip():
            _set_state("error", f"rtl_power produced no data ({r.stderr.strip()[:120]})", [], band, trace=None)
            return
        stations = parse_rtl_power(csv_text, cfg["snap"])
        _set_state("done", f"{len(stations)} signal(s) found", stations, band, trace=sweep_trace(csv_text))
    finally:
        # Leave the tuner free after the sweep — ADS-B is a chosen application now, not the default
        # owner, so we don't silently restart readsb. The operator re-selects it when they want it.
        with _lock:
            _job["running"] = False
            _busy["what"] = None


def start_hunt(band: str) -> dict:
    with _lock:
        if band not in BANDS:
            return {"ok": False, "error": f"band must be one of {sorted(BANDS)}"}
        if _busy["what"] or _owrx_active():
            return {"ok": False, "error": f"SDR is busy ({_busy['what'] or 'owrx'})"}
        _busy["what"] = "hunt"
        _job["running"] = True
        _set_state("starting", f"preparing {band} scan", [], band, trace=None)
        t = threading.Thread(target=_run_hunt, args=(band,), daemon=True)
        _job["thread"] = t
        t.start()
        return {"ok": True, "status": "started"}


# --- Airband scanner --------------------------------------------------------------------------
# rtl_fm's native multi-freq scanner plays audio but never reports which channel it parked on, so
# we drive the hop ourselves: one rtl_fm per channel with the given squelch (it outputs ~zeros when
# squelched), detect activity by the output RMS, park on an active channel until it goes quiet, and
# publish the current frequency in _scan_state. A persistent ffmpeg encodes the whole session;
# silence is fed between/while hopping so the MP3 keeps flowing to the browser.


def _scan_set(**kw):
    with _lock:
        _scan_state.update(updated=_now(), **kw)


def _parse_scan_freqs(scan_raw: str) -> list[int]:
    freqs = []
    for tok in scan_raw.split(","):
        try:
            f = int(tok)
        except ValueError:
            continue
        if RTL_MIN_HZ <= f <= RTL_MAX_HZ:
            freqs.append(f)
    return freqs[:MAX_SCAN]


def _sweep_airband() -> list[int]:
    """One rtl_power sweep of the airband to seed the scanner when no explicit channels are given,
    so 'Scan airband' works with no prior hunt. Returns the active channel frequencies."""
    cfg = BANDS["airband"]
    with tempfile.NamedTemporaryFile("r", suffix=".csv", delete=False) as tf:
        csv_path = tf.name
    try:
        subprocess.run(["rtl_power", "-f", f"{cfg['lo']}:{cfg['hi']}:{cfg['step']}", "-i", "1", "-1", csv_path],
                       capture_output=True, text=True, timeout=120)
        csv_text = open(csv_path).read()
    finally:
        try:
            os.remove(csv_path)
        except OSError:
            pass
    return [s["freq_hz"] for s in parse_rtl_power(csv_text, cfg["snap"])][:MAX_SCAN]


def _scan_controller(freqs, squelch, ff_stdin, stop):
    """Hop the channel list. rtl_fm with a squelch emits bytes ONLY while squelch is open (a quiet
    channel produces nothing), so activity = any output within the probe window. Park on an active
    channel, streaming its audio until it's quiet for SCAN_HANG_S, then move on. Feed silence to the
    encoder while probing/quiet so the MP3 keeps flowing to the browser."""
    SILENCE = b"\x00" * 9600  # 0.1 s @ 48 kHz mono s16
    idx = 0
    try:
        while not stop.is_set():
            f = freqs[idx % len(freqs)]
            idx += 1
            _scan_set(stage="scanning", active=None)
            rtl = subprocess.Popen(
                ["rtl_fm", "-f", str(f), "-M", "am", "-s", "48000", "-r", "48000", "-l", str(squelch)],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            fd = rtl.stdout.fileno()
            try:
                # Probe: wait up to SCAN_DETECT_S (covers rtl_fm's device-init) for first audio.
                first = b""
                deadline = time.monotonic() + SCAN_DETECT_S
                while not stop.is_set() and time.monotonic() < deadline:
                    r, _, _ = select.select([fd], [], [], 0.1)
                    if r:
                        first = os.read(fd, 4096)
                        if first:
                            break
                    else:
                        ff_stdin.write(SILENCE)  # keep the stream alive while probing
                if stop.is_set():
                    break
                if not first:
                    continue  # quiet channel — on to the next
                # Active: park here and stream until it goes quiet for SCAN_HANG_S.
                _scan_set(stage="active", active=f)
                ff_stdin.write(first)
                silent_since = None
                while not stop.is_set():
                    r, _, _ = select.select([fd], [], [], 0.1)
                    if r:
                        chunk = os.read(fd, 4096)
                        if not chunk:
                            break
                        ff_stdin.write(chunk)
                        silent_since = None
                    else:
                        ff_stdin.write(SILENCE)  # 0.1 s silence; squelch currently closed
                        if silent_since is None:
                            silent_since = time.monotonic()
                        elif time.monotonic() - silent_since > SCAN_HANG_S:
                            break
            finally:
                if rtl.poll() is None:
                    rtl.terminate()
                    try:
                        rtl.wait(timeout=2)
                    except subprocess.TimeoutExpired:
                        rtl.kill()
    except (BrokenPipeError, ValueError, OSError):
        pass  # ffmpeg/client went away
    finally:
        try:
            ff_stdin.close()
        except OSError:
            pass


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/hunt/status":
            with _lock:
                running = _job["running"]
            self._json(200, {**_state, "running": running, "busy": _busy["what"],
                             "adsb_active": _adsb_active(), "owrx_active": _owrx_active()})
        elif path == "/listen":
            q = parse_qs(urlparse(self.path).query)
            scan_raw = q.get("scan", [""])[0].strip()
            if scan_raw:
                try:
                    squelch = int(q.get("squelch", ["150"])[0])
                except ValueError:
                    squelch = 150
                self._handle_scan(scan_raw, max(1, min(squelch, 10000)))
            else:
                self._handle_listen()
        elif path == "/scan/status":
            with _lock:
                self._json(200, dict(_scan_state))
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def _handle_listen(self):
        """Stream one channel's live audio: rtl_fm (demod) -> ffmpeg (MP3) -> this HTTP response,
        for as long as the client (the webdash <audio>) stays connected. Receive-only; brackets
        readsb. The airband scanner is a separate path (_handle_scan)."""
        q = parse_qs(urlparse(self.path).query)
        mode = q.get("mode", [""])[0]
        try:
            freq = int(q.get("freq", [""])[0])
        except ValueError:
            freq = 0
        if mode not in RTLFM_MODES or not (RTL_MIN_HZ <= freq <= RTL_MAX_HZ):
            self._json(400, {"ok": False, "error": "mode must be nfm/wbfm/am and freq in range"})
            return

        claim = _claim_stream("listen", {"mode": mode, "freq": freq})
        if isinstance(claim, str):
            self._json(409, {"ok": False, "error": claim})
            return
        gen, stop, done = claim

        rtl = ff = None
        readsb_was_up = False
        try:
            if stop.is_set():  # a newer request took the tuner while this one waited for it
                self._json(409, {"ok": False, "error": "superseded by a newer listen"})
                return
            if not _device_present():
                self._json(409, {"ok": False, "error": "SDR device not found — turn the SDR rail on first"})
                return
            readsb_was_up = subprocess.run(["sudo", "-n", "systemctl", "is-active", "readsb"],
                                           capture_output=True, text=True).stdout.strip() == "active"
            if readsb_was_up:
                _readsb("stop")
                time.sleep(1.2)
            rtl = subprocess.Popen(["rtl_fm", "-f", str(freq), *RTLFM_MODES[mode]],
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            ff = subprocess.Popen(
                ["ffmpeg", "-hide_banner", "-loglevel", "quiet", "-f", "s16le", "-ar", "48000",
                 "-ac", "1", "-i", "pipe:0", "-f", "mp3", "-b:a", "64k", "pipe:1"],
                stdin=rtl.stdout, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            rtl.stdout.close()  # let rtl_fm see SIGPIPE if ffmpeg goes away
            # Preempted: end the pipeline, which ends the read loop below.
            threading.Thread(target=lambda: (stop.wait(), _kill((ff, rtl))), daemon=True).start()

            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            while True:
                chunk = ff.stdout.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass  # client (browser) stopped listening — normal
        except Exception:  # noqa: BLE001
            pass
        finally:
            _kill((ff, rtl))
            # Tuner is released, not handed back to ADS-B — the operator picks the next app.
            _release_stream(gen, done)

    def _handle_scan(self, scan_raw, squelch):
        """Airband scanner: cycle channels, pause on traffic, and publish the active frequency via
        /scan/status. scan_raw is 'airband' (sweep to seed the channel list) or a comma list of Hz.
        A bridge-driven hop (see _scan_controller) feeds a persistent ffmpeg encoder, streamed to
        the browser <audio> as MP3. Receive-only; brackets readsb (stops it, doesn't restart)."""
        claim = _claim_stream("scan", {"squelch": squelch})
        if isinstance(claim, str):
            self._json(409, {"ok": False, "error": claim})
            return
        gen, stop, done = claim

        ff = None
        ctrl = None
        try:
            if stop.is_set():  # a newer request took the tuner while this one waited for it
                self._json(409, {"ok": False, "error": "superseded by a newer listen"})
                return
            if not _device_present():
                self._json(409, {"ok": False, "error": "SDR device not found — turn the SDR rail on first"})
                return
            if subprocess.run(["sudo", "-n", "systemctl", "is-active", "readsb"],
                              capture_output=True, text=True).stdout.strip() == "active":
                _readsb("stop")
                time.sleep(1.2)
            if scan_raw == "airband":
                _scan_set(stage="sweeping", active=None, channels=[])
                freqs = _sweep_airband()
            else:
                freqs = _parse_scan_freqs(scan_raw)
            if stop.is_set():
                self._json(409, {"ok": False, "error": "superseded by a newer listen"})
                return
            if not freqs:
                self._json(409, {"ok": False, "error": "no airband activity found — try again or widen squelch"})
                return
            _scan_set(stage="scanning", active=None, channels=freqs)
            ff = subprocess.Popen(
                ["ffmpeg", "-hide_banner", "-loglevel", "quiet", "-f", "s16le", "-ar", "48000",
                 "-ac", "1", "-i", "pipe:0", "-f", "mp3", "-b:a", "64k", "pipe:1"],
                stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            ctrl = threading.Thread(target=_scan_controller, args=(freqs, squelch, ff.stdin, stop),
                                    daemon=True)
            ctrl.start()

            self.send_response(200)
            self.send_header("Content-Type", "audio/mpeg")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            while True:
                chunk = ff.stdout.read(4096)
                if not chunk:
                    break
                self.wfile.write(chunk)
        except (BrokenPipeError, ConnectionResetError):
            pass
        except Exception:  # noqa: BLE001
            pass
        finally:
            stop.set()
            if ctrl:
                ctrl.join(timeout=4)
            if ff and ff.poll() is None:
                ff.terminate()
                try:
                    ff.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    ff.kill()
            with _lock:
                current = _stream["gen"] == gen
            if current:  # a scan that took over keeps its own status
                _scan_set(stage="idle", active=None, channels=[])
            _release_stream(gen, done)

    def do_POST(self):
        if self.path not in ("/hunt", "/adsb", "/owrx"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "bad request body"})
            return
        if self.path == "/adsb":
            result = set_adsb(str(req.get("action", "")).lower())
            self._json(200 if result.get("ok") else 409 if "busy" in result.get("error", "") else 400,
                       result)
            return
        if self.path == "/owrx":
            result = set_owrx(str(req.get("action", "")).lower())
            err = result.get("error", "")
            self._json(200 if result.get("ok") else 409 if "busy" in err or "USB rail" in err else 400,
                       result)
            return
        result = start_hunt(str(req.get("band", "")).lower())
        self._json(200 if result.get("ok") else 409 if "already" in result.get("error", "") else 400,
                   result)


if __name__ == "__main__":
    # Threaded: a long-lived /listen stream must not block /hunt/status polls.
    ThreadingHTTPServer(BIND, Handler).serve_forever()
