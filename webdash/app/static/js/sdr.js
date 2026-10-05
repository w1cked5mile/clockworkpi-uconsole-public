// SDR broadcast/airband hunt + listen (SDR view). Receive-only. The hunt is a one-shot rtl_power
// sweep on the host (ADS-B paused during it); listen streams rtl_fm -> ffmpeg MP3 into an <audio>
// element. One tuner, so the host bridge serializes hunt vs listen.

import { railOn } from "./ui.js";

let polling = null;
let listening = false;
let scanPoll = null;    // polls /api/sdr/scan/status to show which channel the scanner is on
let lastStatus = null;  // most recent status snapshot, so local actions can refresh the title now
let lastAirbandFreqs = [];  // freqs from the most recent airband hunt, fed to the scanner

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
// high-power one (confirmed on-air at FM03: 162.400 KEC95 1000W@40km beats 162.500 WNG628 300W@33km).
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

// The view title names whichever application currently owns the single tuner, so it reads e.g.
// "SDR — ADS-B" / "SDR — Listen" / "SDR — Scanning", falls back to "SDR — pick an application" when
// the tuner is free, and "SDR — rail off" when the SDR rail has no power. listening/polling are
// local (set the instant the operator acts); ADS-B comes from the shared status snapshot.
function updateSdrTitle() {
  const title = document.getElementById("sdr-title");
  if (!title) return;
  const a = lastStatus && lastStatus.aiov2;
  const adsbRunning = lastStatus && lastStatus.adsb && lastStatus.adsb.state === "running";
  let suffix;
  if (listening) suffix = "Listen";
  else if (adsbRunning) suffix = "ADS-B";
  else if (polling != null) suffix = "Scanning";
  else if (railOn(a, "SDR") === false) suffix = "rail off";
  else suffix = "pick an application";
  title.textContent = `SDR — ${suffix}`;
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
  // The next status tick re-enables and shows the right button via syncSdr().
}

// Reflect current SDR app ownership from the shared status snapshot: which ADS-B button shows,
// and whether starting ADS-B is blocked because a hunt or listen already holds the tuner.
export function syncSdr(data) {
  lastStatus = data;
  const running = data && data.adsb && data.adsb.state === "running";
  const tunerBusy = listening || polling != null;
  const start = document.getElementById("adsb-start");
  const stop = document.getElementById("adsb-stop");
  if (start) { start.style.display = running ? "none" : ""; start.disabled = tunerBusy; }
  if (stop) { stop.style.display = running ? "" : "none"; stop.disabled = false; }
  updateSdrTitle();
  applyNoaaAuto(data && data.gps);
}

function renderStations(stations, band) {
  const body = document.getElementById("sdr-list-body");
  if (!body) return;
  if (!stations || !stations.length) {
    body.innerHTML = '<tr><td colspan="4" class="dim">No signals found.</td></tr>';
    return;
  }
  const mode = band === "airband" ? "am" : "wbfm";
  const digits = band === "airband" ? 3 : 1;
  body.innerHTML = stations.map((s) => `<tr>
    <td class="mono">${s.freq_mhz.toFixed(digits)} MHz</td>
    <td>${s.power_db} dB</td>
    <td>${s.snr_db} dB</td>
    <td><button type="button" class="btn sdr-play" data-mode="${mode}" data-freq="${s.freq_hz}"
        data-label="${s.freq_mhz.toFixed(digits)} MHz">▶ Listen</button></td>
  </tr>`).join("");
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
  // Scan is blocked while the tuner is busy (scanning or listening).
  if (btn) { btn.disabled = running || listening || s.busy === "listen"; btn.textContent = running ? "Scanning…" : "Scan"; }
  if (stage === "done" || (!running && s.stations)) renderStations(s.stations, s.band);
  // Remember the airband channels a sweep found, so "Scan airband" can cycle just the live ones.
  if (s.band === "airband" && Array.isArray(s.stations)) {
    lastAirbandFreqs = s.stations.map((st) => st.freq_hz).filter(Boolean);
  }
  return running;
}

async function pollHunt() {
  let s = { stage: "idle" };
  try { s = await (await fetch("/api/sdr/hunt/status")).json(); } catch { /* */ }
  if (!renderHunt(s) && polling) { clearInterval(polling); polling = null; }
  updateSdrTitle();  // title returns to idle/ADS-B/rail-off once the scan ends
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
  updateSdrTitle();  // reflect "Scanning" at once
  pollHunt();
}

// --- listen ---------------------------------------------------------------------------------
function setPlaying(label) {
  listening = !!label;
  if (!label && scanPoll) { clearInterval(scanPoll); scanPoll = null; }  // stopped: end scan polling
  document.getElementById("sdr-stop").style.display = label ? "" : "none";
  document.getElementById("sdr-now").textContent = label ? `♪ ${label}` : "";
  document.getElementById("sdr-scan").disabled = listening;
  const sb = document.getElementById("sdr-scan-listen");
  if (sb) sb.disabled = listening;
  updateSdrTitle();
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
