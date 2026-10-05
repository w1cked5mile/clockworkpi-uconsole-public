// Shared DOM helpers. Every value that reaches the page goes through textContent: several of them
// (node names, channel names, service error strings, anything received over the air) originate
// outside this app.

export function fmtBytes(n) {
  if (n == null) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let i = 0;
  while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
  return `${n.toFixed(1)} ${units[i]}`;
}

export function fmtUptime(s) {
  if (s == null) return "—";
  const d = Math.floor(s / 86400), h = Math.floor((s % 86400) / 3600), m = Math.floor((s % 3600) / 60);
  return `${d}d ${h}h ${m}m`;
}

// 6-character Maidenhead locator. The repo records location as grid or city only, so this is
// what the dashboard shows by default; precise coordinates need an explicit reveal.
export function maidenhead(lat, lon) {
  const A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";
  let x = lon + 180, y = lat + 90;
  const f1 = A[Math.floor(x / 20)] + A[Math.floor(y / 10)];
  x %= 20; y %= 10;
  const f2 = `${Math.floor(x / 2)}${Math.floor(y)}`;
  x %= 2; y %= 1;
  const f3 = A[Math.floor(x * 12)].toLowerCase() + A[Math.floor(y * 24)].toLowerCase();
  return f1 + f2 + f3;
}

// h("div", {class: "row"}, "text", childEl) — string children become text nodes, never markup.
export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === "class") el.className = v;
    else if (k === "text") el.textContent = v;
    else el.setAttribute(k, v === true ? "" : v);
  }
  // Arrays of children are flattened, so callers can pass optional groups like [" ", badge].
  for (const c of children.flat(Infinity)) {
    if (c == null || c === false) continue;
    el.append(typeof c === "string" || typeof c === "number" ? String(c) : c);
  }
  return el;
}

// Status is shown as colour + glyph + word, never colour alone. Levels map to CSS classes.
const STATUS_GLYPH = { ok: "●", idle: "◐", off: "○", action: "▲", err: "✕" };

export function statusText(level, word) {
  return `${STATUS_GLYPH[level]} ${word}`;
}

// Sets every element carrying data-status="<key>" — a station's status appears on its tile and
// in its detail view, and both must agree.
export function setStatus(key, level, word) {
  for (const el of document.querySelectorAll(`[data-status="${key}"]`)) {
    el.className = `status ${level}`;
    el.textContent = statusText(level, word);
  }
}

// Fact label -> glossary entry, filled in by learn.js once the glossary loads. Labels that match
// get an ⓘ link to their explainer (plan §3.1, "ⓘ on every glossary term").
export const GLOSS_LINKS = {};

// Replaces a container's children with key/value rows.
export function setRows(id, rows) {
  const el = document.getElementById(id);
  if (!el) return;
  el.replaceChildren(...rows.map(([k, v]) => {
    const g = GLOSS_LINKS[k];
    const key = h("span", { class: "k" }, k, g ? h("a", { class: "gloss-i", href: `#/learn/glossary/${g.id}`,
      title: g.tooltip, "aria-label": `What is ${k}?` }, "ⓘ") : null);
    return h("div", { class: "row" }, key, h("span", { class: "v", text: v ?? "—" }));
  }));
}

export function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text ?? "—";
}

export function show(id, visible, display = "block") {
  const el = document.getElementById(id);
  if (el) el.style.display = visible ? display : "none";
}

// true/false for a rail's state, or null when the bridge can't say (don't guess "off").
export function railOn(a, name) {
  if (!a || a.state !== "ok" || !a.rails || !a.rails[name]) return null;
  return !!a.rails[name].on;
}

