// SDR broadcast/airband hunt + listen (SDR view). Receive-only. The hunt is a one-shot rtl_power
// sweep on the host (ADS-B paused during it); listen streams rtl_fm -> ffmpeg MP3 into an <audio>
// element. One tuner, so the host bridge serializes hunt vs listen.

import { railOn, h } from "./ui.js";

let polling = null;
let listening = false;
let scanPoll = null;    // polls /api/sdr/scan/status to show which channel the scanner is on
let lastStatus = null;  // most recent status snapshot (rail state, GPS for the NOAA auto-pick)
let lastAirbandFreqs = [];  // freqs from the most recent airband hunt, fed to the scanner
// Which application holds the single tuner, from the bridge's own record (GET /api/sdr/hunt/status
// -> busy: adsb | hunt | listen | scan | null). ok is false until the bridge has answered.
let tuner = { ok: false, err: false, busy: null, adsbActive: false, owrxActive: false };
let huntSeq = 0;        // orders /hunt/status answers, so an older one never overwrites a newer one
let tunerPoll = null;
let listenHz = null;    // the channel this page is listening to, for the banner (null: scanner)
let lastSweepStamp = null;  // dedupe waterfall rows: one row per completed sweep (state.updated)
let waterfall = [];         // recent sweeps, each resampled to the canvas width; newest last
let waterfallBand = null;   // the waterfall resets when the band changes

function audio() { return document.getElementById("sdr-audio"); }

// --- GPS-coupled NOAA channel selection (static station table, no internet egress) ----------
// nwr-stations.json is a one-time authoring-time capture of the NWS NWR transmitter list bundled
// into the image (see app/static/data/README.md); nothing here fetches NWR data at runtime.
let nwrStations = null;   // loaded once from the bundled static JSON
let noaaAuto = true;      // auto-pick by GPS until the operator picks a channel manually

async function loadNwr() {
  try {
    const r = await fetch("/static/data/nwr-stations.json");
    if (r.ok) nwrStations = await r.json();
  } catch { /* stays null; the manual dropdown still works */ }
}

function haversineKm(la1, lo1, la2, lo2) {
  const R = 6371, p = Math.PI / 180;
  const dLa = (la2 - la1) * p, dLo = (lo2 - lo1) * p;
  const a = Math.sin(dLa / 2) ** 2 + Math.cos(la1 * p) * Math.cos(la2 * p) * Math.sin(dLo / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

// Predicted-strongest local transmitter: maximise power / distance^2 (a free-space received-power
// proxy). Beats nearest-by-distance — a closer low-power site can be weaker than a farther
// high-power one (confirmed on-air 2026-10-03 with Fancy at grid FM03, from its own GPS fix: 162.400
// KEC95 1000W@40km beats 162.500 WNG628 300W@33km). Fancy travels; other days' fixes are elsewhere.
function bestNwr(lat, lon) {
  let best = null, bestScore = -1;
  for (const s of nwrStations) {
    const d = Math.max(haversineKm(lat, lon, s.lat, s.lon), 1);
    const score = (s.pw || 300) / (d * d);
    if (score > bestScore) { bestScore = score; best = { ...s, d }; }
  }
  return best;
}

// Auto-set the NOAA dropdown to the GPS-predicted-strongest station, with a caption. Stops as soon
// as the operator changes the dropdown (noaaAuto=false), with a "↻ use GPS" affordance to resume.
function applyNoaaAuto(gps) {
  const sel = document.getElementById("sdr-noaa");
  const cap = document.getElementById("sdr-noaa-auto");
  if (!sel || !cap) return;
  if (!noaaAuto) {
    cap.innerHTML = 'manual · <button type="button" class="linkbtn" id="noaa-reauto">↻ use GPS</button>';
    return;
  }
  if (!nwrStations) { cap.textContent = ""; return; }
  if (!gps || gps.lat == null || gps.lon == null) { cap.textContent = "waiting for GPS fix…"; return; }
  const b = bestNwr(gps.lat, gps.lon);
  if (!b) { cap.textContent = ""; return; }
  if ([...sel.options].some((o) => +o.value === b.freq_hz)) sel.value = String(b.freq_hz);
  cap.textContent = `GPS → ${b.call} ${(b.freq_hz / 1e6).toFixed(3)} (${b.site}, ${b.st} · ${Math.round(b.d)} km · ${b.pw}W)`;
}

// --- The tuner banner and each tab's "why can't I" line ----------------------------------------
// One line above the tabs names the application holding the tuner, from the bridge's record, so it
// never says "free" while something holds it. A hunt is a power *sweep*; the airband *scanner*
// cycles channels while listening (two different things, two different words).
function setText(id, text) {
  const el = document.getElementById(id);
  if (el && el.textContent !== text) el.textContent = text;
}

function tunerText() {
  if (railOn(lastStatus && lastStatus.aiov2, "SDR") === false) return "Tuner: unpowered (SDR rail off)";
  if (!tuner.ok) return tuner.err ? "Tuner: unknown (SDR bridge not answering)" : "Tuner: checking…";
  // readsb started outside the bridge's record (a bridge restart, sdr-swap.sh) still holds the
  // tuner; the bridge stops it itself before a hunt or listen, so this changes the words only.
  const busy = tuner.busy || (tuner.adsbActive || (lastStatus && lastStatus.adsb && lastStatus.adsb.state === "running") ? "adsb" : null);
  switch (busy) {
    case "adsb": return "Tuner: ADS-B (decoding)";
    case "hunt": return "Tuner: Hunt (sweeping)";
    case "listen": return listening && listenHz ? `Tuner: Listening ${(listenHz / 1e6).toFixed(3)} MHz` : "Tuner: Listening";
    case "scan": return "Tuner: Scanning airband";
    case "owrx": return "Tuner: OpenWebRX (receiver)";
    default: return "Tuner: free";
  }
}

// The bridge's rules (sdr-bridge.py): a sweep needs a free tuner; a listen takes over from another
// listen or the scanner but not from ADS-B or a sweep; ADS-B needs a free tuner.
const HOLDER = { adsb: "ADS-B", hunt: "a sweep", listen: "Listen", scan: "the airband scanner", owrx: "OpenWebRX" };
const TAB_OF = { adsb: "ADS-B", hunt: "Hunt", listen: "Listen", scan: "Listen", owrx: "Receiver" };

function blockedBy(app) {
  const b = tuner.ok ? tuner.busy : null;
  const held = listening ? "listen" : polling != null ? "hunt" : b;
  if (!held || held === app) return null;
  if (app === "listen" && (held === "listen" || held === "scan")) return null;
  return held;
}

function blockText(holder, verb) {
  return holder === "hunt" ? `A sweep is running on the Hunt tab; ${verb} when it finishes.`
    : `The tuner is in use by ${HOLDER[holder]}: stop it on the ${TAB_OF[holder]} tab to ${verb}.`;
}

function updateTuner() {
  setText("sdr-tuner", tunerText());
  const adsbRunning = lastStatus && lastStatus.adsb && lastStatus.adsb.state === "running";
  const forAdsb = adsbRunning ? null : blockedBy("adsb");
  const forHunt = blockedBy("hunt");
  const forListen = blockedBy("listen");
  setText("adsb-block", forAdsb ? blockText(forAdsb, "start ADS-B") : "");
  // A sweep this page didn't start (another browser) still holds the tuner.
  const otherSweep = !forHunt && polling == null && tuner.ok && tuner.busy === "hunt";
  setText("sdr-hunt-block", forHunt ? blockText(forHunt, "sweep") : otherSweep ? "A sweep is already running." : "");
  setText("sdr-listen-block", forListen ? blockText(forListen, "listen") : "");
  const start = document.getElementById("adsb-start");
  if (start) start.disabled = !!forAdsb || (tuner.ok && tuner.busy === "adsb");  // already starting
  const sweep = document.getElementById("sdr-scan");
  if (sweep && polling == null) sweep.disabled = !!forHunt || otherSweep;
  for (const b of document.querySelectorAll("#sdr-noaa-listen, #sdr-scan-listen, .sdr-play")) b.disabled = !!forListen;

  // Receiver (OpenWebRX): running state is the bridge's busy=="owrx" or the container reading as up
  // (started out-of-band). Start/stop mirror ADS-B; the "Open ↗" link and note show while it runs.
  const owrxRunning = tuner.ok && (tuner.busy === "owrx" || tuner.owrxActive);
  const forOwrx = owrxRunning ? null : blockedBy("owrx");
  // The bridge refuses a start with the USB rail on (a start like that preceded a power cut,
  // 2026-10-15); say so here rather than after the click. null (unknown) is left to the bridge.
  const usbOn = !owrxRunning && railOn(lastStatus && lastStatus.aiov2, "USB") === true;
  setText("sdr-owrx-block", forOwrx ? blockText(forOwrx, "start the receiver")
    : usbOn ? "The USB rail is on: turn it off (Overview, or aiov2_ctl USB off) to start the receiver." : "");
  const owrxStart = document.getElementById("owrx-start");
  const owrxStop = document.getElementById("owrx-stop");
  if (owrxStart) { owrxStart.style.display = owrxRunning ? "none" : ""; owrxStart.disabled = !!forOwrx || usbOn; }
  if (owrxStop) owrxStop.style.display = owrxRunning ? "" : "none";
  const owrxLink = document.getElementById("owrx-link");
  if (owrxLink) owrxLink.style.display = owrxRunning ? "" : "none";
  setText("owrx-note", owrxRunning
    ? "Receiver running — open it in a new tab. The first visit asks for the OpenWebRX login."
    : "");
}

function noteTuner(s) {
  tuner = s && "busy" in s
    ? { ok: true, err: false, busy: s.busy || null, adsbActive: !!s.adsb_active, owrxActive: !!s.owrx_active }
    : { ok: false, err: true, busy: null, adsbActive: false, owrxActive: false };
  updateTuner();
}

// Poll the tuner holder only while the SDR view is open (main.js starts and stops this). It's the
// same endpoint as a running sweep's 2 s poll, so it stands down while that runs.
export function startTunerPoll() {
  if (tunerPoll) return;
  pollHunt();
  tunerPoll = setInterval(() => { if (polling == null) pollHunt(); }, 3000);
}
export function stopTunerPoll() {
  if (tunerPoll) clearInterval(tunerPoll);
  tunerPoll = null;
}

// --- ADS-B (readsb) as a chosen application -------------------------------------------------
// readsb is systemctl-disabled on this build, so the SDR rail coming on no longer starts it.
// These controls start/stop it on demand; the host bridge makes it mutually exclusive with
// hunt/listen on the single tuner. Running state is read from the shared status snapshot.
async function setAdsb(action) {
  const errEl = document.getElementById("adsb-error");
  if (errEl) errEl.textContent = "";
  for (const id of ["adsb-start", "adsb-stop"]) {
    const b = document.getElementById(id);
    if (b) b.disabled = true;
  }
  try {
    const resp = await fetch("/api/sdr/adsb", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) { if (errEl) errEl.textContent = data.error || `HTTP ${resp.status}`; }
  } catch (err) { if (errEl) errEl.textContent = String(err); }
  // The next status tick shows the right button via syncSdr(); the banner updates now.
  pollHunt();
}

// OpenWebRX as a chosen application. Start/stop goes through the bridge, which runs the container
// and claims the single tuner; starting it can take a few seconds (docker compose up on first run),
// so the buttons disable for the round-trip. The running state comes back on the next tuner poll.
async function setOwrx(action) {
  const errEl = document.getElementById("owrx-error");
  if (errEl) errEl.textContent = "";
  for (const id of ["owrx-start", "owrx-stop"]) {
    const b = document.getElementById(id);
    if (b) b.disabled = true;
  }
  try {
    const resp = await fetch("/api/sdr/owrx", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) { if (errEl) errEl.textContent = data.error || `HTTP ${resp.status}`; }
  } catch (err) { if (errEl) errEl.textContent = String(err); }
  pollHunt();
}

// Which ADS-B button shows comes from the shared status snapshot; whether it's blocked, from the
// tuner holder (updateTuner).
// Keep the snapshot current while the SDR view is hidden, for local actions and the NOAA auto-pick.
export function cacheSdr(data) { lastStatus = data; }

export function syncSdr(data) {
  cacheSdr(data);
  const running = data && data.adsb && data.adsb.state === "running";
  const start = document.getElementById("adsb-start");
  const stop = document.getElementById("adsb-stop");
  if (start) start.style.display = running ? "none" : "";
  if (stop) { stop.style.display = running ? "" : "none"; stop.disabled = false; }
  updateTuner();
  applyNoaaAuto(data && data.gps);
}

function renderStations(stations, band) {
  const body = document.getElementById("sdr-list-body");
  if (!body) return;
  if (!stations || !stations.length) {
    body.replaceChildren(h("tr", {}, h("td", { colspan: "4", class: "dim" }, "No signals found.")));
    return;
  }
  const mode = band === "airband" ? "am" : "wbfm";
  const digits = band === "airband" ? 3 : 1;
  // rtl_power emits these fields; power_db/snr_db are numbers off the host collector, so build the
  // row with h() (textContent children, no innerHTML) rather than interpolating into markup.
  body.replaceChildren(...stations.map((s) => {
    const label = `${s.freq_mhz.toFixed(digits)} MHz`;
    return h("tr", {},
      h("td", { class: "mono" }, label),
      h("td", {}, `${s.power_db} dB`),
      h("td", {}, `${s.snr_db} dB`),
      h("td", {}, h("button", {
        type: "button", class: "btn sdr-play", "data-mode": mode,
        "data-freq": s.freq_hz, "data-label": label,
      }, "▶ Listen")),
    );
  }));
}

// --- spectrum graph + waterfall (the sweep bins the bridge now returns as s.trace) -------------
// Draws the whole swept band, not just the peaks: a power-vs-frequency trace with the median noise
// floor and the +6 dB detection threshold the station finder uses, and a waterfall that stacks
// each sweep you run (newest on top). Receive-only display of the same one-shot sweep the table
// summarises. Theme-aware: colours come from the CSS custom properties, so skins carry through.
function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}
function toRgb(str) {
  str = (str || "").trim();
  if (str.startsWith("#")) {
    let h = str.slice(1);
    if (h.length === 3) h = h.split("").map((c) => c + c).join("");
    const n = parseInt(h, 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }
  const m = str.match(/\d+(\.\d+)?/g);
  return m && m.length >= 3 ? [+m[0], +m[1], +m[2]] : [34, 197, 94];
}

// Resample the (freq, dB) bins to `w` evenly-spaced columns by max-pooling, so a narrow station
// never falls between columns and vanishes; empty columns hold the nearest neighbour's value.
function resample(points, lo, hi, w) {
  const cols = new Float32Array(w).fill(NaN);
  const span = Math.max(hi - lo, 1);
  for (const [f, db] of points) {
    let x = Math.floor(((f - lo) / span) * (w - 1));
    if (x < 0) x = 0; else if (x >= w) x = w - 1;
    if (Number.isNaN(cols[x]) || db > cols[x]) cols[x] = db;
  }
  let last = cols.find((v) => !Number.isNaN(v));
  if (last === undefined) last = 0;
  for (let i = 0; i < w; i++) { if (Number.isNaN(cols[i])) cols[i] = last; else last = cols[i]; }
  return cols;
}

function drawSpectrum(trace, band, stations) {
  const cv = document.getElementById("sdr-spectrum");
  if (!cv || !cv.getContext) return;
  const ctx = cv.getContext("2d");
  const W = cv.width, H = cv.height;
  const cols = resample(trace.points, trace.lo_hz, trace.hi_hz, W);
  let lo = trace.floor_db, hi = trace.floor_db;
  for (const v of cols) { if (v < lo) lo = v; if (v > hi) hi = v; }
  const pad = Math.max(2, (hi - lo) * 0.08);
  const top = hi + pad, bot = lo - pad;
  const y = (db) => H - ((db - bot) / Math.max(top - bot, 1)) * H;

  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = cssVar("--panel-2"); ctx.fillRect(0, 0, W, H);
  ctx.font = "10px monospace";

  // noise floor and the +6 dB detection threshold, as dashed reference lines
  ctx.setLineDash([3, 3]); ctx.lineWidth = 1;
  for (const [db, tok, label] of [[trace.floor_db, "--dim", "floor"], [trace.threshold_db, "--warn", "+6 dB"]]) {
    const yy = y(db);
    if (yy > 8 && yy < H) {
      const c = cssVar(tok);
      ctx.strokeStyle = c; ctx.beginPath(); ctx.moveTo(0, yy); ctx.lineTo(W, yy); ctx.stroke();
      ctx.fillStyle = c; ctx.textBaseline = "bottom"; ctx.fillText(label, 2, yy - 1);
    }
  }
  ctx.setLineDash([]);

  // the trace itself
  ctx.strokeStyle = cssVar("--accent"); ctx.lineWidth = 1.2; ctx.beginPath();
  for (let i = 0; i < W; i++) { const yy = y(cols[i]); if (i === 0) ctx.moveTo(i, yy); else ctx.lineTo(i, yy); }
  ctx.stroke();

  // the strongest peaks, marked and labelled (the table carries the full list)
  const span = Math.max(trace.hi_hz - trace.lo_hz, 1);
  for (const s of (stations || []).slice(0, 4)) {
    const x = Math.round(((s.freq_hz - trace.lo_hz) / span) * (W - 1));
    const yy = Math.max(y(s.power_db), 4);
    ctx.fillStyle = cssVar("--ok"); ctx.beginPath(); ctx.arc(x, yy, 2.5, 0, Math.PI * 2); ctx.fill();
    const lbl = s.freq_mhz.toFixed(band === "airband" ? 3 : 1);
    const tw = ctx.measureText(lbl).width;
    const tx = Math.max(1, Math.min(x - tw / 2, W - tw - 1));
    ctx.fillStyle = cssVar("--fg"); ctx.textBaseline = "top"; ctx.fillText(lbl, tx, yy + 4);
  }

  // band edges
  ctx.fillStyle = cssVar("--dim"); ctx.textBaseline = "bottom";
  ctx.fillText((trace.lo_hz / 1e6).toFixed(0), 2, H - 1);
  const hiLbl = (trace.hi_hz / 1e6).toFixed(0) + " MHz";
  ctx.fillText(hiLbl, W - ctx.measureText(hiLbl).width - 2, H - 1);
}

function drawWaterfall() {
  const cv = document.getElementById("sdr-waterfall");
  if (!cv || !cv.getContext) return;
  const ctx = cv.getContext("2d");
  const W = cv.width, H = cv.height;
  const [pr, pg, pb] = toRgb(cssVar("--panel-2"));
  const [r, g, b] = toRgb(cssVar("--accent"));
  const img = ctx.createImageData(W, H);
  for (let i = 0; i < img.data.length; i += 4) { img.data[i] = pr; img.data[i + 1] = pg; img.data[i + 2] = pb; img.data[i + 3] = 255; }
  for (let row = 0; row < waterfall.length && row < H; row++) {
    const cols = waterfall[waterfall.length - 1 - row];   // newest at the top
    let lo = Infinity, hi = -Infinity;
    for (const v of cols) { if (v < lo) lo = v; if (v > hi) hi = v; }
    const rng = Math.max(hi - lo, 1);
    for (let x = 0; x < W && x < cols.length; x++) {
      const a = Math.max(0, Math.min(1, (cols[x] - lo) / rng));
      const o = (row * W + x) * 4;
      img.data[o] = Math.round(pr + (r - pr) * a);
      img.data[o + 1] = Math.round(pg + (g - pg) * a);
      img.data[o + 2] = Math.round(pb + (b - pb) * a);
    }
  }
  ctx.putImageData(img, 0, 0);
}

// Show the graph for a completed sweep. Called on every poll while the state stays "done", so the
// trace is repainted (handles reopening the tab) but a waterfall row is added only once per sweep,
// keyed on the state's `updated` stamp.
function renderSpectrum(s) {
  const fig = document.getElementById("sdr-spectrum-fig");
  const trace = s.trace;
  if (!trace || !trace.points || !trace.points.length) { if (fig) fig.hidden = true; return; }
  if (fig) fig.hidden = false;
  const cv = document.getElementById("sdr-waterfall");
  const wfW = cv ? cv.width : 600;
  if (s.stage === "done" && s.updated !== lastSweepStamp) {
    if (s.band !== waterfallBand) { waterfall = []; waterfallBand = s.band; }
    waterfall.push(resample(trace.points, trace.lo_hz, trace.hi_hz, wfW));
    if (waterfall.length > (cv ? cv.height : 70)) waterfall.shift();
    lastSweepStamp = s.updated;
  }
  drawSpectrum(trace, s.band, s.stations || []);
  drawWaterfall();
  const cap = document.getElementById("sdr-spectrum-cap");
  if (cap) {
    cap.textContent = `${(trace.lo_hz / 1e6).toFixed(1)}–${(trace.hi_hz / 1e6).toFixed(1)} MHz · `
      + `floor ${trace.floor_db} dB · ${(s.stations || []).length} peak(s)`
      + (waterfall.length > 1 ? ` · ${waterfall.length} sweeps, newest on top` : "");
  }
}

function renderHunt(s) {
  const statusEl = document.getElementById("sdr-hunt-status");
  const btn = document.getElementById("sdr-scan");
  const stage = s.stage || "idle";
  const running = !!s.running && stage !== "done" && stage !== "error" && stage !== "unavailable";
  if (statusEl) {
    statusEl.className = "sdr-hunt-status" + (stage === "error" ? " err" : stage === "done" ? " ok" : "");
    statusEl.textContent = stage === "idle" ? "" : `${stage}${s.message ? " — " + s.message : ""}`;
  }
  // A sweep is a power survey of the band ("Sweep"), not the airband scanner ("Scan airband").
  if (btn) { btn.textContent = running ? "Sweeping…" : "Sweep"; if (running) btn.disabled = true; }
  if (stage === "done" || (!running && s.stations)) renderStations(s.stations, s.band);
  renderSpectrum(s);
  // Remember the airband channels a sweep found, so "Scan airband" can cycle just the live ones.
  if (s.band === "airband" && Array.isArray(s.stations)) {
    lastAirbandFreqs = s.stations.map((st) => st.freq_hz).filter(Boolean);
  }
  return running;
}

// One request feeds both the hunt panel and the tuner line. A sweep found running (after a reload,
// or started from another browser) gets the 2 s poll too, so its results appear when it ends.
async function pollHunt() {
  const seq = ++huntSeq;
  let s = null;
  try {
    const resp = await fetch("/api/sdr/hunt/status");
    if (resp.ok) s = await resp.json();
  } catch { /* bridge not answering: noteTuner(null) says so */ }
  if (seq !== huntSeq) return;  // a newer answer is on its way
  const running = s ? renderHunt(s) : false;
  if (running && polling == null) polling = setInterval(pollHunt, 2000);
  else if (!running && polling != null) { clearInterval(polling); polling = null; }
  noteTuner(s);
}

async function scan() {
  const errEl = document.getElementById("sdr-hunt-error");
  if (errEl) errEl.textContent = "";
  const band = document.getElementById("sdr-band").value;
  document.getElementById("sdr-scan").disabled = true;
  try {
    const resp = await fetch("/api/sdr/hunt", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ band }),
    });
    const data = await resp.json().catch(() => ({}));
    if (!resp.ok || !data.ok) { if (errEl) errEl.textContent = data.error || `HTTP ${resp.status}`; }
  } catch (err) { if (errEl) errEl.textContent = String(err); }
  if (!polling) polling = setInterval(pollHunt, 2000);
  pollHunt();
}

// --- listen ---------------------------------------------------------------------------------
function setPlaying(label) {
  listening = !!label;
  if (!label && scanPoll) { clearInterval(scanPoll); scanPoll = null; }  // stopped: end scan polling
  document.getElementById("sdr-stop").style.display = label ? "" : "none";
  document.getElementById("sdr-now").textContent = label ? `♪ ${label}` : "";
  if (!label) listenHz = null;
  updateTuner();
  pollHunt();
}

// Airband scanner: cycle the live airband channels (from the last airband hunt) or the whole
// 118–137 MHz range, pausing on any that breaks squelch. rtl_fm does the scan/pause/resume; this
// just opens the stream into the same <audio> as a single listen, so Stop ends it the same way.
function scanAirband() {
  const errEl = document.getElementById("sdr-listen-error");
  if (errEl) errEl.textContent = "";
  const sq = Math.max(1, Math.min(2000, parseInt(document.getElementById("sdr-squelch")?.value, 10) || 150));
  const useFound = lastAirbandFreqs.length > 0;
  const scan = useFound ? lastAirbandFreqs.join(",") : "airband";
  const label = useFound ? `Scanning ${lastAirbandFreqs.length} airband ch (sq ${sq})`
                         : `Scanning airband 118–137 (sq ${sq})`;
  const a = audio();
  if (listening) stopListen();
  listenHz = null;
  a.src = `/api/sdr/listen?scan=${encodeURIComponent(scan)}&squelch=${sq}`;
  a.play().then(() => {
    setPlaying(label);
    if (scanPoll) clearInterval(scanPoll);
    scanPoll = setInterval(pollScanStatus, 800);
    pollScanStatus();
  }).catch(() => {
    if (errEl) errEl.textContent = "couldn't start scan (SDR busy, or rail off?)";
    setPlaying(null);
  });
}

// While scanning, show which channel the bridge is parked on (traffic) or that it's still sweeping.
async function pollScanStatus() {
  if (!listening) { if (scanPoll) { clearInterval(scanPoll); scanPoll = null; } return; }
  let s = {};
  try { s = await (await fetch("/api/sdr/scan/status")).json(); } catch { return; }
  const now = document.getElementById("sdr-now");
  if (!now) return;
  if (s.active) {
    now.textContent = `▶ ${(s.active / 1e6).toFixed(3)} MHz — traffic`;
  } else {
    const n = (s.channels && s.channels.length) || 0;
    now.textContent = s.stage === "sweeping" ? "Sweeping airband for channels…"
      : n ? `Scanning ${n} channels…` : "Scanning…";
  }
}

function stopListen() {
  const a = audio();
  a.pause();
  a.removeAttribute("src");
  a.load();  // tears down the connection -> bridge restores readsb
  setPlaying(null);
}

function listen(mode, freq, label) {
  const errEl = document.getElementById("sdr-listen-error");
  if (errEl) errEl.textContent = "";
  const a = audio();
  if (listening) stopListen();
  listenHz = Number(freq) || null;
  a.src = `/api/sdr/listen?mode=${encodeURIComponent(mode)}&freq=${encodeURIComponent(freq)}`;
  a.play().then(() => setPlaying(label)).catch(() => {
    if (errEl) errEl.textContent = "couldn't start audio (SDR busy, or rail off?)";
    setPlaying(null);
  });
}

export function initSdr() {
  const scanBtn = document.getElementById("sdr-scan");
  if (!scanBtn) return;
  scanBtn.addEventListener("click", scan);

  document.getElementById("adsb-start")?.addEventListener("click", () => setAdsb("start"));
  document.getElementById("adsb-stop")?.addEventListener("click", () => setAdsb("stop"));

  document.getElementById("owrx-start")?.addEventListener("click", () => setOwrx("start"));
  document.getElementById("owrx-stop")?.addEventListener("click", () => setOwrx("stop"));

  document.getElementById("sdr-list-body").addEventListener("click", (ev) => {
    const b = ev.target.closest(".sdr-play");
    if (b) listen(b.dataset.mode, b.dataset.freq, b.dataset.label);
  });
  document.getElementById("sdr-noaa-listen").addEventListener("click", () => {
    const sel = document.getElementById("sdr-noaa");
    listen("nfm", sel.value, `NOAA ${(sel.value / 1e6).toFixed(3)} MHz`);
  });
  // A manual channel pick switches off GPS auto-selection; the caption offers "↻ use GPS" to resume.
  document.getElementById("sdr-noaa")?.addEventListener("change", () => {
    noaaAuto = false;
    applyNoaaAuto(lastStatus && lastStatus.gps);
  });
  document.getElementById("sdr-noaa-auto")?.addEventListener("click", (ev) => {
    if (ev.target.closest("#noaa-reauto")) {
      noaaAuto = true;
      applyNoaaAuto(lastStatus && lastStatus.gps);
    }
  });
  loadNwr().then(() => applyNoaaAuto(lastStatus && lastStatus.gps));
  document.getElementById("sdr-scan-listen")?.addEventListener("click", scanAirband);
  document.getElementById("sdr-stop").addEventListener("click", stopListen);
  audio().addEventListener("error", () => {
    const errEl = document.getElementById("sdr-listen-error");
    if (listening && errEl) errEl.textContent = "audio stream ended (SDR busy, rail off, or no signal?)";
    setPlaying(null);
  });

  pollHunt();  // reflect an in-flight scan if the page was reloaded
}
