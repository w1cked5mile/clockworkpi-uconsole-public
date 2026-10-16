// Boot: hash router, status WebSocket, mesh message polling. No framework, no build step.

import { initRails, syncRails } from "./rails.js";
import { initKismet, syncKismet } from "./kismet.js";
import { cacheSdr, initSdr, startTunerPoll, stopTunerPoll, syncSdr } from "./sdr.js";
import { initWpa, loadList as refreshWpa, pollStatus as refreshCapture } from "./wpa.js";
import { initSurvey, refreshActive as refreshSurvey } from "./survey.js";
import { initTshark, syncTshark } from "./tshark.js";
import { cacheMesh, initMesh, markMeshRead, pollMeshMessages, syncMesh } from "./mesh.js";
import { render, setLinks, toggleCoords } from "./views.js";
import { decorateStations, refreshChip, renderLearn, updateLive } from "./learn.js";
import { renderTimeline } from "./timeline.js";
import { drawSparks, initHistory } from "./spark.js";

const ROUTES = ["overview", "mesh", "gps", "sdr", "wifi", "power", "system",
  "learn", "timeline"];
let route = "overview";
let lastData = null;

// "#/learn/m/M6" -> view "learn", sub-path "m/M6". The learning view and the SDR/Wi-Fi tabs use
// sub-paths.
function hashParts() {
  const [name, ...rest] = (location.hash.replace(/^#\/?/, "") || "overview").split("/");
  return { name, sub: rest.join("/") };
}

// One status snapshot into the page. Only the visible view is drawn; the caches that local input
// handlers read (SDR, mesh) and the rail switches, which appear on several views, stay current.
function tick(data, route) {
  syncRails(data.aiov2);
  cacheSdr(data);
  cacheMesh(data);
  if (route === "wifi") { syncKismet(data.kismet); syncTshark(data.tshark); }
  if (route === "sdr") syncSdr(data);
  if (route === "mesh") syncMesh(data);
  render(data, route);
  drawSparks(data, route);
  if (route === "learn") updateLive(data);
}

// The SDR view's tabs are links to #/sdr/<tab>; bare #/sdr opens ADS-B.
const SDR_TABS = ["adsb", "hunt", "listen", "owrx"];
function selectSdrTab(sub) {
  const tab = SDR_TABS.includes(sub) ? sub : "adsb";
  for (const t of SDR_TABS) {
    const link = document.getElementById(`sdr-tab-${t}`);
    if (t === tab) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current");
    document.getElementById(`sdr-panel-${t}`).hidden = t !== tab;
  }
  return tab;
}

// The Wi-Fi view's tabs mirror the SDR tabs: links to #/wifi/<tab>; bare #/wifi opens Kismet.
const WIFI_TABS = ["kismet", "survey", "capture", "wpa"];
function selectWifiTab(sub) {
  const tab = WIFI_TABS.includes(sub) ? sub : "kismet";
  for (const t of WIFI_TABS) {
    const link = document.getElementById(`wifi-tab-${t}`);
    if (t === tab) link.setAttribute("aria-current", "page"); else link.removeAttribute("aria-current");
    document.getElementById(`wifi-panel-${t}`).hidden = t !== tab;
  }
  return tab;
}

function applyRoute({ focus }) {
  const prev = route;
  let { name, sub } = hashParts();
  // #/survey, #/capture and #/wpa are now tabs of the Wi-Fi view. Rewrite the hash in place (so
  // Back doesn't bounce through the alias) and fall through as the wifi route.
  if (name === "survey" || name === "capture" || name === "wpa") {
    sub = name; name = "wifi";
    history.replaceState(null, "", `#/wifi/${sub}`);
  }
  route = ROUTES.includes(name) ? name : "overview";
  for (const view of document.querySelectorAll(".view")) view.hidden = view.dataset.view !== route;
  for (const chip of document.querySelectorAll("[data-nav]")) {
    if (chip.dataset.nav === route) chip.setAttribute("aria-current", "page");
    else chip.removeAttribute("aria-current");
  }
  let sdrTab = null, wifiTab = null;
  if (route === "sdr") { sdrTab = selectSdrTab(sub); startTunerPoll(); } else stopTunerPoll();
  if (route === "wifi") {
    wifiTab = selectWifiTab(sub);
    // The survey/WPA panels read state another browser may have changed: re-read on tab open.
    if (wifiTab === "survey") refreshSurvey();
    else if (wifiTab === "wpa") { refreshWpa(); refreshCapture(); }
  }
  if (route === "mesh") markMeshRead();
  if (route === "learn") renderLearn(hashParts().sub, lastData);
  if (route === "timeline") renderTimeline(document.getElementById("timeline-root"));
  // Draw the new view from the last snapshot at once, rather than on the next 3 s tick: hidden
  // views aren't kept up to date.
  if (lastData) tick(lastData, route);
  // Move focus to the new view's heading, so keyboard and screen-reader users land in it. Switching
  // SDR/Wi-Fi tabs keeps focus on the tab that was chosen instead.
  if (focus && sdrTab && prev === "sdr") document.getElementById(`sdr-tab-${sdrTab}`).focus();
  else if (focus && wifiTab && prev === "wifi") document.getElementById(`wifi-tab-${wifiTab}`).focus();
  else if (focus && route !== "learn") document.querySelector(`.view[data-view="${route}"] .view-title`)?.focus();
}

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/status`);
  const connState = document.getElementById("conn-state");

  ws.onopen = () => { connState.textContent = "live"; };
  ws.onmessage = (ev) => {
    lastData = JSON.parse(ev.data);
    tick(lastData, route);
  };
  ws.onclose = (ev) => {
    connState.textContent = ev.code === 4401 ? "session expired — reloading…" : "disconnected — retrying…";
    if (ev.code === 4401) { setTimeout(() => location.reload(), 1000); return; }
    setTimeout(connect, 3000);
  };
  ws.onerror = () => ws.close();
}

async function loadLinks() {
  try {
    const resp = await fetch("/api/links");
    if (!resp.ok) return;
    const links = await resp.json();
    setLinks(links);
    document.getElementById("mesh-link").href = links.meshtastic_ui;
    document.getElementById("kismet-link").href = links.kismet;
    const owrxLink = document.getElementById("owrx-link");
    if (owrxLink && links.openwebrx) owrxLink.href = links.openwebrx;
  } catch (err) {
    console.error("failed to load app links:", err);
  }
}

async function pollMesh() {
  await pollMeshMessages();
  if (route === "mesh") markMeshRead();
  if (lastData) render(lastData, route);
}

document.getElementById("gps-coords-btn").addEventListener("click", (ev) => {
  const on = toggleCoords();
  ev.currentTarget.textContent = on ? "Hide coordinates" : "Show coordinates";
  ev.currentTarget.setAttribute("aria-pressed", on ? "true" : "false");
  if (lastData) render(lastData, route);
});

window.addEventListener("hashchange", () => applyRoute({ focus: true }));
initRails();
initKismet();
initSdr();
initWpa();
initSurvey();
initTshark();
initMesh();
// History arrives every 30 s; redraw the visible view's sparks from the last snapshot when it does.
initHistory(() => { if (lastData) drawSparks(lastData, route); });
applyRoute({ focus: false });
connect();
loadLinks();
pollMesh();
setInterval(pollMesh, 4000);
refreshChip();
setInterval(refreshChip, 60000);
decorateStations();
