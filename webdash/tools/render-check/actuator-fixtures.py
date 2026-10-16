#!/usr/bin/env python3
"""Emit fixtures.js for actuator-harness.html: one `data.mesh` status object per transmit-control
state, built by the REAL app/collectors/mesh_radio.py (readiness and copy), so the render shows
exactly the strings the server would send. Stdlib only; run by render-actuator.sh.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from app.collectors import mesh_radio as mr  # noqa: E402

SVC = {"state": "ok", "meshtasticd": {"active": "active", "sub": "running", "crash_looping": False}}
RAIL = {"state": "ok", "rails": {"LORA": {"gpio": 16, "on": True}}}
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


def mesh(radio=None, channels=None, state="running", connected=True, aiov2=RAIL, services=SVC):
    m = {"state": state, "connected": connected, "radio": radio if radio is not None else RADIO,
         "channel_detail": CHANNELS if channels is None else channels}
    m["tx"] = mr.readiness(m, aiov2, services)
    m["mqtt"] = mr.mqtt_model(m, services)
    m["tx_copy"] = {
        "captions": mr.channel_captions(m["radio"], m["channel_detail"]),
        "legal": mr.LEGAL, "public": mr.PUBLIC, "retries": mr.RETRIES, "no_retries": mr.NO_RETRIES,
        "power": mr.power_line(None, m["radio"].get("tx_power_dbm")), "byte_limit": mr.BYTE_LIMIT,
    }
    return m


# state -> {mesh, channel (select index), text (typed message)}
STATES = {
    "ready": {"mesh": mesh(), "channel": 0, "text": "Fancy test"},
    "secondary": {"mesh": mesh(), "channel": 1, "text": "Fancy test"},
    "no-relay": {"mesh": mesh(), "channel": 0, "text": "Fancy test", "relay": False},
    "too-long": {"mesh": mesh(), "channel": 0, "text": "é" * 101},
    "rail-off": {"mesh": mesh(aiov2={"state": "ok", "rails": {"LORA": {"on": False}}}), "channel": 0},
    "rail-unknown": {"mesh": mesh(aiov2={"state": "unavailable"}), "channel": 0},
    "unreachable": {"mesh": mesh(connected=False), "channel": 0},
    "no-channels": {"mesh": mesh(channels=[]), "channel": None},
    "disagree": {"mesh": mesh(radio={**RADIO, "freq_check": "disagrees"}), "channel": 0},
    "checking": {"mesh": None, "channel": None},
    "mqtt-off": {"mesh": mesh(radio={**RADIO, "mqtt_enabled": False}), "channel": 0},
}

print("export default " + json.dumps(STATES, ensure_ascii=False, indent=1) + ";")
