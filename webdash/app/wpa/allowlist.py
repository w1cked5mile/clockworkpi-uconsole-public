"""Server-enforced allowlist of BSSIDs authorized for active WPA auditing.

The active steps (deauth, handshake capture) run ONLY against a BSSID on this list. The operator
adds a BSSID through the webdash — a deliberate authorization assertion for own equipment or a
documented engagement — and the host-side capture helper re-reads this same file and refuses any
target not on it, so the gate is enforced where the privileged commands actually run, not just in
the browser. Keyed on BSSID (hardware), not SSID: SSIDs are spoofable and shared, so authorization
attaches to a specific radio; the SSID is kept only as a human label.

Stored in the read-write data dir, outside the repo and git — the list of what you are authorized
to attack is itself sensitive, like the captures and recovered PSKs (see the repo's
knowledge/README.md responsible-use section).
"""
import json
import os
import re
import time
from pathlib import Path

DATA_DIR = Path(os.environ.get("WEBDASH_DATA_DIR", "/data"))
ALLOWLIST_PATH = DATA_DIR / "wpa-authorized.json"
BSSID_RE = re.compile(r"^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$")
_RESERVED = {"FF:FF:FF:FF:FF:FF", "00:00:00:00:00:00"}


def normalize_bssid(bssid: str) -> str | None:
    """Canonical upper-case colon form, or None if it isn't a real unicast MAC. Rejects broadcast,
    all-zero, and multicast addresses (LSB of the first octet set) — none can be an AP's BSSID."""
    b = (bssid or "").strip().upper()
    if not BSSID_RE.match(b) or b in _RESERVED:
        return None
    if int(b[0:2], 16) & 1:  # multicast/broadcast bit
        return None
    return b


def load() -> list[dict]:
    try:
        return json.loads(ALLOWLIST_PATH.read_text()).get("entries", [])
    except (OSError, ValueError):
        return []


def _save(entries: list[dict]) -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    tmp = ALLOWLIST_PATH.with_suffix(".json.tmp")
    tmp.write_text(json.dumps({"version": 1, "entries": entries}, indent=2))
    tmp.replace(ALLOWLIST_PATH)  # atomic; a half-written allowlist must never gate a capture


def is_authorized(bssid: str) -> bool:
    b = normalize_bssid(bssid)
    return bool(b) and any(e.get("bssid") == b for e in load())


def add(bssid: str, basis: str, ssid_label: str = "") -> dict:
    b = normalize_bssid(bssid)
    if not b:
        return {"ok": False, "error": "BSSID must be a unicast MAC like AA:BB:CC:DD:EE:FF"}
    basis = (basis or "").strip()
    if not basis:
        return {"ok": False, "error": "an authorization basis is required (e.g. 'owned' or an engagement ref)"}
    entries = load()
    if any(e.get("bssid") == b for e in entries):
        return {"ok": False, "error": f"{b} is already authorized"}
    entry = {
        "bssid": b,
        "ssid_label": (ssid_label or "").strip()[:64],
        "basis": basis[:128],
        "added": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    entries.append(entry)
    _save(entries)
    return {"ok": True, "entry": entry}


def remove(bssid: str) -> dict:
    b = normalize_bssid(bssid)
    entries = load()
    kept = [e for e in entries if e.get("bssid") != b]
    if len(kept) == len(entries):
        return {"ok": False, "error": "not on the allowlist"}
    _save(kept)
    return {"ok": True}
