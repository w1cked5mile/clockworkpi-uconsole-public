---
id: LAB-18
title: Band survey and AIS
themed_title: Sea trial · Survey the traffic
mode: guided
est_minutes: 60
requires: {rails: [SDR], services: [readsb]}
transmits: false
world: "Receive only. You confirm the receiver on NOAA Weather Radio (the band's always-on control), sweep a VHF or UHF land-mobile band with rtl_power, classify at least five active channels by width and pattern, then run rtl_ais for ten minutes. AIS is expected to be SILENT here — your location is inland, so zero messages is the correct result, not a fault. Classify only: never log message contents, and treat any encrypted or paging channel as 'identified, stop there'. The whole session rides on another emitter being on the air, so a quiet band may take patience or a second session."
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
  - id: noaa-control
    text: "Confirm the receiver with a known transmitter before you survey anything. Tune NOAA Weather Radio and listen: rtl_fm -f 162.550M -M fm -s 24k -g 30 -p 1 - | aplay -t raw -r 24000 -f S16_LE -c 1 (if 162.550 is quiet here, try 162.400 / 162.425 / 162.450 / 162.475 / 162.500 / 162.525 — one is active in any US area). Audio present means antenna, gain and tuning all work. Attest you heard it."
    check: {type: attest, prompt: "I heard NOAA Weather Radio as continuous NFM voice on a 162.4xx-162.550 MHz channel, confirming the receiver works on the band."}
  - id: sweep
    text: "Sweep a land-mobile band for activity, logging power vs frequency. VHF: rtl_power -f 150M:165M:12.5k -i 10 -e 30m -g 30 ~/labs/vhf-survey.csv (or UHF: 450M:470M:12.5k). It runs ~30 minutes and appends rows as it goes - LET IT FINISH even though this step goes green early; longer integration catches intermittent users a short sweep misses. Sort or plot the CSV afterwards to rank the occupied channels."
    check: {type: file, op: csv_shape, path: "~/labs/vhf-survey.csv", min_rows: 100}
    timeout_s: 2100
  - id: classify
    text: "For each of at least FIVE active channels, open a waterfall (gqrx or SDR++) at the frequency and classify it by width and pattern: analog NFM (sloped, continuous while keyed), digital narrowband (sharp edges, repeating bursts - name the probable mode: DMR two-slot TDMA, P25 Phase 1 C4FM, NXDN narrow), or unknown. There is no P25/DMR decoder on this build, so 'digital, probably DMR' IS the honest endpoint. If a channel is encrypted or is paging, log that it is and STOP - never its contents. Save a finding as a markdown table in the repo at knowledge/communications/findings/<date>-band-survey.md (date YYYY-MM-DD, UTC) with the band, date, grid square, equipment and settings, and one table row per channel carrying its frequency, bandwidth, and a classification word (analog / digital / unknown). The check counts five classified rows; the grading - right mode, honest confidence, no content - is yours."
    check: {type: file, op: regex_count, path: "~/clockworkpi-uconsole/knowledge/communications/findings/*-band-survey.md", pattern: '(?im)^\|.*\|.*(analog|digital|unknown)\b', min: 5, fresh: true}
  - id: ais-run
    text: "Now the maritime half. Give AIS ten minutes: sudo systemctl stop readsb was already done, so run rtl_ais -n -p 1 and let it sit for 10 minutes, then Ctrl-C and paste its output. your location is inland - expect ZERO !AIVDM sentences. That silence is the correct result; you are proving the discipline and that the decoder runs, not catching ships."
    check: {type: paste, parser: rtl_ais_count}
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

A whole band, surveyed and classified, plus a disciplined AIS run that is meant to hear nothing. The
check confirms the CSV has real rows and that your finding holds five classified channels; the
judgement that matters - correct modulation, honest confidence on the digital modes, and not one line
of message content - is yours to hold. NOAA is the anchor you trust before anything else; the five
channels are the M8 workflow scaled to a survey; and the silent AIS run is the honest zero that proves
the capability travels even where the signal does not. The CSV is a lab output (kept in ~/labs,
gitignored) - do not commit it; the finding carries the summary. All receive-only.
