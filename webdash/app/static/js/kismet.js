// Start/Stop Kismet from the Wi-Fi view. Kismet runs as a user systemd service on the host,
// started/stopped through the aiov2 bridge (POST /api/kismet/control). The button's label and
// action are driven from the status tick (syncKismet); a click posts, then lets the next tick
// settle the label to Kismet's real state — it takes a couple of seconds to open/close its port.

let pending = false;

// "running" and "locked" both mean the process is up ("locked" = up but its REST API wants a
// login); only a clean "stopped" means it's down and can be started.
function isUp(k) {
  return !!k && (k.state === "running" || k.state === "locked");
}

export function syncKismet(k) {
  const btn = document.getElementById("kismet-toggle");
  if (!btn || pending) return;
  const up = isUp(k);
  btn.dataset.action = up ? "stop" : "start";
  btn.textContent = up ? "Stop Kismet" : "Start Kismet";
  btn.classList.toggle("danger", up);
  btn.disabled = false;
  btn.title = (!k || k.state === "unavailable")
    ? "Kismet status unknown — Start will try to bring it up" : "";
}

async function send(action) {
  const btn = document.getElementById("kismet-toggle");
  const errEl = document.getElementById("kismet-error");
  if (errEl) errEl.textContent = "";
  pending = true;
  if (btn) {
    btn.disabled = true;
    btn.setAttribute("aria-busy", "true");
    btn.textContent = action === "start" ? "Starting…" : "Stopping…";
  }
  let error = null;
  try {
    const resp = await fetch("/api/kismet/control", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action }),
    });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      error = body.error || body.stderr || `HTTP ${resp.status}`;
    }
  } catch (err) {
    error = String(err);
  }
  pending = false;
  if (btn) {
    btn.removeAttribute("aria-busy");
    btn.disabled = false;
  }
  if (error && errEl) errEl.textContent = `Kismet didn't ${action}: ${error}`;
  // Label/action are left to resync on the next status tick, once Kismet's REST port reflects it.
}

export function initKismet() {
  const btn = document.getElementById("kismet-toggle");
  if (!btn) return;
  btn.addEventListener("click", () => {
    if (btn.disabled) return;
    send(btn.dataset.action === "stop" ? "stop" : "start");
  });
}
