// Mesh text messages and the transmit control. Messages are polled separately from the status
// websocket, like CyberDeck's panel; the transmit control follows the status tick (syncMesh), so
// a rail flip or a dead meshtasticd reaches the button within one tick.
// Message text, sender names and channel names come off the air from anyone on the channel, so
// they are only ever inserted with textContent, never innerHTML.
import { isBlocked, reasonText, renderActuator } from "./actuator.js";

// For the Mesh tile: the newest received message and how many arrived since the Mesh view was
// last open. Held per page load only.
export const meshSummary = { last: null, unread: 0 };
let readUpTo = null; // id of the newest message when the Mesh view was last open

function trackUnread(msgs) {
  const received = msgs.filter((m) => !m.mine);
  meshSummary.last = received.length ? received[received.length - 1] : null;
  if (readUpTo === null) readUpTo = msgs.length ? msgs[msgs.length - 1].id : 0; // first load: nothing is "new"
  meshSummary.unread = received.filter((m) => m.id > readUpTo).length;
}

export function markMeshRead() {
  const last = meshSummary.last;
  if (last && (readUpTo === null || last.id > readUpTo)) readUpTo = last.id;
  meshSummary.unread = 0;
}

const BYTE_LIMIT = 200;
const SEEN_KEY = "webdash.act.mesh-tx.seen"; // detail stays open until the first successful send
const RELAY_KEY = "webdash.act.mesh-tx.relay-check"; // "0" = unticked; anything else = ticked
const enc = new TextEncoder();

let channels = [];        // mesh.channel_detail from the status tick
let channelsKey = null;   // null, not "[]", so the very first tick always renders
let lastMesh = null;      // the latest data.mesh, for re-rendering on local input
let busy = false;

function fmtClock(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function channelName(idx) {
  const c = channels.find((c) => c.index === idx);
  return c ? c.name : `ch${idx}`;
}

function bytesOf(text) {
  return enc.encode(text).length;
}

function seenBefore() {
  try { return localStorage.getItem(SEEN_KEY) === "1"; } catch { return false; }
}

function relayCheck() {
  return document.getElementById("mesh-relay-check").checked;
}

function loadRelayPref() {
  try { return localStorage.getItem(RELAY_KEY) !== "0"; } catch { return true; }
}

function saveRelayPref(on) {
  try { localStorage.setItem(RELAY_KEY, on ? "1" : "0"); } catch { /* private window: default */ }
}

function markSeen() {
  try { localStorage.setItem(SEEN_KEY, "1"); } catch { /* private window: keep detail open */ }
}

function renderChannels(detail) {
  const key = JSON.stringify(detail.map((c) => [c.index, c.name]));
  if (key === channelsKey) return;
  channelsKey = key;
  channels = detail;
  const sel = document.getElementById("mesh-channel");
  const prev = sel.value;
  if (!detail.length) {
    const o = document.createElement("option");
    o.value = "";
    o.textContent = "No channels yet";
    o.disabled = true;
    sel.replaceChildren(o);
    sel.disabled = true;
    return;
  }
  sel.replaceChildren(...detail.map((c) => {
    const o = document.createElement("option");
    o.value = c.index;
    o.textContent = c.role === "PRIMARY" ? `${c.name} (primary)` : c.name;
    return o;
  }));
  sel.disabled = false;
  if (detail.some((c) => String(c.index) === prev)) sel.value = prev;
}

// Build the actuator model from the server's readiness and copy, plus local input state.
function renderTx() {
  const root = document.getElementById("mesh-act");
  const m = lastMesh;
  const sel = document.getElementById("mesh-channel");
  const input = document.getElementById("mesh-text");
  const count = document.getElementById("mesh-bytes");
  const n = bytesOf(input.value.trim());
  count.textContent = `${n}/${BYTE_LIMIT} bytes`;
  count.classList.toggle("over", n > BYTE_LIMIT);

  if (!m || !m.tx) {
    renderActuator(root, { medium: "rf", caption: "Checking the radio…", verb: "Transmit",
      blocked: { reason: "Checking the radio…" }, busy: false, detail: [] });
    return;
  }
  const copy = m.tx_copy || {};
  const idx = sel.value === "" ? null : Number(sel.value);
  const cap = (copy.captions || []).find((c) => c.index === idx) || (copy.captions || [])[0] || null;
  const ch = channels.find((c) => c.index === idx);
  let blocked = m.tx.can_send ? null : { reason: m.tx.reason, fix: m.tx.fix };
  if (!blocked && n > BYTE_LIMIT) {
    blocked = { reason: `Over by ${n - BYTE_LIMIT} bytes: ${BYTE_LIMIT} bytes max (emoji and accents count as 2–4).` };
  }
  renderActuator(root, {
    medium: "rf",
    caption: cap ? cap.caption : "Transmits on the SX1262 LoRa radio · 902–928 MHz",
    note: cap ? cap.note : null,
    retries: (relayCheck() ? copy.retries : copy.no_retries) || null,
    verb: ch ? `Transmit on ${ch.name}` : "Transmit",
    blocked,
    busy,
    detail: [copy.legal, cap && cap.public ? copy.public : null, copy.power,
      cap ? cap.position_line : null, cap ? cap.mqtt_line : null],
  });
}

let mqttBusy = false;

// The MQTT on/off control. Its readiness and copy come from the server (mesh.mqtt).
function renderMqtt() {
  const root = document.getElementById("mesh-mqtt");
  const q = lastMesh && lastMesh.mqtt;
  if (!q) {
    renderActuator(root, { medium: "local", caption: "Checking the radio…", verb: "Turn MQTT on/off",
      blocked: { reason: "Checking the radio…" }, busy: false, detail: [] });
    return;
  }
  renderActuator(root, {
    medium: "local",
    caption: q.caption,
    note: q.note,
    retries: q.restart,
    verb: q.verb,
    blocked: q.ready.can_send ? null : { reason: q.ready.reason, fix: q.ready.fix },
    busy: mqttBusy,
    detail: q.detail,
  });
}

// Keep data.mesh current while the Mesh view is hidden: the transmit control's input handlers read it.
export function cacheMesh(data) { lastMesh = (data && data.mesh) || {}; }

export function syncMesh(data) {
  cacheMesh(data);
  const m = lastMesh;
  renderChannels(m.channel_detail || []);
  renderTx();
  renderMqtt();
}

// --- Message log: append-only, so role=log announces only new rows ---------------------------

let lastId = -1;
const rows = new Map(); // message id -> {meta, tier}: the parts the server fills in after the fact

function tierLines(m) {
  return [m.tier_text, m.tier_sub, m.counter_text].filter(Boolean).join(" ");
}

function metaLine(m) {
  const who = m.mine ? "me" : (m.from_name || m.from_id || "?");
  let text = `${fmtClock(m.ts)} · ${who} · ${m.direct ? "direct" : channelName(m.channel)}`;
  // Rough sender location, from their last broadcast position (a place name, never coordinates).
  if (m.place) text += ` · ${m.place}`;
  if (m.snr != null) text += ` · SNR ${m.snr} dB`;
  if (m.rssi != null) text += ` · RSSI ${m.rssi} dBm`;
  return text;
}

function buildRow(m) {
  const row = document.createElement("div");
  row.className = "mesh-msg" + (m.mine ? " mine" : "");
  const meta = document.createElement("div");
  meta.className = "mesh-meta";
  meta.textContent = metaLine(m);
  const body = document.createElement("div");
  body.className = "mesh-text";
  body.textContent = m.text;
  row.append(meta, body);
  let tier = null;
  if (m.mine) {
    tier = document.createElement("div");
    tier.className = "mesh-tier";
    tier.textContent = tierLines(m);
    row.append(tier);
  }
  rows.set(m.id, { meta, tier });
  return row;
}

function renderMessages(data) {
  const msgs = data.messages || [];
  const log = document.getElementById("mesh-log");
  const newest = msgs.length ? msgs[msgs.length - 1].id : 0;
  const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 24;

  if (!msgs.length) {
    if (lastId !== 0) {
      const empty = document.createElement("div");
      empty.className = "panel-empty";
      empty.textContent = "No messages yet.";
      log.replaceChildren(empty);
      rows.clear();
    }
    lastId = 0;
    return;
  }
  if (lastId < 0 || newest < lastId || !log.querySelector(".mesh-msg")) {
    // First render, or the server restarted (ids went back): rebuild once, quietly.
    log.setAttribute("aria-busy", "true");
    rows.clear();
    log.replaceChildren(...msgs.map(buildRow));
    log.setAttribute("aria-busy", "false");
    log.scrollTop = log.scrollHeight;
  } else if (newest > lastId) {
    for (const m of msgs) if (m.id > lastId) log.append(buildRow(m));
    while (log.children.length > 200) {
      log.firstElementChild.remove();
    }
    const oldest = msgs[0].id;
    for (const id of rows.keys()) if (id < oldest) rows.delete(id);
    if (atBottom) log.scrollTop = log.scrollHeight;
  }
  lastId = newest;
  // Delivery tiers and sender places arrive after the row does (a node's position often follows
  // its first text), so they change in place; under aria-relevant="additions" these edits aren't
  // announced.
  for (const m of msgs) {
    const r = rows.get(m.id);
    if (!r) continue;
    const meta = metaLine(m);
    if (r.meta.textContent !== meta) r.meta.textContent = meta;
    if (r.tier && r.tier.textContent !== tierLines(m)) r.tier.textContent = tierLines(m);
  }
}

export async function pollMeshMessages() {
  try {
    const resp = await fetch("/api/mesh/messages");
    if (resp.ok) {
      const data = await resp.json();
      renderMessages(data);
      trackUnread(data.messages || []);
    }
  } catch (err) {
    console.error("mesh messages poll failed:", err);
  }
}

// --- Sending ----------------------------------------------------------------------------------

function initMqtt() {
  const root = document.getElementById("mesh-mqtt");
  const status = document.getElementById("mesh-mqtt-status");
  document.getElementById("mesh-mqtt-btn").addEventListener("click", async () => {
    if (mqttBusy) return;
    if (isBlocked(root)) {
      status.className = "mesh-send-status err";
      status.textContent = `Not changed: ${reasonText(root)}`;
      return;
    }
    const enable = !(lastMesh && lastMesh.mqtt && lastMesh.mqtt.enabled);
    mqttBusy = true;
    renderMqtt();
    status.className = "mesh-send-status";
    status.textContent = enable ? "Turning MQTT on…" : "Turning MQTT off…";
    try {
      const resp = await fetch("/api/mesh/mqtt", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled: enable }),
      });
      const body = await resp.json().catch(() => ({}));
      if (resp.ok && body.ok) {
        status.textContent = body.message;
      } else {
        status.className = "mesh-send-status err";
        status.textContent = `Not changed: ${body.error || `HTTP ${resp.status}`}`;
      }
    } catch (err) {
      status.className = "mesh-send-status err";
      status.textContent = `Not changed: ${err}`;
    } finally {
      mqttBusy = false;
      renderMqtt();
    }
  });
}

export function initMesh() {
  initMqtt();
  const form = document.getElementById("mesh-send-form");
  const input = document.getElementById("mesh-text");
  const sel = document.getElementById("mesh-channel");
  const status = document.getElementById("mesh-send-status");
  const detail = document.getElementById("mesh-act-detail");
  const root = document.getElementById("mesh-act");
  detail.open = !seenBefore();
  const relay = document.getElementById("mesh-relay-check");
  relay.checked = loadRelayPref();
  relay.addEventListener("change", () => { saveRelayPref(relay.checked); renderTx(); });

  input.addEventListener("input", renderTx);
  sel.addEventListener("change", renderTx);
  input.addEventListener("keydown", (ev) => { if (ev.key === "Enter" && ev.repeat) ev.preventDefault(); });

  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    if (busy) return;
    const text = input.value.trim();
    if (!text) {
      status.className = "mesh-send-status err";
      status.textContent = "Not sent: the message is empty.";
      return;
    }
    if (isBlocked(root)) {
      status.className = "mesh-send-status err";
      status.textContent = `Not sent: ${reasonText(root)}`;
      return;
    }
    busy = true;
    renderTx();
    status.className = "mesh-send-status";
    status.textContent = "Handing to meshtasticd…";
    try {
      const resp = await fetch("/api/mesh/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text, channel: Number(sel.value), want_ack: relayCheck() }),
      });
      const body = await resp.json().catch(() => ({}));
      if (resp.ok && body.ok) {
        input.value = "";
        status.textContent = body.message || "Queued in meshtasticd.";
        markSeen();
        pollMeshMessages();
      } else {
        status.className = "mesh-send-status err";
        const d = Array.isArray(body.detail) ? body.detail[0].msg : body.detail;
        status.textContent = `Not sent: ${body.error || d || `HTTP ${resp.status}`}`;
      }
    } catch (err) {
      status.className = "mesh-send-status err";
      status.textContent = `Not sent: ${err}`;
    } finally {
      busy = false;
      renderTx();
      input.focus();
    }
  });
}
