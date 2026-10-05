#!/usr/bin/env python3
"""Tiny localhost JSON bridge for `aiov2_ctl` — status and rail control, plus read-only systemd
state for the services webdash reads (GET /services).

Runs on the HOST (not in the webdash container) because `aiov2_ctl` shells out to `pinctrl`,
which needs GPIO device access (`/dev/gpiomem` et al.) — bind-mounting a compiled binary plus its
device nodes into a python:3.12-slim container is more fragile than just exposing this over
localhost HTTP, the same shape as gpsd/meshtasticd/Kismet already use. See
docs/reference/webdash-architecture.md's "the one exception" section.

Binds 127.0.0.1 only — not reachable off this host, same trust boundary as gpsd
(127.0.0.1:2947) and meshtasticd's own ports. POST /rail actually changes hardware state (GPS/
LORA/SDR/USB power) — the only write path in this whole app; see the architecture doc's
"Rail control" section for why that's acceptable here (same auth gate as everything else, same
thing `aiov2_ctl <FEATURE> on|off` does by hand).
"""
import json
import re
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer

BIND = ("127.0.0.1", 8765)
RAIL_RE = re.compile(r"^(\w+)\s+GPIO(\d+):\s+(ON|OFF)$")
KV_RE = re.compile(r"^(\w[\w ]*?)\s*:\s*(.+)$")
VALID_FEATURES = {"GPS", "LORA", "SDR", "USB"}
VALID_STATES = {"on", "off"}
# Kismet is started as a *user* systemd service (see host-helpers/kismet-user.service), not the
# root kismet.service: the user manager gives it a clean exec so kismet_cap_linux_wifi keeps its
# file capabilities (cap_net_admin,cap_net_raw) and ~/kismet-logs stays writable — neither of
# which survives being spawned under this bridge's hardened unit, and the root unit crash-loops.
# No sudo: wicked5mile is in the kismet group already. Needs XDG_RUNTIME_DIR to reach the user
# bus, which the bridge unit sets.
KISMET_USER_UNIT = "kismet.service"
VALID_KISMET_ACTIONS = {"start", "stop"}


def kismet_control(action: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["systemctl", "--user", action, KISMET_USER_UNIT],
        capture_output=True, text=True, timeout=15,
    )
# Read-only systemd state for the services webdash aggregates (learning-platform S2). Fixed list:
# the route takes no arguments, so nothing a client sends reaches systemctl.
SERVICES = ("readsb", "gpsd", "meshtasticd", "kismet")
SHOW_PROPS = "ActiveState,SubState,NRestarts,LoadState"


def service_states() -> dict:
    out = subprocess.run(
        ["systemctl", "show", *[f"{s}.service" for s in SERVICES], "-p", SHOW_PROPS],
        capture_output=True, text=True, timeout=5,
    )
    result = {}
    # `systemctl show` prints one KEY=VALUE block per unit, separated by blank lines, in the order
    # the units were given.
    blocks = [b for b in out.stdout.strip().split("\n\n") if b.strip()]
    for name, text in zip(SERVICES, blocks):
        block = dict(line.split("=", 1) for line in text.splitlines() if "=" in line)
        active, sub = block.get("ActiveState"), block.get("SubState")
        result[name] = {
            "active": active,
            "sub": sub,
            "n_restarts": int(block.get("NRestarts") or 0),
            "loaded": block.get("LoadState") == "loaded",
            # "activating/auto-restart" is systemd waiting to retry a failed start: a crash loop.
            "crash_looping": active == "activating" and sub == "auto-restart",
        }
    return result


def parse_status(text: str) -> dict:
    rails, power = {}, {}
    for line in text.splitlines():
        line = line.strip()
        m = RAIL_RE.match(line)
        if m:
            name, gpio, state = m.groups()
            rails[name] = {"gpio": int(gpio), "on": state == "ON"}
            continue
        m = KV_RE.match(line)
        if m and m.group(1) not in ("AIO v2 Status",):
            power[m.group(1).strip().lower()] = m.group(2).strip()
    return {"rails": rails, "power": power}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):  # quiet; systemd journal doesn't need per-request noise
        pass

    def _json(self, status: int, payload: dict):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/services":
            try:
                self._json(200, {"ok": True, "services": service_states()})
            except Exception as exc:  # noqa: BLE001
                self._json(200, {"ok": False, "error": str(exc)})
            return
        if self.path != "/status":
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            out = subprocess.run(
                ["aiov2_ctl", "--status"], capture_output=True, text=True, timeout=5
            )
            self._json(200, {"ok": out.returncode == 0, **parse_status(out.stdout)})
        except Exception as exc:  # noqa: BLE001 — always return *something* parseable
            self._json(200, {"ok": False, "error": str(exc)})

    def do_POST(self):
        if self.path not in ("/rail", "/kismet"):
            self._json(404, {"ok": False, "error": "not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", 0))
            req = json.loads(self.rfile.read(length) or b"{}")
        except (ValueError, json.JSONDecodeError):
            self._json(400, {"ok": False, "error": "bad request body"})
            return

        if self.path == "/kismet":
            action = str(req.get("action", "")).lower()
            if action not in VALID_KISMET_ACTIONS:
                self._json(400, {"ok": False,
                                 "error": f"action must be one of {sorted(VALID_KISMET_ACTIONS)}"})
                return
            try:
                out = kismet_control(action)
                self._json(
                    200 if out.returncode == 0 else 502,
                    {"ok": out.returncode == 0, "output": out.stdout.strip(),
                     "stderr": out.stderr.strip()},
                )
            except Exception as exc:  # noqa: BLE001
                self._json(502, {"ok": False, "error": str(exc)})
            return

        feature = str(req.get("feature", "")).upper()
        state = str(req.get("state", "")).lower()
        if feature not in VALID_FEATURES or state not in VALID_STATES:
            self._json(
                400,
                {
                    "ok": False,
                    "error": f"feature must be one of {sorted(VALID_FEATURES)}, "
                    f"state one of {sorted(VALID_STATES)}",
                },
            )
            return

        try:
            out = subprocess.run(
                ["aiov2_ctl", feature, state], capture_output=True, text=True, timeout=10
            )
            self._json(
                200 if out.returncode == 0 else 502,
                {"ok": out.returncode == 0, "output": out.stdout.strip(), "stderr": out.stderr.strip()},
            )
        except Exception as exc:  # noqa: BLE001
            self._json(502, {"ok": False, "error": str(exc)})


if __name__ == "__main__":
    HTTPServer(BIND, Handler).serve_forever()
