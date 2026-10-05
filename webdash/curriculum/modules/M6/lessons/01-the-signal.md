---
id: M6.signal
title: What is on 1090 MHz
est_minutes: 20
glossary: [messages-per-second, crash-loop]
---

**ADS-B** (Automatic Dependent Surveillance–Broadcast) is aircraft broadcasting their own
position, altitude and identity, with no radar asking. It rides on **Mode S**, the transponder
format, as an "extended squitter" — a squitter is an unprompted broadcast. **UAT** is a
separate US system on 978 MHz that Fancy doesn't decode.

@ref knowledge/aerospace/learned/adsb-basics.md#the-signal

The signal is vertically polarised, so hold the whip vertical.

On Fancy the decoder is **readsb** and the map is **tar1090**. readsb needs the SDR rail: with
the rail off it restarts in a loop, which is normal. Right now readsb is **{live:adsb.state}**
and systemd reports it as {live:services.readsb.active} ({live:services.readsb.sub}).

When it runs, the SDR station shows the decode rate: **{live:adsb.messages_per_s}** messages per
second from **{live:adsb.aircraft_count}** aircraft. With the SDR rail off these read "—".
