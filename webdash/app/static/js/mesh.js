// Mesh text messages — polled separately from the status websocket, like CyberDeck's panel.
// Message text and sender names come off the air from anyone on the channel, so they are only
// ever inserted with textContent, never innerHTML.

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

let meshChannels = [];
let meshLastId = -1;

function fmtClock(ts) {
  return new Date(ts * 1000).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

function renderMeshChannels(channels) {
  const key = JSON.stringify(channels);
  if (key === JSON.stringify(meshChannels)) return;
  meshChannels = channels;
  const sel = document.getElementById("mesh-channel");
  const prev = sel.value;
  sel.replaceChildren(...channels.map((c) => {
    const o = document.createElement("option");
    o.value = c.index;
    o.textContent = c.name;
    return o;
  }));
  if (channels.some((c) => String(c.index) === prev)) sel.value = prev;
  // No channel list means no live interface — never fall back to sending on index 0 unasked.
  sel.disabled = !channels.length;
  document.getElementById("mesh-send-btn").disabled = !channels.length;
}

function channelName(idx) {
  const c = meshChannels.find((c) => c.index === idx);
  return c ? c.name : `ch${idx}`;
}

function renderMeshMessages(data) {
  renderMeshChannels(data.channels || []);
  const msgs = data.messages || [];
  // Keyed on the newest message's id, not the count: the server buffer stays at 200 once full.
  const lastId = msgs.length ? msgs[msgs.length - 1].id : 0;
  if (lastId === meshLastId) return;
  const firstRender = meshLastId < 0;
  meshLastId = lastId;
  const log = document.getElementById("mesh-log");
  const atBottom = log.scrollHeight - log.scrollTop - log.clientHeight < 24;
  if (!msgs.length) {
    const empty = document.createElement("div");
    empty.className = "panel-empty";
    empty.textContent = "No messages yet.";
    log.replaceChildren(empty);
    return;
  }
  log.replaceChildren(...msgs.map((m) => {
    const row = document.createElement("div");
    row.className = "mesh-msg" + (m.mine ? " mine" : "");
    const meta = document.createElement("div");
    meta.className = "mesh-meta";
    const who = m.mine ? "me" : (m.from_name || m.from_id || "?");
    let metaText = `${fmtClock(m.ts)} · ${who} · ${m.direct ? "direct" : channelName(m.channel)}`;
    if (m.snr != null) metaText += ` · SNR ${m.snr} dB`;
    if (m.rssi != null) metaText += ` · RSSI ${m.rssi} dBm`;
    meta.textContent = metaText;
    const body = document.createElement("div");
    body.className = "mesh-text";
    body.textContent = m.text;
    row.append(meta, body);
    return row;
  }));
  // Follow new messages unless the reader has scrolled up to look at older ones.
  if (atBottom || firstRender) log.scrollTop = log.scrollHeight;
}

export async function pollMeshMessages() {
  try {
    const resp = await fetch("/api/mesh/messages");
    if (resp.ok) {
      const data = await resp.json();
      renderMeshMessages(data);
      trackUnread(data.messages || []);
    }
  } catch (err) {
    console.error("mesh messages poll failed:", err);
  }
}

export function initMesh() {
document.getElementById("mesh-send-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const input = document.getElementById("mesh-text");
  const btn = document.getElementById("mesh-send-btn");
  const status = document.getElementById("mesh-send-status");
  const text = input.value.trim();
  const sel = document.getElementById("mesh-channel");
  if (!text || sel.value === "") return;
  // The server limit is 200 UTF-8 bytes; maxlength counts UTF-16 units, so check bytes here too.
  if (new TextEncoder().encode(text).length > 200) {
    status.className = "mesh-send-status err";
    status.textContent = "Too long: 200 bytes max (emoji and accents count as 2–4).";
    return;
  }
  btn.disabled = true;
  status.className = "mesh-send-status";
  status.textContent = "Sending…";
  try {
    const resp = await fetch("/api/mesh/send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, channel: Number(sel.value) }),
    });
    const body = await resp.json().catch(() => ({}));
    if (resp.ok && body.ok) {
      input.value = "";
      status.textContent = "";
      pollMeshMessages();
    } else {
      status.className = "mesh-send-status err";
      const detail = Array.isArray(body.detail) ? body.detail[0].msg : body.detail;
      status.textContent = `Send failed: ${body.error || detail || resp.status}`;
    }
  } catch (err) {
    status.className = "mesh-send-status err";
    status.textContent = `Send failed: ${err}`;
  } finally {
    btn.disabled = !meshChannels.length;
    input.focus();
  }
});
}
