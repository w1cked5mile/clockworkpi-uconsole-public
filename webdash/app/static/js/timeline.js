// Project build log ("the shipwright's log"): how Fancy was built, in order — from the first
// orders through assembly, radio bring-up, the dashboard, the NVMe upgrade, the knowledge/learning
// platform, and field tuning. Each step carries a category tag; steps that were driven by a prompt
// to the assistant also carry a callout summarising that prompt.
//
// Dates/facts are drawn from CHANGELOG.md, docs/logs/build-log.md and docs/records/
// order-and-warranty.md. The "prompt" callouts are SUMMARISED, not verbatim — representative of
// what was asked, reconstructed from the logs (same spirit as the repo's verify-marker rule). The
// view says so, so no one mistakes them for a captured transcript.

// Category → { label, CSS token } for the coloured tag chips.
const CATS = {
  order:    { label: "Order",     tok: "--learn" },
  arrival:  { label: "Arrived",   tok: "--ok" },
  hardware: { label: "Hardware",  tok: "--tx" },
  bringup:  { label: "Bring-up",  tok: "--idle" },
  webdash:  { label: "webdash",   tok: "--accent" },
  docs:     { label: "Docs & learning", tok: "--warn" },
  tooling:  { label: "Tooling",   tok: "--err" },
};

const MILESTONES = [
  // ---- Procurement ----
  {
    date: "2026-09-02", phase: "Procurement", cat: "order",
    title: "uConsole kit + AIO V2 ordered",
    body: "One OpenSourceSDRLab order on AliExpress (#8214…9843, $326.84 combined) for the uConsole " +
      "v3.14 mainboard kit and the AIO V2 expansion board. It later shipped as two separate parcels " +
      "on a single YunExpress tracking number — a detail that confused delivery tracking later.",
  },
  {
    date: "2026-09-03", phase: "Procurement", cat: "order",
    title: "CM4 and the HackerGadgets upgrade kit ordered",
    body: "CM4 Lite 8GB from Newark (#10397194, $171.20) and the HackerGadgets upgrade kit #11953 " +
      "($64.00) — the CM4/5 Adapter Pro, NVMe battery board and RJ45 + USB3 board (Dual-18650-holder " +
      "variant, no Wi-Fi card).",
  },
  {
    date: "2026-09-09", phase: "Procurement", cat: "order",
    title: "Battery packs: Meshnology bought, UNIKARO cancelled",
    body: "A UNIKARO 15000 mAh pack was ordered then cancelled the same morning over an unreasonable " +
      "shipping estimate; a Meshnology 1S LiPo pair (Amazon #114-7650902-4482665, $42.79) was ordered " +
      "3 min 34 s later as the replacement. Its confirmation email was titled “Ordered 1 item: " +
      "Toys & Games,” which is why product-name searches missed it.",
  },

  // ---- Repo & order tracking ----
  {
    date: "2026-09-04", phase: "Repo & order tracking", cat: "tooling",
    title: "The documentation-first repo, scaffolded onto GitHub",
    body: "Before the first part was in hand, the build got its home: a documentation-first " +
      "repository scaffolded from a reusable method — directory tree, sourced spec-sheet stubs, " +
      "staged config files, bring-up acceptance checklists, a BOM, order records and a " +
      "seven-discipline RF knowledge base — then pushed to GitHub. Two read-only subagents " +
      "(per-component sourcing and an adversarial pre-commit audit) plus a mechanical audit and link " +
      "check were wired in from the start.",
    prompt: "Set up a documentation-first repo for this build — the structure, checklists, BOM " +
      "and knowledge base, with sourcing and audit agents — and put it on GitHub.",
  },
  {
    date: "2026-09-11", phase: "Repo & order tracking", cat: "tooling",
    title: "A shipment tracker for the parts in flight",
    body: "With parts moving across several carriers and two mailboxes, a small shipment tracker went " +
      "up on the home server (SQLite-backed, Tailscale-only). Its Newark/AliExpress tracking links " +
      "auto-refresh every couple of hours through the Anthropic API rather than needing a manual " +
      "‘ask Claude to refresh it’ step; orders are added or edited through its UI or " +
      "POST /api/shipments. It was already in use for the 09-14 ‘order split into two parcels’ " +
      "check.",
    prompt: "Build a shipment tracker on the home server that keeps the orders in SQLite and refreshes " +
      "the carrier tracking automatically, so I don't have to ask each time.",
  },

  // ---- Parts arrive & inventory ----
  {
    date: "2026-09-04", phase: "Parts arrive & inventory", cat: "arrival",
    title: "CM4 delivered, then inspected",
    body: "The CM4 arrived by FedEx on 09-04 and was unboxed and inspected 09-06: box part code " +
      "CM4108000 (wireless, 8 GB, Lite) matches the order, regulatory IDs transcribed, a u.FL " +
      "external-antenna connector found on the module, no visible damage.",
  },
  {
    date: "2026-09-10", phase: "Parts arrive & inventory", cat: "arrival",
    title: "Meshnology LiPo pair delivered",
    body: "The pack of record arrived and went on the shelf. It stayed unfitted — it needs the NVMe " +
      "battery board's JST connector, which didn't arrive until the #11953 kit on 09-23.",
  },
  {
    date: "2026-09-14", phase: "Parts arrive & inventory", cat: "arrival",
    title: "AIO V2 parcel in; order found split in two",
    body: "The first of the two AliExpress parcels (the AIO V2) was unboxed and identified from " +
      "photos. A shipment check established the single order had shipped as two physical parcels, " +
      "and a mailbox sweep turned up that upgrade kit #11953 had already shipped.",
  },
  {
    date: "2026-09-15", phase: "Parts arrive & inventory", cat: "arrival",
    title: "uConsole kit + AIO V2 fully unboxed and inventoried",
    body: "The second parcel arrived; the kit and AIO V2 were photographed (12 frames) and inventoried " +
      "— shell, display, keyboard, stock battery board + 18650 holder, EXT board, CM4→CPI3.14 " +
      "adapter, the 7-way ANT1–ANT7 breakout and all antennas. The AC1200 Wi-Fi card (#12253, " +
      "$63.00) was ordered the same day to feed the four still-empty antenna ports.",
  },

  // ---- Assembly & first boot ----
  {
    date: "2026-09-15", phase: "Assembly & first boot", cat: "hardware",
    title: "microSD flashed",
    body: "uConsole_CM4_v3.1_64bit written to the build's card and verified by reading it back and " +
      "comparing SHA-256 against the image.",
  },
  {
    date: "2026-09-15", phase: "Assembly & first boot", cat: "hardware",
    title: "First assembly, then the shell closed",
    body: "Mainboard in the shell, CM4 on the kit's adapter, AIO V2 in the expansion slot, stock " +
      "battery board with an interim 2×18650 pack. The shell was then closed with the display and " +
      "keyboard in and all 8 antennas fitted (ANT1–ANT7 plus the SDR bulkhead whip).",
  },
  {
    date: "2026-09-16", phase: "Assembly & first boot", cat: "hardware",
    title: "First boot",
    body: "The device powered on and booted to the desktop on the interim 18650 pair. Captured every " +
      "identifier the running system exposes — CM4 serial <cm4-serial-redacted>, Wi-Fi/Ethernet MACs, " +
      "the USB input-controller identity — and confirmed two unverified claims on hardware: PMIC " +
      "3.886 V (1S, not 2S), and dtparam=ant2 selecting the external u.FL antenna.",
  },

  // ---- Radio bring-up ----
  {
    date: "2026-09-16", phase: "Radio bring-up", cat: "bringup",
    title: "aiov2_ctl + RTC/GPS/LoRa overlays",
    body: "aiov2_ctl installed and the SDR rail verified end-to-end — first hands-on software on " +
      "the booted device. The RTC/GPS/LoRa device-tree overlays were applied and reboot-verified: the " +
      "PCF85063A RTC on I2C, the GPS rail streaming full NMEA with ANTENNA OK, and the LoRa rail " +
      "exposing spidev1.0.",
  },
  {
    date: "2026-09-17", phase: "Radio bring-up", cat: "bringup",
    title: "Meshtastic on real hardware, US915",
    body: "meshtasticd installed and run against the SX1262 for the first time; LoRa region set to US, " +
      "the full us915.yaml applied, and the NCMesh and SCMesh channels joined.",
  },
  {
    date: "2026-09-18", phase: "Radio bring-up", cat: "bringup",
    title: "GPS fix, ADS-B, airband",
    body: "GPS reached a real fix; ADS-B tracking was installed and airband listening confirmed. GPS " +
      "was briefly wired into meshtasticd, then handed back so gpsd could own the serial port. The " +
      "node was renamed uWicked.",
  },
  {
    date: "2026-09-20", phase: "Radio bring-up", cat: "bringup",
    title: "Renamed to Fancy; Ethernet puzzle opens",
    body: "The Linux hostname moved clockworkpi→fancy (fixing a stale /etc/hosts entry). Onboard " +
      "Ethernet was first diagnosed as a hardware fault — a call later overturned (it was the " +
      "interim adapter, not the mainboard).",
  },
  {
    date: "2026-09-21", phase: "Radio bring-up", cat: "bringup",
    title: "Kismet, gpsd, and aircrack-ng",
    body: "Kismet installed with group-based (no-sudo) capture; a monitor-capable Ralink RT5370 was " +
      "found already attached, standing in for the still-pending AC1200. gpsd was swapped back from " +
      "meshtasticd so tools could share the receiver. aircrack-ng was installed for authorized " +
      "WPA/WPA2 auditing only — own gear or written authorization, spelled out in CLAUDE.md.",
  },

  // ---- The dashboard ----
  {
    date: "2026-09-21", phase: "The dashboard", cat: "webdash",
    title: "First dashboard — one page behind a login",
    body: "A single Docker container (FastAPI + Uvicorn on python:3.12-slim) serving a TOTP-gated page " +
      "that aggregates the status of aiov2_ctl, Kismet, gpsd, meshtasticd and readsb. Modelled on the " +
      "sibling CyberDeck dashboard, but scoped to aggregate services that already run their own " +
      "daemons rather than own the hardware. A WebSocket close-code bug was found and fixed in testing.",
    prompt: "Build me an operator dashboard like the CyberDeck one, but for this build — a single " +
      "authenticated page that pulls together the status of every radio and service.",
  },
  {
    date: "2026-09-21", phase: "The dashboard", cat: "webdash",
    title: "Rails become switches, apps get proxied",
    body: "Panels regrouped by use case. The AIO V2 rails turned from read-only status into real " +
      "toggle switches (POST /api/aiov2/rail) — hardware control past the original read-only v1 " +
      "scope. tar1090's ADS-B map was reverse-proxied through the app; Kismet and meshtasticd's own " +
      "UIs were linked via their own tailscale serve mappings. A mesh-collector reconnect bug that " +
      "spammed broken-pipe tracebacks was fixed by holding one persistent connection.",
    prompt: "Group the panels by what they're for and declutter it — and let me actually flip the " +
      "rails on and off from the page, not just read them.",
  },
  {
    date: "2026-09-21", phase: "The dashboard", cat: "webdash",
    title: "Reachable over the tailnet",
    body: "Exposed via tailscale serve with a real Tailscale-issued cert. The app's own Uvicorn bind " +
      "stayed loopback-only; Tailscale does the proxying. Confirmed tailnet-only (serve, not funnel) " +
      "— never exposed to the public internet.",
    prompt: "Make it reachable from my other devices over HTTPS through Tailscale, but keep it off " +
      "the public internet.",
  },
  {
    date: "2026-09-22", phase: "The dashboard", cat: "webdash",
    title: "Sub-pages embedded as frames, gated by rails",
    body: "tar1090, Kismet and meshtasticd's own UIs were made available inline as iframes in their " +
      "panels, each gated by the radio rail its panel depends on, with an “Open ↗” link " +
      "beside each. (The mesh and Kismet frames were later removed; only the same-origin tar1090 one " +
      "survived the redesign, and it, too, moved to its own tab.)",
    prompt: "Make the other web UIs available inside the dashboard, each gated by the same radio that " +
      "gates its panel.",
  },
  {
    date: "2026-09-23", phase: "The dashboard", cat: "webdash",
    title: "Mesh text messaging",
    body: "The Meshtastic panel gained a message log and a send box talking to meshtasticd over its " +
      "TCP API (the CyberDeck MeshClient pattern, but with no serial ownership). A 15 s keepalive " +
      "keeps the interface connected so messages arrive with no dashboard open; a 200-message buffer, " +
      "broadcast-only send, text inserted with textContent only.",
    prompt: "Let me read and send Meshtastic messages straight from the dashboard.",
  },
  {
    date: "2026-09-23", phase: "The dashboard", cat: "webdash",
    title: "The design team proposes a redesign",
    body: "Six agents (design planning, creative direction, web UI, syllabus, tutor, guided learning) " +
      "reviewed webdash and produced webdash-design.md: one station per radio, a learning layer with " +
      "explainers, a 12-module syllabus and missions checked against live data, and an 8-phase build " +
      "plan. Four messaging bugs the review surfaced were fixed.",
    prompt: "Have the design team look over webdash and come back with a redesign — and a way to " +
      "actually learn the radio concepts from the live device.",
  },
  {
    date: "2026-09-23", phase: "The dashboard", cat: "webdash",
    title: "Redesign phases 1–3 built",
    body: "Status became a word + glyph, never colour alone, and reflects the rail that powers each " +
      "service. Rail switches work from the keyboard. One shared 3 s collection loop replaced " +
      "per-client polling, with 2 h of vitals history at /api/history. The layout became an overview " +
      "of six station tiles with per-station detail views, hash-routed, fitting the uConsole screen " +
      "with no scrolling. GPS shows a Maidenhead grid square unless coordinates are revealed.",
    prompt: "Build the redesign: station tiles that fit the screen, keyboard-driven, one collection " +
      "loop, and keep GPS to a grid square by default.",
  },

  // ---- NVMe upgrade & bring-up tests ----
  {
    date: "2026-09-23", phase: "NVMe upgrade & bring-up tests", cat: "arrival",
    title: "HackerGadgets kit #11953 delivered",
    body: "Ordered 09-03, shipped 09-14, delivered 09-23: the CM4/5 Adapter Pro, the NVMe battery " +
      "board and the RJ45 + USB3 board. Its arrival unblocked the NVMe boot, the JST LiPo path, and " +
      "wired Ethernet.",
  },
  {
    date: "2026-09-23", phase: "NVMe upgrade & bring-up tests", cat: "hardware",
    title: "Root migrated to NVMe; a batch of tests pass",
    body: "The kit was fitted with a WD PC SN730 256 GB (M.2 2280, OPAL, not locked) as root. " +
      "NVMe-only boot passed with the microSD removed; onboard Ethernet linked at 1 Gbps and the pack " +
      "charged at ~2 A; the RJ45/USB3 ports enumerated; JP1 confirmed open (correct for the 18650s), " +
      "closing checklist 1.7. A baseline file-level backup was taken to another host.",
  },

  // ---- Knowledge & learning ----
  {
    date: "2026-09-23", phase: "Knowledge & learning", cat: "docs",
    title: "doc-review agent; stale claims fixed",
    body: "A read-only doc-review agent was added to check that documented claims are still true " +
      "against the newest dated evidence and the live device. Its first two runs found ~20 stale " +
      "claims (NVMe/kit still “pending”, microSD still “inserted”, AC1200 " +
      "“pre-order”, checklist items shown open after they passed), fixed across 17 files.",
    prompt: "Add an agent that keeps catching documentation that's gone stale against the real device, " +
      "and fix what it finds.",
  },
  {
    date: "2026-09-24", phase: "Knowledge & learning", cat: "docs",
    title: "Licence, learning-platform plan, RF reviewer",
    body: "A licence was added (docs/knowledge CC BY 4.0, code/configs MIT). A six-agent analysis " +
      "produced the learning-platform plan — 38 concepts with a dependency graph, 3 tracks / 15 " +
      "modules, 21 labs with automated validation. A senior-rf-engineer agent joined the team and its " +
      "hardware-scope review was applied (NOAA APT dropped, BLE limited to passive, numbers corrected).",
    prompt: "Plan a learning platform built on the knowledge base, with a hands-on lab on this device " +
      "per module — and have an RF engineer check every exercise fits the real hardware and the " +
      "legal posture.",
  },
  {
    date: "2026-09-25", phase: "Knowledge & learning", cat: "webdash",
    title: "Wi-Fi interface collector + learning MVP",
    body: "Added net.py, reading Wi-Fi interface modes (managed / monitor) from sysfs without ever " +
      "touching MAC addresses. The learning platform's MVP landed — curriculum compiler, #/learn " +
      "pages, SQLite progress, a lab engine with graded checks, and Track A — then the whole team " +
      "reviewed Track A and fixed collector bugs that had made labs unpassable.",
    prompt: "Build the learning platform from the plan — lessons and hands-on labs checked against " +
      "Fancy's real data — and have the team review it.",
  },
  {
    date: "2026-09-25", phase: "Knowledge & learning", cat: "bringup",
    title: "First passive Wi-Fi survey (LAB-15)",
    body: "The first passive 2.4 GHz survey ran end to end on the RT5370 and was filed as a finding. " +
      "It drove real config fixes (Kismet binding to loopback, data/EAPOL frames confirmed absent " +
      "from the log) and new M7 knowledge docs on passive Wi-Fi and BLE observation.",
  },
  {
    date: "2026-09-26", phase: "Knowledge & learning", cat: "bringup",
    title: "GPU crack-offload + authorized handshake capture",
    body: "The crack-offload path to gpu-host-wsl (Kali WSL, RTX 3070 Ti) was validated, and " +
      "LAB-22 ran a hardware dry-run of an authorized WPA2 handshake capture against an owned AP — " +
      "inside the own-gear / documented-authorization carve-out.",
  },

  // ---- Last part in & field tuning ----
  {
    date: "2026-09-30", phase: "Last part in & field tuning", cat: "arrival",
    title: "AC1200 Wi-Fi card received and installed",
    body: "Ordered 09-15, shipped 09-21, installed and verified 09-30 — the last outstanding BOM " +
      "component. A MediaTek MT7921AUN: wlan1 with monitor mode on 2.4 / 5 / 6 GHz and Bluetooth on " +
      "hci1. It feeds the four antenna ports that had no radio behind them, closing that blocker.",
  },
  {
    date: "2026-10-01", phase: "Last part in & field tuning", cat: "webdash",
    title: "SDR beyond ADS-B; survey & diagnostics",
    body: "The SDR view gained a receive-only band hunt (FM / airband) and live listening (rtl_fm " +
      "→ ffmpeg MP3 to a browser <audio>) with a NOAA weather picker, through a host bridge that " +
      "brackets readsb on the shared tuner. A Kismet Start/Stop button and authenticated Kismet reads " +
      "landed. An authorized WPA audit pipeline was added, kept narrow by a server-enforced BSSID " +
      "allowlist. The Pi under-voltage throttle and 1 h average CPU temp were surfaced for the Fancy " +
      "hang / undervoltage investigation.",
    prompt: "Open up the SDR for receive-only FM/airband/NOAA listening, let me start Kismet from the " +
      "page, add the authorized WPA audit behind an allowlist, and surface the under-voltage and " +
      "temperature signals I need for the hang diagnosis.",
  },
  {
    date: "2026-10-02", phase: "Last part in & field tuning", cat: "bringup",
    title: "GPS disciplines the clock; mesh gets position",
    body: "chrony replaced systemd-timesyncd so GPS time keeps the clock correct offline (fixing " +
      "offline TOTP and timestamps). A new mesh-gps-bridge pushes the gpsd fix into meshtasticd over " +
      "its admin API, so the node shares position on the mesh while gpsd still owns the serial port.",
  },
  {
    date: "2026-10-03", phase: "Last part in & field tuning", cat: "webdash",
    title: "SDR rail made power-only; ADS-B becomes a choice",
    body: "Turning the SDR rail on now only powers the tuner; ADS-B, the band hunt and listening are " +
      "three applications that share it, so starting one stops the others. The SDR view gained an " +
      "airband scanner that pauses on traffic and a NOAA picker that follows the GPS fix.",
    prompt: "Make the SDR rail just power the tuner and let me pick which app runs on it — and add " +
      "an airband scanner and a NOAA picker that follows my location.",
  },
  {
    date: "2026-10-04", phase: "Last part in & field tuning", cat: "hardware",
    title: "RTC backup cell fitted; GNSS first fix recorded",
    body: "A coin cell was fitted to the PCF85063A RTC and confirmed to hold time across a cold " +
      "power-off, closing a long-standing blocker. The GNSS first 3D fix was recorded as a finding — " +
      "15 satellites used (10 GPS + 5 GLONASS), HDOP 0.7, grid EM94 (coordinates kept off-repo). The " +
      "mechanical audit was cleared to 0 findings.",
  },
  {
    date: "2026-10-04", phase: "Last part in & field tuning", cat: "webdash",
    title: "A second “vintage” skin",
    body: "A selectable alternative skin was added — the faceplate of a mid-century Simpson " +
      "analog panel meter — re-pointing the same CSS tokens the rest of the sheet reads, with no " +
      "theme-specific markup.",
    prompt: "Give the dashboard a second skin that looks like an old analog panel meter, switchable " +
      "without touching the markup.",
  },
  {
    date: "2026-10-06", phase: "Last part in & field tuning", cat: "webdash",
    title: "WatchDogsGo (passive) + packet-capture tap",
    body: "WatchDogsGo was installed as a passive layer only — the game isn't launched and its " +
      "system reconfig isn't applied; active attacks stay out of scope. The System view gained a " +
      "passive tshark packet-capture tap to a bounded ring buffer, for the hang/dropout diagnosis, " +
      "alongside a new curriculum module.",
    prompt: "Install WatchDogsGo but keep it passive and in-scope, and add a passive packet-capture " +
      "tap I can use to chase the hangs.",
  },
  {
    date: "2026-10-08", phase: "Last part in & field tuning", cat: "webdash",
    title: "A Wi-Fi site-survey tool, built on the fly from parts already here",
    body: "A new need — walk a building and survey its Wi-Fi — was met without buying or flashing " +
      "anything: the AC1200 in monitor mode + Kismet (passive) became the capture radio, gpsd tagged " +
      "each waypoint with a grid square, and webdash gained a survey workflow — start, drop GPS-tagged " +
      "waypoints, generate a technical and an executive report (PDF or Markdown). It then grew an " +
      "SSID-focused mode with per-AP, per-waypoint signal, channel width, overlap (co-channel vs " +
      "harmful adjacent) and contention (from each AP's own QBSS beacon load), plus a site map. The " +
      "senior-rf-engineer agent designed the metrics and, reviewing a real 12-BSSID guest network " +
      "walked across a facility, caught two field bugs (Kismet's min/max signal and client counts are " +
      "whole-capture cumulative, not per-waypoint) and gated “self co-channel” so healthy " +
      "frequency reuse stopped being over-reported. Receive-only throughout; no SNR or airtime " +
      "invented, counts are lower bounds. The first counts-only survey (2026-09-25) grown into a " +
      "repeatable instrument.",
    prompt: "I need to do a Wi-Fi site survey — build it from what the system already has, add an " +
      "SSID-focused report with overlap and contention, and bring in the RF engineer for the design.",
  },
];

// Group consecutive milestones under their phase heading.
function phases(items) {
  const out = [];
  for (const m of items) {
    const last = out[out.length - 1];
    if (last && last.phase === m.phase) last.items.push(m);
    else out.push({ phase: m.phase, items: [m] });
  }
  return out;
}

function el(tag, cls, text) {
  const n = document.createElement(tag);
  if (cls) n.className = cls;
  if (text != null) n.textContent = text;
  return n;
}

let built = false;

// Static content — build the DOM once, on first visit to #/timeline.
export function renderTimeline(root) {
  if (!root || built) return;
  built = true;

  const intro = el("div", "panel tl-intro");
  intro.appendChild(el("h2", null, "How Fancy got built"));
  intro.appendChild(el("p", "hint",
    "The whole build in order, oldest first — orders placed, parts as they arrived, assembly, " +
    "radio bring-up, the dashboard, the NVMe upgrade, the learning platform, and field tuning. " +
    "Steps driven by a prompt to the assistant carry a callout summarising it; those are paraphrased " +
    "from the repo's CHANGELOG and build log, not verbatim transcripts."));
  const legend = el("div", "tl-legend");
  for (const key of Object.keys(CATS)) {
    const c = CATS[key];
    const chip = el("span", "tl-tag");
    chip.style.setProperty("--tag", `var(${c.tok})`);
    chip.textContent = c.label;
    legend.appendChild(chip);
  }
  intro.appendChild(legend);
  root.appendChild(intro);

  const line = el("div", "tl");
  for (const group of phases(MILESTONES)) {
    const g = el("section", "tl-phase");
    g.appendChild(el("h3", "tl-phase-head", group.phase));
    for (const m of group.items) {
      const item = el("article", "tl-item");
      item.style.setProperty("--dot", `var(${(CATS[m.cat] || CATS.hardware).tok})`);
      const card = el("div", "tl-card");

      const head = el("div", "tl-card-head");
      head.appendChild(el("time", "tl-date", m.date));
      const cat = CATS[m.cat] || CATS.hardware;
      const tag = el("span", "tl-tag", cat.label);
      tag.style.setProperty("--tag", `var(${cat.tok})`);
      head.appendChild(tag);
      head.appendChild(el("h4", "tl-title", m.title));
      card.appendChild(head);

      card.appendChild(el("p", "tl-body", m.body));

      if (m.prompt) {
        const callout = el("div", "tl-callout");
        callout.appendChild(el("span", "tl-callout-label", "Prompt"));
        callout.appendChild(el("p", "tl-callout-text", m.prompt));
        card.appendChild(callout);
      }

      item.appendChild(card);
      g.appendChild(item);
    }
    line.appendChild(g);
  }
  root.appendChild(line);
}
