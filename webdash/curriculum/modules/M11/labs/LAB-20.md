---
id: LAB-20
title: Shakedown cruise
themed_title: Sea trial · The shakedown
mode: guided
est_minutes: 150
requires: {rails: [SDR, GPS, LORA, USB], services: [readsb]}
transmits: false
world: "A ~2 h session on battery with GPS, mesh RX, ADS-B and a Wi-Fi survey all live, receive-only. This lab is POWER-GATED and must not be run until the battery path is verified: the fitted pack capacity-tested, OR the Meshnology pack fitted with JP1 soldered closed. As of the current build state the interim 18650 pair is unverified and JP1 is open, so do NOT run the battery session yet - compose the budget and design the session now, and run it once the gate is met. Abort immediately at 3.5 V. Outdoors, with the charger to hand."
steps:
  - id: gate
    text: "POWER-SAFETY GATE. Do not proceed to the battery run unless the battery path is verified: EITHER the fitted pack has been capacity-tested and voltage-matched, OR the Meshnology LiPo is fitted with JP1 soldered closed and its PH2.0 polarity confirmed with a meter. The cell must be charged and the charger within reach. Attest the gate is met - if it is not, stop here and do the planning steps only."
    check: {type: attest, prompt: "The battery path is verified (fitted pack capacity-tested, or Meshnology pack fitted with JP1 closed and polarity confirmed), the cell is charged, and I am ready to abort at 3.5 V."}
  - id: compose
    text: "Compose your power budget BEFORE unplugging: measured ~5.0 W idle floor + 0.64 W SDR rail + 0.29 W GPS rail + ~0.5-1 W readsb decoding + ~1-1.8 W AC1200 monitor. Paste your composed average draw in watts (it lands near 7-9 W) and, in your notes, the runtime you predict from ~31 Wh usable."
    check: {type: paste, parser: regex, pattern: '\b(?:7|8|9)(?:\.\d+)?\b', min_matches: 1}
  - id: charged
    text: "Confirm the pack is charged before you start - aim for near full so the 2 h session has margin above the 3.5 V floor."
    check: {type: status, path: aiov2.power_num.capacity_pct, op: gte, value: 90}
  - id: on-battery
    text: "Unplug from AC so the whole session runs on battery. The dashboard should show it is now on battery."
    check: {type: status, path: aiov2.power_num.on_battery, op: eq, value: true}
  - id: gps-live
    text: "Bring GPS up and get a fix (GPS rail on; wait for satellites). All four stations must be live at once for the session to count."
    check: {type: status, path: gps.satellites_used, op: gte, value: 4}
    timeout_s: 300
  - id: mesh-live
    text: "Confirm the mesh node is up and receiving (meshtasticd active). Receive only - the node listens; you do not originate traffic for this lab."
    check: {type: status, path: services.meshtasticd.active, op: eq, value: active}
  - id: adsb-live
    text: "Confirm ADS-B is decoding (readsb active on the SDR rail)."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
  - id: survey-live
    text: "Bring the Wi-Fi survey up on the AC1200 (wlan1 into monitor mode, as in M7). The dashboard should show at least one monitor interface."
    check: {type: status, path: net.monitor_ifaces, op: gte, value: 1}
    timeout_s: 120
  - id: session
    text: "Run the session for ~2 hours with all four stations live, screen as you would use it in the field. The dashboard records the mean draw across the window. WATCH THE VOLTAGE - abort at 3.5 V. This step records the measured mean power over the 2 h window for you to compare against your composed estimate."
    check: {type: computed, fn: mean, path: aiov2.power_num.power_w, window_s: 7200, op: gte, value: 5.0, save_as: session_mean_w}
    timeout_s: 7800
  - id: reflection
    text: "Write the capstone reflection as a finding: your composed budget and predicted runtime, the measured mean draw and how long the pack actually lasted (or the voltage trend over 2 h), where measured and composed diverged and why (screen, readsb traffic, survey band activity, CPU load), and what you would change. Save it in the repo as knowledge/rf-fundamentals/findings/<date>-shakedown.md (date YYYY-MM-DD, UTC)."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/rf-fundamentals/findings/*-shakedown.md", pattern: '(?im)^#', min: 1, fresh: true}
restore:
  - {type: status, path: aiov2.power_num.on_battery, op: eq, value: false}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: [aiov2.power_num.power_w, aiov2.power_num.voltage_v, aiov2.power_num.capacity_pct]
---

The shakedown is a measurement, not a demonstration. The checks confirm you ran a real ~2 h battery
session with all four stations live and recorded the mean draw; the capstone itself is the reflection -
setting what your budget predicted beside what the session measured, and accounting honestly for the
gap. The power gate is real and current: the fitted 18650 pair is unverified and JP1 is open, so the
battery run waits until that is resolved. Compose the budget and design the session now; run it when the
gate is met, outdoors, with the charger to hand and 3.5 V as the hard stop. Receive-only throughout.
