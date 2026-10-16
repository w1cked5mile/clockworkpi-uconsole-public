// Actuator: a control that transmits or changes hardware (docs/reference/webdash-design-team.md,
// backlog item 1). It always says what it does, at the control; when it can't act it says why and
// what clears it, in text, never by fading alone. The button is never natively disabled: it keeps
// aria-disabled, stays in the tab order, and points at its reason with aria-describedby, so a
// keyboard or screen-reader user can find out why.
//
// Pure DOM rendering, no fetch and no module state, so the render-check harness can drive it with
// fixture models. Every string is set with textContent: channel names come off the air.
//
// Markup it expects inside `root` (elements are found by data-act):
//   caption · note · retries · reason · button · detail (a <details>) · detail-list (a <ul>)
//
// model = {
//   medium: "rf" | "local",       // rf: transmits over the air (TX tag and antenna glyph shown)
//   caption: string,              // what it does, always visible
//   note: string | null,          // a qualifier, e.g. a secondary channel's real frequency
//   retries: string | null,       // what the radio may do on its own after a press
//   verb: string,                 // the button label: the effect, e.g. "Transmit on SCMesh"
//   blocked: {reason, fix} | null,
//   busy: boolean,
//   detail: string[],             // consequences and rules, in the expandable list
// }

function setIfChanged(el, text) {
  if (el && el.textContent !== text) el.textContent = text;
}

function part(root, name) {
  return root.querySelector(`[data-act="${name}"]`);
}

export function renderActuator(root, model) {
  root.dataset.medium = model.medium;
  setIfChanged(part(root, "caption"), model.caption || "");

  const note = part(root, "note");
  if (note) {
    setIfChanged(note, model.note || "");
    note.hidden = !model.note;
  }
  const retries = part(root, "retries");
  if (retries) {
    setIfChanged(retries, model.retries || "");
    retries.hidden = !model.retries;
  }

  const btn = part(root, "button");
  setIfChanged(btn, model.verb);
  const blocked = !!model.blocked || !!model.busy;
  btn.setAttribute("aria-disabled", blocked ? "true" : "false");
  btn.setAttribute("aria-busy", model.busy ? "true" : "false");

  // The reason line is a role=status region. Re-render it only when the reason changes, so the
  // 3 s status tick never re-announces it.
  const reason = part(root, "reason");
  const key = model.blocked ? `${model.blocked.reason}\n${model.blocked.fix || ""}` : "";
  if (reason.dataset.key !== key) {
    reason.dataset.key = key;
    if (!model.blocked) {
      reason.replaceChildren();
    } else {
      const parts = [document.createTextNode(model.blocked.reason)];
      if (model.blocked.fix) {
        const fix = document.createElement("span");
        fix.className = "act-fix";
        fix.textContent = model.blocked.fix;
        parts.push(fix);
      }
      reason.replaceChildren(...parts);
    }
  }

  const list = part(root, "detail-list");
  if (list) {
    const want = (model.detail || []).filter(Boolean);
    const have = [...list.children].map((li) => li.textContent);
    if (want.join("\n") !== have.join("\n")) {
      list.replaceChildren(...want.map((t) => {
        const li = document.createElement("li");
        li.textContent = t;
        return li;
      }));
    }
  }
}

export function isBlocked(root) {
  return part(root, "button").getAttribute("aria-disabled") === "true";
}

export function reasonText(root) {
  const r = part(root, "reason");
  return r && r.dataset.key ? r.dataset.key.split("\n")[0] : "";
}
