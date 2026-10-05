---
id: LAB-13
title: Decode APRS
themed_title: Sea trial · Read the packets
mode: guided
est_minutes: 40
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Receive only, on 144.390 MHz (the North American APRS channel). You decode real position/telemetry packets with multimon-ng. This WAITS ON THE WORLD: it needs an APRS station, digipeater or iGate in range beaconing during your session, so a quiet window may need patience or a second session - that is normal, not a fault. Never beacon: this build has no amateur transmitter, and APRS TX needs a licence and a radio Fancy does not have."
steps:
  - id: sdr-on
    text: "Switch the SDR rail on (on this page, or aiov2_ctl SDR on)."
    check: {type: status, path: aiov2.rails.SDR.on, op: eq, value: true}
  - id: readsb-up
    text: "Wait for readsb to take the dongle (it starts when the SDR rail comes on). If it stays inactive, run sudo systemctl start readsb."
    check: {type: status, path: services.readsb.active, op: eq, value: active}
    timeout_s: 90
  - id: stop-readsb
    text: "Free the dongle from readsb so you can tune it: sudo systemctl stop readsb"
    check: {type: status, path: services.readsb.active, op: ne, value: active}
  - id: antenna
    text: "Set up for 2 m: extend the whip toward its maximum (~490-520 mm - measure yours), vertical, at a window or outdoors. There is no ground plane on the whip, so expect several dB of loss; height and a clear view matter more than anything else for catching a distant digipeater. Attest the antenna is set."
    check: {type: attest, prompt: "I extended the whip toward its ~490-520 mm maximum, vertical, at a window or outdoors for 2 m reception."}
  - id: decode
    text: "Decode APRS on 144.390 MHz and log it. Run: rtl_fm -f 144.390M -M fm -s 22050 -g 35 -p 1 - | multimon-ng -t raw -a AFSK1200 -A - | tee ~/labs/aprs-$(date -u +%Y%m%dT%H%M%SZ).log . Let it run at least 15 minutes (longer in a quiet area). multimon-ng prints decoded packets as 'APRS: CALL>DEST,path:...' lines; -A gives the APRS-aware output. The check needs at least one decoded packet in the log. If nothing appears, confirm tuning first on a known-live frequency, re-seat/raise the antenna, and be patient - APRS is bursty and depends on a station being up."
    check: {type: file, op: regex_count, path: "~/labs/aprs-*.log", pattern: '^APRS: \S+>\S+', min: 1, fresh: true}
    timeout_s: 1800
  - id: finding
    text: "File a finding recording the session: the frequency (144.390 MHz), date and grid square, antenna and gain, how long you listened, and how many distinct stations you decoded - callsigns and paths are public APRS data, but record counts and the signal-chain observations, not any message-text content. Save it in the repo as knowledge/ham-radio/findings/<date>-aprs.md (date YYYY-MM-DD, UTC)."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/ham-radio/findings/*-aprs.md", pattern: '(?im)^#', min: 1, fresh: true}
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

A real APRS decode, end to end: antenna → FM demod → AFSK1200 → AX.25 → a position you can read. The
check counts one decoded packet in your log and one finding on disk; the understanding - that you ran
the whole signal chain receive-only, and that beaconing would need a licence and a transmitter Fancy
does not have - is the point. APRS is bursty and depends on a station being on the air, so a quiet
session is a real outcome, not a failure; try again or move to higher ground. The log lives in ~/labs
(gitignored) - the finding carries the summary. All receive-only.
