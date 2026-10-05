---
id: snr
term: SNR (signal-to-noise ratio)
tooltip: How far a signal sits above the noise, in dB. For LoRa it can be negative and still decode.
good_bad: "LONG_FAST (SF11) decodes down to about −17.5 dB (datasheet). Fancy's desk link to the owner's Heltec V3 node read 6.5 dB."
try_this: Compare the SNR of a packet from across the room with one from outdoors.
learn_more: "#/learn/m/M4"
live: mesh.last_rx_snr
live_prompt: "The last packet Fancy heard arrived at SNR {value} dB. Would LONG_FAST still decode it, and how much margin is left?"
example: "-4"
---

A ratio, not a power: signal divided by noise, in decibels. 0 dB means the signal is as strong
as the noise. LoRa's spreading lets it recover signals below the noise.
