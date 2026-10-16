// Claude-assisted Wi-Fi site survey (Wi-Fi view).
//
// Start a survey, drop a waypoint at each location (the server captures a passive Kismet snapshot
// + the GPS grid square), stop, then download reports: a comprehensive technical write-up, a
// leadership executive summary, or a brief to paste into Claude for a narrative pass. Receive-only
// throughout. All text from the survey (SSIDs, labels, notes) is inserted with textContent / the
// esc() helper, never raw innerHTML of untrusted data.

function esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) =>
    ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

let busy = false;

async function api(path, opts) {
  const resp = await fetch(path, opts);
  let body = {};
  try { body = await resp.json(); } catch { /* non-JSON (e.g. 404 html) */ }
  return { ok: resp.ok, status: resp.status, body };
}

function setErr(id, msg) {
  const el = document.getElementById(id);
  if (el) el.textContent = msg || "";
}

// --- Active-vs-idle view toggle --------------------------------------------------------------

function renderActive(active) {
  const idle = document.getElementById("survey-idle");
  const act = document.getElementById("survey-active");
  if (!idle || !act) return;
  const on = !!active;
  idle.hidden = on;
  act.hidden = !on;
  if (!on) return;

  document.getElementById("survey-active-name").textContent = active.name;
  const n = active.waypoints.length;
  document.getElementById("survey-active-count").textContent = `${n} waypoint${n === 1 ? "" : "s"}`;

  const body = document.getElementById("survey-wp-body");
  body.innerHTML = active.waypoints.length
    ? active.waypoints.map((w) => `<tr>
        <td>${w.seq}</td>
        <td>${esc(w.label)}</td>
        <td>${esc(w.grid) || '<span class="dim">—</span>'}</td>
        <td>${esc(w.fix) || '<span class="dim">—</span>'}</td>
        <td>${w.snapshot_error
          ? `<span class="warn-text" title="${esc(w.snapshot_error)}">no data</span>`
          : (w.device_count ?? 0)}</td>
        <td>${esc(w.note) || ""}</td>
      </tr>`).join("")
    : '<tr><td colspan="6" class="dim">No waypoints yet — walk to a spot and drop one.</td></tr>';
}

// --- Past surveys + report links -------------------------------------------------------------

function reportLinks(id) {
  const base = `/api/survey/${encodeURIComponent(id)}/report`;
  // Technical and Executive each come in PDF and Markdown; the Claude brief is a prompt, MD only.
  return `
    <span class="report-group">Technical:
      <a class="report-link" href="${base}?kind=comprehensive&fmt=pdf">PDF</a>
      <a class="report-link" href="${base}?kind=comprehensive&fmt=md">MD</a></span>
    <span class="report-group">Executive:
      <a class="report-link" href="${base}?kind=executive&fmt=pdf">PDF</a>
      <a class="report-link" href="${base}?kind=executive&fmt=md">MD</a></span>
    <span class="report-group">Claude brief:
      <a class="report-link" href="${base}?kind=brief&fmt=md">MD</a></span>`;
}

async function loadList() {
  const body = document.getElementById("survey-list-body");
  if (!body) return;
  let surveys = [];
  try {
    const resp = await fetch("/api/survey/list");
    if (resp.ok) surveys = (await resp.json()).surveys || [];
  } catch { /* leave placeholder */ }

  body.innerHTML = surveys.length
    ? surveys.map((s) => `<tr>
        <td><button type="button" class="linklike survey-view" data-id="${esc(s.id)}">${esc(s.name)}</button>
          ${s.status === "active" ? '<span class="pill">active</span>' : ""}</td>
        <td class="dim">${esc((s.created || "").replace("T", " ").replace("Z", ""))}</td>
        <td>${s.waypoint_count}</td>
        <td class="report-links">${s.status === "active" ? '<span class="dim">finish to export</span>' : reportLinks(s.id)}</td>
        <td><button type="button" class="btn danger survey-del" data-id="${esc(s.id)}"
          ${s.status === "active" ? "disabled title='stop the survey first'" : ""}>Delete</button></td>
      </tr>`).join("")
    : '<tr><td colspan="5" class="dim">No surveys yet.</td></tr>';
}

// --- Inline analysis preview -----------------------------------------------------------------

async function showPreview(id) {
  const el = document.getElementById("survey-preview");
  if (!el) return;
  el.hidden = false;
  el.innerHTML = '<p class="dim">Loading…</p>';
  const { ok, body: a } = await api(`/api/survey/${encodeURIComponent(id)}`);
  if (!ok) { el.innerHTML = `<p class="warn-text">${esc(a.error || "could not load survey")}</p>`; return; }

  const t = a.totals;
  const sec = Object.entries(a.security || {}).map(([k, v]) => `${esc(k)}: ${v}`).join(" · ") || "—";
  const bands = Object.entries(a.bands || {}).map(([k, v]) => `${esc(k)}: ${v}`).join(" · ") || "—";
  const findings = (a.findings || []).map((f) =>
    `<li class="finding finding-${esc(f.severity)}"><strong>${esc(f.title)}</strong><br>
      <span class="dim">${esc(f.detail)}</span></li>`).join("") || '<li class="dim">No findings flagged.</li>';

  el.innerHTML = `
    <div class="survey-preview-head">
      <strong>${esc(a.survey_name)}</strong>
      <button type="button" class="linklike" id="survey-preview-close">close</button>
    </div>
    <div class="survey-stats">
      <span><b>${t.unique_aps}</b> APs</span>
      <span><b>${t.unique_clients}</b> clients</span>
      <span><b>${t.hidden_ssids}</b> hidden</span>
      <span><b>${t.waypoints_with_data}/${a.waypoint_count}</b> waypoints with data</span>
    </div>
    <p class="dim">Bands — ${bands}<br>Security — ${sec}</p>
    <ul class="survey-findings">${findings}</ul>
    <p class="report-links">Download: ${reportLinks(a.survey_id)}</p>
    <div class="survey-focus-pick">
      <label>Focus on one SSID:
        <select id="survey-focus-ssid"><option value="">— whole survey —</option></select></label>
      <span class="dim" id="survey-focus-hint"></span>
    </div>
    <div id="survey-focus" hidden></div>`;
  document.getElementById("survey-preview-close").addEventListener("click", () => { el.hidden = true; });
  loadFocusSsids(id);
  document.getElementById("survey-focus-ssid").addEventListener("change", (ev) => {
    if (ev.target.value) renderFocus(id, ev.target.value);
    else document.getElementById("survey-focus").hidden = true;
  });
  const still = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  el.scrollIntoView({ behavior: still ? "auto" : "smooth", block: "nearest" });
}

async function loadFocusSsids(id) {
  const sel = document.getElementById("survey-focus-ssid");
  if (!sel) return;
  const { ok, body } = await api(`/api/survey/${encodeURIComponent(id)}/ssids`);
  if (!ok) return;
  const ssids = body.ssids || [];
  sel.innerHTML = '<option value="">— whole survey —</option>' + ssids.map((s) =>
    `<option value="${esc(s.ssid)}">${esc(s.ssid)} (${s.bssid_count} BSSID${s.bssid_count === 1 ? "" : "s"}, ${esc(s.bands.join("/"))})</option>`).join("");
  const hint = document.getElementById("survey-focus-hint");
  if (hint) hint.textContent = ssids.length ? `${ssids.length} named SSIDs` : "no named SSIDs heard";
}

function fsig(v) { return typeof v === "number" ? `${v} dBm` : "—"; }

async function renderFocus(id, ssid) {
  const host = document.getElementById("survey-focus");
  if (!host) return;
  host.hidden = false;
  host.innerHTML = '<p class="dim">Loading focused analysis…</p>';
  const base = `/api/survey/${encodeURIComponent(id)}/report?kind=focus&ssid=${encodeURIComponent(ssid)}`;
  const { ok, body } = await api(`/api/survey/${encodeURIComponent(id)}/focus?ssid=${encodeURIComponent(ssid)}`);
  if (!ok) { host.innerHTML = `<p class="warn-text">${esc(body.error || "focus failed")}</p>`; return; }
  const f = body.focus;

  const findings = (f.findings || []).map((x) =>
    `<li class="finding finding-${esc(x.severity)}"><strong>${esc(x.title)}</strong><br>
      <span class="dim">${esc(x.detail)}</span></li>`).join("") || '<li class="dim">No findings flagged.</li>';

  const ess = f.ess_bssids.map((m) => `<tr>
    <td class="mono">${esc(m.mac)}</td><td>${esc(m.band || "—")}</td><td>${esc(m.channel || "—")}</td>
    <td>${m.width_mhz ? m.width_mhz + " MHz" : "—"}</td><td>${esc(m.manuf || "—")}</td></tr>`).join("");

  const wps = f.waypoints.map((wp) => {
    if (wp.snapshot_error) return `<tr><td>${esc(wp.label)}</td><td colspan="7" class="dim">no data: ${esc(wp.snapshot_error)}</td></tr>`;
    if (!wp.observations.length) return `<tr><td>${esc(wp.label)}</td><td colspan="7" class="dim">SSID not heard here</td></tr>`;
    return wp.observations.map((o, i) => `<tr>
      <td>${i === 0 ? esc(wp.label) + (wp.coverage ? ` <span class="dim">(${esc(wp.coverage)})</span>` : "") : ""}</td>
      <td class="mono">${esc(o.bssid)}</td>
      <td>${esc(o.channel || "—")}${o.width_mhz ? "/" + o.width_mhz : ""}</td>
      <td>${fsig(o.signal_dbm)}</td>
      <td>${o.overlap.co_channel_bssids}/${o.overlap.co_channel_radios}${o.overlap.self_co_channel.length ? " (self " + o.overlap.self_co_channel.length + ")" : ""}</td>
      <td>${o.overlap.adjacent.length || "—"}</td>
      <td>${o.contention.qbss_util_pct != null ? o.contention.qbss_util_pct + "%" : "—"}${o.contention.qbss_stations != null ? ", " + o.contention.qbss_stations + " sta" : ""}</td>
    </tr>`).join("");
  }).join("");

  const pairs = f.roaming.self_co_channel_pairs || [];
  const contending = pairs.filter((p) => p.contending_waypoints.length);
  const healthy = pairs.filter((p) => !p.contending_waypoints.length);
  const selfco = contending.length
    ? `<p class="warn-text">Self co-channel contention: ${contending.map((p) => `ch${esc(p.channel)} (${esc(p.bssid_a)}+${esc(p.bssid_b)}) @ ${esc(p.contending_waypoints.join(", "))}`).join("; ")}</p>`
      + (healthy.length ? `<p class="dim">Healthy reuse: ${healthy.map((p) => "ch" + esc(p.channel)).join(", ")}</p>` : "")
    : (pairs.length ? `<p class="dim">Same-channel siblings are all healthy reuse (never mutually strong).</p>` : "");

  host.innerHTML = `
    <h4>Focused: ${esc(ssid)} — ${f.ess_bssids.length} BSSID(s)</h4>
    <ul class="survey-findings">${findings}</ul>
    ${body.map_svg ? `<div class="survey-map">${body.map_svg}</div>`
                   : '<p class="dim">No GPS positions — site map unavailable (supply a floor plan for indoor placement; planned).</p>'}
    <table class="survey-wp-list"><thead><tr><th>BSSID</th><th>Band</th><th>Ch</th><th>Width</th><th>Vendor</th></tr></thead>
      <tbody>${ess || '<tr><td colspan="5" class="dim">none</td></tr>'}</tbody></table>
    <table class="survey-wp-list"><thead><tr>
      <th>Waypoint</th><th>BSSID</th><th>Ch/W</th><th>Signal</th><th>Co-ch B/R</th><th>Adj</th><th>Util/sta</th>
    </tr></thead><tbody>${wps}</tbody></table>
    ${selfco}
    <p class="report-links">Focused report:
      <a class="report-link" href="${base}&fmt=pdf">PDF</a>
      <a class="report-link" href="${base}&fmt=md">MD</a></p>`;
}

// --- Actions ---------------------------------------------------------------------------------

// The active survey only: main.js calls this when the overview opens, for its Bench chip.
export async function refreshActive() {
  try {
    const { body } = await api("/api/survey/active");
    renderActive(body.active);
  } catch { /* offline: the chip keeps its last word */ }
}

async function refresh() {
  const { body } = await api("/api/survey/active");
  renderActive(body.active);
  await loadList();
}

async function start(ev) {
  ev.preventDefault();
  if (busy) return;
  busy = true;
  setErr("survey-start-error", "");
  const name = document.getElementById("survey-name").value;
  const { ok, body } = await api("/api/survey/start", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  busy = false;
  if (!ok) { setErr("survey-start-error", body.error || "could not start"); return; }
  document.getElementById("survey-name").value = "";
  await refresh();
}

async function dropWaypoint() {
  if (busy) return;
  busy = true;
  setErr("survey-wp-error", "");
  const btn = document.getElementById("survey-wp-drop");
  btn.disabled = true; btn.setAttribute("aria-busy", "true"); btn.textContent = "Capturing…";
  const label = document.getElementById("survey-wp-label").value;
  const note = document.getElementById("survey-wp-note").value;
  const { ok, body } = await api("/api/survey/waypoint", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ label, note }),
  });
  busy = false;
  btn.disabled = false; btn.removeAttribute("aria-busy"); btn.textContent = "Drop waypoint";
  if (!ok) { setErr("survey-wp-error", body.error || "could not capture"); return; }
  if (body.waypoint && body.waypoint.snapshot_error) {
    setErr("survey-wp-error", `Recorded, but Kismet gave no data: ${body.waypoint.snapshot_error}`);
  }
  document.getElementById("survey-wp-label").value = "";
  document.getElementById("survey-wp-note").value = "";
  await refresh();
}

async function undo() {
  if (busy) return;
  busy = true; setErr("survey-wp-error", "");
  const { ok, body } = await api("/api/survey/waypoint/undo", { method: "POST" });
  busy = false;
  if (!ok) setErr("survey-wp-error", body.error || "nothing to undo");
  await refresh();
}

async function stop() {
  if (busy) return;
  if (!confirm("Finish this survey? It will close and become available for reports.")) return;
  busy = true; setErr("survey-wp-error", "");
  const { ok, body } = await api("/api/survey/stop", { method: "POST" });
  busy = false;
  if (!ok) { setErr("survey-wp-error", body.error || "could not stop"); return; }
  await refresh();
  if (body.survey_id) showPreview(body.survey_id);
}

async function del(id) {
  if (!confirm("Delete this survey and its data? This cannot be undone.")) return;
  await api(`/api/survey/${encodeURIComponent(id)}`, { method: "DELETE" });
  const el = document.getElementById("survey-preview");
  if (el) el.hidden = true;
  await refresh();
}

export function initSurvey() {
  const form = document.getElementById("survey-start-form");
  if (!form) return;
  form.addEventListener("submit", start);
  document.getElementById("survey-wp-drop").addEventListener("click", dropWaypoint);
  document.getElementById("survey-wp-undo").addEventListener("click", undo);
  document.getElementById("survey-stop").addEventListener("click", stop);
  document.getElementById("survey-list-body").addEventListener("click", (ev) => {
    const v = ev.target.closest(".survey-view");
    const d = ev.target.closest(".survey-del");
    if (v) showPreview(v.dataset.id);
    else if (d && !d.disabled) del(d.dataset.id);
  });
  refresh();
}
