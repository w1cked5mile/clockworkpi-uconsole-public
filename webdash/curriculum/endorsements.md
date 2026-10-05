---
# Endorsements (badges). Each is awarded once, from evidence the server saw — never for time,
# streaks, or transmitting (creative direction, plan §3.8). A rule lists labs and/or checks that
# must all have passed. Only endorsements whose labs exist are listed; the rest of the set in the
# plan arrives with its modules.
endorsements:
  - id: rules-of-the-road
    name: Rules of the Road
    plain: Rules and safety passed
    type: S
    when: Every M0 question right, including the ones about what makes Fancy transmit.
    rule: {assessment_pass: [M0.quiz]}
  - id: walked-the-deck
    name: Walked the Deck
    plain: Orientation done
    type: L
    when: LAB-00 passed.
    rule: {lab_pass: [LAB-00]}
  - id: first-sighting
    name: First Sighting
    plain: First aircraft decoded
    type: L
    when: LAB-12 passed — readsb reported an aircraft with a position, and the SDR rail went back off.
    rule: {lab_pass: [LAB-12]}
  - id: know-the-load
    name: Know the Load
    plain: Power measured
    type: L
    when: LAB-02 passed — the SDR's cost measured on battery, and the charger back on.
    rule: {lab_pass: [LAB-02]}
  - id: fix-taken
    name: Fix Taken
    plain: First GPS fix
    type: L
    when: LAB-04 passed — a 3D fix with at least four satellites used, and time to first fix recorded after you cycled the GPS rail.
    rule: {lab_pass: [LAB-04]}
  - id: first-hail-heard
    name: First Hail Heard
    plain: First mesh packet received
    type: L
    when: LAB-06 passed — a packet from another node, receive only.
    rule: {lab_pass: [LAB-06]}
  - id: signal-report
    name: Signal Report
    plain: Read a signal report
    type: L+S
    when: LAB-06 passed and the M4 check passed.
    rule: {lab_pass: [LAB-06], assessment_pass: [M4.quiz]}
  - id: quiet-survey
    name: Quiet Survey
    plain: Passive survey done cleanly
    type: L
    when: LAB-15 passed — Kismet surveyed on the USB adapter, wlan1 came back in managed mode, and wlan0 was never touched.
    rule: {lab_pass: [LAB-15]}
  - id: running-lights
    name: Running Lights
    plain: Bluetooth LE observed passively
    type: L
    when: LAB-21 passed — btmon's record shows a passive scan with no scan requests and no scan responses, and its filtered log holds no addresses.
    rule: {lab_pass: [LAB-21]}
---
