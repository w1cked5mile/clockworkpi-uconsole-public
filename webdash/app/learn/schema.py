"""Shared vocabulary for the learning platform: status paths content may reference, check types
labs may use, and the value helpers both sides need.

Imported by the host-side compiler (webdash/host-helpers/learn-compile.py, loaded by file path —
it runs outside the container) and by the server's validator, so this module must stay free of
third-party imports. See docs/reference/learning-platform-plan.md §3.2 and §2.3.
"""

# Status paths a lesson's {live:…} token or a lab check may read. Anything else fails compilation,
# so a typo is caught before it reaches a learner as a check that can never pass. gps.lat/gps.lon
# are deliberately absent: learning content handles location as gps.grid only.
_RAILS = ("GPS", "LORA", "SDR", "USB")
_SERVICES = ("readsb", "gpsd", "meshtasticd", "kismet")
LIVE_PATHS = frozenset(
    [
        "system.cpu_percent", "system.temp_c", "system.load.1m", "system.load.5m",
        "system.mem.percent", "system.disk.percent", "system.uptime_s",
        "aiov2.state",
        "aiov2.power.source", "aiov2.power.status", "aiov2.power.direction", "aiov2.power.mode",
        "aiov2.power_num.voltage_v", "aiov2.power_num.current_a", "aiov2.power_num.power_w",
        "aiov2.power_num.capacity_pct", "aiov2.power_num.on_battery",
        "gps.state", "gps.fix", "gps.grid", "gps.satellites_visible", "gps.satellites_used",
        "gps.hdop", "gps.pdop", "gps.eph_m", "gps.tpv_age_s",
        "adsb.state", "adsb.aircraft_count", "adsb.with_position", "adsb.messages_per_s",
        "mesh.state", "mesh.node_id", "mesh.long_name", "mesh.nodes_seen", "mesh.channels",
        "mesh.rx_packets", "mesh.rx_nodes", "mesh.last_rx_ts", "mesh.last_rx_snr",
        "mesh.last_rx_rssi",
        "kismet.state", "kismet.devices",
        "services.state",
        "net.state", "net.monitor_ifaces",
    ]
    + [f"aiov2.rails.{r}.on" for r in _RAILS]
    + [f"services.{s}.{f}" for s in _SERVICES for f in ("active", "sub", "n_restarts", "crash_looping")]
    + [f"net.{i}.{f}" for i in ("wlan0", "wlan1") for f in ("present", "mode")]
)

FORBIDDEN_PATHS = frozenset(["gps.lat", "gps.lon"])

# Host paths a lab's file check may look under (labs.py enforces this at runtime, the compiler at
# build time). "~" is the owner's home. Checks return booleans and counts, never contents.
HOME = "/home/user"
FILE_ROOTS = (f"{HOME}/labs", f"{HOME}/kismet-logs", f"{HOME}/meshtastic-first-packet.log",
              f"{HOME}/clockworkpi-uconsole/knowledge", f"{HOME}/clockworkpi-uconsole/configs",
              "/etc/default", "/etc/kismet", "/etc/modprobe.d", "/etc/profile.d", "/etc/udev/rules.d",
              "/sys/class/net", "/run/readsb")


def file_allowed(path: str) -> bool:
    import os
    p = os.path.normpath(path.replace("~", HOME, 1) if path.startswith("~") else path)
    return any(p == r or p.startswith(r.rstrip("/") + "/") for r in FILE_ROOTS)

STATUS_OPS = frozenset(["eq", "ne", "gte", "lte", "gt", "lt", "in", "contains", "exists"])

# Check types a lab step may use (§2.3 validator API). `computed` and `messages` are named
# registries — never expressions — so content can't smuggle code into the server.
CHECK_TYPES = frozenset(["status", "computed", "messages", "file", "paste", "attest", "quiz"])
COMPUTED_FNS = frozenset(["mean", "delta", "rise", "first_true_elapsed", "counter_rate"])
FILE_OPS = frozenset(
    ["exists", "absent", "mtime_after_step", "size_range", "sha256_equal", "regex_count",
     "csv_shape", "not_under_repo"]
)
PASTE_PARSERS = frozenset(
    ["regex", "rtl_test_t", "rtl_test_loss", "rtl_test_ppm", "journal_set_radio",
     "alert_dry_run", "vcgencmd_throttled", "rtl_ais_count"]
)
MESSAGE_FIELDS = frozenset(["mine", "direct", "snr", "rssi", "channel"])

LAB_MODES = frozenset(["observe", "guided", "offline", "sandbox"])
TODAY_STATES = frozenset(["ready", "degraded", "blocked"])
STATIONS = frozenset(["mesh", "gps", "sdr", "wifi", "power", "system"])
ITEM_TYPES = frozenset(["single", "multi", "numeric"])  # "order" returns when the browser can answer it
DISCIPLINES = frozenset(
    ["rf-fundamentals", "sdr", "mesh-networks", "wardriving", "aerospace", "communications",
     "ham-radio", "platform"]
)


def get_path(status: dict, path: str):
    """Walk a dotted path through the status snapshot. Missing -> KeyError (the validator reports
    'can't evaluate: field missing', which is different from 'false')."""
    cur = status
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            raise KeyError(path)
        cur = cur[part]
    return cur


def num(v):
    """'4.2 V' / '0.83 W' / '100%' / 4.2 -> float; None when not numeric."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return float(v)
    try:
        return float(str(v).split()[0].rstrip("%"))
    except (ValueError, IndexError):
        return None
