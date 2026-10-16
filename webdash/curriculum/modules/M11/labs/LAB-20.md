---
id: LAB-20
title: Shakedown cruise
themed_title: Sea trial · The shakedown
mode: guided
est_minutes: 150
requires: {rails: [SDR, GPS, LORA, USB], services: [readsb]}
transmits: false
world: "A ~2 h session on battery with GPS, mesh RX, ADS-B and a Wi-Fi survey all live, receive-only. This lab is POWER-GATED; the gate is now met - the Meshnology pair is fitted with JP1 soldered closed (2026-10-11) and was discharge-tested (2026-10-13). Mind the measured floor: the device cuts power with no warning at ≈3.53 V under load and the fuel-gauge % is wrong, so run on voltage - plug in by 3.60 V, shut down by 3.55 V. Outdoors, with the charger to hand."
steps:
  - id: gate
    text: "POWER-SAFETY GATE. The battery path is verified (Meshnology LiPo fitted with JP1 soldered closed, 2026-10-11, and discharge-tested 2026-10-13). Before the run: the cell must be charged and the charger within reach, and you run on voltage because the % gauge is wrong - plug in by 3.60 V, shut down by 3.55 V. Attest you are set up and know the floor."
    check: {type: attest, prompt: "The battery path is verified (Meshnology pack fitted with JP1 closed), the cell is charged, the charger is to hand, and I will plug in by 3.60 V and shut down by 3.55 V."}
  - id: compose
    text: "Compose your power budget BEFORE unplugging: measured ~5.0 W idle floor + 0.64 W SDR rail + 0.29 W GPS rail + ~0.5-1 W readsb decoding + ~1-1.8 W AC1200 monitor. Paste your composed average draw in watts (it lands near 7-9 W) and, in your notes, the runtime you predict from the measured 52 Wh usable."
    check: {type: paste, parser: regex, pattern: '\b(?:7|8|9)(?:\.\d+)?\b', min_matches: 1}
  - id: charged
    text: "Confirm the pack is charged before you start - aim for near full so the 2 h session has margin above the 3.55 V shut-down floor."
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
    text: "Run the session for ~2 hours with all four stations live, screen as you would use it in the field. The dashboard records the mean draw across the window. WATCH THE VOLTAGE - plug in by 3.60 V and shut down by 3.55 V (the device cuts out with no warning at ≈3.53 V). This step records the measured mean power over the 2 h window for you to compare against your composed estimate."
    check: {type: computed, fn: mean, path: aiov2.power_num.power_w, window_s: 7200, op: gte, value: 5.0, save_as: session_mean_w}
    timeout_s: 7800
  - id: reflection
    text: "Write the capstone reflection as a finding: your composed budget and predicted runtime, the measured mean draw and how long the pack actually lasted (or the voltage trend over 2 h), where measured and composed diverged and why (screen, readsb traffic, survey band activity, CPU load), and what you would change. Save it in the repo as knowledge/rf-fundamentals/findings/<date>-shakedown.md (date YYYY-MM-DD, UTC)."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/rf-fundamentals/findings/*-shakedown.md", pattern: '(?im)^#', min: 1, fresh: true}
restore:
  - {type: status, path: aiov2.power_num.on_battery, op: eq, value: false}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.6}
evidence: [aiov2.power_num.power_w, aiov2.power_num.voltage_v, aiov2.power_num.capacity_pct]
---

The shakedown is a measurement, not a demonstration. The checks confirm you ran a real ~2 h battery
session with all four stations live and recorded the mean draw; the capstone itself is the reflection -
setting what your budget predicted beside what the session measured, and accounting honestly for the
gap. The power gate is met: the Meshnology pair is fitted with JP1 soldered closed (2026-10-11) and was
discharge-tested (2026-10-13, 52.2 Wh to a hard cut at ≈3.53 V). Run it outdoors with the charger to
hand, on **voltage** not the % gauge: plug in by 3.60 V, shut down by 3.55 V. Receive-only throughout.
