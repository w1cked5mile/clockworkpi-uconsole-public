---
id: LAB-02
title: Rail economics
themed_title: Sea trial · Know your power
mode: guided
est_minutes: 10
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Nothing outside — but it runs on battery, so start with the pack charged."
steps:
  - id: sdr-off-first
    text: "Start with the SDR rail off, so the baseline doesn't include it."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - id: unplug
    text: "Unplug the charger. The measurement only means something on battery."
    check: {type: status, path: aiov2.power_num.on_battery, op: eq, value: true}
  - id: idle
    text: "Leave everything as it is for a minute: this is the baseline."
    check: {type: computed, fn: mean, path: aiov2.power_num.power_w, window_s: 60, save_as: idle_w}
  - id: sdr-on
    text: "Switch the SDR rail on (the switch is on this page)."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to start decoding — up to about a minute. If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: sdr
    text: "Another minute with SDR on and readsb decoding."
    check: {type: computed, fn: mean, path: aiov2.power_num.power_w, window_s: 60, save_as: sdr_w}
  - id: delta
    text: "The difference is what the SDR costs while ADS-B is decoding."
    check: {type: computed, fn: delta, a: sdr_w, b: idle_w, op: gte, value: 0.3, save_as: sdr_delta_w}
  - id: sdr-off
    text: "Switch the SDR rail off."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - id: plug-in
    text: "Plug the charger back in."
    check: {type: status, path: aiov2.power_num.on_battery, op: eq, value: false}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
  - {type: status, path: aiov2.power_num.capacity_pct, op: lte, value: 30}
restore:
  - {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - {type: status, path: aiov2.power_num.on_battery, op: eq, value: false}
evidence: [aiov2.power_num.voltage_v]
---

Expect roughly +1.1 to +1.6 W (*estimate*): the rail alone measured +0.64 W with nothing
running, and readsb decoding adds more. Record what you get — it becomes the measured figure.
If the cell falls to 3.5 V or 30% the lab stops on its own.
