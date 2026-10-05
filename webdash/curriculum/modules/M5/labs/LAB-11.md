---
id: LAB-11
title: Known transmitter and archived IQ
themed_title: Sea trial · Log a known light
mode: guided
est_minutes: 35
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "NOAA Weather Radio is an always-on voice transmitter, here on 162.475 MHz. Fit the SDR antenna (the bulkhead SMA) before you start."
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
  - id: listen
    text: "Tune NOAA Weather Radio and confirm you can hear the voice: rtl_fm -f 162.475M -M fm -s 22050 -g 30 -p 1 - | aplay -t raw -r 22050 -f S16_LE -c 1 (Ctrl-C when done). The -t raw and -c 1 matter - without them aplay tries to read a WAV header and fails. A synthesized weather voice confirms the receiver, antenna and PPM are all working."
    check: {type: attest, prompt: "I heard the NOAA Weather Radio voice on 162.475 MHz."}
  - id: capture
    text: "Archive a raw IQ capture (30 s at 250 kS/s, cu8 format): rtl_sdr -f 162.475M -s 250000 -g 30 -n 7500000 ~/labs/$(date -u +%Y%m%dT%H%MZ)_162475k_250k_g30_noaa-wx.cu8. cu8 is 2 bytes per sample, so 7,500,000 samples is exactly 15,000,000 bytes - a good check the capture completed."
    check: {type: file, op: size_range, path: "~/labs/*_162475k_250k_g30_noaa-wx.cu8", min: 15000000, max: 15000000, fresh: true}
    timeout_s: 120
  - id: finding
    text: "File a finding with the capture's filename, its sha256 (sha256sum the .cu8), the center freq / sample rate / gain, date + grid square, and that NOAA WX voice was confirmed. Save it as knowledge/sdr/findings/<date>-noaa-wx-capture.md. The .cu8 stays in ~/labs - raw IQ is gitignored and never committed."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/sdr/findings/*-noaa-wx-capture.md", pattern: '(?i)sha-?256', min: 1, fresh: true}
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

This is the whole capture discipline in one run: hear a known signal, archive the raw IQ under the
naming convention, checksum it, and record it in a finding - so the capture still means something in
a month. The exact-byte-count check (15,000,000) catches a truncated capture. The .cu8 never goes in
the repo; the finding carries its sha256 so the bytes are pinned without storing them.
