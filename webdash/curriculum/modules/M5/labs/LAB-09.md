---
id: LAB-09
title: PPM calibration
themed_title: Sea trial · Set the chronometer
mode: guided
est_minutes: 25
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "No signal needed - this measures the dongle's own crystal. Let it warm a few minutes first; the frequency drifts until the crystal settles. The measurement itself runs about 12 minutes."
steps:
  - id: sdr-on
    text: "Switch the SDR rail on (on this page, or aiov2_ctl SDR on)."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to take the dongle (it starts when the SDR rail comes on). If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: stop-readsb
    text: "Now free the dongle from readsb: sudo systemctl stop readsb"
    check: {type: status, path: services.readsb.active, op: ne, value: active}
  - id: found
    text: "Confirm the receiver: run rtl_test -t and paste the output. It should find the device; the tuner reports R820T on this build (sold as R860, same family). '[R82XX] PLL not locked!' is harmless here."
    check: {type: paste, parser: rtl_test_t}
  - id: ppm
    text: "Measure the crystal offset over ~12 minutes: run timeout 720 rtl_test -p | tee ~/labs/ppm-$(date -u +%Y%m%dT%H%MZ).log and paste the last 5-10 'cumulative PPM:' lines. It settles near +1 ppm on this build; single outliers of a few ppm are USB jitter."
    check: {type: paste, parser: rtl_test_ppm, expect: 1, tolerance: 2, save_as: ppm}
    timeout_s: 780
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

The check reads the median of the last 20 "cumulative PPM" lines and passes when it lands within
2 ppm of the build's +1. Only the result is kept, never the pasted text. The passwordless
systemctl stop|start readsb comes from the scoped sudoers rule in software/adsb-tar1090.md; the log
in ~/labs is yours and is not committed. Carry PPM=1 into the SDR runbooks after this.
