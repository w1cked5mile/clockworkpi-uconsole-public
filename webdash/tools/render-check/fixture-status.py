#!/usr/bin/env python3
"""Emit fixture-status.js: one hand-authored status snapshot shaped exactly like
main.build_status() (webdash/app/main.py), for view-harness.html. Clearly a FIXTURE — NOT live
device data. The mesh transmit-control fields (mesh.tx / mesh.mqtt / mesh.tx_copy) are built with
the REAL app/collectors/mesh_radio.py (as actuator-fixtures.py does), so that copy matches the
server; every other value is static, chosen to exercise each branch of views.js render() and the
per-view syncs. Location is invented (grid-only policy) and is NOT Fancy's real position.
Stdlib only; run by render-view.sh.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.collectors import mesh_radio as mr  # noqa: E402

NOW = int(time.time())

# aiov2.collect() ; power_num. All four rails on so every tile/switch shows a powered state; flip
# individual .on to false to render "rail off" branches.
AIOV2 = {
    "state": "ok", "ok": True,
    "power": {"source": "BAT", "status": "discharging", "mode": "1S", "capacity": "41%",
              "voltage": "3.97 V", "current": "0.96 A", "power": "3.81 W"},
    "power_num": {"voltage_v": 3.97, "current_a": 0.96, "power_w": 3.81,
                  "capacity_pct": 41.0, "on_battery": True},
    "rails": {"GPS": {"gpio": 17, "on": True}, "LORA": {"gpio": 16, "on": True},
              "SDR": {"gpio": 13, "on": True}, "USB": {"gpio": 26, "on": True}},
}

# services.collect() — state + one dict per unit. Used by mesh_radio.readiness at build time and by
# learn live paths (services.<unit>.active) at runtime.
SERVICES = {
    "state": "ok",
    "meshtasticd": {"active": "active", "sub": "running", "crash_looping": False},
    "gpsd": {"active": "active", "sub": "running", "crash_looping": False},
    "readsb": {"active": "inactive", "sub": "dead", "crash_looping": False},
    "kismet": {"active": "active", "sub": "running", "crash_looping": False},
}

# mesh radio/channels — same shape as actuator-fixtures.py (mesh.py builds these).
RADIO = {"region": "US", "preset": "LONG_FAST", "tx_enabled": True, "is_licensed": False,
         "freq_mhz": 924.125, "freq_source": "config", "freq_check": "agrees", "primary": "SCMesh",
         "position_on": True, "mqtt_enabled": True, "tx_power_dbm": 22,
         "mqtt_address": "mqtt.scmesh.us", "mqtt_map_reporting": True, "mqtt_map_precision_km": 2.9,
         "mqtt_map_interval_s": 3600}
CHANNELS = [
    {"index": 0, "name": "SCMesh", "role": "PRIMARY", "public": True, "uplink": True,
     "position_km": 2.9, "own_freq_mhz": 924.125},
    {"index": 1, "name": "NCMesh", "role": "SECONDARY", "public": True, "uplink": False,
     "position_km": None, "own_freq_mhz": 916.875},
]


def mesh():
    # mesh.collect() ; tx/mqtt/tx_copy added by mesh.with_tx via mesh_radio.
    m = {
        "state": "running", "connected": True,
        "node_id": "!fa000001", "long_name": "Fancy",
        "battery_percent": 101,              # 101 == external power (views.js)
        "nodes_seen": 12, "rx_packets": 48, "rx_nodes": 7,
        "last_rx_ts": NOW - 120, "last_rx_snr": -8.5, "last_rx_rssi": -96,
        "channels": ["NCMesh", "SCMesh"], "web_ui": False,
        "radio": RADIO, "channel_detail": CHANNELS,
    }
    m["tx"] = mr.readiness(m, AIOV2, SERVICES)
    m["mqtt"] = mr.mqtt_model(m, SERVICES)
    m["tx_copy"] = {
        "captions": mr.channel_captions(m["radio"], m["channel_detail"]),
        "legal": mr.LEGAL, "public": mr.PUBLIC, "retries": mr.RETRIES, "no_retries": mr.NO_RETRIES,
        "power": mr.power_line(None, m["radio"].get("tx_power_dbm")), "byte_limit": mr.BYTE_LIMIT,
    }
    return m


STATUS = {
    # system.collect() ; temp_avg_1h_c is added in main.py.
    "system": {
        "cpu_percent": 23.0, "cpu_count": 4,
        "load": {"1m": 0.62, "5m": 0.48, "15m": 0.41},
        "mem": {"total": 8205037568, "available": 6039797760, "percent": 26.4},
        "disk": {"total": 250685575168, "used": 41231048704, "free": 196612345856, "percent": 17.3},
        "temp_c": 52.4, "temp_avg_1h_c": 50.1, "undervoltage": False, "uptime_s": 384210,
    },
    "aiov2": AIOV2,
    "kismet": {"state": "running", "devices": 137},
    # gps.py — INVENTED coordinates (grid IO91, London-ish); NOT Fancy's real location.
    "gps": {"state": "running", "fix": "3D", "lat": 51.5, "lon": -0.12, "grid": "IO91wm",
            "satellites_visible": 15, "satellites_used": 15, "hdop": 0.7, "pdop": 1.1,
            "eph_m": 4.8, "tpv_age_s": 1.2},
    "adsb": {"state": "running", "aircraft_count": 6, "with_position": 4,
             "messages_per_s": 120.0},
    "mesh": mesh(),
    "services": SERVICES,
    "net": {"state": "ok", "monitor_ifaces": 1,
            "wlan0": {"present": True, "mode": "managed"},
            "wlan1": {"present": True, "mode": "monitor"}},
    # tshark.collect() ({"state":"ok", **bridge}); inner shape from tshark.js syncTshark.
    "tshark": {"state": "ok", "running": False, "stage": "idle", "message": "",
               "interfaces": ["wlan1", "eth0", "lo"],
               "segment_packets": None, "segment_kb": None,
               "findings": {}, "protocols": [], "pcaps": []},
    "generated_at": NOW,
}

print("export default " + json.dumps(STATUS, ensure_ascii=False, indent=1) + ";")
