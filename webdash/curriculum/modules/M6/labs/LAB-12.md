---
id: LAB-12
title: Watch the skies
themed_title: Sea trial · First sighting
mode: guided
est_minutes: 20
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Aircraft in range. Near a city this is almost always true in daytime; allow 30 minutes."
steps:
  - id: rail-on
    text: "On the SDR station, switch the SDR rail on. The lab never does this for you."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to stop crash-looping and start decoding — under 90 seconds. If systemd shows it inactive, run sudo systemctl start readsb."
    check: {type: status, path: adsb.state, op: eq, value: running}
    timeout_s: 90
  - id: decoding
    text: "Messages are being decoded. With no aircraft in range this waits."
    check: {type: status, path: adsb.messages_per_s, op: gt, value: 0}
    world_wait: true
  - id: aircraft
    text: "At least one aircraft is tracked."
    check: {type: status, path: adsb.aircraft_count, op: gte, value: 1}
    world_wait: true
  - id: position
    text: "At least one aircraft has a position (it has sent both CPR halves)."
    check: {type: status, path: adsb.with_position, op: gte, value: 1}
    world_wait: true
  - id: map
    text: "Open the map (SDR station → Show embedded map, or tar1090 in a new tab) and find an aircraft on it."
    check: {type: attest, prompt: "I saw an aircraft on the map."}
  - id: rail-off
    text: "Before switching off, save a note on this page with Pin reading ticked and write down tar1090's farthest range — the finding needs them. Then switch the SDR rail off; readsb goes back to its normal crash loop."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - id: finding
    text: "File a finding: on this page save a note with what you saw, use Copy as finding, and save it in the repo on Fancy as knowledge/aerospace/findings/<date>-adsb-first-light.md (date as YYYY-MM-DD, UTC). Record messages per second, aircraft count and the farthest range tar1090 shows. Grid square only, never coordinates."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/aerospace/findings/*.md", pattern: '^# Finding:', min: 1, fresh: true}
restore:
  - {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: [adsb.messages_per_s, adsb.aircraft_count, adsb.with_position]
---

The SDR rail costs about 0.64 W on its own and more once readsb is decoding. Switch it off at the
end.
