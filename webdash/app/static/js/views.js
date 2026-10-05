// Renders one status snapshot into the status strip, the overview tiles and the detail views.
// Station status (data-status="<station>") combines each service with the rail that powers it:
// a service whose rail is off reads "rail off", however the service itself reports.

import { fmtBytes, fmtUptime, maidenhead, railOn, setRows, setStatus, setText, show } from "./ui.js";
import { meshSummary } from "./mesh.js";

export let LINKS = {};
export function setLinks(links) { LINKS = links; }

// Which station each rail chip in the status strip leads to.
const RAIL_STATION = { GPS: "gps", LORA: "mesh", SDR: "sdr", USB: "wifi" };

let showCoords = false; // GPS precise position, revealed per page load only
export function toggleCoords() { showCoords = !showCoords; return showCoords; }

function stationStatus(data) {
  const a = data.aiov2, st = {};

  const m = data.mesh;
  const lora = railOn(a, "LORA");
  // meshtasticd stays reachable with the LORA rail off — the daemon runs, the SX1262 is unpowered.
  st.mesh = lora === false ? ["off", "rail off"] : m.state === "running" ? ["ok", "live"] : ["err", m.state || "error"];

  const g = data.gps;
  const gpsRail = railOn(a, "GPS");
  const fixed = g.fix === "3D" || g.fix === "2D";
  st.gps = gpsRail === false ? ["off", "rail off"]
    : g.state === "running" ? (fixed ? ["ok", `${g.fix} fix`] : ["idle", "searching"])
    : g.state === "stopped" ? ["action", "gpsd stopped"] : ["err", "error"];

  const ad = data.adsb;
  const sdr = railOn(a, "SDR");
  // The SDR rail only powers the tuner; readsb is systemctl-disabled and starts only when ADS-B is
  // chosen in the SDR view, so rail on + readsb stopped is a resting state, not "starting".
  st.sdr = sdr === false ? ["off", "rail off"]
    : ad.state === "running" ? (ad.aircraft_count > 0 ? ["ok", "live"] : ["idle", "listening"])
    : ad.state === "stopped" ? (sdr ? ["idle", "ADS-B off"] : ["off", "stopped"]) : ["err", "error"];

  // The USB rail powers the AIO V2's internal USB-C port, where the AC1200-class Wi-Fi radio sits.
  const k = data.kismet;
  const usb = railOn(a, "USB");
  st.wifi = usb === false ? ["off", "rail off"] : k.state === "running" ? ["ok", "live"] : k.state === "locked" ? ["action", "login needed"]
    : k.state === "stopped" ? ["off", "off"] : ["err", "error"];

  st.power = a.state === "ok" ? ["ok", (a.power && a.power.source) || "ok"] : ["err", "bridge down"];
  const t = data.system.temp_c;
  st.system = t == null ? ["ok", "ok"] : t >= 80 ? ["action", "hot"] : ["ok", "ok"];
  return st;
}

function renderStrip(data) {
  const a = data.aiov2, p = (a && a.power) || {};
  setText("strip-power", a.state === "ok" ? `${p.source || "?"} ${p.voltage || ""}`.trim() : "power ?");
  setText("strip-temp", data.system.temp_c != null ? `${data.system.temp_c.toFixed(0)}°C` : "—");
  for (const chip of document.querySelectorAll(".rail-chip")) {
    const on = railOn(a, chip.dataset.rail);
    const level = on === null ? "err" : on ? "ok" : "off";
    chip.className = `rail-chip status ${level}`;
    chip.textContent = `${on === null ? "✕" : on ? "●" : "○"} ${chip.dataset.rail}`;
    chip.setAttribute("aria-label", `${chip.dataset.rail} rail ${on === null ? "unknown" : on ? "on" : "off"}`);
    chip.href = `#/${RAIL_STATION[chip.dataset.rail]}`;
  }
}

function renderTiles(data, st) {
  const a = data.aiov2;

  const m = data.mesh;
  const others = m.state === "running" && m.nodes_seen != null ? Math.max(0, m.nodes_seen - 1) : null;
  setText("tile-mesh-hero", others ?? "—");
  setText("tile-mesh-caption", others === 1 ? "other node known" : "other nodes known");
  const last = meshSummary.last;
  setRows("tile-mesh-facts", [
    ["Node", m.long_name || m.node_id],
    ["Last heard", last ? `${last.from_name || last.from_id || "?"}: ${last.text}` : "no messages yet"],
  ]);
  setText("tile-mesh-link", meshSummary.unread ? `Details · ${meshSummary.unread} new →` : "Details →");

  const g = data.gps;
  const fixed = g.fix === "3D" || g.fix === "2D";
  setText("tile-gps-hero", g.state === "running" ? (fixed ? g.fix : "No fix") : "—");
  setText("tile-gps-caption", fixed ? "position fix" : st.gps[1] === "searching" ? "needs sky view" : "position fix");
  setRows("tile-gps-facts", [
    ["Satellites", g.state === "running" ? `${g.satellites_used} used / ${g.satellites_visible} seen` : "—"],
    ["Grid", g.lat != null ? maidenhead(g.lat, g.lon) : "—"],
  ]);

  const ad = data.adsb;
  setText("tile-sdr-hero", ad.state === "running" ? ad.aircraft_count : "—");
  setText("tile-sdr-caption", "aircraft tracked");
  setRows("tile-sdr-facts", [
    ["With position", ad.state === "running" ? ad.with_position : "—"],
    ["Decoder", st.sdr[1]],
  ]);

  const k = data.kismet;
  setText("tile-wifi-hero", k.state === "running" ? (k.devices ?? "—") : "—");
  setText("tile-wifi-caption", "devices seen");
  setRows("tile-wifi-facts", [
    ["Kismet", k.state === "locked" ? "running, login not set" : k.state],
    ["Mode", "passive: listens only"],
  ]);

  const p = (a && a.power) || {};
  setText("tile-power-hero", a.state === "ok" ? p.voltage || "—" : "—");
  setText("tile-power-caption", "pack voltage");
  setRows("tile-power-facts", [
    ["Source", a.state === "ok" ? [p.source, p.status].filter(Boolean).join(" · ") : "bridge unavailable"],
    ["Power", p.power || "—"],
  ]);

  const s = data.system;
  setText("tile-system-hero", s.temp_c != null ? `${s.temp_c.toFixed(0)}°C` : "—");
  setText("tile-system-caption", "CPU temp");
  setRows("tile-system-facts", [
    ["CPU", `${s.cpu_percent.toFixed(0)}% of ${s.cpu_count} cores`],
    ["Memory", `${s.mem.percent.toFixed(0)}% used`],
  ]);
}

function renderDetails(data, route) {
  const s = data.system;
  setText("sys-cpu", `${s.cpu_percent.toFixed(0)}% (${s.cpu_count} cores)`);
  setText("sys-load", `${s.load["1m"].toFixed(2)} / ${s.load["5m"].toFixed(2)} / ${s.load["15m"].toFixed(2)}`);
  setText("sys-mem", `${fmtBytes(s.mem.available)} free of ${fmtBytes(s.mem.total)} (${s.mem.percent.toFixed(0)}% used)`);
  setText("sys-disk", `${fmtBytes(s.disk.free)} free of ${fmtBytes(s.disk.total)} (${s.disk.percent.toFixed(0)}% used)`);
  setText("sys-temp", s.temp_c != null ? `${s.temp_c.toFixed(1)}°C` : "—");
  setText("sys-temp-avg", s.temp_avg_1h_c != null ? `${s.temp_avg_1h_c.toFixed(1)}°C` : "—");
  setText("sys-uptime", fmtUptime(s.uptime_s));

  const a = data.aiov2, p = (a && a.power) || {};
  setRows("power-body", a.state === "ok"
    ? [["Source", p.source], ["Status", p.status], ["Mode", p.mode], ["Capacity", p.capacity],
       ["Voltage", p.voltage], ["Current", p.current], ["Power", p.power]]
    : [["Bridge", "unavailable"]]);
  // Throttle: the Pi firmware's under-voltage alarm (5 V rail sagging). From data.system, not the
  // AIO V2 bridge, so it shows even when the bridge is down.
  const uv = data.system.undervoltage;
  setText("power-throttle", uv == null ? "—" : uv ? "⚠ under-voltage" : "none");

  const k = data.kismet;
  setRows("kismet-body", k.state === "running"
    ? [["Devices seen", k.devices]]
    : [["State", railOn(a, "USB") === false ? "USB rail off"
        : k.state === "locked" ? "running, admin login not set" : k.state]]);
  show("kismet-link", k.state === "running" || k.state === "locked", "inline-block");

  const g = data.gps;
  setRows("gps-body", g.state === "running"
    ? [
        ["Fix", g.fix === "none" || g.fix === "unknown" ? "none yet (needs sky view)" : g.fix],
        ["Satellites (used/seen)", `${g.satellites_used}/${g.satellites_visible}`],
        ["Grid square", g.lat != null ? maidenhead(g.lat, g.lon) : "no fix"],
        ...(showCoords ? [["Position", g.lat != null ? `${g.lat.toFixed(5)}, ${g.lon.toFixed(5)}` : "no fix"]] : []),
      ]
    : [["State", g.state]]);

  const ad = data.adsb;
  const sdr = railOn(a, "SDR");
  setRows("adsb-body", ad.state === "running"
    ? [["Aircraft tracked", ad.aircraft_count], ["With position", ad.with_position]]
    : [["State", sdr === false ? "SDR rail off" : ad.state]]);
  // The ADS-B map opens in its own browser tab via the link rather than embedding in the
  // dashboard, so it's never reloaded out from under the operator by a status tick and doesn't
  // keep rendering behind other views.
  show("adsb-link", ad.state === "running", "inline-block");

  const m = data.mesh;
  // Meshtastic reports batteryLevel 101 to mean "on external power", not a charge level.
  const meshPower = m.battery_percent == null ? "—" : m.battery_percent > 100 ? "external power" : `${m.battery_percent}%`;
  setRows("mesh-body", m.state === "running"
    ? [
        ["Node", m.long_name || m.node_id],
        ["Battery", meshPower],
        ["Nodes seen (incl. this one)", m.nodes_seen],
        ["Channels", (m.channels || []).join(", ")],
      ]
    : [["State", m.state]]);
  // meshtasticd's own web UI: link only when its port actually answers (it currently doesn't —
  // known issue); otherwise the note explaining why stays visible.
  const webUi = m.web_ui === true && LINKS.meshtastic_ui;
  show("mesh-link", webUi, "inline-block");
  show("mesh-webui-note", !webUi);
}

export function render(data, route) {
  const st = stationStatus(data);
  for (const [key, [level, word]] of Object.entries(st)) setStatus(key, level, word);
  renderStrip(data);
  renderTiles(data, st);
  renderDetails(data, route);
}

