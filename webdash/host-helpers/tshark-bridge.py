#!/usr/bin/env python3
"""Localhost control bridge for passive packet capture — the host-side orchestrator the webdash
calls (POST /api/tshark/capture -> here). Separate from the other bridges because this one must
sudo the capture wrapper, so it is NOT run NoNewPrivileges.

Runs as wicked5mile on 127.0.0.1:8768 (localhost only, same trust boundary as the aiov2 and
wpa-audit bridges). It independently re-validates the requested interface against the host's real
interfaces, launches the root capture wrapper through a scoped sudoers entry, and exposes the job's
address-free summary. PASSIVE ONLY — the wrapper never transmits; this is a troubleshooting tap for
the hang/dropout investigation, not an auditing tool.
"""
import json
import os
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIND = ("127.0.0.1", 8768)
HOME = os.path.expanduser("~")
DATA_DIR = os.environ.get("TSHARK_DATA_DIR", f"{HOME}/.local/share/uconsole-webdash/data")
CAPTURE_SCRIPT = os.environ.get("TSHARK_CAPTURE_SCRIPT", "/usr/local/sbin/uconsole-tshark-capture.sh")
OUTDIR = os.environ.get("TSHARK_OUTDIR", f"{HOME}/labs/tshark")
STATEFILE = f"{DATA_DIR}/tshark-capture-state.json"
CANCELFILE = f"{DATA_DIR}/tshark-capture-cancel"
AUDITLOG = f"{DATA_DIR}/tshark-audit.log"

# Bounds the request can move within; defaults keep a long capture well under ~100 MB of SD card.
IFACE_RE = re.compile(r"^[A-Za-z0-9._-]{1,15}$")
FILTER_RE = re.compile(r"^[][()A-Za-z0-9 ._:/<>=!&|-]{0,200}$")
LIMITS = {"ringsize": (256, 65536, 10240), "ringfiles": (2, 50, 10),
          "duration": (0, 86400, 0), "stats_interval": (3, 300, 10)}

_lock = threading.Lock()
_job = {"proc": None, "iface": None, "started": None}


def _ifaces() -> set[str]:
    try:
        return set(os.listdir("/sys/class/net")) | {"any"}
    except OSError:
        return {"any"}


def _audit(line: str) -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(AUDITLOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {line}\n")
    except OSError:
        pass


def _clamp(name: str, value) -> int:
    lo, hi, default = LIMITS[name]
    try:
        return max(lo, min(hi, int(value)))
    except (TypeError, ValueError):
        return default


def _write_state(stage: str, message: str) -> None:
    try:
        json.dump({"stage": stage, "message": message, "iface": _job["iface"],
                   "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, open(STATEFILE, "w"))
    except OSError:
        pass


def _monitor(proc: subprocess.Popen) -> None:
    proc.wait()
    _audit(f"capture finished rc={proc.returncode} iface={_job['iface']}")
    with _lock:
        _job["proc"] = None


def _start_capture(req: dict) -> dict:
    iface = str(req.get("iface", "")).strip()
    flt = str(req.get("filter", "")).strip()
    with _lock:
        if _job["proc"] and _job["proc"].poll() is None:
            return {"ok": False, "error": "a capture is already running"}
        if not IFACE_RE.match(iface) or iface not in _ifaces():
            _audit(f"REFUSED bad interface iface={iface!r}")
            return {"ok": False, "error": f"{iface or '(empty)'} is not a capturable interface"}
        if flt and not FILTER_RE.match(flt):
            return {"ok": False, "error": "unsupported capture filter"}

        try:
            os.remove(CANCELFILE)
        except OSError:
            pass
        os.makedirs(OUTDIR, exist_ok=True)

        ringsize = _clamp("ringsize", req.get("ringsize"))
        ringfiles = _clamp("ringfiles", req.get("ringfiles"))
        duration = _clamp("duration", req.get("duration"))
        stats_interval = _clamp("stats_interval", req.get("stats_interval"))

        _job.update(iface=iface, started=time.time())
        _write_state("starting", "launching capture")
        cmd = ["sudo", "-n", CAPTURE_SCRIPT, "--iface", iface, "--outdir", OUTDIR,
               "--statefile", STATEFILE, "--cancelfile", CANCELFILE,
               "--ringsize", str(ringsize), "--ringfiles", str(ringfiles),
               "--duration", str(duration), "--stats-interval", str(stats_interval)]
        if flt:
            cmd += ["--filter", flt]
        _audit(f"START capture iface={iface} filter={flt or '(none)'} "
               f"ring={ringsize}KBx{ringfiles} duration={duration}")
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _job["proc"] = proc
        threading.Thread(target=_monitor, args=(proc,), daemon=True).start()
        return {"ok": True, "status": "started"}


def _status() -> dict:
    try:
        state = json.load(open(STATEFILE))
    except (OSError, ValueError):
        state = {"stage": "idle", "message": ""}
    with _lock:
        state["running"] = bool(_job["proc"] and _job["proc"].poll() is None)
    state["interfaces"] = sorted(i for i in _ifaces()
                                 if i not in ("lo",) and IFACE_RE.match(i))
    state["pcaps"] = _pcaps()
    return state


def _pcaps() -> list[dict]:
    """Ring files currently on disk, so the GUI can point the user at a pcap for a Wireshark
    deep-dive. Names and sizes only — the files themselves are not served over this bridge."""
    out = []
    try:
        for name in sorted(os.listdir(OUTDIR), reverse=True):
            if name.endswith(".pcapng"):
                p = os.path.join(OUTDIR, name)
                try:
                    out.append({"name": name, "kb": round(os.path.getsize(p) / 1024, 1)})
                except OSError:
                    pass
    except OSError:
        pass
    return out[:20]


def _cancel() -> dict:
    with _lock:
        if not (_job["proc"] and _job["proc"].poll() is None):
            return {"ok": False, "error": "no capture is running"}
    try:
        open(CANCELFILE, "w").close()
    except OSError as exc:
        return {"ok": False, "error": str(exc)}
    _audit("CANCEL requested")
    return {"ok": True}


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
        if self.path == "/capture/status":
            try:
                self._json(200, _status())
            except Exception as exc:  # noqa: BLE001
                self._json(200, {"stage": "error", "message": str(exc), "running": False})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def do_POST(self):
        if self.path not in ("/capture", "/capture/cancel"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "bad request body"})
            return
        try:
            if self.path == "/capture/cancel":
                self._json(200, _cancel())
                return
            result = _start_capture(req)
            self._json(200 if result.get("ok") else 409 if "already" in result.get("error", "")
                       else 400, result)
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"ok": False, "error": str(exc)})


if __name__ == "__main__":
    # Threaded so a status poll doesn't block a start/cancel request.
    ThreadingHTTPServer(BIND, Handler).serve_forever()
