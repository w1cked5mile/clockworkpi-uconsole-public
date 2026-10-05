// WPA audit — authorized-equipment allowlist + handshake capture + GPU crack-offload (Wi-Fi view).
// The operator adds a BSSID (own gear or a documented engagement); the server enforces that active
// auditing only ever targets an allowlisted BSSID. Capture sends bounded, targeted deauth; once a
// handshake is captured it can be offloaded to the GPU host (gpu-host) to recover the PSK. The
// recovered PSK is shown here but never persisted.

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

let polling = null;
let crackPolling = null;
let lastCap = null;

async function loadList() {
  const body = document.getElementById("wpa-list-body");
  const sel = document.getElementById("wpa-cap-target");
  if (!body) return;
  let entries = [];
  try {
    const resp = await fetch("/api/wpa/allowlist");
    if (resp.ok) entries = (await resp.json()).entries || [];
  } catch { /* leave the placeholder */ }

  body.innerHTML = entries.length
    ? entries.map((e) => `<tr>
        <td class="mono">${esc(e.bssid)}</td>
        <td>${esc(e.ssid_label) || '<span class="dim">—</span>'}</td>
        <td>${esc(e.basis)}</td>
        <td class="dim">${esc((e.added || "").replace("T", " ").replace("Z", ""))}</td>
        <td><button type="button" class="btn danger wpa-remove" data-bssid="${esc(e.bssid)}">Remove</button></td>
      </tr>`).join("")
    : '<tr><td colspan="5" class="dim">No authorized BSSIDs yet.</td></tr>';

  if (sel) {
    const prev = sel.value;
    sel.innerHTML = '<option value="">— no authorized BSSID —</option>' +
      entries.map((e) => `<option value="${esc(e.bssid)}">${esc(e.bssid)}${e.ssid_label ? " (" + esc(e.ssid_label) + ")" : ""}</option>`).join("");
    if (entries.some((e) => e.bssid === prev)) sel.value = prev;
    document.getElementById("wpa-cap-start").disabled = !sel.value;
  }
}

async function addEntry(ev) {
  ev.preventDefault();
  const errEl = document.getElementById("wpa-add-error");
  if (errEl) errEl.textContent = "";
  const bssid = document.getElementById("wpa-bssid").value.trim();
  const basis = document.getElementById("wpa-basis").value.trim();
  const ssid_label = document.getElementById("wpa-ssid").value.trim();
  try {
    const resp = await fetch("/api/wpa/allowlist", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bssid, basis, ssid_label }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) { if (errEl) errEl.textContent = data.error || `HTTP ${resp.status}`; return; }
    document.getElementById("wpa-add-form").reset();
    loadList();
  } catch (err) { if (errEl) errEl.textContent = String(err); }
}

async function removeEntry(bssid) {
  try { await fetch(`/api/wpa/allowlist/${encodeURIComponent(bssid)}`, { method: "DELETE" }); } catch { /* */ }
  loadList();
}

// --- capture ---------------------------------------------------------------------------------
const TERMINAL = { captured: 1, no_handshake: 1, error: 1, cancelled: 1, unavailable: 1, idle: 1 };

function renderStatus(s) {
  const el = document.getElementById("wpa-cap-status");
  const start = document.getElementById("wpa-cap-start");
  const cancel = document.getElementById("wpa-cap-cancel");
  if (!el) return;
  const stage = s.stage || "idle";
  const running = !!s.running && !TERMINAL[stage];
  const cls = stage === "captured" ? "ok" : (stage === "error" || stage === "no_handshake") ? "err" : "";
  el.className = "wpa-cap-status " + cls;
  el.textContent = stage === "idle" ? "" : `${stage.replace(/_/g, " ")}${s.message ? " — " + s.message : ""}`;
  if (start) start.style.display = running ? "none" : "";
  if (cancel) cancel.style.display = running ? "" : "none";
  if (start) start.disabled = running || !document.getElementById("wpa-cap-target").value;
  // A completed capture unlocks the crack-offload step.
  const crackBlock = document.getElementById("wpa-crack");
  if (crackBlock && stage === "captured" && s.cap) {
    lastCap = s.cap;
    crackBlock.style.display = "";
  }
  return running;
}

async function pollStatus() {
  let s = { stage: "idle" };
  try { s = await (await fetch("/api/wpa/capture/status")).json(); } catch { /* */ }
  const running = renderStatus(s);
  if (!running && polling) { clearInterval(polling); polling = null; }
}

async function startCapture() {
  const errEl = document.getElementById("wpa-cap-error");
  if (errEl) errEl.textContent = "";
  const bssid = document.getElementById("wpa-cap-target").value;
  if (!bssid) return;
  document.getElementById("wpa-cap-start").disabled = true;
  try {
    const resp = await fetch("/api/wpa/capture", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bssid }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) { if (errEl) errEl.textContent = data.error || `HTTP ${resp.status}`; }
  } catch (err) { if (errEl) errEl.textContent = String(err); }
  if (!polling) polling = setInterval(pollStatus, 2000);
  pollStatus();
}

async function cancelCapture() {
  try { await fetch("/api/wpa/capture/cancel", { method: "POST" }); } catch { /* */ }
  pollStatus();
}

// --- crack offload ---------------------------------------------------------------------------
const CRACK_TERMINAL = { done: 1, error: 1, unavailable: 1, idle: 1 };

function renderCrack(s) {
  const statusEl = document.getElementById("wpa-crack-status");
  const resultEl = document.getElementById("wpa-crack-result");
  const btn = document.getElementById("wpa-crack-start");
  if (!statusEl) return false;
  const stage = s.stage || "idle";
  const running = !!s.running && !CRACK_TERMINAL[stage];
  statusEl.className = "wpa-crack-status" + (stage === "error" ? " err" : "");
  statusEl.textContent = stage === "idle" ? "" : `${stage}${s.message ? " — " + s.message : ""}`;
  if (btn) { btn.disabled = running; btn.textContent = running ? "Cracking…" : "Send to gpu-host (crack)"; }
  if (resultEl) {
    if (s.cracked === true) {
      resultEl.className = "wpa-crack-result ok";
      resultEl.textContent = `✓ PSK recovered: ${s.psk ?? ""}`;
    } else if (stage === "done") {
      resultEl.className = "wpa-crack-result";
      resultEl.textContent = "— passphrase not in the wordlist";
    } else {
      resultEl.textContent = "";
    }
  }
  return running;
}

async function pollCrack() {
  let s = { stage: "idle" };
  try { s = await (await fetch("/api/wpa/crack/status")).json(); } catch { /* */ }
  if (!renderCrack(s) && crackPolling) { clearInterval(crackPolling); crackPolling = null; }
}

async function startCrack() {
  if (!lastCap) return;
  const btn = document.getElementById("wpa-crack-start");
  if (btn) btn.disabled = true;
  try {
    const resp = await fetch("/api/wpa/crack", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ cap: lastCap }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) {
      const el = document.getElementById("wpa-crack-status");
      if (el) { el.className = "wpa-crack-status err"; el.textContent = data.error || `HTTP ${resp.status}`; }
      if (btn) btn.disabled = false;
      return;
    }
  } catch (err) {
    const el = document.getElementById("wpa-crack-status");
    if (el) { el.className = "wpa-crack-status err"; el.textContent = String(err); }
    if (btn) btn.disabled = false;
    return;
  }
  if (!crackPolling) crackPolling = setInterval(pollCrack, 3000);
  pollCrack();
}

export function initWpa() {
  const form = document.getElementById("wpa-add-form");
  if (!form) return;
  form.addEventListener("submit", addEntry);
  document.getElementById("wpa-list-body").addEventListener("click", (ev) => {
    const btn = ev.target.closest(".wpa-remove");
    if (btn) removeEntry(btn.dataset.bssid);
  });
  const sel = document.getElementById("wpa-cap-target");
  if (sel) sel.addEventListener("change", () => {
    document.getElementById("wpa-cap-start").disabled = !sel.value;
  });
  document.getElementById("wpa-cap-start")?.addEventListener("click", startCapture);
  document.getElementById("wpa-cap-cancel")?.addEventListener("click", cancelCapture);
  document.getElementById("wpa-crack-start")?.addEventListener("click", startCrack);
  loadList();
  pollStatus();  // reflect an in-flight capture if the page was reloaded mid-run
  pollCrack();   // and an in-flight / finished crack
}
