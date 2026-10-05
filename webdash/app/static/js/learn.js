// The Chart Table — learning pages. Content comes from /api/learn/* as typed blocks (never HTML)
// and is rendered with h(), so every string lands as text. {live:path} spans are filled from the
// same status snapshot the stations use. Routes (all under #/learn):
//   (empty)          learning home: tracks and modules
//   m/<module>       module page
//   l/<lesson>       lesson, with a live-data card docked beside it
//   glossary         every glossary term
// Design: docs/reference/learning-platform-plan.md §3.1.

import { GLOSS_LINKS, h } from "./ui.js";

let catalog = null;          // /api/learn/catalog, fetched once per page load (and on demand)
let lastStatus = null;
const cache = new Map();     // url -> JSON

async function getJSON(url) {
  if (cache.has(url)) return cache.get(url);
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: HTTP ${r.status}`);
  const data = await r.json();
  cache.set(url, data);
  return data;
}

// Uncached fetch that turns an HTTP error into a thrown message (with the server's detail).
async function fetchJSON(url) {
  const r = await fetch(url);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.detail || `${url}: HTTP ${r.status}`);
  return data;
}

// Human labels for status paths shown in live cards; the raw path stays in the tooltip.
const LABELS = {
  "aiov2.power.source": "Power source", "aiov2.power_num.voltage_v": "Cell voltage (V)",
  "aiov2.power_num.power_w": "Power (W)", "aiov2.power_num.capacity_pct": "Charge (%)",
  "aiov2.power_num.on_battery": "On battery", "gps.fix": "Fix", "gps.grid": "Grid square",
  "gps.satellites_used": "Satellites used", "gps.satellites_visible": "Satellites visible",
  "gps.hdop": "HDOP", "gps.pdop": "PDOP", "gps.eph_m": "Error estimate (m)", "gps.tpv_age_s": "Fix age (s)",
  "adsb.state": "Decoder", "adsb.aircraft_count": "Aircraft", "adsb.with_position": "With position",
  "adsb.messages_per_s": "Messages/s", "mesh.state": "Mesh link", "mesh.channels": "Channels",
  "mesh.nodes_seen": "Nodes in NodeDB", "mesh.rx_packets": "Packets heard", "mesh.rx_nodes": "Nodes heard",
  "mesh.last_rx_ts": "Last packet", "mesh.last_rx_snr": "Last SNR (dB)", "mesh.last_rx_rssi": "Last RSSI (dBm)",
  "kismet.state": "Kismet", "kismet.devices": "Devices seen",
  "net.monitor_ifaces": "Monitor interfaces", "net.wlan0.present": "wlan0 present", "net.wlan0.mode": "wlan0 mode",
  "net.wlan1.present": "wlan1 present", "net.wlan1.mode": "wlan1 mode",
};
function label(path) {
  if (LABELS[path]) return LABELS[path];
  let m = path.match(/^aiov2\.rails\.(\w+)\.on$/); if (m) return `${m[1]} rail`;
  m = path.match(/^services\.(\w+)\.(\w+)$/); if (m) return `${m[1]} ${m[2].replace("_", " ")}`;
  return path;
}
function liveRow(p) {
  return h("div", { class: "row" }, h("span", { class: "k", title: p }, label(p)), h("span", { class: "v live", "data-live": p }, "—"));
}
const SAFE_HREF = /^(#\/|https:\/\/)/;

// Restore / put-back instructions in words, not paths.
function restoreText(c, now) {
  const m = (c.path || "").match(/^aiov2\.rails\.(\w+)\.on$/);
  if (m) return `${m[1]} rail: switch it ${c.value ? "on" : "off"} (now ${now === true ? "on" : now === false ? "off" : "unknown"})`;
  if (c.path === "aiov2.power_num.on_battery") return c.value ? "Unplug the charger" : "Plug the charger back in";
  if (c.path === "services.readsb.active") return "Start readsb again: sudo systemctl start readsb";
  if (c.path === "system.load.1m") return "Stop the busy loops: pkill -x yes (the load then falls over a couple of minutes)";
  return `${label(c.path || c.op)} should be ${c.value ?? c.op} (now ${fmtVal(now)})`;
}

async function loadCatalog() {
  if (!catalog) catalog = await getJSON("/api/learn/catalog");
  return catalog;
}

// ---------------------------------------------------------------------------
// Progress (server-side, learn.db) and a small offline write-behind queue
// ---------------------------------------------------------------------------

let progress = {};
async function loadProgress() {
  try {
    const r = await fetch("/api/learn/progress");
    if (r.ok) progress = (await r.json()).items || {};
  } catch { /* offline: keep what we have */ }
  return progress;
}

const QKEY = "fancy.v1.learnq";
function qLoad() { try { return JSON.parse(localStorage.getItem(QKEY) || "[]"); } catch { return []; } }
function qSave(q) { try { localStorage.setItem(QKEY, JSON.stringify(q.slice(-200))); } catch { /* private window */ } }

// Writes that fail (Wi-Fi drop, container restart) are queued and replayed later, in order.
async function send(method, url, body) {
  try {
    const r = await fetch(url, { method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
    if (r.ok || (r.status >= 400 && r.status < 500 && r.status !== 401)) return r.ok;
  } catch { /* fall through */ }
  const q = qLoad(); q.push({ method, url, body }); qSave(q);
  return false;
}

async function flushQueue() {
  const q = qLoad();
  if (!q.length) return;
  qSave([]);
  for (const item of q) await send(item.method, item.url, item.body);
}

// Active time: a 30 s heartbeat while this tab is visible and someone touched it in the last
// 60 s (plan §3.7). Heartbeats only ever add time to an item the learner has open.
let current = null;          // {item_type, item_id}
let lastInput = Date.now();
let events = [];
for (const ev of ["keydown", "pointerdown", "wheel", "touchstart"]) {
  addEventListener(ev, () => { lastInput = Date.now(); }, { passive: true });
}
setInterval(() => {
  if (current && document.visibilityState === "visible" && Date.now() - lastInput < 60000) {
    events.push({ kind: "heartbeat", ...current, seconds: 30 });
  }
  if (events.length) { const batch = events; events = []; send("POST", "/api/learn/events", { events: batch }); }
  flushQueue();
}, 30000);

// Progress glyphs: learning state is brass glyph + word, never colour alone.
function progGlyph(id) {
  const p = progress[id];
  if (!p) return h("span", { class: "prog" }, "○");
  if (p.state === "done") return h("span", { class: "prog done", title: p.earlier_version ? "done (earlier version)" : "done" }, p.earlier_version ? "✓*" : "✓");
  return h("span", { class: "prog doing", title: "in progress" }, "◐");
}

// ---------------------------------------------------------------------------
// Live values
// ---------------------------------------------------------------------------

function getPath(obj, path) {
  let cur = obj;
  for (const part of path.split(".")) {
    if (cur == null || typeof cur !== "object" || !(part in cur)) return undefined;
    cur = cur[part];
  }
  return cur;
}

export function fmtLive(path, v) {
  if (v === undefined) return "—";
  if (v === null) return "—";
  if (typeof v === "boolean") return path.endsWith(".on") ? (v ? "on" : "off") : (v ? "yes" : "no");
  if (Array.isArray(v)) return v.length ? v.join(", ") : "none";
  if (typeof v === "number") {
    if (path.endsWith("_ts")) {
      const s = Math.max(0, Math.round(Date.now() / 1000 - v));
      return s < 90 ? `${s} s ago` : s < 5400 ? `${Math.round(s / 60)} min ago` : `${Math.round(s / 3600)} h ago`;
    }
    return Number.isInteger(v) ? String(v) : String(Math.round(v * 100) / 100);
  }
  return String(v);
}

export function updateLive(data) {
  if (data) lastStatus = data;
  if (data && labOpen?.run?.open) labRefresh();
  if (!lastStatus) return;
  const stale = Date.now() / 1000 - (lastStatus.generated_at || 0) > 15;
  for (const el of document.querySelectorAll("#learn-root [data-live]")) {
    el.textContent = fmtLive(el.dataset.live, getPath(lastStatus, el.dataset.live));
    el.classList.toggle("stale", stale);
  }
}

// ---------------------------------------------------------------------------
// Blocks -> DOM
// ---------------------------------------------------------------------------

function spans(list) {
  const frag = document.createDocumentFragment();
  for (const sp of list || []) {
    if (sp.live) {
      frag.append(h("span", { class: "live", "data-live": sp.live, title: sp.live }, "—"));
      continue;
    }
    let el = sp.code ? h("code", {}, sp.t) : document.createTextNode(sp.t);
    if (sp.i) el = h("em", {}, el);
    if (sp.b) el = h("strong", {}, el);
    if (sp.href) {
      const ext = sp.href.startsWith("https://");
      el = h("a", { href: sp.href, target: ext ? "_blank" : null, rel: ext ? "noopener" : null }, el);
    }
    frag.append(el);
  }
  return frag;
}

function block(b, base = 2) {
  switch (b.type) {
    case "h": return h(`h${Math.min(6, b.level + base - 1)}`, {}, spans(b.spans));
    case "p": return h("p", {}, spans(b.spans));
    case "list": return h(b.ordered ? "ol" : "ul", {}, ...b.items.map((it) => h("li", {}, spans(it))));
    case "code": return h("pre", { class: "cmd" }, h("code", {}, b.text));
    case "callout": return h("div", { class: "callout" }, ...b.paras.map((p) => h("p", {}, spans(p))));
    case "table":
      return h("div", { class: "table-wrap" }, h("table", {},
        h("thead", {}, h("tr", {}, ...b.head.map((c) => h("th", {}, spans(c))))),
        h("tbody", {}, ...b.rows.map((r) => h("tr", {}, ...r.map((c) => h("td", {}, spans(c))))))));
    case "ref":
      return h("section", { class: "ref" },
        h("div", { class: "ref-src" }, "From the knowledge base: ", h("code", {}, b.anchor ? `${b.path}#${b.anchor}` : b.path)),
        ...b.blocks.map((x) => block(x, base + 1)));
    default: return null;
  }
}

function blocks(list, base) { return (list || []).map((b) => block(b, base)).filter(Boolean); }

function livePaths(list, out = new Set()) {
  for (const b of list || []) {
    const groups = b.type === "list" ? b.items : b.type === "callout" ? b.paras
      : b.type === "table" ? [...b.head, ...b.rows.flat()] : [b.spans];
    for (const g of groups) for (const sp of g || []) if (sp.live) out.add(sp.live);
    if (b.type === "ref") livePaths(b.blocks, out);
  }
  return out;
}

// ---------------------------------------------------------------------------
// Shared bits
// ---------------------------------------------------------------------------

// Learning state is shown as glyph + word in brass, never colour alone; status colours stay
// reserved for live data (webdash-design.md §Visual system).
const TODAY = { ready: ["○", "ready"], degraded: ["▲", "partly available"], blocked: ["⊘", "blocked today"] };

function todayBadge(t) {
  const [g, word] = TODAY[t?.state] || ["?", "unknown"];
  return h("span", { class: `learn-state ${t?.state || ""}`, title: t?.reason || "" }, `${g} ${word}`);
}

function title(main, themed) {
  return themed ? [main, " ", h("span", { class: "sub" }, `· ${themed}`)] : [main];
}

// "Plain labels" hides the themed layer everywhere (creative direction, plan §3.8).
const PLAIN_KEY = "fancy.v1.plainLabels";
function plainOn() { try { return localStorage.getItem(PLAIN_KEY) === "1"; } catch { return false; } }
function applyPlain() { document.body.classList.toggle("plain-labels", plainOn()); }
applyPlain();
function plainToggle() {
  const b = h("button", { type: "button", class: "btn", "aria-pressed": plainOn() ? "true" : "false" }, "Plain labels");
  b.addEventListener("click", () => {
    try { localStorage.setItem(PLAIN_KEY, plainOn() ? "0" : "1"); } catch { /* private window */ }
    applyPlain(); b.setAttribute("aria-pressed", plainOn() ? "true" : "false");
  });
  return b;
}

// Skin: the visual look, independent of theme/plain labels. "chart" is the default dark
// instrument skin; "vintage" is the Simpson analog-meter skin (styles.css). The loader in
// index.html reads this key before first paint so a reload never flashes the wrong skin.
const SKIN_KEY = "fancy.v1.skin";
const SKINS = ["chart", "vintage"];
const SKIN_LABEL = { chart: "Chart room", vintage: "Vintage" };
function skinNow() { try { return localStorage.getItem(SKIN_KEY) || "chart"; } catch { return "chart"; } }
function applySkin() {
  const s = skinNow();
  if (s === "chart") document.documentElement.removeAttribute("data-skin");
  else document.documentElement.setAttribute("data-skin", s);
}
applySkin();
function skinToggle() {
  const b = h("button", { type: "button", class: "btn" }, `Skin: ${SKIN_LABEL[skinNow()] || skinNow()}`);
  b.addEventListener("click", () => {
    const next = SKINS[(SKINS.indexOf(skinNow()) + 1) % SKINS.length];
    try { localStorage.setItem(SKIN_KEY, next); } catch { /* private window */ }
    applySkin(); b.textContent = `Skin: ${SKIN_LABEL[next] || next}`;
  });
  return b;
}

function head(backHref, backText, heading, extra) {
  return h("div", { class: "view-head" },
    h("a", { class: "back", href: backHref }, backText),
    h("h1", { class: "view-title", tabindex: "-1" }, ...heading),
    extra || null);
}

function mins(m) { return m ? `${m} min` : ""; }

const STATION_NAME = { mesh: "Mesh", gps: "GPS", sdr: "ADS-B (SDR)", wifi: "Wi-Fi survey", power: "Power", system: "System" };
function stationLink(st) {
  return st ? h("p", {}, h("a", { class: "tile-link", href: `#/${st}` }, `Open the ${STATION_NAME[st] || st} station →`)) : null;
}

let navSeq = 0;        // bumped on every route change; a page renders only if it is still current
function mountIf(seq, ...nodes) { if (seq === navSeq) mount(...nodes); }
function mount(...nodes) {
  const root = document.getElementById("learn-root");
  root.replaceChildren(...nodes.filter(Boolean));
  root.querySelector(".view-title")?.focus();
  updateLive();
}

function fail(err) {
  mount(head("#/learn", "← Learn", ["Couldn't load this page"]),
    h("div", { class: "panel" }, h("p", { class: "error" }, String(err.message || err)),
      h("p", {}, "Check that webdash is running (docker ps shows uconsole-webdash), then reload the page.")));
}

// ---------------------------------------------------------------------------
// Pages
// ---------------------------------------------------------------------------

// A module counts as done when every lesson is read and its lab(s) and check are passed. Labs and
// checks only get progress rows from the server (S6/S7), so until then this is lessons-only.
function moduleDone(cat, mid) {
  const m = cat.modules[mid];
  if (!m) return false;
  const ids = [...m.lessons.map((l) => l.id), ...m.labs.map((l) => l.id), ...(m.assessment ? [m.assessment] : [])];
  return ids.every((id) => progress[id]?.state === "done");
}

function moduleRow(cat, mid) {
  const m = cat.modules[mid];
  if (!m) {
    return h("li", { class: "mod-row unsurveyed" },
      h("span", { class: "mod-id" }, mid), " ",
      h("span", { class: "dim" }, "Not written yet"), h("span", { class: "sub" }, " · unsurveyed"));
  }
  const pre = (m.prerequisites || []).map((p) => p.id);
  const done = m.lessons.filter((l) => progress[l.id]?.state === "done").length;
  const unmet = pre.filter((p) => !moduleDone(cat, p));
  const items = [...m.lessons.map((l) => l.id), ...m.labs.map((l) => l.id), ...(m.assessment ? [m.assessment] : [])];
  const state = moduleDone(cat, mid) ? "✓ done" : items.some((id) => progress[id]) ? "◐ in progress"
    : unmet.length ? `⊘ needs ${unmet.join(", ")}` : "○ available";
  return h("li", { class: "mod-row" },
    h("span", { class: "learn-state" }, state), " ",
    h("a", { href: `#/learn/m/${mid}` }, h("span", { class: "mod-id" }, mid), " ", m.title),
    m.today?.state && m.today.state !== "ready" ? [" ", todayBadge(m.today)] : null,
    h("span", { class: "dim" }, ` · ${done}/${m.lessons.length} lessons`),
    m.est_minutes ? h("span", { class: "dim" }, ` · ${mins(m.est_minutes)}`) : null);
}

// "What next?": the most recently started unfinished lab or lesson, else the first unread lesson.
function continueCard(cat) {
  const byId = {};
  for (const [mid, m] of Object.entries(cat.modules)) {
    for (const l of m.lessons) byId[l.id] = { href: `#/learn/l/${l.id}`, label: `${mid} · ${l.title}` };
    for (const x of m.labs) byId[x.id] = { href: `#/learn/lab/${x.id}`, label: `${x.id} ${x.title}` };
  }
  const doing = Object.entries(progress).filter(([id, p]) => p.state === "in_progress" && byId[id])
    .sort((a, b) => (b[1].started_at || 0) - (a[1].started_at || 0))[0];
  let target = doing && byId[doing[0]], word = "Continue";
  if (!target) {
    const order = cat.tracks.flatMap((t) => t.modules).filter((m) => cat.modules[m]);
    const next = order.flatMap((m) => cat.modules[m].lessons).find((l) => progress[l.id]?.state !== "done");
    if (next) { target = byId[next.id]; word = Object.keys(progress).length ? "Next" : "Start here"; }
  }
  if (!target) return null;
  const a = h("a", { class: "btn primary", href: target.href }, `${word}: ${target.label} →`);
  return h("section", { class: "panel learn-track continue" }, a);
}

async function home() {
  const seq = navSeq;
  current = null;
  const cat = await loadCatalog();
  await loadProgress();
  if (cat.state !== "ok") {
    return mountIf(seq, head("#/", "← Overview", ["Learn"]),
      h("div", { class: "panel" },
        h("p", {}, "No curriculum has been compiled yet."),
        h("pre", { class: "cmd" }, "python3 webdash/host-helpers/learn-compile.py")));
  }
  const inTrack = new Set(cat.tracks.flatMap((t) => t.modules));
  const others = Object.keys(cat.modules).filter((m) => !inTrack.has(m));
  mountIf(seq, 
    head("#/", "← Overview", ["Learn ", h("span", { class: "sub" }, "· The Chart Table")],
      h("span", { class: "head-links" }, skinToggle(), " ", plainToggle(), " ", h("a", { class: "tile-link", href: "#/learn/search" }, "Search (/)"), " · ",
        h("a", { class: "tile-link", href: "#/learn/review" }, "Review"), " · ",
        h("a", { class: "tile-link", href: "#/learn/notes" }, "Notes"), " · ",
        h("a", { class: "tile-link", href: "#/learn/glossary" }, "Glossary"), " · ",
        h("a", { class: "tile-link", href: "#/learn/owner" }, "Owner"))),
    continueCard(cat),
    ...cat.tracks.map((t) => h("section", { class: "panel learn-track" },
      h("h2", {}, h("span", {}, ...title(`Track ${t.id.toUpperCase()} — ${t.title}`, t.themed_title)),
        h("span", { class: "dim" }, t.est_minutes ? `about ${Math.round(t.est_minutes / 60)} h` : "")),
      t.summary ? h("p", { class: "dim" }, t.summary) : null,
      t.note ? h("p", { class: "callout" }, t.note) : null,
      h("ol", { class: "mod-list" }, ...t.modules.map((mid) => moduleRow(cat, mid))))),
    ...(await homeExtras()),
    others.length ? h("section", { class: "panel learn-track" }, h("h2", {}, "Other modules"),
      h("ul", { class: "mod-list" }, ...others.map((mid) => moduleRow(cat, mid)))) : null,
    h("p", { class: "dim learn-meta" },
      `Curriculum ${cat.meta.bundle_sha} · compiled from ${cat.meta.source}` +
      (cat.meta.commit ? ` @ ${cat.meta.commit.slice(0, 7)}` : "")),
  );
}

async function modulePage(mid) {
  const seq = navSeq;
  current = null;
  const cat = await loadCatalog();
  await loadProgress();
  const m = await getJSON(`/api/learn/module/${encodeURIComponent(mid)}`);
  const summary = cat.modules[mid];
  const pre = m.prerequisites || [];
  const firstOpen = summary.lessons.find((l) => progress[l.id]?.state !== "done");
  const action = firstOpen ? h("a", { class: "btn primary", href: `#/learn/l/${firstOpen.id}` },
    `${summary.lessons.some((l) => progress[l.id]) ? "Continue" : "Start"}: ${firstOpen.title} →`) : null;
  mountIf(seq, 
    head("#/learn", "← Learn", title(`${m.id} ${m.title}`, m.themed_title), [" ", todayBadge(m.today), " ", action]),
    h("div", { class: "learn-cols" },
      h("div", { class: "panel learn-main prose" },
        driftBanner(summary),
        ...blocks(m.blocks, 2),
        h("h2", {}, "You will be able to"),
        h("ul", {}, ...(m.objectives || []).map((o) => h("li", {}, boldText(o)))),
        m.today?.reason ? h("p", { class: "dim" }, `Today: ${m.today.reason}`) : null),
      h("aside", { class: "panel learn-side" },
        pre.length ? h("div", {}, h("h2", {}, "Before this"),
          h("ul", { class: "plain" }, ...pre.map((p) => h("li", {},
            h("a", { href: `#/learn/m/${p.id}` }, p.id), p.soft ? " (recommended)" : ""))),
          h("p", { class: "dim" }, "Prerequisites are advice: reading is always open.")) : null,
        h("h2", {}, "Lessons"),
        h("ol", { class: "plain" }, ...summary.lessons.map((l) =>
          h("li", {}, progGlyph(l.id), " ", h("a", { href: `#/learn/l/${l.id}` }, l.title), h("span", { class: "dim" }, l.est_minutes ? ` · ${mins(l.est_minutes)}` : "")))),
        summary.labs.length ? h("h2", {}, "Labs") : null,
        summary.labs.length ? h("ul", { class: "plain" }, ...summary.labs.map((x) =>
          h("li", {}, progGlyph(x.id), " ", h("a", { href: `#/learn/lab/${x.id}` }, `${x.id} ${x.title}`),
            x.transmits ? h("span", { class: "tx" }, " · transmits") : null))) : null,
        m.assessment ? h("h2", {}, "Check") : null,
        m.assessment ? h("p", {}, progGlyph(m.assessment), " ", h("a", { href: `#/learn/quiz/${m.assessment}` }, m.assessment)) : null,
        stationLink(m.station))));
}

// Objectives are plain strings with **bold** verbs.
function boldText(s) {
  const frag = document.createDocumentFragment();
  s.split(/(\*\*[^*]+\*\*)/).forEach((part) => {
    if (part.startsWith("**") && part.endsWith("**")) frag.append(h("strong", {}, part.slice(2, -2)));
    else if (part) frag.append(part);
  });
  return frag;
}

async function markDone(lid) {
  await send("PUT", "/api/learn/progress", { item_type: "lesson", item_id: lid, state: "done" });
  progress[lid] = { ...(progress[lid] || {}), state: "done" };
}

async function lessonPage(lid) {
  const seq = navSeq;
  const le = await getJSON(`/api/learn/lesson/${encodeURIComponent(lid)}`);
  const cat = await loadCatalog();
  await loadProgress();
  current = { item_type: "lesson", item_id: lid };
  if (!progress[lid]) send("PUT", "/api/learn/progress", { item_type: "lesson", item_id: lid, state: "in_progress" });
  const isDone = progress[lid]?.state === "done";
  const doneBtn = h("button", { type: "button", class: "btn", "aria-pressed": isDone ? "true" : "false" },
    isDone ? "✓ Read" : "Mark as read");
  doneBtn.addEventListener("click", async () => {
    await markDone(lid);
    doneBtn.textContent = "✓ Read";
    doneBtn.setAttribute("aria-pressed", "true");
  });
  const mod = cat.modules[le.module];
  const idx = mod.lessons.findIndex((l) => l.id === lid);
  const prev = mod.lessons[idx - 1], next = mod.lessons[idx + 1];
  const paths = [...livePaths(le.blocks)];
  const gloss = Object.values(le.glossary_entries || {});
  const side = h("aside", { class: "panel learn-side" },
    h("h2", {}, "Live on Fancy"),
    paths.length ? h("div", {}, ...paths.map(liveRow))
      : h("p", { class: "dim" }, "This lesson has no live readings; the station link below shows the radio."),
    stationLink(mod.station),
    gloss.length ? h("h2", {}, "Terms") : null,
    ...gloss.map((g) => h("details", { class: "gloss" }, h("summary", {}, g.term),
      h("p", {}, g.tooltip), g.good_bad ? h("p", { class: "dim" }, g.good_bad) : null)),
    notesPanel(lid, mod.discipline));
  side.prepend(sheetToggle(side));
  mountIf(seq, 
    head(`#/learn/m/${le.module}`, `← ${le.module} ${mod.title}`,
      [`Lesson ${idx + 1}/${mod.lessons.length} · ${le.title}`]),
    h("div", { class: "learn-cols" },
      h("article", { class: "panel learn-main prose" }, driftBanner(mod), ...blocks(le.blocks, 2),
        !next && mod.labs.length ? h("p", { class: "try-it" }, "Try it: ",
          ...mod.labs.map((x, n) => [n ? " · " : "", h("a", { href: `#/learn/lab/${x.id}` }, `${x.id} ${x.title}`)])) : null,
        h("nav", { class: "lesson-nav" },
          prev ? h("a", { href: `#/learn/l/${prev.id}` }, `← ${prev.title}`) : h("span"),
          doneBtn,
          nextLink(next ? `#/learn/l/${next.id}` : `#/learn/m/${le.module}`,
            next ? `${next.title} →` : "Back to the module →", lid))),
      side),
  );
}

// Moving on to the next lesson counts as having read this one.
function nextLink(href, text, lid) {
  const a = h("a", { href }, text);
  a.addEventListener("click", () => { markDone(lid); });
  return a;
}

async function glossaryPage(focusId) {
  const seq = navSeq;
  current = null;
  const g = await getJSON("/api/learn/glossary");
  const entries = Object.values(g).sort((a, b) => a.term.localeCompare(b.term));
  mountIf(seq, head("#/learn", "← Learn", ["Glossary"]),
    h("div", { class: "panel prose" }, ...entries.map((e) => h("section", { class: "gloss-entry", id: `g-${e.id}` },
      h("h2", {}, e.term), h("p", {}, h("strong", {}, e.tooltip)), ...blocks(e.blocks, 3),
      e.good_bad ? h("p", {}, h("span", { class: "dim" }, "On Fancy: "), e.good_bad) : null,
      e.try_this ? h("p", {}, h("span", { class: "dim" }, "Try this: "), e.try_this) : null,
      e.learn_more && SAFE_HREF.test(e.learn_more) ? h("p", {}, h("a", { href: e.learn_more }, "Learn more →")) : null))));
}

// ---------------------------------------------------------------------------
// Labs (doing mode): the steps with their live check state; the station card docked beside them.
// The server evaluates every check; this page only shows results and sends attest/paste input.
// ---------------------------------------------------------------------------

let labOpen = null;   // {lab, run} while a lab page is showing

const STEP_STATE = {
  passed: ["✓", "passed"], holding: ["◐", "holding"], active: ["○", "not yet"],
  pending: ["·", "later"], missing: ["✕", "can't check yet"],
};

function fmtTime(ts) { return ts ? new Date(ts * 1000).toISOString().slice(11, 16) + "Z" : ""; }

function fmtVal(v) {
  if (v == null || v === "attested") return v === "attested" ? "attested" : "";
  if (typeof v === "object") return Object.entries(v).map(([k, x]) => `${k} ${x}`).join(", ");
  return typeof v === "number" ? String(Math.round(v * 1000) / 1000) : String(v);
}

function stepItem(lab, run, step) {
  const rs = run?.steps?.[step.id] || { state: "pending" };
  const c = step.check;
  let [glyph, word] = STEP_STATE[rs.state] || ["?", rs.state];
  if (rs.state === "active" && step.world_wait) [glyph, word] = ["◌", "waiting on the world"];
  if (rs.state === "holding") word = `holding ${rs.ticks || 1}/${step.hold_ticks || (c.type === "status" ? 2 : 1)} readings`;
  const detail = [];
  if (rs.state === "passed") detail.push(`${fmtTime(rs.passed_at)} ${fmtVal(rs.value)}`.trim());
  else if (rs.value != null && rs.state !== "pending") detail.push(`now ${fmtVal(rs.value)}`);
  if (rs.detail) detail.push(rs.state === "missing"
    ? `${rs.detail} right now. Open the station to see why; if it never appears, see Owner view → Content health.`
    : rs.detail);
  if (rs.overdue) detail.push(`taking longer than expected · open the ${STATION_NAME[labOpen?.mod?.station] || ""} station and check its rail and service`);
  const li = h("li", { class: `step ${rs.state}${step.world_wait ? " world" : ""}` },
    h("div", { class: "step-head" }, h("span", { class: "step-glyph" }, glyph), " ", step.text),
    h("div", { class: "step-state" }, word, detail.length ? ` · ${detail.join(" · ")}` : ""),
    c.type === "status" ? h("details", { class: "step-check" }, h("summary", {}, "How this is checked"),
      `${c.path} ${c.op} ${c.value ?? ""}`) : null);
  const current = run?.open && (rs.state === "active" || rs.state === "missing");
  if (current && c.type === "attest") {
    const b = h("button", { type: "button", class: "btn", "data-focus-key": `attest-${step.id}` }, c.prompt || "Done");
    b.addEventListener("click", () => labSubmit(run.id, step.id, null));
    li.append(b);
  } else if (current && c.type === "paste") {
    const ta = h("textarea", { class: "paste", rows: "5", placeholder: "Paste the command output here", "aria-label": "Command output" });
    const b = h("button", { type: "button", class: "btn" }, "Check output");
    b.addEventListener("click", () => labSubmit(run.id, step.id, ta.value));
    li.append(ta, b, h("div", { class: "dim small" }, "Only the result is kept, not what you paste."));
  } else if (current && c.type === "quiz") {
    li.append(h("p", {}, h("a", { href: `#/learn/quiz/${c.assessment}` }, `Take ${c.assessment} →`)));
  }
  return li;
}

function stationCard(lab, mod) {
  const rails = lab.requires?.rails || [];
  const ev = lab.evidence || [];
  return h("aside", { class: "panel learn-side" },
    h("h2", {}, "Live on Fancy"),
    ...rails.map((r) => h("div", { class: "row" }, h("span", { class: "k" }, `${r} rail`),
      h("span", { class: "rail-ctl" }, h("button", { type: "button", class: "rail-switch", role: "switch", "data-feature": r, "aria-label": `${r} rail`, "data-focus-key": `rail-${r}` })))),
    rails.length ? h("div", { class: "switch-error", role: "alert" }) : null,
    ...ev.map(liveRow),
    ...(lab.requires?.services || []).map((sv) => liveRow(`services.${sv}.active`)),
    stationLink(mod?.station));
}

function evidenceText(ev) {
  return Object.entries(ev || {}).filter(([k, v]) => v != null && k !== "safety" && k !== "restore_needed")
    .map(([k, v]) => `${label(k)} ${fmtVal(v)}`).join(" · ");
}

// Partial update: when the page is already showing this run, refresh only the parts that change
// (status, banner, steps, controls) so focus, the rail switch and a note being typed are left
// alone. Announces newly passed steps to screen readers.
function updateLabInPlace(prevRun) {
  const { lab, run } = labOpen;
  const root = document.getElementById("learn-root");
  const stepsEl = root.querySelector("ol.steps");
  if (!stepsEl || root.dataset.labRun !== String(run?.id) || !run?.open || !prevRun?.open) return false;
  if (document.activeElement?.tagName === "TEXTAREA" && document.activeElement.closest("ol.steps")) return true;
  const focusKey = document.activeElement?.dataset?.focusKey;
  stepsEl.replaceChildren(...lab.steps.map((st) => stepItem(lab, run, st)));
  const stepCount = run.step_count || lab.steps.length;
  const status = root.querySelector(".lab-status");
  if (status) status.textContent = `◐ step ${Math.min((run.steps_passed || 0) + 1, stepCount)}/${stepCount}`;
  const restoreBox = root.querySelector(".lab-restore");
  const allPassed = lab.steps.every((s) => run.steps?.[s.id]?.state === "passed");
  restoreBox?.replaceChildren(...(allPassed && run.restore?.length ? [h("div", { class: "callout warn" },
    h("p", {}, h("strong", {}, "Device left in a changed state. "), "Put it back and the lab completes by itself:"),
    h("ul", {}, ...run.restore.filter((x) => !x.ok).map((x) => h("li", {}, restoreText(x.check, x.value)))))] : []));
  const newly = lab.steps.filter((s) => run.steps?.[s.id]?.state === "passed" && prevRun.steps?.[s.id]?.state !== "passed");
  if (newly.length) {
    const live = root.querySelector(".lab-announce");
    if (live) live.textContent = newly.map((s) => `Passed: ${s.text}`).join(" ");
  }
  if (focusKey) root.querySelector(`[data-focus-key="${focusKey}"]`)?.focus();
  updateLive();
  return true;
}

function renderLab(force = false) {
  const { lab, run, mod, error } = labOpen;
  const open = run?.open;
  const passed = run && !open && run.outcome === "pass";
  const allStepsPassed = run && lab.steps.every((s) => run.steps?.[s.id]?.state === "passed");
  const controls = h("div", { class: "lab-controls" });
  if (!open) {
    const b = h("button", { type: "button", class: "btn primary", "data-focus-key": "start" }, run ? "Start again" : "Start lab");
    b.addEventListener("click", labStart);
    controls.append(b);
  } else {
    const b = h("button", { type: "button", class: "btn", "data-focus-key": "stop" }, "Stop lab");
    b.addEventListener("click", labStop);
    controls.append(b);
  }
  const putBack = (run?.saved?.restore_needed || []);
  const banner = passed
    ? h("div", { class: "callout pass" }, h("p", {}, h("strong", {}, `Lab passed · ${lab.title}. `), evidenceText(run.evidence)))
    : run && !open && run.outcome ? h("div", { class: "callout warn", role: "alert" }, h("p", {},
        run.outcome === "safety_stop" ? (run.safety || "Stopped for safety. Check the Power station before starting again.")
          : run.outcome === "abandoned" ? "The last run was stopped before it finished. Start again when ready."
          : `The last run ended without passing (${run.outcome}). Start again when ready.`),
        putBack.length ? h("ul", {}, ...putBack.map((c) => h("li", {}, restoreText(c, c.now)))) : null)
    : null;
  const restore = open && allStepsPassed && run.restore?.length
    ? h("div", { class: "callout warn" }, h("p", {}, h("strong", {}, "Device left in a changed state. "),
        "Put it back and the lab completes by itself:"),
        h("ul", {}, ...run.restore.filter((r) => !r.ok).map((r) => h("li", {}, restoreText(r.check, r.value)))))
    : null;
  const root = document.getElementById("learn-root");
  const typing = root.contains(document.activeElement) && document.activeElement.tagName === "TEXTAREA";
  // Don't wipe a paste or note in progress — unless the run just ended (a safety stop must show).
  if (typing && !force && open) { labOpen.dirty = true; return; }
  labOpen.dirty = false;
  const stepCount = run?.step_count || lab.steps.length;
  const status = open ? h("span", { class: "learn-state lab-status" }, `◐ step ${Math.min((run.steps_passed || 0) + 1, stepCount)}/${stepCount}`) : null;
  root.dataset.labRun = String(run?.id ?? "");
  const dock = h("div", { class: "dock" }, stationCard(lab, mod), labNotes(lab, mod));
  dock.prepend(sheetToggle(dock));
  root.replaceChildren(
    head(`#/learn/m/${lab.module}`, `← ${lab.module} ${mod?.title || ""}`, title(`${lab.id} ${lab.title}`, lab.themed_title),
      [" ", todayBadge(mod?.today), " ", status, lab.transmits ? h("span", { class: "tx" }, " · TX") : null]),
    h("div", { class: "learn-cols doing" },
      h("div", { class: "panel learn-main" },
        h("div", { class: "visually-hidden lab-announce", "aria-live": "polite" }),
        banner, h("div", { class: "lab-restore" }, restore),
        error ? h("p", { class: "error" }, error) : null,
        controls,
        h("ol", { class: "steps" }, ...lab.steps.map((st) => stepItem(lab, run, st))),
        h("details", { class: "lab-about" }, h("summary", {}, "About this lab"),
          h("div", { class: "prose" }, ...blocks(lab.blocks, 2)),
          lab.world ? h("p", { class: "dim" }, `Waiting on the world: ${lab.world}`) : null,
          lab.transmits ? h("p", { class: "tx" }, `Transmits: ${lab.legal_basis}. Optional — never needed to pass.`) : null)),
      dock));
  updateLive();
  if (lastStatus) import("./rails.js").then((m) => m.syncRails(lastStatus.aiov2));
}

// The notes panel is built once per lab page, so a 3 s re-render doesn't wipe a note being typed.
let labNotesEl = null;
function labNotes(lab, mod) {
  if (!labNotesEl || labNotesEl.dataset.lab !== lab.id) {
    labNotesEl = h("div", { class: "panel learn-side", "data-lab": lab.id }, notesPanel(lab.id, mod?.discipline));
  }
  return labNotesEl;
}

async function labRefresh() {
  const mine = labOpen;
  if (!mine) return;
  const r = await fetch(`/api/learn/labs/${encodeURIComponent(mine.lab.id)}/run`);
  if (!r.ok) return;
  const run = (await r.json()).run;
  if (labOpen !== mine || (run && run.lab_id !== mine.lab.id)) return;  // navigated away meanwhile
  // Re-render only when something changed, so keyboard focus isn't reset every 3 s.
  if (JSON.stringify(run) === JSON.stringify(mine.run) && !mine.dirty) return;
  const ended = mine.run?.open && !run?.open;
  const prev = mine.run;
  mine.run = run; mine.error = null;
  if (!ended && updateLabInPlace(prev)) return;
  const focusedId = document.activeElement?.dataset?.focusKey;
  renderLab(ended);
  if (focusedId) document.querySelector(`[data-focus-key="${focusedId}"]`)?.focus();
}

async function labPost(url, body) {
  const mine = labOpen;
  const r = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body || {}) });
  const data = await r.json().catch(() => ({}));
  if (labOpen !== mine) return;
  if (!r.ok) { mine.error = data.detail || `HTTP ${r.status}`; renderLab(true); return; }
  mine.run = data.run !== undefined ? data.run : data;
  mine.error = data.error || null;
  renderLab(true);
}

function labStart() { labPost(`/api/learn/labs/${encodeURIComponent(labOpen.lab.id)}/start`); }
function labStop() { if (labOpen.run) labPost(`/api/learn/labs/run/${labOpen.run.id}/stop`); }
function labSubmit(runId, stepId, text) {
  document.activeElement?.blur();
  labPost(`/api/learn/labs/run/${runId}/submit`, { step_id: stepId, text });
}

async function labPage(id) {
  current = { item_type: "lab", item_id: id };
  const lab = await getJSON(`/api/learn/lab/${encodeURIComponent(id)}`);
  const cat = await loadCatalog();
  const seq = navSeq;
  const r = await fetch(`/api/learn/labs/${encodeURIComponent(id)}/run`);
  const run = r.ok ? (await r.json()).run : null;
  if (seq !== navSeq) return;
  labOpen = { lab, mod: cat.modules[lab.module], run, error: null };
  renderLab();
  document.querySelector("#learn-root .view-title")?.focus();
}

// ---------------------------------------------------------------------------
// Checks ("Soundings"): graded on the server; answers never reach the browser.
// ---------------------------------------------------------------------------

function itemField(it) {
  const name = `q-${it.id}`;
  if (it.type === "single" || it.type === "multi") {
    const kind = it.type === "single" ? "radio" : "checkbox";
    return h("div", { class: "choices" }, ...it.choices.map((c, i) =>
      h("label", { class: "choice" }, h("input", { type: kind, name, value: String(i) }), " ", String(c))));
  }
  if (it.type === "numeric") {
    return h("label", { class: "choice" }, h("input", { type: "number", name, step: "any", inputmode: "decimal", class: "num-in" }),
      it.unit ? ` ${it.unit}` : "");
  }
  return h("p", { class: "dim" }, "(This question type isn't supported in the browser yet.)");
}

function readAnswers(form, items) {
  const out = {};
  for (const it of items) {
    const els = [...form.querySelectorAll(`[name="${CSS.escape(`q-${it.id}`)}"]`)];
    if (it.type === "single") { const e = els.find((x) => x.checked); if (e) out[it.id] = Number(e.value); }
    else if (it.type === "multi") out[it.id] = els.filter((x) => x.checked).map((x) => Number(x.value));
    else if (it.type === "numeric" && els[0]?.value !== "") out[it.id] = Number(els[0].value);
  }
  return out;
}

async function quizPage(aid) {
  const seq = navSeq;
  current = { item_type: "assessment", item_id: aid };
  const a = await fetchJSON(`/api/learn/assessment/${encodeURIComponent(aid)}`);
  const cat = await loadCatalog();
  const mod = cat.modules[a.module];
  const result = h("div", { "aria-live": "polite" });
  const form = h("form", { class: "quiz", autocomplete: "off" },
    ...a.items.map((it, n) => h("fieldset", { class: "q", id: `item-${it.id}` },
      h("legend", {}, `${n + 1}. ${it.prompt}`, it.required ? h("span", { class: "req" }, " · must be right") : null),
      itemField(it),
      h("div", { class: "q-result" }))),
    h("button", { type: "submit", class: "btn primary" }, "Check my answers"));
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const r = await fetch(`/api/learn/assessment/${encodeURIComponent(aid)}/submit`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ answers: readAnswers(form, a.items) }),
    });
    const g = await r.json();
    if (!r.ok) { result.replaceChildren(h("p", { class: "error" }, g.detail || `HTTP ${r.status}`)); return; }
    for (const it of g.results) {
      const box = form.querySelector(`#item-${CSS.escape(it.id)} .q-result`);
      box.className = `q-result ${it.correct ? "ok" : "no"}`;
      box.replaceChildren(h("strong", {}, it.correct ? "✓ Right. " : "✕ Not quite. "), it.explanation || "");
    }
    // Voice: real numbers, no exclamation marks; a miss says what to do next.
    result.replaceChildren(g.passed
      ? h("div", { class: "callout pass" }, h("p", {}, h("strong", {}, `Passed · ${aid}. `), `${g.right} of ${g.total}.`))
      : h("div", { class: "callout" }, h("p", {}, h("strong", {}, `Not yet: ${g.right} of ${g.total}. `),
          ...g.required_missed.map((id) => {
            const n = a.items.findIndex((x) => x.id === id);
            return `Question ${n + 1} must be right to pass. `;
          }),
          "Reread the explanations and try again — nothing is lost.")));
    result.scrollIntoView({ block: "nearest" });
  });
  mountIf(seq, 
    head(`#/learn/m/${a.module}`, `← ${a.module} ${mod?.title || ""}`, [`Check · ${aid}`],
      a.passed ? h("span", { class: "learn-state" }, "✓ passed") : null),
    h("div", { class: "panel prose quiz-panel" },
      ...blocks(a.blocks, 2),
      h("p", { class: "dim" }, `Pass mark ${Math.round(a.pass_threshold * 100)}%. Retry as often as you like.`),
      form, result));
}

// ---------------------------------------------------------------------------
// Review queue ("watch bill"), notes, endorsements and the ship's log (S8)
// ---------------------------------------------------------------------------

function fmtDate(ts) { return ts ? new Date(ts * 1000).toISOString().slice(0, 16).replace("T", " ") + "Z" : ""; }

// Learn chip in the status strip: "◆ Learn 3" when review cards are due.
export async function refreshChip() {
  const chip = document.querySelector(".learn-chip");
  if (!chip) return;
  try {
    const r = await fetch("/api/learn/summary");
    if (!r.ok) return;
    const n = (await r.json()).review_due;
    chip.textContent = n ? `◆ Learn ${n}` : "◆ Learn";
    chip.title = n ? `${n} review card${n > 1 ? "s" : ""} due` : "Learn: lessons and labs (The Chart Table)";
  } catch { /* offline */ }
}

async function homeExtras() {
  const [rv, en, lg] = await Promise.all(["/api/learn/review", "/api/learn/endorsements", "/api/learn/log"]
    .map((u) => fetch(u).then((r) => (r.ok ? r.json() : null)).catch(() => null)));
  const panels = [];
  if (rv) {
    panels.push(h("section", { class: "panel learn-track" }, h("h2", {}, "Review ", h("span", { class: "sub" }, "· watch bill")),
      rv.count_due ? h("p", {}, `${rv.count_due} due for review. `, h("a", { class: "tile-link", href: "#/learn/review" }, "Start review →"))
        : h("p", { class: "dim" }, rv.total ? `Nothing due. Next review ${fmtDate(rv.next_due_at)}.`
          : "Nothing to review yet. Terms join the review when you finish a lesson that uses them.")));
  }
  if (lg && lg.log.length) {
    panels.push(h("section", { class: "panel learn-track" }, h("h2", {}, "Recent milestones ", h("span", { class: "sub" }, "· ship's log")),
      h("ul", { class: "plain log" }, ...lg.log.map((e) => h("li", {}, h("span", { class: "dim" }, fmtDate(e.ts)), " ",
        e.kind === "lab_pass" ? `✓ Lab passed · ${e.item_id}` : e.kind === "assessment_pass" ? `✓ Check passed · ${e.item_id}`
          : (() => { const x = (en?.endorsements || []).find((y) => y.id === e.item_id);
              return `◆ Badge · ${x ? `${x.plain} (${x.name})` : e.item_id}`; })())))));
  }
  if (en && en.endorsements.length) {
    const got = en.endorsements.filter((e) => e.awarded_at).length;
    panels.push(h("section", { class: "panel learn-track" }, h("h2", {}, `Badges · ${got} of ${en.endorsements.length} `, h("span", { class: "sub" }, "· endorsements")),
      h("ul", { class: "plain" }, ...en.endorsements.map((e) => h("li", { class: e.awarded_at ? "" : "dim" },
        e.awarded_at ? "◆ " : "◇ ", h("strong", {}, e.plain), h("span", { class: "sub" }, ` · ${e.name}`),
        h("span", { class: "dim" }, e.awarded_at ? ` · ${fmtDate(e.awarded_at)}` : ` · ${e.when}`))))));
  }
  return panels;
}

let reviewState = null;

async function reviewPage() {
  current = null;
  const rv = await fetchJSON("/api/learn/review");
  reviewState = { cards: rv.due, i: 0, shown: false, rv };
  renderReview();
}

function renderReview() {
  const { cards, i, shown, rv } = reviewState;
  const card = cards[i];
  if (!card) {
    mount(head("#/learn", "← Learn", ["Review"]),
      h("div", { class: "panel prose" }, h("p", {}, cards.length ? `Done — ${cards.length} reviewed.` : "Nothing due for review."),
        rv.next_due_at ? h("p", { class: "dim" }, `Next review ${fmtDate(rv.next_due_at)}.`) : null,
        h("p", {}, h("a", { href: "#/learn" }, "Back to Learn →"))));
    refreshChip();
    return;
  }
  const reveal = h("button", { type: "button", class: "btn primary", "data-focus-key": "reveal" }, "Show answer (Space)");
  reveal.addEventListener("click", () => { reviewState.shown = true; renderReview(); });
  const DAYS = { 1: 1, 2: 2, 3: 4, 4: 8, 5: 16 };
  const nb = Math.min(5, card.box + 1);
  const grades = [["again", "1 Again: tomorrow"], ["hard", `2 Hard: box ${card.box}, ${DAYS[card.box]} d`], ["good", `3 Good: box ${nb}, ${DAYS[nb]} d`]]
    .map(([g, label]) => {
      const b = h("button", { type: "button", class: "btn", "data-grade": g }, label);
      b.addEventListener("click", () => gradeCard(g));
      return b;
    });
  mount(
    head("#/learn", "← Learn", [`Review · card ${i + 1} of ${cards.length} · box ${card.box} of 5`]),
    h("div", { class: "panel prose review-card" },
      h("div", { class: "dim" }, card.kind === "live" ? "LIVE-READ CARD" : "TERM",
        card.kind === "live" && !card.live ? h("span", { class: "live stale" }, " · example, not live") : null),
      h("p", { class: "review-prompt" }, card.prompt),
      shown ? h("div", { class: "review-answer", tabindex: "-1" }, h("p", {}, h("strong", {}, card.answer || "")),
        card.detail ? h("p", {}, card.detail) : null,
        card.learn_more && SAFE_HREF.test(card.learn_more) ? h("p", {}, h("a", { href: card.learn_more }, "Learn more →")) : null) : null,
      h("div", { class: "lab-controls" }, ...(shown ? grades : [reveal]))));
  // After reveal, focus the answer (not a grade button), so a second Space can't grade by accident.
  document.querySelector(shown ? ".review-answer" : "[data-focus-key='reveal']")?.focus();
}

async function gradeCard(g) {
  if (!reviewState || reviewState.busy) return;
  const card = reviewState.cards[reviewState.i];
  if (!card) return;
  reviewState.busy = true;
  reviewState.i += 1;  // advance first, so a fast double press can't grade the same card twice
  reviewState.shown = false;
  await send("POST", `/api/learn/review/${encodeURIComponent(card.card_id)}`, { grade: g });
  reviewState.busy = false;
  renderReview();
}

addEventListener("keydown", (ev) => {
  if (!reviewState || !location.hash.startsWith("#/learn/review") || ev.target.closest("input, textarea")) return;
  if (ev.ctrlKey || ev.altKey || ev.metaKey || ev.repeat) return;
  if (ev.key === " " && !reviewState.shown) { ev.preventDefault(); reviewState.shown = true; renderReview(); }
  else if (reviewState.shown && ["1", "2", "3"].includes(ev.key)) gradeCard(["again", "hard", "good"][Number(ev.key) - 1]);
});

// Notes: a panel on lesson and lab pages; "Pin reading" snapshots location-safe values server-side.
function findingMarkdown(note, discipline) {
  const p = note.pinned || {};
  const date = fmtDate(note.created_at).replace(" ", "T");
  const title = note.body.split("\n")[0].slice(0, 80);
  const reading = Object.entries(p).filter(([k, v]) => !k.startsWith("_") && v != null).map(([k, v]) => `- \`${k}\`: ${v}`);
  return [
    "---", `title: ${JSON.stringify(title)}`, `discipline: ${discipline || ""}`, `date: ${date}`, `location: ${p["gps.grid"] || ""}`, "---", "",
    `# Finding: ${title}`, "",
    "- **Frequency / band:**", "- **Mode / modulation:**", "- **Equipment:** Fancy (uConsole CM4, AIO V2)", "- **Software:**", "",
    "## Observation", "", note.body, "", ...(reading.length ? ["Reading pinned in webdash:", "", ...reading, ""] : []),
    "## Identification", "", "- Candidate signal(s):", "- Confidence:", "", "## Conclusion / next steps", "",
  ].join("\n");
}

async function copyText(text, btn) {
  try { await navigator.clipboard.writeText(text); btn.textContent = "Copied"; }
  catch { btn.replaceWith(h("textarea", { class: "paste", rows: "8", readonly: true }, text)); }
}

function noteItem(n, discipline, onChange) {
  const copy = h("button", { type: "button", class: "btn" }, "Copy as finding");
  copy.addEventListener("click", () => copyText(findingMarkdown(n, discipline), copy));
  const del = h("button", { type: "button", class: "btn", "aria-label": `Delete note from ${fmtDate(n.created_at)}` }, "Delete");
  del.addEventListener("click", async () => {
    if (!confirm("Delete this note? This can't be undone.")) return;
    const r = await fetch(`/api/learn/notes/${n.id}`, { method: "DELETE" });
    if (r.ok) onChange();
  });
  return h("li", { class: "note" }, h("div", { class: "dim" }, `${fmtDate(n.created_at)} · ${n.anchor}`),
    h("div", { class: "note-body" }, n.body),
    n.pinned ? h("div", { class: "dim small-pin" }, `Pinned: ${n.pinned["gps.grid"] || "no fix"}, ${n.pinned["aiov2.power_num.power_w"] ?? "?"} W`) : null,
    h("div", { class: "lab-controls" }, copy, del));
}

function notesPanel(anchor, discipline) {
  const list = h("ul", { class: "notes" });
  const ta = h("textarea", { class: "paste", rows: "3", placeholder: "A note for yourself…", "aria-label": "Note" });
  const pinBox = h("input", { type: "checkbox" });
  const save = h("button", { type: "button", class: "btn" }, "Save note");
  async function load() {
    const r = await fetch(`/api/learn/notes?anchor=${encodeURIComponent(anchor)}`);
    const ns = r.ok ? (await r.json()).notes : [];
    list.replaceChildren(...ns.map((n) => noteItem(n, discipline, load)));
  }
  save.addEventListener("click", async () => {
    if (!ta.value.trim()) return;
    await send("POST", "/api/learn/notes", { anchor, body: ta.value.trim(), pin: pinBox.checked });
    ta.value = ""; pinBox.checked = false; load();
  });
  load();
  return h("div", { class: "notes-panel" }, h("h2", {}, "Notes"), ta,
    h("label", { class: "choice small-pin" }, pinBox, " Pin the current reading (grid square, never coordinates)"), save, list);
}

async function notesPage() {
  const seq = navSeq;
  current = null;
  const cat = await loadCatalog();
  const r = await fetch("/api/learn/notes");
  const ns = r.ok ? (await r.json()).notes : [];
  const disc = (anchor) => cat.modules[(anchor || "").split(".")[0]]?.discipline
    || cat.modules[Object.keys(cat.modules).find((m) => cat.modules[m].labs.some((l) => l.id === anchor))]?.discipline;
  mountIf(seq, head("#/learn", "← Learn", ["All notes"]),
    h("div", { class: "panel prose" }, ns.length ? h("ul", { class: "notes" }, ...ns.map((n) => noteItem(n, disc(n.anchor), notesPage)))
      : h("p", { class: "dim" }, "No notes yet. Lessons and labs have a notes panel.")));
}

// ---------------------------------------------------------------------------
// Owner view (S9): content review queue fed by learn-sync, and content health.
// ---------------------------------------------------------------------------

const REASON = { content_changed: "lesson content changed", source_drift: "source doc changed, lesson didn't" };

async function ownerPage() {
  const seq = navSeq;
  current = null;
  const o = await fetchJSON("/api/learn/owner");
  const open = o.review_items.filter((r) => r.state === "open");
  const done = o.review_items.filter((r) => r.state !== "open");
  const row = (r) => {
    const li = h("li", { class: "note" },
      h("div", {}, h("strong", {}, r.module_id), ` · ${REASON[r.reason] || r.reason}`,
        h("span", { class: "dim" }, ` · ${fmtDate(r.created_at)}${r.commit_to ? ` · ${r.commit_to.slice(0, 7)}` : ""}`)),
      r.changed_paths.length ? h("div", { class: "dim" }, r.changed_paths.join(", ")) : null);
    if (r.state === "open") {
      for (const [st, label] of [["accepted", "Still accurate"], ["edited", "Needs an edit"]]) {
        const b = h("button", { type: "button", class: "btn" }, label);
        b.addEventListener("click", async () => {
          await send("POST", `/api/learn/owner/review/${r.id}`, { state: st });
          catalog = null; cache.clear(); ownerPage();
        });
        li.append(" ", b);
      }
    } else li.append(h("div", { class: "dim" }, `resolved: ${r.state}`));
    return li;
  };
  mountIf(seq, head("#/learn", "← Learn", ["Owner view"]),
    h("section", { class: "panel prose" }, h("h2", {}, `Content review · ${open.length} open`),
      open.length ? h("ul", { class: "notes" }, ...open.map(row))
        : h("p", { class: "dim" }, "Nothing to review. learn-sync flags a module here when its sources change on main."),
      done.length ? h("details", {}, h("summary", {}, `Resolved (${done.length})`), h("ul", { class: "notes" }, ...done.map(row))) : null),
    h("section", { class: "panel prose" }, h("h2", {}, "Content health"),
      h("p", { class: "dim" }, "Every status field a lab checks, and whether the collectors report it right now. " +
        "Not reported can be normal (readsb stopped); never reported is a data gap."),
      h("div", { class: "table-wrap" }, h("table", {},
        h("thead", {}, h("tr", {}, h("th", {}, "Field"), h("th", {}, "Now"), h("th", {}, "Used by"))),
        h("tbody", {}, ...o.health.map((x) => h("tr", {}, h("td", {}, h("code", {}, x.path)),
          h("td", { class: x.reported ? "" : "dim" }, x.reported ? "✓ reported" : "— not reported"), h("td", {}, x.labs.join(", ")))))))),
    h("section", { class: "panel prose" }, h("h2", {}, "Bundle"),
      h("p", {}, `${o.meta?.bundle_sha || "none"} · from ${o.meta?.source || "?"}` + (o.meta?.commit ? ` @ ${o.meta.commit.slice(0, 7)}` : "")),
      o.bundle_error ? h("p", { class: "error" }, o.bundle_error) : null,
      h("pre", { class: "cmd" }, "python3 webdash/host-helpers/learn-sync.py --force   # recompile main now")));
}

function driftBanner(m) {
  if (!m?.open_review?.length) return null;
  return h("div", { class: "callout warn" }, h("p", {},
    m.open_review.includes("source_drift")
      ? "Source material changed since this module was last reviewed. Check any fact you rely on against the linked source; the owner has it flagged for review."
      : "This module was updated since it was last reviewed."));
}

// ---------------------------------------------------------------------------
// Links from the stations into learning: a brass module link on each tile and view head, and ⓘ
// on fact labels that have a glossary entry.
// ---------------------------------------------------------------------------

const STATION_MODULE = { mesh: "M4", gps: "M3", sdr: "M6", wifi: "M7", power: "M1", system: "M1b" };
const FACT_GLOSSARY = {
  "Aircraft tracked": "aircraft-count", "With position": "with-position", "Fix": "fix-mode",
  "Grid": "grid-square", "Grid square": "grid-square", "Satellites": "satellites-used",
  "Satellites (used/seen)": "satellites-used", "Nodes seen (incl. this one)": "nodes-seen",
  "Source": "power-source", "Voltage": "cell-voltage", "Capacity": "charge-capacity",
};

export async function decorateStations() {
  let cat, gloss;
  try { [cat, gloss] = await Promise.all([loadCatalog(), getJSON("/api/learn/glossary")]); } catch { return; }
  if (cat.state !== "ok") return;
  for (const [label, id] of Object.entries(FACT_GLOSSARY)) {
    if (gloss[id]) GLOSS_LINKS[label] = { id, tooltip: gloss[id].tooltip };
  }
  for (const [st, mid] of Object.entries(STATION_MODULE)) {
    const m = cat.modules[mid];
    if (!m) continue;
    const link = () => h("a", { class: "learn-link", href: `#/learn/m/${mid}`, title: `Learn: ${m.title}` }, `◆ ${mid}`);
    document.querySelector(`#tile-${st}-title`)?.closest(".tile")?.querySelector(".tile-foot")?.prepend(link());
    document.querySelector(`.view[data-view="${st}"] .view-head`)?.append(link());
  }
}

// ---------------------------------------------------------------------------
// Search ("/"): modules, lessons, labs, checks and glossary terms, client-side.
// ---------------------------------------------------------------------------

async function searchPage(q) {
  const seq = navSeq;
  const cat = await loadCatalog();
  const gloss = await getJSON("/api/learn/glossary");
  const input = h("input", { type: "search", class: "search-in", value: q, placeholder: "Search lessons, labs and terms", "aria-label": "Search" });
  const results = h("div", { "aria-live": "polite" });
  const run = () => {
    const t = input.value.trim().toLowerCase();
    const hits = [];
    if (t.length >= 2) {
      for (const [mid, m] of Object.entries(cat.modules)) {
        if (`${mid} ${m.title}`.toLowerCase().includes(t)) hits.push(["Module", `${mid} ${m.title}`, `#/learn/m/${mid}`]);
        for (const l of m.lessons) if (l.title.toLowerCase().includes(t)) hits.push(["Lesson", `${mid} · ${l.title}`, `#/learn/l/${l.id}`]);
        for (const x of m.labs) if (`${x.id} ${x.title}`.toLowerCase().includes(t)) hits.push(["Lab", `${x.id} ${x.title}`, `#/learn/lab/${x.id}`]);
      }
      for (const g of Object.values(gloss)) {
        if (`${g.term} ${g.tooltip}`.toLowerCase().includes(t)) hits.push(["Term", g.term, `#/learn/glossary/${g.id}`]);
      }
    }
    results.replaceChildren(t.length < 2 ? h("p", { class: "dim" }, "Type at least two letters.")
      : hits.length ? h("ul", { class: "plain" }, ...hits.slice(0, 40).map(([k, t2, href]) =>
          h("li", {}, h("span", { class: "dim" }, `${k} · `), h("a", { href }, t2))))
        : h("p", { class: "dim" }, "Nothing matches. Try a shorter word, or browse the glossary."));
  };
  input.addEventListener("input", run);
  input.addEventListener("keydown", (ev) => {
    if (ev.key === "Enter") { const a = results.querySelector("a"); if (a) location.hash = a.getAttribute("href"); }
  });
  mountIf(seq, head("#/learn", "← Learn", ["Search"]), h("div", { class: "panel prose" }, input, results));
  run();
  input.focus();
}

// Keys on learning pages: "/" search, "r" review, "n" notes, "]" hide or show the side panel.
addEventListener("keydown", (ev) => {
  if (!location.hash.startsWith("#/learn") || ev.ctrlKey || ev.altKey || ev.metaKey) return;
  if (ev.target.closest("input, textarea, select, [contenteditable]")) return;
  if (ev.key === "/") { ev.preventDefault(); location.hash = "#/learn/search"; }
  else if (ev.key === "r" && !location.hash.startsWith("#/learn/review")) location.hash = "#/learn/review";
  else if (ev.key === "n") {
    const ta = document.querySelector("#learn-root .notes-panel textarea");
    if (ta) { ev.preventDefault(); ta.focus(); }
  } else if (ev.key === "]") document.body.classList.toggle("dock-hidden");
});

// Phone: the side panel is a bottom sheet; its heading toggles it open and closed.
function sheetToggle(panel) {
  const btn = h("button", { type: "button", class: "sheet-handle", "aria-expanded": "false" }, "Live on Fancy ▴");
  btn.addEventListener("click", () => {
    const open = panel.classList.toggle("sheet-open");
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.textContent = open ? "Live on Fancy ▾" : "Live on Fancy ▴";
  });
  return btn;
}

export async function renderLearn(sub, status) {
  if (status) lastStatus = status;
  ++navSeq;
  const [kind, ...rest] = (sub || "").split("/");
  const arg = decodeURIComponent(rest.join("/"));
  if (kind !== "lab") labOpen = null;
  if (kind !== "review") reviewState = null;
  try {
    if (!kind) await home();
    else if (kind === "m") await modulePage(arg);
    else if (kind === "l") await lessonPage(arg);
    else if (kind === "glossary") {
      await glossaryPage(arg);
      if (arg) document.getElementById(`g-${arg}`)?.scrollIntoView({ block: "start" });
    }
    else if (kind === "lab") await labPage(arg);
    else if (kind === "quiz") await quizPage(arg);
    else if (kind === "review") await reviewPage();
    else if (kind === "notes") await notesPage();
    else if (kind === "owner") await ownerPage();
    else if (kind === "search") await searchPage(arg);
    else await home();
  } catch (err) {
    fail(err);
  }
}

// Last chance to deliver queued events when the tab is hidden or closed.
document.addEventListener("visibilitychange", () => {
  if (document.visibilityState === "hidden" && events.length) {
    navigator.sendBeacon("/api/learn/events", new Blob([JSON.stringify({ events })], { type: "application/json" }));
    events = [];
  }
});
