// Fancy Dashboard — iOS home/lock screen widget for the Scriptable app (https://scriptable.app).
// Reads webdash's GET /api/widget over Tailscale with a bearer token. Setup, token rotation and
// the threat model: software/webdash.md#phone-widget. MIT, per this repo's LICENSE.
//
// Run once inside Scriptable to enter the URL and token (stored in the iOS Keychain, never in this
// file). Run it again in-app to preview, change the settings, or forget them.
//
// Widget sizes: small, medium, large (home screen); accessoryRectangular, accessoryInline,
// accessoryCircular (lock screen).

const KEY_URL = "fancy.widget.url";
const KEY_TOKEN = "fancy.widget.token";
const DEFAULT_URL = "https://fancy.example-tailnet.ts.net/api/widget";
const CACHE_FILE = "fancy-widget-cache.json";
const REFRESH_MIN = 15; // a request to iOS, not a guarantee; iOS sets the real cadence
const STALE_S = 30 * 60;

// webdash's skin tokens (webdash/app/static/styles.css).
const C = {
  bg: new Color("#0b0f0c"),
  panel: new Color("#121712"),
  fg: new Color("#d7f5d7"),
  dim: new Color("#7fa87f"),
  ok: new Color("#4ade80"),
  warn: new Color("#facc15"),
  err: new Color("#f87171"),
  idle: new Color("#38bdf8"),
  off: new Color("#5c725c"),
};
const LEVEL_COLOR = { ok: C.ok, low: C.warn, plug_in: C.err, charging: C.idle, unknown: C.dim };
const LEVEL_TEXT = { ok: "battery", low: "low", plug_in: "PLUG IN", charging: "charging", unknown: "—" };
const PLUG_IN_V = 3.6;

// ---------------------------------------------------------------- settings

function settings() {
  if (!Keychain.contains(KEY_TOKEN)) return null;
  return {
    url: Keychain.contains(KEY_URL) ? Keychain.get(KEY_URL) : DEFAULT_URL,
    bearer: Keychain.get(KEY_TOKEN),
  };
}

async function editSettings() {
  const cur = settings();
  const a = new Alert();
  a.title = "Fancy widget";
  a.message = "Widget endpoint and the token printed by `python -m app.widget --rotate`.";
  a.addTextField("https://<host>.ts.net/api/widget", cur ? cur.url : DEFAULT_URL);
  a.addSecureTextField("token", "");
  a.addAction("Save");
  a.addCancelAction("Cancel");
  if ((await a.present()) === -1) return;
  const url = a.textFieldValue(0).trim();
  const token = a.textFieldValue(1).trim();
  if (url) Keychain.set(KEY_URL, url);
  if (token) Keychain.set(KEY_TOKEN, token);
}

function forgetSettings() {
  for (const k of [KEY_URL, KEY_TOKEN]) if (Keychain.contains(k)) Keychain.remove(k);
  const fm = FileManager.local();
  const p = fm.joinPath(fm.cacheDirectory(), CACHE_FILE);
  if (fm.fileExists(p)) fm.remove(p);
}

// ---------------------------------------------------------------- data

function cachePath() {
  const fm = FileManager.local();
  return fm.joinPath(fm.cacheDirectory(), CACHE_FILE);
}

async function load(cfg) {
  // Returns { data, error }: data may be the last good copy when the fetch fails (off the
  // tailnet, device asleep), so the widget still shows something, marked stale by its age.
  const fm = FileManager.local();
  let error = null;
  try {
    const req = new Request(cfg.url);
    req.headers = { Authorization: `Bearer ${cfg.bearer}` };
    req.timeoutInterval = 10;
    const body = await req.loadString();
    const code = req.response.statusCode;
    if (code === 200) {
      const data = JSON.parse(body);
      fm.writeString(cachePath(), body);
      return { data, error: null };
    }
    error = code === 401 ? "token rejected" : `HTTP ${code}`;
  } catch (e) {
    error = "unreachable";
  }
  const p = cachePath();
  const data = fm.fileExists(p) ? JSON.parse(fm.readString(p)) : null;
  return { data, error };
}

// ---------------------------------------------------------------- formatting

const fmt = {
  v: (x) => (x == null ? "—" : `${x.toFixed(2)} V`),
  w: (x) => (x == null ? "" : `${x.toFixed(1)} W`),
  t: (x) => (x == null ? "—" : `${Math.round(x)}°C`),
  age(ts) {
    if (!ts) return "—";
    const s = Math.max(0, Date.now() / 1000 - ts);
    if (s < 90) return "now";
    if (s < 3600) return `${Math.round(s / 60)}m ago`;
    if (s < 86400) return `${Math.round(s / 3600)}h ago`;
    return `${Math.round(s / 86400)}d ago`;
  },
  gps: (g) => (g.fix === "none" ? "no fix" : `${g.fix} · ${g.sats ?? "?"} sat`),
  svc: (s, n, unit) => (s.state === "running" ? `${n ?? 0} ${unit}` : s.state),
};

function stale(d) {
  return !d.generated_at || Date.now() / 1000 - d.generated_at > STALE_S;
}

// ---------------------------------------------------------------- drawing helpers

function text(stack, s, size, color, opts = {}) {
  const t = stack.addText(String(s));
  t.font = opts.bold ? Font.boldMonospacedSystemFont(size) : Font.mediumMonospacedSystemFont(size);
  t.textColor = color;
  t.lineLimit = 1;
  t.minimumScaleFactor = 0.6;
  return t;
}

function header(w, d, error) {
  const h = w.addStack();
  h.centerAlignContent();
  text(h, "FANCY", 11, C.fg, { bold: true });
  h.addSpacer();
  const late = error || stale(d);
  text(h, error ? `${error} · ${fmt.age(d.generated_at)}` : fmt.age(d.generated_at), 9,
       late ? C.warn : C.dim);
}

function sparkline(values, width, height) {
  const ctx = new DrawContext();
  ctx.size = new Size(width, height);
  ctx.opaque = false;
  ctx.respectScreenScale = true;
  if (values.length < 2) return ctx.getImage();
  const lo = Math.min(...values, PLUG_IN_V) - 0.02;
  const hi = Math.max(...values) + 0.02;
  const y = (v) => height - ((v - lo) / (hi - lo)) * height;
  const x = (i) => (i / (values.length - 1)) * width;
  // Plug-in threshold.
  const t = new Path();
  t.move(new Point(0, y(PLUG_IN_V)));
  t.addLine(new Point(width, y(PLUG_IN_V)));
  ctx.addPath(t);
  ctx.setStrokeColor(C.err);
  ctx.setLineWidth(1);
  ctx.strokePath();
  const p = new Path();
  values.forEach((v, i) => (i ? p.addLine(new Point(x(i), y(v))) : p.move(new Point(x(i), y(v)))));
  ctx.addPath(p);
  ctx.setStrokeColor(C.ok);
  ctx.setLineWidth(2);
  ctx.strokePath();
  return ctx.getImage();
}

function powerBlock(stack, d) {
  const p = d.power;
  const col = LEVEL_COLOR[p.level] || C.dim;
  text(stack, fmt.v(p.voltage_v), 24, col, { bold: true });
  const row = stack.addStack();
  text(row, LEVEL_TEXT[p.level] || p.level, 10, col);
  row.addSpacer(6);
  text(row, fmt.w(p.power_w), 10, C.dim);
}

function kv(stack, k, v, color = C.fg) {
  const r = stack.addStack();
  text(r, k, 10, C.dim);
  r.addSpacer();
  text(r, v, 10, color);
}

// ---------------------------------------------------------------- layouts

function small(w, d, error) {
  header(w, d, error);
  w.addSpacer(6);
  powerBlock(w, d);
  w.addSpacer();
  kv(w, "gps", fmt.gps(d.gps), d.gps.fix === "3D" ? C.ok : C.warn);
  kv(w, "grid", d.gps.grid || "—");
  kv(w, "cpu", fmt.t(d.system.temp_c));
}

function rails(stack, r) {
  const row = stack.addStack();
  row.spacing = 4;
  for (const name of ["GPS", "LORA", "SDR", "USB"]) {
    if (!(name in r)) continue;
    const chip = row.addStack();
    chip.setPadding(1, 4, 1, 4);
    chip.cornerRadius = 3;
    chip.backgroundColor = r[name] ? C.ok : C.off;
    text(chip, name, 8, C.bg, { bold: true });
  }
}

function medium(w, d, error, large = false) {
  header(w, d, error);
  w.addSpacer(6);
  const body = w.addStack();
  const left = body.addStack();
  left.layoutVertically();
  powerBlock(left, d);
  left.addSpacer(4);
  left.addImage(sparkline(d.power.history_v || [], 130, large ? 60 : 30));
  text(left, "2 h", 8, C.dim);
  body.addSpacer(12);
  const right = body.addStack();
  right.layoutVertically();
  right.spacing = 1;
  kv(right, "gps", fmt.gps(d.gps), d.gps.fix === "3D" ? C.ok : C.warn);
  kv(right, "grid", d.gps.grid || "—");
  kv(right, "cpu", `${fmt.t(d.system.temp_c)} · ${Math.round(d.system.cpu_percent ?? 0)}%`);
  kv(right, "kismet", fmt.svc(d.kismet, d.kismet.devices, "dev"),
     d.kismet.state === "running" ? C.ok : C.dim);
  kv(right, "mesh", fmt.svc(d.mesh, d.mesh.nodes, "nodes"),
     d.mesh.state === "running" ? C.ok : C.dim);
  kv(right, "ads-b", fmt.svc(d.adsb, d.adsb.aircraft, "ac"),
     d.adsb.state === "running" ? C.ok : C.dim);
  w.addSpacer();
  rails(w, d.rails || {});
  if (large) {
    w.addSpacer(8);
    kv(w, "disk", d.system.disk_percent == null ? "—" : `${Math.round(d.system.disk_percent)}%`);
    kv(w, "uptime", d.system.uptime_s == null ? "—" : `${Math.floor(d.system.uptime_s / 3600)} h`);
    if (d.system.undervoltage) kv(w, "5 V rail", "UNDERVOLTAGE", C.err);
  }
}

// Lock screen widgets are tinted by iOS; colour is ignored there, so state goes in the words.
function lockRect(w, d, error) {
  const p = d.power;
  text(w, `FANCY ${fmt.v(p.voltage_v)} ${p.level === "ok" ? "" : LEVEL_TEXT[p.level]}`, 13, C.fg,
       { bold: true });
  text(w, `${fmt.gps(d.gps)} · ${d.gps.grid || "—"}`, 11, C.fg);
  text(w, `${fmt.t(d.system.temp_c)} · ${error || fmt.age(d.generated_at)}`, 11, C.fg);
}

function lockInline(w, d) {
  const p = d.power;
  text(w, `Fancy ${fmt.v(p.voltage_v)} · ${d.gps.fix} · ${fmt.t(d.system.temp_c)}`, 12, C.fg);
}

function lockCircular(w, d) {
  w.addSpacer();
  const v = d.power.voltage_v;
  const t = text(w, v == null ? "—" : v.toFixed(2), 14, C.fg, { bold: true });
  t.centerAlignText();
  const u = text(w, d.power.level === "plug_in" ? "PLUG" : "V", 9, C.fg);
  u.centerAlignText();
  w.addSpacer();
}

function message(w, lines) {
  text(w, "FANCY", 11, C.fg, { bold: true });
  w.addSpacer(4);
  for (const l of lines) text(w, l, 10, C.warn);
}

// ---------------------------------------------------------------- main

async function build(family) {
  const w = new ListWidget();
  w.backgroundColor = C.bg;
  w.setPadding(12, 12, 12, 12);
  w.refreshAfterDate = new Date(Date.now() + REFRESH_MIN * 60 * 1000);
  const cfg = settings();
  if (!cfg) {
    message(w, ["not set up", "run the script in Scriptable"]);
    return w;
  }
  w.url = cfg.url.replace(/\/api\/widget\/?$/, "/");
  const { data, error } = await load(cfg);
  if (!data) {
    message(w, [error || "no data"]);
    return w;
  }
  if (family === "accessoryRectangular") lockRect(w, data, error);
  else if (family === "accessoryInline") lockInline(w, data);
  else if (family === "accessoryCircular") lockCircular(w, data);
  else if (family === "large") medium(w, data, error, true);
  else if (family === "medium") medium(w, data, error);
  else small(w, data, error);
  return w;
}

if (config.runsInWidget) {
  Script.setWidget(await build(config.widgetFamily));
} else {
  const a = new Alert();
  a.title = "Fancy widget";
  a.addAction("Preview small");
  a.addAction("Preview medium");
  a.addAction("Preview large");
  a.addAction("Settings");
  a.addDestructiveAction("Forget URL and token");
  a.addCancelAction("Done");
  const choice = await a.presentSheet();
  if (choice === 3 || (choice !== 4 && choice !== -1 && !settings())) await editSettings();
  if (choice === 4) forgetSettings();
  if (choice >= 0 && choice <= 2) {
    const fam = ["small", "medium", "large"][choice];
    const w = await build(fam);
    if (fam === "small") await w.presentSmall();
    else if (fam === "medium") await w.presentMedium();
    else await w.presentLarge();
  }
}
Script.complete();
