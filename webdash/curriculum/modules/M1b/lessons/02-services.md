---
id: M1b.services
title: Services and restart loops
est_minutes: 25
glossary: [crash-loop]
---

**systemd** is the program that starts Linux's background services at boot and restarts them
when they fail. Every radio on Fancy has one: gpsd for GPS, meshtasticd for the mesh, readsb for
aircraft.

@ref docs/reference/platform-basics/systemd.md#units-enabled-and-active

@ref docs/reference/platform-basics/systemd.md#restart-loops

Right now systemd reports readsb as **{live:services.readsb.active}**
({live:services.readsb.sub}), restarted {live:services.readsb.n_restarts} times; crash-looping:
{live:services.readsb.crash_looping}. gpsd is {live:services.gpsd.active}, meshtasticd
{live:services.meshtasticd.active}, Kismet {live:services.kismet.active}.

@ref docs/reference/platform-basics/systemd.md#the-journal
