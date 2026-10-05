---
id: M3.nmea
title: NMEA and gpsd
est_minutes: 20
glossary: [nmea]
---

@ref knowledge/rf-fundamentals/learned/gnss-basics.md#nmea-versus-gpsd-json

To see Fancy's own sentences without disturbing gpsd:

```bash
gpspipe -r -n 20
```

They contain your position. Look, but don't paste them anywhere that gets committed — the lab
only checks their shape.
