---
id: LAB-03
title: Heat and throttling
themed_title: Sea trial · Engine room
mode: guided
est_minutes: 15
requires: {rails: [], services: []}
transmits: false
world: "Run it on AC. Nobody has run a sustained four-core load on this unit yet; if it reaches 78 °C the lab stops itself."
steps:
  - id: settle
    text: "Let Fancy settle first — nothing heavy running. If you are restarting, wait for it to cool down."
    check: {type: status, path: system.load.1m, op: lte, value: 1.5}
  - id: baseline
    text: "Leave Fancy idle for half a minute: the starting temperature."
    check: {type: computed, fn: mean, path: system.temp_c, window_s: 30, save_as: temp_idle}
  - id: load
    text: "In a terminal run for i in 1 2 3 4; do timeout 300 yes > /dev/null & done — four busy loops, one per core, each stopping by itself after 5 minutes. The 1-minute load average climbs past 3."
    check: {type: status, path: system.load.1m, op: gte, value: 3}
    timeout_s: 180
  - id: hot
    text: "Keep it running for another minute while the temperature climbs."
    check: {type: computed, fn: mean, path: system.temp_c, window_s: 60, save_as: temp_loaded}
  - id: rise
    text: "How much did the load heat the CPU?"
    check: {type: computed, fn: delta, a: temp_loaded, b: temp_idle, op: gte, value: 3, save_as: temp_rise}
  - id: throttled
    text: "In a second terminal run sudo vcgencmd get_throttled and paste the output. 0x0 means no throttling or under-voltage has happened since boot."
    check: {type: paste, parser: vcgencmd_throttled, save_as: throttled}
  - id: stop-load
    text: "Stop the busy loops with pkill -x yes (Ctrl-C won't reach background jobs) and let the load fall back."
    check: {type: status, path: system.load.1m, op: lte, value: 1.5}
    timeout_s: 300
safety_stops:
  - {type: status, path: system.temp_c, op: gte, value: 78}
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
restore:
  - {type: status, path: system.load.1m, op: lte, value: 1.5}
evidence: [system.temp_c]
---

The CM4's firmware starts slowing the CPU at 80 °C, so the lab stops itself at 78 °C, just before;
`get_throttled` then shows whether capping happened anyway. If it stops, run `pkill -x yes`. Idle
on this build has read 62–64 °C (above the bring-up checklist's "under 60 °C" bar, item 1.4). In
the `throttled=` value, bit 0 means under-voltage now, bit 1 ARM frequency capped, bit 2 throttled
now, bit 3 soft temperature limit active, and bits 16–19 the same things "has happened since
boot".
