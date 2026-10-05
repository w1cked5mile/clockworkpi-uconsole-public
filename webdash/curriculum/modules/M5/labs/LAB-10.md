---
id: LAB-10
title: Noise-floor baseline
themed_title: Sea trial · Read the water
mode: guided
est_minutes: 25
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Broadcast FM (88-108 MHz) is always present indoors as a reference. The sweep takes about 5 minutes; let it run to the end even though the step passes earlier."
steps:
  - id: sdr-on
    text: "Switch the SDR rail on."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to take the dongle. If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: stop-readsb
    text: "Free the dongle: sudo systemctl stop readsb"
    check: {type: status, path: services.readsb.active, op: ne, value: active}
  - id: sweep
    text: "Sweep the FM band, logging power vs frequency: rtl_power -f 88M:108M:25k -i 10 -e 5m -g 20 ~/labs/baseline-fm.csv. It runs ~5 minutes and appends rows as it goes - LET IT FINISH even though this step goes green early, or your baseline will be short. Gain 20 is a reasonable knee for this band."
    check: {type: file, op: csv_shape, path: "~/labs/baseline-fm.csv", min_rows: 100}
    timeout_s: 360
  - id: finding
    text: "File a finding recording the baseline: the strongest FM carriers, the noise floor between them (dB), the gain used (20), and date + grid square. Save it in the repo as knowledge/sdr/findings/<date>-fm-baseline.md (date YYYY-MM-DD, UTC)."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/sdr/findings/*-fm-baseline.md", pattern: '^# Finding:', min: 1, fresh: true}
  - id: restart-readsb
    text: "Give the dongle back: sudo systemctl start readsb"
    check: {type: status, path: services.readsb.active, op: eq, value: active}
  - id: sdr-off
    text: "Switch the SDR rail off."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
restore:
  - {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - {type: status, path: services.readsb.active, op: ne, value: inactive}
safety_stops:
  - {type: status, path: aiov2.power_num.voltage_v, op: lte, value: 3.5}
evidence: []
---

The check confirms the CSV has real rows; you interpret it. rtl_power writes rows of power in dB
across the band, so the FM carriers stand out as peaks above the floor between them - your first look
at what "noise floor" means in numbers. The CSV is a lab output (kept in ~/labs, gitignored); the
finding holds the summary. Do not commit the CSV.
