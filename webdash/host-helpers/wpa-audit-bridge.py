#!/usr/bin/env python3
"""Localhost control bridge for authorized WPA capture — the host-side orchestrator the webdash
calls (POST /api/wpa/capture -> here). Separate from the aiov2 bridge because this one must sudo
the capture script, so it is NOT run NoNewPrivileges.

Runs as wicked5mile on 127.0.0.1:8766 (localhost only, same trust boundary as the aiov2 bridge).
It independently re-checks the target BSSID against the webdash allowlist before doing anything,
brackets Kismet (which shares wlan1 — stop before, restore after), launches the root capture script
through a scoped sudoers entry, and exposes the job's status. AUTHORIZED EQUIPMENT ONLY.
"""
import glob
import json
import os
import re
import subprocess
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

BIND = ("127.0.0.1", 8766)
HOME = os.path.expanduser("~")
DATA_DIR = os.environ.get("WPA_DATA_DIR", f"{HOME}/.local/share/uconsole-webdash/data")
ALLOWLIST = os.environ.get("WPA_ALLOWLIST", f"{DATA_DIR}/wpa-authorized.json")
CAPTURE_SCRIPT = os.environ.get("WPA_CAPTURE_SCRIPT", "/usr/local/sbin/uconsole-wpa-capture.sh")
OUTDIR = os.environ.get("WPA_OUTDIR", f"{HOME}/labs/wpa")
STATEFILE = f"{DATA_DIR}/wpa-capture-state.json"
CANCELFILE = f"{DATA_DIR}/wpa-capture-cancel"
AUDITLOG = f"{DATA_DIR}/wpa-audit.log"
# Crack offload: the existing script (mode 644, invoked via bash) SSHes to the GPU host and runs
# hashcat. The recovered PSK is a secret, so it lives ONLY in this process's memory (served to the
# authenticated UI) — never written to a statefile or the audit log.
CRACK_SCRIPT = os.environ.get("WPA_CRACK_SCRIPT", f"{HOME}/labs/wpa/crack-offload.sh")
CRACK_HOST = os.environ.get("WPA_CRACK_HOST", "gpu-host-wsl")

_lock = threading.Lock()
_job = {"proc": None, "bssid": None, "kismet_was_running": False, "started": None}
_crack = {"proc": None, "stage": "idle", "message": "", "cracked": None,
          "psk": None, "cap": None, "updated": None}


def _authorized(bssid: str) -> bool:
    try:
        entries = json.load(open(ALLOWLIST)).get("entries", [])
    except (OSError, ValueError):
        return False
    return any(e.get("bssid", "").upper() == bssid.upper() for e in entries)


def _kismet(action: str) -> None:
    env = dict(os.environ, XDG_RUNTIME_DIR=os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    subprocess.run(["systemctl", "--user", action, "kismet.service"],
                   capture_output=True, text=True, timeout=20, env=env)


def _kismet_running() -> bool:
    env = dict(os.environ, XDG_RUNTIME_DIR=os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}"))
    r = subprocess.run(["systemctl", "--user", "is-active", "kismet.service"],
                       capture_output=True, text=True, timeout=10, env=env)
    return r.stdout.strip() == "active"


def _audit(line: str) -> None:
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(AUDITLOG, "a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {line}\n")
    except OSError:
        pass


def _write_state(stage: str, message: str) -> None:
    try:
        json.dump({"stage": stage, "message": message, "bssid": _job["bssid"],
                   "updated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}, open(STATEFILE, "w"))
    except OSError:
        pass


def _monitor(proc: subprocess.Popen, restore_kismet: bool) -> None:
    proc.wait()
    if restore_kismet:
        _kismet("start")
    _audit(f"capture finished rc={proc.returncode} bssid={_job['bssid']}")
    with _lock:
        _job["proc"] = None


def _start_capture(bssid: str, channel: str | None) -> dict:
    with _lock:
        if _job["proc"] and _job["proc"].poll() is None:
            return {"ok": False, "error": "a capture is already running"}
        if not _authorized(bssid):
            _audit(f"REFUSED unauthorized bssid={bssid}")
            return {"ok": False, "error": f"{bssid} is not on the authorized allowlist"}

        try:
            os.remove(CANCELFILE)
        except OSError:
            pass
        os.makedirs(OUTDIR, exist_ok=True)

        was_running = _kismet_running()
        if was_running:
            _kismet("stop")

        _job.update(bssid=bssid.upper(), kismet_was_running=was_running, started=time.time())
        _write_state("starting", "launching capture")
        cmd = ["sudo", "-n", CAPTURE_SCRIPT, "--bssid", bssid, "--allowlist", ALLOWLIST,
               "--outdir", OUTDIR, "--statefile", STATEFILE, "--cancelfile", CANCELFILE]
        if channel:
            cmd += ["--channel", str(channel)]
        _audit(f"START capture bssid={bssid.upper()} channel={channel or 'auto'}")
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        _job["proc"] = proc
        threading.Thread(target=_monitor, args=(proc, was_running), daemon=True).start()
        return {"ok": True, "status": "started"}


def _status() -> dict:
    try:
        state = json.load(open(STATEFILE))
    except (OSError, ValueError):
        state = {"stage": "idle", "message": ""}
    with _lock:
        running = bool(_job["proc"] and _job["proc"].poll() is None)
    state["running"] = running
    return state


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


def _valid_cap(cap: str) -> str | None:
    """Only a .cap this webdash produced: a real file directly under OUTDIR named wpa-*.cap. Stops
    the crack route from being pointed at arbitrary host paths."""
    try:
        real = os.path.realpath(cap)
    except OSError:
        return None
    if os.path.dirname(real) != os.path.realpath(OUTDIR):
        return None
    if not re.fullmatch(r"wpa-[0-9A-Za-z._-]+\.cap", os.path.basename(real)):
        return None
    return real if os.path.isfile(real) else None


def _set_crack(**kw):
    _crack.update(updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), **kw)


def _run_crack(cap: str):
    env = dict(os.environ, CRACK_HOST=CRACK_HOST)
    try:
        proc = subprocess.Popen(["bash", CRACK_SCRIPT, cap], env=env, text=True, bufsize=1,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    except OSError as exc:
        _set_crack(stage="error", message=str(exc), cracked=False)
        with _lock:
            _crack["proc"] = None
        return
    with _lock:
        _crack["proc"] = proc

    tail, result_lines, in_result = [], [], False
    for line in proc.stdout:
        line = line.rstrip()
        tail.append(line)
        del tail[:-40]
        if in_result:
            result_lines.append(line)
        if line.startswith("=== result"):
            in_result = True
        m = re.match(r"\[(\d)/4\]\s*(.*)", line)
        if m:
            _set_crack(stage=f"step {m.group(1)}/4", message=m.group(2)[:120])
        elif any(k in line for k in ("Speed.", "Recovered.", "Progress.")):
            _set_crack(message=line.strip()[:120])
        elif "FAIL:" in line:
            _set_crack(message=line.strip()[:160])
    proc.wait()

    cracked, psk = False, None
    for line in result_lines:
        s = line.strip()
        if not s or s.startswith("done.") or "nothing recovered" in s:
            continue
        if "*" in s and ":" in s:            # hashcat -m 22000 --show -> <hash>:<psk>
            cracked, psk = True, s.rsplit(":", 1)[-1]
            break
    if cracked:
        _set_crack(stage="done", cracked=True, psk=psk, message="passphrase recovered")
        _audit(f"CRACK success cap={os.path.basename(cap)}")   # PSK intentionally not logged
    elif proc.returncode != 0:
        fail = next((l for l in reversed(tail) if "FAIL" in l), "crack-offload failed")
        _set_crack(stage="error", cracked=False, message=fail.strip()[:160])
    else:
        _set_crack(stage="done", cracked=False, psk=None, message="not in wordlist")
        _audit(f"CRACK no-result cap={os.path.basename(cap)}")
    with _lock:
        _crack["proc"] = None


def start_crack(cap: str) -> dict:
    real = _valid_cap(cap)
    if not real:
        return {"ok": False, "error": "cap must be a wpa-*.cap this webdash captured"}
    with _lock:
        if _crack["proc"] and _crack["proc"].poll() is None:
            return {"ok": False, "error": "a crack is already running"}
        _crack.update(proc=None, stage="starting", message=f"offloading to {CRACK_HOST}",
                      cracked=None, psk=None, cap=os.path.basename(real),
                      updated=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    _audit(f"CRACK start cap={os.path.basename(real)} host={CRACK_HOST}")
    threading.Thread(target=_run_crack, args=(real,), daemon=True).start()
    return {"ok": True, "status": "started"}


def crack_status() -> dict:
    with _lock:
        running = bool(_crack["proc"] and _crack["proc"].poll() is None)
    out = {k: _crack[k] for k in ("stage", "message", "cracked", "psk", "cap", "updated")}
    out["running"] = running
    return out


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
            self._json(200, self._status_safe())
        elif self.path == "/crack/status":
            try:
                self._json(200, crack_status())
            except Exception as exc:  # noqa: BLE001
                self._json(200, {"stage": "error", "message": str(exc), "running": False})
        else:
            self._json(404, {"ok": False, "error": "not found"})

    def _status_safe(self):
        try:
            return _status()
        except Exception as exc:  # noqa: BLE001
            return {"stage": "error", "message": str(exc), "running": False}

    def do_POST(self):
        if self.path not in ("/capture", "/capture/cancel", "/crack"):
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
            if self.path == "/crack":
                result = start_crack(str(req.get("cap", "")).strip())
                self._json(200 if result.get("ok") else 409 if "already" in result.get("error", "")
                           else 400, result)
                return
            bssid = str(req.get("bssid", "")).strip()
            result = _start_capture(bssid, req.get("channel"))
            self._json(200 if result.get("ok") else 409 if "running" in result.get("error", "")
                       else 400, result)
        except Exception as exc:  # noqa: BLE001
            self._json(500, {"ok": False, "error": str(exc)})


if __name__ == "__main__":
    # Threaded so a long crack job / status poll doesn't block capture status.
    ThreadingHTTPServer(BIND, Handler).serve_forever()
