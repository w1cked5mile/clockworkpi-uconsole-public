---
id: messages-per-second
term: Messages per second (ADS-B)
tooltip: How many Mode S / ADS-B messages readsb decodes each second.
good_bad: "Any value above 0 proves the receive chain works. Fancy's whip indoors decoded about 9/s on 2026-09-24."
try_this: Change the whip length and compare the rate back-to-back, over the same few minutes — traffic changes over time.
learn_more: "#/learn/m/M6"
live: adsb.messages_per_s
live_prompt: "readsb is decoding {value} messages per second. What does any value above zero prove?"
example: "9"
---

Each aircraft transmits several short messages a second on 1090 MHz in Mode S, the transponder
format ADS-B rides on. The rate readsb decodes depends on how many aircraft are in range and how
good the antenna and its placement are, so it is the best single number for comparing setups.
