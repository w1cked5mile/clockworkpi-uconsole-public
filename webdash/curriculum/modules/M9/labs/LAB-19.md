---
id: LAB-19
title: Record an ISS pass
themed_title: Sea trial · Catch the pass
mode: guided
est_minutes: 60
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Receive only. You plan a pass of the ISS packet digipeater, record it from before AOS through LOS, and decode afterwards. This WAITS ON THE WORLD twice over: the ISS packet station must be ON (check first - it has run on 145.825 and 437.825 MHz and been off entirely), and you need a predicted pass above ~30 degrees, which may be hours away or overnight. The planning steps you can always do; the capture you do when a good pass arrives. Decoding packets is a bonus - a clean recording spanning the pass is the pass-mark. Receive only: Fancy has no amateur transmitter and never beacons."
steps:
  - id: check-status
    text: "Check the ISS packet digipeater's CURRENT frequency and status before anything else (it has run on 145.825 MHz and on 437.825 MHz, and been switched off). Use n2yo.com, the ARRL news, or an ISS status page. Decide your target frequency: 145.825 MHz (2 m, Doppler ~±3.4 kHz, no retune) or 437.825 MHz (70 cm, Doppler ~±10 kHz, needs -s 48k). Attest you confirmed the station is active and chose a frequency."
    check: {type: attest, prompt: "I confirmed the ISS packet digipeater is currently active and chose my target frequency (145.825 or 437.825 MHz) with its Doppler in mind."}
  - id: plan-pass
    text: "Predict a pass with n2yo.com (gpredict is not installed): get AOS and LOS in UTC, the maximum elevation, and the direction. Pick a pass above ~30 deg for a first attempt; below ~20 deg expect mostly noise. If the elements look old, refresh them first - a stale TLE is the most common cause of 'nothing at the predicted time'. Attest you have AOS/LOS, a max elevation, and direction for a specific upcoming pass."
    check: {type: attest, prompt: "I predicted a specific upcoming pass with AOS/LOS (UTC), maximum elevation (aiming for >=30 deg) and direction, from fresh orbital elements."}
  - id: sdr-on
    text: "When the pass is near, switch the SDR rail on (on this page, or aiov2_ctl SDR on)."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to take the dongle. If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: stop-readsb
    text: "Free the dongle from readsb: sudo systemctl stop readsb"
    check: {type: status, path: services.readsb.active, op: ne, value: active}
  - id: antenna
    text: "Set up outdoors with a clear view of the sky along the pass direction. Extend the whip for your band: ~490 mm for 2 m (145.825) or ~160 mm for 70 cm (437.825), vertical. A whip loses ~3 dB into the circular downlink and more at low elevation, so height and a clear horizon matter most. Attest the antenna is set for your target band, outdoors."
    check: {type: attest, prompt: "I set up the whip for my target band (~490 mm for 2 m or ~160 mm for 70 cm), vertical, outdoors with a clear sky view."}
  - id: capture
    text: "Start recording about a minute BEFORE AOS and run through LOS; decode afterwards, gain fixed the whole time. For 2 m: timeout 900 rtl_fm -f 145.825M -M fm -s 22050 -g 35 -p 1 - | tee ~/labs/iss-pass-$(date -u +%Y%m%dT%H%MZ).raw | multimon-ng -t raw -a AFSK1200 -A - . For 70 cm use -f 437.825M -s 48k instead (wider for the ±10 kHz Doppler). Let it run the full pass. The check confirms the raw recording spans several minutes; decoded packets ('APRS:' lines) are a bonus, not required to pass."
    check: {type: file, op: size_range, path: "~/labs/iss-pass-*.raw", min: 6000000, fresh: true}
    timeout_s: 1000
  - id: finding
    text: "File a finding for the pass: target and frequency, AOS/LOS (UTC) and maximum elevation, antenna/gain/PPM, general location (grid square only), and the honest result - packets decoded, audio only, or nothing, and at what point in the pass. Grade it against the geometry. Save it in the repo as knowledge/aerospace/findings/<date>-iss-pass.md (date YYYY-MM-DD, UTC)."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/aerospace/findings/*-iss-pass.md", pattern: '(?im)^#', min: 1, fresh: true}
  - id: restart-readsb
    text: "Give the dongle back to readsb: sudo systemctl start readsb"
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

A planned pass, recorded end to end. The check confirms you captured a real multi-minute recording
spanning the pass and filed a finding; whether packets decoded is a bonus, because the skill this module
teaches is the planning and capture discipline - check the station, predict the pass, respect Doppler
and elevation, record then decode. A pass with nothing is a real result you diagnose from the plan
(stale TLE, low elevation, or an inactive station), not a hardware fault. The raw recording lives in
~/labs (gitignored); the finding carries the summary. All receive-only - Fancy never beacons.
