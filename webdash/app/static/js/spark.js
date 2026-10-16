// Sparklines from GET /api/history — drawn into .spark figures in the visible view only, from the
// 2 h in-memory series. Fetched on its own 30 s cadence (the sample rate), not the 3 s status tick.
// Inline SVG, tokens only, status-neutral trace. Pointer over a spark: a crosshair snaps to the
// nearest sample and the caption reads its value and age. See docs/reference/webdash-design.md
// §Sparklines.

const SVGNS = "http://www.w3.org/2000/svg";
let samples = [];
let onUpdate = null;

export async function fetchHistory() {
  try {
    const r = await fetch("/api/history");
    if (r.ok) { const d = await r.json(); if (Array.isArray(d.samples)) samples = d.samples; }
  } catch { /* keep prior samples */ }
  if (onUpdate) onUpdate();
}

// cb is called after every fetch so the caller can redraw the visible view's sparks.
export function initHistory(cb) {
  onUpdate = cb;
  fetchHistory();
  setInterval(fetchHistory, 30000);
}

// bare: the number at the unit's precision with no suffix, for the "lo–hi" range.
function fmt(v, unit, bare = false) {
  if (v == null) return "—";
  const n = unit === "V" ? v.toFixed(2) : Math.abs(v) >= 100 ? String(Math.round(v)) : v.toFixed(1);
  if (bare) return n;
  const u = unit === "°C" || unit === "%" ? unit : unit ? " " + unit : "";
  return `${n}${u}`;
}

function spanText(sec) {
  if (sec < 90) return `${Math.max(1, Math.round(sec))} s`;
  if (sec < 5400) return `${Math.round(sec / 60)} min`;
  return `${(sec / 3600).toFixed(1)} h`;
}

function el(name, attrs) {
  const n = document.createElementNS(SVGNS, name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n;
}

// Only the voltage dot mirrors a status, and only on battery — it never invents one.
function voltDotClass(field, v, status) {
  if (field !== "voltage_v") return "";
  const pn = (status && status.aiov2 && status.aiov2.power_num) || {};
  if (!pn.on_battery || v == null) return "";
  if (v <= 3.55) return "crit";
  if (v <= 3.60) return "low";
  return "";
}

function drawOne(fig, status) {
  const svg = fig.querySelector(".spark-svg");
  const cap = fig.querySelector(".spark-cap");
  if (!svg || !cap) return;
  const field = fig.dataset.field;
  const unit = fig.dataset.unit || "";
  const label = fig.dataset.label || "value";
  const h = parseInt(fig.dataset.h || "24", 10);
  let warnRef = fig.dataset.warn ? parseFloat(fig.dataset.warn) : null;
  const onBattery = !!(status && status.aiov2 && status.aiov2.power_num && status.aiov2.power_num.on_battery);
  if (field === "voltage_v" && !onBattery) warnRef = null;   // on AC the threshold is meaningless

  const pts = samples
    .map((s) => ({ t: s.ts, v: s[field] }))
    .filter((p) => p.v != null && isFinite(p.v));
  const w = Math.max(80, Math.min(fig.clientWidth || 160, h > 40 ? 640 : 240));
  svg.setAttribute("width", w);
  svg.setAttribute("height", h);
  svg.replaceChildren();

  fig._spark = null;
  if (pts.length === 0) {
    const none = samples.length === 0;
    cap.textContent = none ? "history clears on restart — collecting…" : "no data";
    svg.setAttribute("aria-label",
      `${label} history: ${none ? "none yet; it clears on restart" : "no data"}.`);
    return;
  }

  const vals = pts.map((p) => p.v);
  const dmin = Math.min(...vals), dmax = Math.max(...vals);
  const last = vals[vals.length - 1];
  const span = pts[pts.length - 1].t - pts[0].t;
  const pad = 2;
  // y-range includes the warn reference so its line is on-canvas.
  const lo = warnRef != null ? Math.min(dmin, warnRef) : dmin;
  const hi = warnRef != null ? Math.max(dmax, warnRef) : dmax;
  const yr = hi - lo || 1;
  const x = (p) => (pts.length === 1 ? w / 2 : pad + ((p.t - pts[0].t) / (span || 1)) * (w - 2 * pad));
  const y = (v) => pad + ((hi - v) / yr) * (h - 2 * pad);

  if (warnRef != null) {
    svg.appendChild(el("line", { x1: 0, x2: w, y1: y(warnRef).toFixed(1), y2: y(warnRef).toFixed(1), class: "spark-ref" }));
  }
  svg.appendChild(el("polyline", {
    class: "spark-line", fill: "none",
    points: pts.map((p) => `${x(p).toFixed(1)},${y(p.v).toFixed(1)}`).join(" "),
  }));
  const dotCls = voltDotClass(field, last, status);
  svg.appendChild(el("circle", {
    cx: x(pts[pts.length - 1]).toFixed(1), cy: y(last).toFixed(1),
    r: h > 40 ? 3 : 2.5, class: `spark-dot ${dotCls}`.trim(),
  }));

  const st = spanText(span);
  fig._spark = { pts, x, y, h, unit };
  const sparse = pts.length < 20;
  const range = dmin === dmax ? "" : `${fmt(dmin, unit, true)}–${fmt(dmax, unit, true)} · `;
  cap.textContent = `${fmt(last, unit)} · ${range}${sparse ? `last ${st} (${pts.length})` : `over ${st}`}`;
  svg.setAttribute("aria-label",
    `${label}: now ${fmt(last, unit)}, ranging ${fmt(dmin, unit)} to ${fmt(dmax, unit)} over the last ${st}` +
    `${sparse ? `, ${pts.length} samples` : ""}.`);
  fig._spark.summary = cap.textContent;
  bindHover(fig);
  if (fig._hoverX != null) showHover(fig, fig._hoverX);   // a redraw mid-hover keeps the readout
}

// The crosshair is redrawn from the stored pointer x, so the 3 s status redraw doesn't drop it.
function showHover(fig, px) {
  const sp = fig._spark;
  const svg = fig.querySelector(".spark-svg");
  const cap = fig.querySelector(".spark-cap");
  if (!sp || !svg || !cap) return;
  let best = sp.pts[0];
  for (const p of sp.pts) if (Math.abs(sp.x(p) - px) < Math.abs(sp.x(best) - px)) best = p;
  svg.querySelector(".spark-cross")?.remove();
  const g = el("g", { class: "spark-cross" });
  const cx = sp.x(best).toFixed(1);
  g.appendChild(el("line", { x1: cx, x2: cx, y1: 0, y2: sp.h, class: "spark-cross-line" }));
  g.appendChild(el("circle", { cx, cy: sp.y(best.v).toFixed(1), r: 4, class: "spark-cross-dot" }));
  svg.appendChild(g);
  const ago = Date.now() / 1000 - best.t;
  cap.textContent = `${fmt(best.v, sp.unit)} · ${ago < 45 ? "now" : `${spanText(ago)} ago`}`;
}

function clearHover(fig) {
  fig._hoverX = null;
  fig.querySelector(".spark-cross")?.remove();
  const cap = fig.querySelector(".spark-cap");
  if (cap && fig._spark) cap.textContent = fig._spark.summary;
}

function bindHover(fig) {
  if (fig.dataset.bound) return;
  fig.dataset.bound = "1";
  const svg = fig.querySelector(".spark-svg");
  const move = (ev) => {
    const r = svg.getBoundingClientRect();
    fig._hoverX = ev.clientX - r.left;
    showHover(fig, fig._hoverX);
  };
  svg.addEventListener("pointermove", move);
  svg.addEventListener("pointerdown", move);   // touch: a tap reads the nearest sample
  svg.addEventListener("pointerleave", () => clearHover(fig));
}

// Draw every .spark in the currently visible view, from the cached history and the latest status.
export function drawSparks(status, route) {
  const view = document.querySelector(`.view[data-view="${route}"]`);
  if (!view) return;
  for (const fig of view.querySelectorAll(".spark")) drawOne(fig, status || {});
}
