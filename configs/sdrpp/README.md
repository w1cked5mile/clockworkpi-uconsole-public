# SDR++ starting points

SDR++ stores its own JSON config under `~/.config/sdrpp/`. Rather than committing a
machine-specific blob, this file records the **settings that matter** so a fresh install can be
brought to a known state quickly. Fill in the "measured" column during bring-up.

**Corrected 2026-09-18** — `aiov2_ctl --add-apps` does not work on this image (see
[`../../docs/logs/known-issues.md`](../../docs/logs/known-issues.md)), so it never installed
SDR++ here. A plain `sdrpp` binary is present on this build with no apt/dpkg record of its
origin — not confirmed to be the `sdrpp-brown` fork this file previously assumed. See
[`../../software/sdr-stack.md`](../../software/sdr-stack.md) for current install status.

## Device settings (RTL-SDR on the AIO V2)

| Setting | Starting value | Why | Measured |
|---|---|---|---|
| Sample rate | 2.048 MS/s | USB 2.0 on CM4 is shared; 2.4 MS/s often drops samples | |
| Direct sampling | Off | Only relevant to HF mods, which this board does not have | |
| Bias tee | **Off** unless powering an LNA | 5 V on the SMA centre pin — see [`../../docs/reference/antennas-and-rf-connectors.md`](../../docs/reference/antennas-and-rf-connectors.md) | |
| AGC | Off, manual gain | Manual gain is repeatable; AGC hides overload | |
| PPM correction | from `rtl_test -p` | Per-dongle TCXO offset; record it once | |
| RTL AGC | Off | | |

## Band presets

| Purpose | Frequency | Mode | Bandwidth | Notes |
|---|---|---|---|---|
| Broadcast FM | 88–108 MHz | WFM | 200 kHz | Easiest first-signal sanity check |
| NOAA weather radio | 162.400–162.550 MHz | NFM | 12.5 kHz | Always-on local transmitter — good antenna test |
| Airband (AM voice) | 118–137 MHz | AM | 8 kHz | |
| NOAA APT weather satellites | 137.100 / 137.9125 / 137.62 MHz | WFM | 40 kHz | Needs a V-dipole or QFH; pass prediction required |
| ADS-B | 1090 MHz | — | — | Use tar1090/dump1090, not SDR++ |
| LoRa / ISM watch | 902–928 MHz | — | wide | Observe only; do not attempt to decode with SDR++ |
| 2 m / 70 cm amateur | 144–148 / 420–450 MHz | NFM | 12.5 kHz | Receive is unlicensed; TX is not |

## Workflow

1. Confirm the device first at the CLI: `aiov2_ctl SDR on && rtl_test -t`.
2. Set sample rate and manual gain before tuning — changing them mid-capture invalidates
   comparisons.
3. Log anything worth keeping as a finding using
   [`../../knowledge/_templates/signal-id.md`](../../knowledge/_templates/signal-id.md); per-band
   gain profiles belong in `knowledge/sdr/configs/`.
