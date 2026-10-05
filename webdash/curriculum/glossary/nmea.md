---
id: nmea
term: NMEA 0183
tooltip: The comma-separated text sentences a GNSS receiver sends, like $GNGGA and $GNRMC.
good_bad: "Sentences streaming means the receiver is powered and talking; a fix is a separate question."
try_this: "gpspipe -r -n 20 — read them through gpsd, never straight off /dev/serial0."
learn_more: "#/learn/m/M3"
---

A National Marine Electronics Association standard that GNSS receivers adopted. Each sentence
starts with `$`, a two-letter talker (GP, GB, GN…) and a type (GGA, RMC, GSV…), and ends with a
checksum.
