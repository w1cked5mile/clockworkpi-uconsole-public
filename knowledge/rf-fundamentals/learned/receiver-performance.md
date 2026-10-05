# Receiver performance — gain, noise, and the 8-bit ceiling

Why "turn the gain up" stops helping, and what actually limits this build.

## The three numbers

| Term | Meaning | Consequence |
|---|---|---|
| Noise figure (NF) | How much noise the receiver adds | Sets the weakest recoverable signal |
| Dynamic range | Span between the noise floor and overload | Sets whether a strong signal blinds you to a weak one |
| Sensitivity | NF + required SNR + bandwidth | The practical "can I hear it" number |

The RTL-SDR's limit is **dynamic range**, not sensitivity. An 8-bit ADC provides roughly
6 dB per bit ≈ 48 dB of instantaneous range. A strong local FM or pager transmitter inside the
captured bandwidth consumes that range and desensitizes everything else — a phenomenon that looks
exactly like "my antenna got worse".

## Gain staging

Gain is not volume. The goal is enough gain to lift the signal above the ADC's quantization noise,
and no more.

1. Start with gain low (~20 dB).
2. Raise it until the noise floor just begins to rise on the waterfall.
3. Stop. If the floor rises but the signal does not, you are amplifying noise.
4. If signals appear at impossible frequencies, or the display goes mushy, you are overloading —
   back off, and consider a filter or attenuator.

Use manual gain, not AGC: AGC hides overload and makes captures incomparable between sessions.

## Overload symptoms

| Symptom | Likely cause |
|---|---|
| Ghost signals at multiple frequencies | Front-end overload / intermodulation |
| Signals that move when you retune | Images and aliases |
| Noise floor rises with gain but SNR does not | Past the useful gain point |
| Everything vanishes when a strong transmitter keys up | Dynamic-range exhaustion (desense) |

Fixes, in order of preference: reduce gain → filter the offender (FM broadcast filter, band-pass)
→ attenuate → move or reorient the antenna.

## Where an LNA helps and where it hurts

A low-noise amplifier at the antenna improves the system noise figure when feedline loss dominates
— for weak-signal work like ADS-B or satellites. Indoors near strong transmitters, an LNA usually
makes things worse by pushing the front end into overload sooner. It is not a general upgrade.

## Frequency stability

The AIO V2's RTL-SDR has a TCXO, which is a real improvement over base-model dongles: drift
after warm-up is small enough for narrowband digital work. Still measure PPM once
(`rtl_test -p`, 10+ minutes warm) and record it — every later frequency measurement inherits it.

## This build's specific limits

- 8-bit ADC → ~48 dB instantaneous dynamic range.
- ~2.048 MS/s sustainable on CM4's shared USB 2.0 bus.
- Receive only. No transmit path exists on the RTL-SDR side.
- Below ~24 MHz is not usable without direct sampling or an upconverter — treat HF as out of scope.

See also: [`db-and-link-budget.md`](db-and-link-budget.md),
[`../../sdr/learned/aio-v2-vs-hackrf.md`](../../sdr/learned/aio-v2-vs-hackrf.md).
