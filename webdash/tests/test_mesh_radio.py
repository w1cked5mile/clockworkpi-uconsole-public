"""Unit tests for the mesh transmit control's pure helpers: the firmware frequency rule, position
precision, power wording, send readiness, per-channel captions, and the copy rules from the RF
review. Also checks the skin colour tokens used by the control for WCAG contrast. stdlib unittest,
no network, device or meshtastic import, so it runs on the host as well as in the container:

  cd webdash && PYTHONPATH=. python3 tests/test_mesh_radio.py
  sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/test_mesh_radio.py
"""
import os
import re
import unittest

import threading

from app.collectors import mesh  # noqa: E402  (meshtastic is imported lazily, never here)
from app.collectors import mesh_radio as mr  # noqa: E402

US = dict(region="US", preset="LONG_FAST", use_preset=True, bandwidth=250, channel_num=0)

# Status fragments shaped like build_status() output.
SVC_OK = {"state": "ok", "meshtasticd": {"active": "active", "sub": "running",
                                         "crash_looping": False}}
RAIL_ON = {"state": "ok", "rails": {"LORA": {"gpio": 16, "on": True}}}
RADIO = {"region": "US", "tx_enabled": True, "is_licensed": False, "freq_mhz": 924.125,
         "freq_source": "config", "freq_check": "agrees", "primary": "SCMesh", "position_on": True}
CHANNELS = [
    {"index": 0, "name": "SCMesh", "role": "PRIMARY", "public": True, "position_km": 2.9,
     "own_freq_mhz": 924.125},
    {"index": 1, "name": "NCMesh", "role": "SECONDARY", "public": True, "position_km": None,
     "own_freq_mhz": 916.875},
]
MESH_OK = {"state": "running", "connected": True, "radio": RADIO, "channel_detail": CHANNELS}


class FrequencyTest(unittest.TestCase):
    def test_djb2_slots(self):
        for name, slot in (("LongFast", 19), ("SCMesh", 88), ("NCMesh", 59)):
            self.assertEqual(mr.djb2(name) % 104, slot, name)

    def test_us_long_fast(self):
        for name, mhz in (("LongFast", 906.875), ("SCMesh", 924.125), ("NCMesh", 916.875),
                          ("MediumFast", 913.125)):
            f = mr.lora_frequency(name=name, **US)
            self.assertEqual(f["mhz"], mhz, name)
            self.assertEqual(f["slots"], 104)
            self.assertEqual(f["source"], "config")

    def test_other_bandwidths(self):
        f = mr.lora_frequency("US", "SHORT_TURBO", True, 0, 0, "ShortTurbo")
        self.assertEqual((f["slots"], f["slot"], f["mhz"]), (52, 49, 926.75))
        f = mr.lora_frequency("US", "LONG_SLOW", True, 0, 0, "LongSlow")
        self.assertEqual((f["slots"], f["slot"], f["mhz"]), (208, 26, 905.3125))

    def test_channel_num_pins_the_slot(self):
        self.assertEqual(mr.lora_frequency(name="SCMesh", **{**US, "channel_num": 1})["mhz"], 902.125)
        self.assertEqual(mr.lora_frequency(name="SCMesh", **{**US, "channel_num": 105})["slot"], 0)
        # The 2026-10-11 fault: channel_num 20 held an SCMesh primary on LongFast's slot.
        self.assertEqual(mr.lora_frequency(name="SCMesh", **{**US, "channel_num": 20})["mhz"], 906.875)

    def test_override(self):
        f = mr.lora_frequency(name="SCMesh", override_mhz=915.0, **US)
        self.assertEqual(f, {"mhz": 915.0, "source": "override", "slot": None, "slots": None})

    def test_unknown(self):
        self.assertIsNone(mr.lora_frequency("EU_868", "LONG_FAST", True, 0, 0, "LongFast"))
        self.assertIsNone(mr.lora_frequency("US", "LITE_FAST", True, 0, 0, "LiteFast"))
        self.assertIsNone(mr.lora_frequency(name="", **US))
        self.assertIsNone(mr.preset_display_name("VERY_LONG_SLOW"))
        self.assertEqual(mr.preset_display_name("LONG_FAST"), "LongFast")


class PrecisionPowerTest(unittest.TestCase):
    def test_precision(self):
        self.assertAlmostEqual(mr.precision_km(13), 2.9, delta=0.05)
        self.assertIsNone(mr.precision_km(0))
        self.assertEqual(mr.precision_km(32), "precise")

    def test_power_never_shows_config_value(self):
        self.assertEqual(mr.power_dbm(30), (22, "clamped"))
        self.assertEqual(mr.power_dbm(0), (22, "clamped"))
        self.assertEqual(mr.power_dbm(30, 22), (22, "journal"))
        self.assertEqual(mr.power_dbm(10), (10, "clamped"))
        line = mr.power_line(30)
        self.assertIn("22 dBm (≈160 mW)", line)
        self.assertNotIn("30", line)


class ReadinessTest(unittest.TestCase):
    def code(self, mesh=MESH_OK, aiov2=RAIL_ON, services=SVC_OK):
        return mr.readiness(mesh, aiov2, services)["code"]

    def test_ready(self):
        r = mr.readiness(MESH_OK, RAIL_ON, SVC_OK)
        self.assertTrue(r["can_send"])
        self.assertEqual(r["code"], "ready")

    def test_each_block(self):
        svc = lambda **kw: {"state": "ok", "meshtasticd": {**SVC_OK["meshtasticd"], **kw}}  # noqa: E731
        self.assertEqual(self.code(services=svc(crash_looping=True)), "daemon_crash")
        self.assertEqual(self.code(services=svc(active="inactive")), "daemon_down")
        self.assertEqual(self.code(mesh={**MESH_OK, "state": "unreachable"}), "daemon_unreachable")
        self.assertEqual(self.code(mesh={**MESH_OK, "connected": False}), "daemon_unreachable")
        self.assertEqual(self.code(aiov2={"state": "unavailable"}), "rail_unknown")
        self.assertEqual(self.code(aiov2={"state": "ok", "rails": {}}), "rail_unknown")
        self.assertEqual(self.code(aiov2={"state": "ok", "rails": {"LORA": {"on": False}}}),
                         "rail_off")
        radio = lambda **kw: {**MESH_OK, "radio": {**RADIO, **kw}}  # noqa: E731
        self.assertEqual(self.code(mesh=radio(region="UNSET")), "region_unset")
        self.assertEqual(self.code(mesh=radio(region="EU_868")), "region_other")
        self.assertEqual(self.code(mesh=radio(tx_enabled=False)), "tx_disabled")
        self.assertEqual(self.code(mesh=radio(is_licensed=True)), "licensed")
        self.assertEqual(self.code(mesh={**MESH_OK, "channel_detail": []}), "no_channels")

    def test_unknown_rail_never_allows_a_send(self):
        r = mr.readiness(MESH_OK, {"state": "unavailable"}, SVC_OK)
        self.assertFalse(r["can_send"])

    def test_bridge_down_does_not_hide_daemon_state(self):
        # services unavailable is not a daemon fault; fall through to the mesh/rail checks.
        self.assertEqual(self.code(services={"state": "unavailable"}), "ready")


class ResponseTest(unittest.TestCase):
    def test_tiers(self):
        ack = {"decoded": {"routing": {}}}  # errorReason omitted == NONE
        self.assertEqual(mr.classify_response(ack)[0], "relayed")
        self.assertEqual(mr.classify_response({"decoded": {"routing": {"errorReason": "NONE"}}})[0],
                         "relayed")
        self.assertEqual(mr.classify_response({**ack, "transportMechanism": "TRANSPORT_MQTT"})[0],
                         "mqtt_echo")
        self.assertEqual(mr.classify_response(
            {"decoded": {"routing": {"errorReason": "MAX_RETRANSMIT"}}})[0], "no_relay")
        tier, text = mr.classify_response({"decoded": {"routing": {"errorReason": "DUTY_CYCLE_LIMIT"}}})
        self.assertEqual((tier, text), ("not_sent", "Not sent: the radio's airtime limit was reached."))
        self.assertEqual(mr.classify_response({"decoded": {"routing": {"errorReason": "WEIRD"}}}),
                         ("not_sent", "Not sent: the radio refused it (WEIRD)."))

    def test_mqtt_line_needs_module_and_channel_uplink(self):
        chans = [{**CHANNELS[0], "uplink": True}, {**CHANNELS[1], "uplink": False}]
        on = mr.channel_captions({**RADIO, "mqtt_enabled": True}, chans)
        self.assertEqual(on[0]["mqtt_line"], mr.MQTT_LINE)
        self.assertIsNone(on[1]["mqtt_line"])
        off = mr.channel_captions({**RADIO, "mqtt_enabled": False}, chans)
        self.assertIsNone(off[0]["mqtt_line"])


class MqttModelTest(unittest.TestCase):
    RADIO_ON = {**RADIO, "mqtt_enabled": True, "mqtt_address": "mqtt.scmesh.us",
                "mqtt_map_reporting": True, "mqtt_map_precision_km": 2.9, "mqtt_map_interval_s": 3600}

    def model(self, radio, channels=None, mesh_extra=None, services=SVC_OK):
        chans = channels if channels is not None else [{**CHANNELS[0], "uplink": True}, CHANNELS[1]]
        return mr.mqtt_model({**MESH_OK, "radio": radio, "channel_detail": chans,
                              **(mesh_extra or {})}, services)

    def test_on_with_uplink_and_map(self):
        q = self.model(self.RADIO_ON)
        self.assertEqual(q["caption"], "MQTT on: this node posts SCMesh traffic to mqtt.scmesh.us.")
        self.assertEqual(q["note"], "Map reporting on: publishes its position (~2.9 km) to the "
                                    "public map every 60 min.")
        self.assertEqual(q["verb"], "Turn MQTT off")
        self.assertTrue(q["ready"]["can_send"])
        self.assertIn("restarts meshtasticd", q["restart"])
        self.assertIn("announces itself", q["restart"])

    def test_on_without_uplink(self):
        q = self.model(self.RADIO_ON, channels=[{**CHANNELS[0], "uplink": False}])
        self.assertIn("no channel has uplink enabled, so nothing is posted", q["caption"])

    def test_off_names_where_it_would_go(self):
        q = self.model({**self.RADIO_ON, "mqtt_enabled": False})
        self.assertEqual(q["caption"], "MQTT off: this node posts nothing online.")
        self.assertEqual(q["verb"], "Turn MQTT on (to mqtt.scmesh.us)")
        self.assertIsNone(q["note"])
        blank = self.model({**self.RADIO_ON, "mqtt_enabled": False, "mqtt_address": None})
        self.assertEqual(blank["verb"], "Turn MQTT on (to mqtt.meshtastic.org)")

    def test_blocked_when_daemon_unreachable_or_unknown(self):
        q = self.model(self.RADIO_ON, mesh_extra={"connected": False})
        self.assertEqual(q["ready"]["code"], "daemon_unreachable")
        q = self.model({})
        self.assertEqual(q["ready"]["code"], "mqtt_unknown")
        # The LORA rail doesn't matter: this is a config write, not a transmission.
        self.assertTrue(mr.mqtt_model({**MESH_OK, "radio": self.RADIO_ON}, SVC_OK)["ready"]["can_send"])


class CaptionTest(unittest.TestCase):
    def test_primary_and_secondary(self):
        caps = {c["index"]: c for c in mr.channel_captions(RADIO, CHANNELS)}
        self.assertEqual(caps[0]["caption"],
                         "Transmits on 924.125 MHz (from config) · LoRa SX1262 · public channel SCMesh")
        self.assertIsNone(caps[0]["note"])
        self.assertEqual(caps[1]["note"], "Sent on 924.125 MHz (set by primary SCMesh). "
                                          "NCMesh nodes on 916.875 MHz won't hear it.")
        self.assertEqual(caps[0]["position_line"],
                         "This node also broadcasts its position to ~2.9 km on SCMesh")
        self.assertEqual(caps[1]["position_line"], "Position broadcast: off")

    def test_disagree_shows_unknown(self):
        cap = mr.channel_captions({**RADIO, "freq_check": "disagrees"}, CHANNELS[:1])[0]
        self.assertIn("frequency unknown (config and radio log disagree)", cap["caption"])
        self.assertNotIn("924.125", cap["caption"])

    def test_override_badge(self):
        cap = mr.channel_captions({**RADIO, "freq_mhz": 915.0, "freq_source": "override"},
                                  CHANNELS[:1])[0]
        self.assertTrue(cap["caption"].startswith("Transmits on 915 MHz [override]"))


class CopyRulesTest(unittest.TestCase):
    STATIC = os.path.join(os.path.dirname(mr.__file__), "..", "static")

    def test_no_compliance_claims(self):
        texts = [mr.LEGAL, mr.PUBLIC, mr.QUEUED, mr.COUNTER, mr.RETRIES, mr.RELAYED, mr.NO_RELAY,
                 mr.NO_ANSWER, mr.MQTT_ECHO, mr.MQTT_LINE, *mr.NOT_SENT.values()]
        js = os.path.join(self.STATIC, "js")
        if os.path.isdir(js):
            for f in sorted(os.listdir(js)):
                if f.endswith(".js"):
                    with open(os.path.join(js, f), encoding="utf-8") as fh:
                        texts.append(fh.read())
        for t in texts:
            self.assertNotRegex(t, r"(?i)legal under")

    def test_success_copy_claims_only_what_is_witnessed(self):
        for s in (mr.QUEUED, mr.COUNTER, mr.NO_ANSWER, mr.MQTT_ECHO):
            self.assertNotRegex(s, r"(?i)part 15|delivered|relayed|received")
        for s in (mr.RELAYED, mr.RELAYED_SUB, mr.NO_RELAY):  # never names or claims a reader
            self.assertNotRegex(s, r"(?i)part 15|delivered|was read")
        self.assertEqual(mr.QUEUED.format(mhz="924.125"), "Queued in meshtasticd for 924.125 MHz.")


class _FakeIface:
    def __init__(self, connected=True, reader_alive=True, sock=object()):
        self.isConnected = threading.Event()
        if connected:
            self.isConnected.set()
        self._rxThread = threading.Thread(target=lambda: None)
        if reader_alive:
            self._rxThread.is_alive = lambda: True
        self.socket = sock


class RadioLogTest(unittest.TestCase):
    def data(self, **radio):
        return {"state": "running", "radio": {"freq_mhz": 924.125, "freq_check": "unchecked",
                                              "tx_power_dbm": 22, "tx_power_source": "clamped",
                                              **radio}}

    def test_agrees(self):
        d = self.data()
        mesh.apply_radio_log(d, {"freq_mhz": 924.125, "tx_dbm": 22})
        self.assertEqual(d["radio"]["freq_check"], "agrees")
        self.assertEqual(d["radio"]["tx_power_source"], "journal")

    def test_disagrees(self):
        d = self.data()
        mesh.apply_radio_log(d, {"freq_mhz": 906.875, "tx_dbm": 22})
        self.assertEqual(d["radio"]["freq_check"], "disagrees")

    def test_config_unknown_uses_log(self):
        d = self.data(freq_mhz=None)
        mesh.apply_radio_log(d, {"freq_mhz": 924.125, "tx_dbm": None})
        self.assertEqual((d["radio"]["freq_mhz"], d["radio"]["freq_source"]), (924.125, "radio log"))
        cap = mr.channel_captions(d["radio"], CHANNELS[:1])[0]["caption"]
        self.assertTrue(cap.startswith("Transmits on 924.125 MHz (from radio log)"))

    def test_no_log_changes_nothing(self):
        d = self.data()
        mesh.apply_radio_log(d, None)
        self.assertEqual(d["radio"]["freq_check"], "unchecked")


class LivenessTest(unittest.TestCase):
    def tearDown(self):
        mesh._IFACE = None

    def test_alive(self):
        self.assertFalse(mesh._alive(None))
        self.assertTrue(mesh._alive(_FakeIface()))
        self.assertFalse(mesh._alive(_FakeIface(connected=False)))
        self.assertFalse(mesh._alive(_FakeIface(reader_alive=False)))
        self.assertFalse(mesh._alive(_FakeIface(sock=None)))

    def test_messages_reports_dead_interface(self):
        mesh._IFACE = _FakeIface(connected=False)
        out = mesh.messages()
        self.assertFalse(out["connected"])
        self.assertEqual(out["channels"], [])

    def test_with_tx_uses_live_connection_not_cache(self):
        mesh._IFACE = _FakeIface(connected=False)
        m = mesh.with_tx(MESH_OK, RAIL_ON, SVC_OK)
        self.assertEqual(m["tx"]["code"], "daemon_unreachable")
        mesh._IFACE = _FakeIface()
        m = mesh.with_tx(MESH_OK, RAIL_ON, SVC_OK)
        self.assertTrue(m["tx"]["can_send"])
        self.assertEqual(m["tx_copy"]["power"], "Set to 22 dBm (≈160 mW) at the radio chip; not measured.")
        self.assertEqual(len(m["tx_copy"]["captions"]), 2)
        self.assertNotIn("tx", MESH_OK)  # the cached dict is never mutated


class _SendIface(_FakeIface):
    """Records sendData calls; never transmits. Lets a test fire the Routing callback."""
    def __init__(self, tx=10, **kw):
        super().__init__(**kw)
        self.calls, self.responseHandlers, self.readded = [], {}, []
        self.myInfo = type("I", (), {"my_node_num": 1})()
        self.nodesByNum = {1: {"localStats": {"numPacketsTx": tx, "airUtilTx": 0.1}}}

    def sendData(self, data, **kw):
        self.calls.append((data, kw))
        self.cb = kw.get("onResponse")
        return type("P", (), {"id": 4242})()

    def _addResponseHandler(self, rid, cb, ackPermitted=False):
        self.readded.append((rid, ackPermitted))


def _have_meshtastic():
    try:
        import meshtastic.protobuf.portnums_pb2  # noqa: F401
        return True
    except ImportError:
        return False


@unittest.skipUnless(_have_meshtastic(), "needs the meshtastic library (run in the container)")
class SendTest(unittest.TestCase):
    def setUp(self):
        import asyncio
        self.run = asyncio.run
        mesh._MESSAGES.clear(); mesh._PENDING.clear()
        mesh._STATS.update(num_packets_tx=None, air_util_tx=None, changed_at=None)
        mesh._CACHE["data"] = {"state": "running", "radio": {"freq_mhz": 924.125,
                                                            "freq_check": "agrees"}}
        mesh._IFACE = self.iface = _SendIface()

    def tearDown(self):
        mesh._IFACE = None; mesh._MESSAGES.clear(); mesh._PENDING.clear()

    def send(self, text="hello"):
        return self.run(mesh.send_text(text, 0))

    def last(self):
        return mesh.messages()["messages"][-1]

    def test_queued_with_want_ack(self):
        out = self.send()
        self.assertEqual(out, {"ok": True, "tier": "queued", "freq_mhz": 924.125,
                               "message": "Queued in meshtasticd for 924.125 MHz.",
                               "relay_check": True})
        data, kw = self.iface.calls[0]
        self.assertEqual(data, b"hello")
        self.assertTrue(kw["wantAck"]); self.assertTrue(kw["onResponseAckPermitted"])
        row = self.last()
        self.assertEqual((row["tier"], row["packet_id"], row["tx_base"]), ("queued", 4242, 10))

    def test_without_relay_check(self):
        out = self.run(mesh.send_text("hello", 0, want_ack=False))
        self.assertTrue(out["ok"]); self.assertFalse(out["relay_check"])
        _, kw = self.iface.calls[0]
        self.assertFalse(kw["wantAck"])
        self.assertNotIn("onResponse", kw)
        self.assertEqual(mesh._PENDING, {})
        row = self.last()
        self.assertEqual((row["tier"], row["relay_check"]), ("queued", False))
        mesh._MESSAGES[-1]["ts"] -= 120  # long past the timeout: never becomes "no answer"
        self.assertEqual(self.last()["tier"], "queued")

    def test_dead_interface_refuses_and_leaves_no_row(self):
        mesh._IFACE = _SendIface(connected=False)
        out = self.send()
        self.assertFalse(out["ok"])
        self.assertIn("not connected", out["error"])
        self.assertEqual(mesh.messages()["messages"], [])

    def test_relayed(self):
        self.send()
        self.iface.cb({"decoded": {"routing": {}}})
        row = self.last()
        self.assertEqual((row["tier"], row["tier_text"]), ("relayed", mr.RELAYED))
        self.assertEqual(row["tier_sub"], mr.RELAYED_SUB)
        self.assertNotIn(4242, mesh._PENDING)

    def test_mqtt_echo_keeps_waiting(self):
        self.send()
        self.iface.cb({"decoded": {"routing": {}}, "transportMechanism": "TRANSPORT_MQTT"})
        self.assertEqual(self.last()["tier"], "mqtt_echo")
        self.assertIn(4242, mesh._PENDING)
        self.assertEqual(self.iface.readded, [(4242, True)])

    def test_timeout_and_handler_cleanup(self):
        self.send()
        self.iface.responseHandlers[4242] = object()
        mesh._PENDING[4242]["deadline"] = 0
        row = self.last()
        self.assertEqual((row["tier"], row["tier_text"]), ("no_answer", mr.NO_ANSWER))
        self.assertNotIn(4242, self.iface.responseHandlers)

    def test_counter_rose_only_after_send(self):
        self.send()
        ts = mesh._MESSAGES[-1]["ts"]
        mesh._STATS.update(num_packets_tx=11, changed_at=ts - 5)  # rose before the send: no
        self.assertFalse(self.last()["counter_rose"])
        mesh._STATS.update(changed_at=ts + 5)
        row = self.last()
        self.assertTrue(row["counter_rose"]); self.assertEqual(row["counter_text"], mr.COUNTER)

    def test_not_sent_overrides_counter(self):
        self.send()
        self.iface.cb({"decoded": {"routing": {"errorReason": "DUTY_CYCLE_LIMIT"}}})
        mesh._STATS.update(num_packets_tx=11, changed_at=mesh._MESSAGES[-1]["ts"] + 5)
        row = self.last()
        self.assertEqual(row["tier"], "not_sent"); self.assertFalse(row["counter_rose"])

    def test_set_mqtt_writes_only_enabled(self):
        node = type("N", (), {})()
        node.moduleConfig = type("M", (), {})()
        node.moduleConfig.mqtt = type("Q", (), {"enabled": True, "address": "mqtt.scmesh.us"})()
        node.writes = []
        node.writeConfig = lambda name: node.writes.append((name, node.moduleConfig.mqtt.enabled))
        self.iface.localNode = node
        out = self.run(mesh.set_mqtt(False))
        self.assertTrue(out["ok"]); self.assertFalse(out["enabled"])
        self.assertEqual(node.writes, [("mqtt", False)])
        self.assertEqual(node.moduleConfig.mqtt.address, "mqtt.scmesh.us")
        self.assertIn("restarting", out["message"])

    def test_set_mqtt_refuses_when_dead(self):
        mesh._IFACE = _SendIface(connected=False)
        out = self.run(mesh.set_mqtt(False))
        self.assertFalse(out["ok"]); self.assertIn("not connected", out["error"])

    def test_over_200_bytes(self):
        out = self.send("é" * 101)  # 202 bytes, 101 characters
        self.assertFalse(out["ok"]); self.assertEqual(self.iface.calls, [])


def _tokens(css: str, selector: str) -> dict:
    """Colour tokens declared in `selector`'s block: hex values, or var(--other) references."""
    m = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return dict(re.findall(r"(--[\w-]+)\s*:\s*(#[0-9a-fA-F]{6}|var\(--[\w-]+\))", m.group(1))) if m else {}


def _skins(css: str) -> dict:
    base = _tokens(css, ":root")
    skins = {"default": base, "vintage": {**base, **_tokens(css, ':root[data-skin="vintage"]')}}
    for t in skins.values():  # resolve var(--x) against the same skin
        for k, v in t.items():
            while v.startswith("var("):
                v = t[v[4:-1]]
            t[k] = v
    return skins


def _lum(hex_):
    def ch(c):
        c = int(c, 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(hex_[i:i + 2]) for i in (1, 3, 5))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _ratio(a, b):
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


class ContrastTest(unittest.TestCase):
    """Text tokens the transmit control uses must reach 4.5:1 on both panel colours, in every
    skin. Runs only where styles.css is present (the host checkout; tests/ isn't in the image)."""
    CSS = os.path.join(os.path.dirname(mr.__file__), "..", "static", "styles.css")

    def test_tokens(self):
        if not os.path.exists(self.CSS):
            self.skipTest("styles.css not present")
        for skin, t in self._skins().items():
            for fg in ("--tx", "--warn", "--dim", "--err", "--fg"):
                for bg in ("--panel", "--panel-2"):
                    r = _ratio(t[fg], t[bg])
                    self.assertGreaterEqual(r, 4.5, f"{skin} {fg} on {bg}: {r:.2f}")

    def test_strip_text_on_bg(self):
        """Text drawn on --bg needs 4.5:1 there: the strip's readouts (--dim), the Learn chip
        (--learn), and the status words in view headings (--ok / --idle / --err) (redesign phase 2)."""
        for skin, t in self._skins().items():
            for fg in ("--dim", "--learn", "--ok", "--idle", "--err", "--fg"):
                r = _ratio(t[fg], t["--bg"])
                self.assertGreaterEqual(r, 4.5, f"{skin} {fg} on --bg: {r:.2f}")

    def test_ui_components(self):
        """WCAG 1.4.11: the switch's off track and form-control edges need 3:1 where they sit."""
        for skin, t in self._skins().items():
            for bg in ("--panel", "--panel-2"):  # tiles, and the Power view's rail cards
                r = _ratio(t["--off"], t[bg])
                self.assertGreaterEqual(r, 3.0, f"{skin} --off track on {bg}: {r:.2f}")
            for bg in ("--panel", "--panel-2", "--bg"):
                r = _ratio(t["--edge"], t[bg])
                self.assertGreaterEqual(r, 3.0, f"{skin} --edge on {bg}: {r:.2f}")

    def _skins(self):
        if not os.path.exists(self.CSS):
            self.skipTest("styles.css not present")
        with open(self.CSS, encoding="utf-8") as fh:
            return _skins(fh.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
