// Rail switches: <button class="rail-switch" role="switch" data-feature="SDR">. The same rail can
// have a switch on its station tile and another in the Power view; all of them are kept in sync
// from the status tick, and a click on any of them goes through one handler.

let pending = new Set();

function switchesFor(feature) {
  return document.querySelectorAll(`.rail-switch[data-feature="${feature}"]`);
}

export function syncRails(a) {
  const known = a && a.state === "ok" && a.rails;
  for (const btn of document.querySelectorAll(".rail-switch")) {
    const f = btn.dataset.feature;
    if (!known || !a.rails[f]) {
      // Bridge unavailable: the rail's state is unknown, so the switch can't honestly show one.
      btn.disabled = true;
      btn.removeAttribute("aria-checked");
      btn.title = "aiov2 bridge unavailable";
      continue;
    }
    btn.title = "";
    // Skip a rail whose request is in flight — otherwise the next ~3 s tick can stomp the
    // optimistic state before the request resolves, and the switch flickers.
    if (pending.has(f)) continue;
    btn.disabled = false;
    btn.setAttribute("aria-checked", a.rails[f].on ? "true" : "false");
  }
}

function setAll(feature, fn) {
  for (const btn of switchesFor(feature)) fn(btn);
}

async function toggleRail(feature, desired) {
  const errEl = document.getElementById("rail-error");
  if (errEl) errEl.textContent = "";
  pending.add(feature);
  setAll(feature, (b) => {
    b.disabled = true;
    b.setAttribute("aria-busy", "true");
    b.setAttribute("aria-checked", desired ? "true" : "false");
  });
  let error = null;
  try {
    const resp = await fetch("/api/aiov2/rail", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ feature, state: desired ? "on" : "off" }),
    });
    if (!resp.ok) {
      const body = await resp.json().catch(() => ({}));
      error = body.error || `HTTP ${resp.status}`;
    }
  } catch (err) {
    error = String(err);
  }
  pending.delete(feature);
  setAll(feature, (b) => {
    b.disabled = false;
    b.removeAttribute("aria-busy");
    if (error) b.setAttribute("aria-checked", desired ? "false" : "true"); // hardware didn't change
  });
  if (error) {
    const msg = `${feature} didn't switch: ${error}`;
    if (errEl) errEl.textContent = msg;
    // The tile the operator used may not be the Power view — surface it next to the switch too.
    for (const b of switchesFor(feature)) {
      const local = b.closest(".tile, .panel")?.querySelector(".switch-error");
      if (local) local.textContent = msg;
    }
  }
}

export function initRails() {
  document.addEventListener("click", (ev) => {
    const btn = ev.target.closest(".rail-switch");
    if (!btn || btn.disabled) return;
    for (const e of document.querySelectorAll(".switch-error")) e.textContent = "";
    toggleRail(btn.dataset.feature, btn.getAttribute("aria-checked") !== "true");
  });
}
