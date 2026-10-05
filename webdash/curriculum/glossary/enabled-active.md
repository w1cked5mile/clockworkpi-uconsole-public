---
id: enabled-active
term: Enabled vs active
tooltip: 'Enabled: starts at boot. Active: running now. Two separate systemd questions.'
good_bad: stop changes active only; the service still starts at the next boot if enabled.
try_this: systemctl is-enabled readsb; systemctl is-active readsb
learn_more: '#/learn/m/M1b'
---

enable --now does both; mask stops it being started at all.
