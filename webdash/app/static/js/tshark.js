// Passive packet-capture tile (System view). A receive-only troubleshooting tap for the
// hang/dropout hunt: start a bounded dumpcap ring buffer on a chosen interface and watch the
// address-free summary the host bridge produces. Everything here is driven from the 3 s status
// tick (syncTshark) — the start/stop buttons post and let the next tick settle the state, the same
// way kismet.js does. No separate polling.

import { setRows, setText, show } from "./ui.js";

let pending = false;

function isRunning(t) {
  return !!t && t.running === true;
}

function startState(btn, busy, label) {
  if (!btn) return;
  btn.disabled = busy;
  if (busy) btn.setAttribute("aria-busy", "true");
  else btn.removeAttribute("aria-busy");
  btn.textContent = label;
}

async function post(path, body) {
  const resp = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body || {}),
  });
  if (!resp.ok) {
    const b = await resp.json().catch(() => ({}));
    throw new Error(b.error || `HTTP ${resp.status}`);
  }
  return resp.json().catch(() => ({}));
}

async function startCapture() {
  const err = document.getElementById("tshark-error");
  const start = document.getElementById("tshark-start");
  const iface = document.getElementById("tshark-iface").value;
  const filter = document.getElementById("tshark-filter").value.trim();
  const dur = parseInt(document.getElementById("tshark-duration").value, 10);
  if (err) err.textContent = "";
  if (!iface) { if (err) err.textContent = "Pick an interface first."; return; }

  pending = true;
  startState(start, true, "Starting…");
  let error = null;
  try {
    await post("/api/tshark/capture", {
      iface, filter, duration: Number.isFinite(dur) ? dur : 0,
    });
  } catch (e) {
    error = String(e.message || e);
  }
  pending = false;
  startState(start, false, "Start capture");
  if (error && err) err.textContent = `Couldn't start: ${error}`;
  // Running/stopped label is left to resync on the next status tick.
}

async function cancelCapture() {
  const err = document.getElementById("tshark-error");
  const cancel = document.getElementById("tshark-cancel");
  if (err) err.textContent = "";
  pending = true;
  startState(cancel, true, "Stopping…");
  let error = null;
  try {
    await post("/api/tshark/capture/cancel", {});
  } catch (e) {
    error = String(e.message || e);
  }
  pending = false;
  startState(cancel, false, "Stop");
  if (error && err) err.textContent = `Couldn't stop: ${error}`;
}

function fillInterfaces(sel, interfaces) {
  if (!sel || !Array.isArray(interfaces)) return;
  const want = interfaces.join(",");
  if (sel.dataset.filled === want) return;   // only rebuild when the set actually changes
  const cur = sel.value;
  sel.replaceChildren(...interfaces.map((i) => {
    const o = document.createElement("option");
    o.value = i; o.textContent = i;
    return o;
  }));
  if (interfaces.includes(cur)) sel.value = cur;
  sel.dataset.filled = want;
}

export function initTshark() {
  const start = document.getElementById("tshark-start");
  const cancel = document.getElementById("tshark-cancel");
  if (!start) return;
  start.addEventListener("click", () => { if (!start.disabled) startCapture(); });
  cancel.addEventListener("click", () => { if (!cancel.disabled) cancelCapture(); });
}

// Called every status tick with data.tshark.
export function syncTshark(t) {
  const start = document.getElementById("tshark-start");
  const cancel = document.getElementById("tshark-cancel");
  if (!start) return;

  const unavailable = !t || t.state === "unavailable";
  const up = isRunning(t);

  if (!unavailable) fillInterfaces(document.getElementById("tshark-iface"), t.interfaces);

  if (!pending) {
    show("tshark-start", !up, "inline-block");
    show("tshark-cancel", up, "inline-block");
    start.disabled = unavailable || up;
    start.title = unavailable ? "Capture bridge not reachable — is tshark-bridge.service installed?" : "";
  }

  if (unavailable) {
    setText("tshark-status", "Capture bridge not reachable — install tshark-bridge.service on the host.");
    setRows("tshark-body", []);
    setText("tshark-protos", "");
    return;
  }

  const stage = t.stage || "idle";
  const msg = t.message ? ` — ${t.message}` : "";
  setText("tshark-status", `${stage}${msg}`);

  const f = t.findings || {};
  const idle = stage === "idle" && !up;
  setRows("tshark-body", idle ? [] : [
    ["Packets (this segment)", t.segment_packets != null ? t.segment_packets.toLocaleString() : "—"],
    ["Segment size", t.segment_kb != null ? `${t.segment_kb} KB` : "—"],
    ["TCP retransmissions", f.tcp_retransmit ?? "—"],
    ["TCP duplicate ACKs", f.tcp_dup_ack ?? "—"],
    ["TCP resets", f.tcp_reset ?? "—"],
    ["ICMP unreachable", f.icmp_unreachable ?? "—"],
  ]);

  const protos = Array.isArray(t.protocols) ? t.protocols : [];
  setText("tshark-protos", protos.length
    ? `Protocols: ${protos.map((p) => `${p.name} ${p.packets}`).join(" · ")}` : "");

  const pcaps = Array.isArray(t.pcaps) ? t.pcaps : [];
  setText("tshark-pcaps", pcaps.length
    ? pcaps.map((p) => `${p.name} (${p.kb} KB)`).join("\n")
    : "No captures saved yet.");
}
