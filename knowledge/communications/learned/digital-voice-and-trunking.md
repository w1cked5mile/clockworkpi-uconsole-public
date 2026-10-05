# Digital voice modes and trunked systems

What is on VHF/UHF land-mobile spectrum, how to recognize it, and where the legal line sits.

## Digital voice modes

| Mode | Where | Recognition | Open decoder? |
|---|---|---|---|
| DMR | Commercial, amateur (Brandmeister) | 12.5 kHz, two TDMA slots — a distinctive alternating pattern | Yes, for unencrypted traffic |
| P25 Phase 1 | Public safety | 12.5 kHz FDMA, C4FM | Yes, for unencrypted traffic |
| P25 Phase 2 | Public safety | TDMA, two voice paths per channel | Yes, for unencrypted traffic |
| NXDN | Commercial, some public safety | 6.25/12.5 kHz narrow | Yes, for unencrypted traffic |
| D-STAR | Amateur | 6.25 kHz GMSK | Yes |
| System Fusion (C4FM) | Amateur | 12.5 kHz | Yes |

**Encrypted traffic stays encrypted.** Many public-safety systems encrypt some or all talkgroups;
attempting to defeat that is not a decoding exercise, it is unlawful. Decoding *unencrypted*
public-safety audio is legal in most US states but not all — verify your state's rules, and note
that recording or divulging can carry separate restrictions.

## Trunking

Conventional systems assign one frequency per channel. **Trunked** systems pool frequencies and
assign them per call, directed by a control channel.

To follow a trunked system you must:

1. Find and lock the **control channel** (a continuous data stream, distinctive on a waterfall).
2. Decode the channel-grant messages.
3. Retune to the assigned voice frequency for each call.

On a single-tuner RTL-SDR this means either following one talkgroup at a time, or capturing enough
bandwidth to hold the control channel and the voice channel simultaneously — which the ~2 MS/s
ceiling on this build allows only when the system's frequencies are close together.

`op25` and `sdrtrunk` implement this; `trunk-recorder` targets multi-dongle setups.

## Other things living in this spectrum

| Signal | Frequency | Notes |
|---|---|---|
| NOAA weather radio | 162.400–162.550 MHz | Always on — the best antenna test on the band |
| Marine VHF | 156–162 MHz | Voice; AIS occupies 161.975 / 162.025 |
| Business itinerant | 151–159, 461–469 MHz | Short-range commercial |
| GMRS / FRS | 462 / 467 MHz | Licensed (GMRS) and license-free (FRS) family radios |
| POCSAG / FLEX paging | 929–932 MHz | Still active; often unencrypted **and often carrying personal data** |

Paging deserves a specific caution: it frequently carries medical and personal information.
Receiving it is trivially easy; storing or divulging its contents is exactly what the ECPA
addresses. Classify and move on.

## Practical approach on this build

1. Identify the mode from bandwidth and waterfall shape
   ([`../../rf-fundamentals/learned/modulation-basics.md`](../../rf-fundamentals/learned/modulation-basics.md)).
2. Confirm with a decoder only where the traffic is unencrypted and lawful to decode.
3. Log the system type, frequencies, and technical observations — not message contents.

Legal framing: [`../../rf-fundamentals/learned/us-spectrum-and-legal.md`](../../rf-fundamentals/learned/us-spectrum-and-legal.md).
