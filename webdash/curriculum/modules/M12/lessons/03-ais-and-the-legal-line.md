---
id: M12.ais-legal
title: AIS, and the legal line
est_minutes: 30
---

AIS is the maritime counterpart to ADS-B: ships broadcast their identity, position, course and speed
in the clear on two fixed VHF channels. It is an unencrypted safety broadcast meant for public
reception, so it is one of the few things on these bands you may decode freely:

@ref knowledge/communications/learned/ais-and-maritime.md#the-signal

You receive it with `rtl_ais`, which prints NMEA sentences. Both channels sit within a 50 kHz span, so
one capture covers them at once:

@ref knowledge/communications/learned/ais-and-maritime.md#receiving-it

The important thing for this build: **your location is inland.** AIS is line-of-sight VHF from
vessels, so a landlocked site hears nothing — and that silence is the expected result, not a fault.
Running `rtl_ais` here is a discipline exercise: you confirm the receiver works on the band (NOAA is
your proof of that), run the decoder, and record a message count of zero with the honest note that
the site is inland. The capability travels; the reception does not.

That AIS is fair game is the exception that frames the rule for everything else on these bands.
Receiving is broad; **recording and divulging are narrower**, and some traffic is off-limits to
decode at all:

@ref knowledge/communications/learned/ais-and-maritime.md#legality

Three lines you do not cross, pulled together:

- **Encrypted traffic** — identify that it is encrypted, then stop. Defeating encryption is not a
  decoding exercise; it is unlawful.
- **Paging (POCSAG/FLEX)** — trivially easy to receive, frequently carries medical and personal
  data. Classify the signal, never store or divulge its contents (the ECPA is exactly about this).
- **Unencrypted public-safety voice** — legal to listen to in most US states but not all, and
  recording or divulging can carry separate restrictions. Verify your state's rules first.

The survey discipline that keeps you on the right side of all three is the same one you log by:
record the technical characterization, not the message content.

@ref knowledge/communications/configs/monitoring-frequency-list.md#discipline
