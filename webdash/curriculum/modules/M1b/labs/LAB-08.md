---
id: LAB-08
title: Is the receiver alive?
themed_title: Sea trial · Sound the receiver
mode: guided
est_minutes: 15
requires: {rails: [SDR], services: [readsb]}
transmits: false
steps:
  - id: sdr-on
    text: "Switch the SDR rail on (on this page)."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to take the dongle. If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: claim-error
    text: "In a terminal on Fancy, run rtl_test -t and paste the output. With readsb holding the dongle it should fail."
    check: {type: paste, parser: rtl_test_t, expect_claim_error: true}
  - id: stop-readsb
    text: "Free the dongle: sudo systemctl stop readsb"
    check: {type: status, path: services.readsb.active, op: ne, value: active}
  - id: found
    text: "Run rtl_test -t again and paste the output. It should find the device and its tuner. The tuner reports as R820T on this build — the board is sold as R860; same family."
    check: {type: paste, parser: rtl_test_t}
  - id: samples
    text: "Run timeout 30 rtl_test -s 2048000 and paste the output, including the final summary line."
    check: {type: paste, parser: rtl_test_loss, max: 5}
  - id: restart-readsb
    text: "Give the dongle back: sudo systemctl start readsb"
    check: {type: status, path: services.readsb.active, op: eq, value: active}
  - id: sdr-off
    text: "Switch the SDR rail off. readsb goes back to its normal crash loop."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
restore:
  - {type: status, path: aiov2.rails.SDR.on, op: eq, value: false}
  - {type: status, path: services.readsb.active, op: ne, value: inactive}
evidence: []
---

`[R82XX] PLL not locked!` in the output is harmless on this build. A few samples lost per
million is normal on the CM4's shared USB bus. Only the result of each paste is kept, never the
text itself. The passwordless `systemctl stop|start readsb` comes from the scoped sudoers rule in
`software/adsb-tar1090.md`.
