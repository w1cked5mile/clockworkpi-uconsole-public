// Boot: hash router, status WebSocket, mesh message polling. No framework, no build step.

import { initRails, syncRails } from "./rails.js";
import { initKismet, syncKismet } from "./kismet.js";
import { initSdr, syncSdr } from "./sdr.js";
import { initWpa } from "./wpa.js";
import { initTshark, syncTshark } from "./tshark.js";
import { initMesh, markMeshRead, pollMeshMessages } from "./mesh.js";
import { render, setLinks, toggleCoords } from "./views.js";
import { decorateStations, refreshChip, renderLearn, updateLive } from "./learn.js";

const ROUTES = ["overview", "mesh", "gps", "sdr", "wifi", "power", "system", "learn"];
let route = "overview";
let lastData = null;

// "#/learn/m/M6" -> view "learn", sub-path "m/M6". Only the learning view has sub-paths.
function hashParts() {
  const [name, ...rest] = (location.hash.replace(/^#\/?/, "") || "overview").split("/");
  return { name, sub: rest.join("/") };
}

function currentRoute() {
  const { name } = hashParts();
  return ROUTES.includes(name) ? name : "overview";
}

function applyRoute({ focus }) {
  route = currentRoute();
  for (const view of document.querySelectorAll(".view")) view.hidden = view.dataset.view !== route;
  for (const chip of document.querySelectorAll("[data-nav]")) {
    if (chip.dataset.nav === route) chip.setAttribute("aria-current", "page");
    else chip.removeAttribute("aria-current");
  }
  if (route === "mesh") markMeshRead();
  if (route === "learn") renderLearn(hashParts().sub, lastData);
  // Re-render at once so a frame that belongs to the new view (or the old one) opens or closes
  // now rather than on the next 3 s tick.
  if (lastData) render(lastData, route);
  // Move focus to the new view's heading, so keyboard and screen-reader users land in it.
  if (focus && route !== "learn") document.querySelector(`.view[data-view="${route}"] .view-title`)?.focus();
}

function connect() {
  const proto = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${proto}://${location.host}/ws/status`);
  const connState = document.getElementById("conn-state");

  ws.onopen = () => { connState.textContent = "live"; };
  ws.onmessage = (ev) => {
    lastData = JSON.parse(ev.data);
    syncRails(lastData.aiov2);
    syncKismet(lastData.kismet);
    syncSdr(lastData);
    syncTshark(lastData.tshark);
    render(lastData, route);
    if (route === "learn") updateLive(lastData);
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
initTshark();
initMesh();
applyRoute({ focus: false });
connect();
loadLinks();
pollMesh();
setInterval(pollMesh, 4000);
refreshChip();
setInterval(refreshChip, 60000);
decorateStations();
