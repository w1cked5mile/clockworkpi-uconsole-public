# Capture metadata conventions

A capture without its settings is not reproducible. These conventions apply across every
discipline in this knowledge base.

## Filename

```
YYYYMMDDTHHMMZ_<centre-freq>_<sample-rate>_<gain>_<label>.<ext>
20260915T2130Z_162550k_250k_g30_noaa-wx.cu8
20260920T1805Z_144390k_22k_g35_aprs.wav
```

UTC always. Frequencies and rates in k/M with no decimal point, so filenames sort cleanly.

## Required metadata in every finding

| Field | Why |
|---|---|
| UTC timestamp (start/end) | Many systems are schedule-driven |
| General location (city / Maidenhead grid) | Comparability without exposing a home address |
| Antenna type, orientation, height | The dominant variable in almost every result |
| Centre frequency and PPM correction applied | Frequency claims are meaningless without it |
| Sample rate | Determines what was even capturable |
| Gain setting and whether AGC was off | Gain changes make sessions incomparable |
| Software and version | Decoder behavior changes between releases |
| Result and confidence | Confirmed / probable / unknown |

## File formats

| Extension | Contents | In git? |
|---|---|---|
| `.cu8` | 8-bit unsigned IQ (rtl_sdr native) | No — gitignored |
| `.cf32` | 32-bit float IQ | No — gitignored |
| `.wav` | Demodulated audio | No, unless very small |
| `.sigmf-meta` | SigMF metadata sidecar | **Yes** — it is text and it is the point |
| `.png` | Waterfall screenshots, decoded images | Yes if small |
| `.csv` | `rtl_power` sweeps | Summarize in the finding; commit only if small |

Raw IQ is excluded by `.gitignore` (`*.iq`, `*.cf32`, `*.cs8`, `*.cu8`, `*.sigmf-data`). Store
captures on external media and reference them by filename and checksum from the finding.

## Storage discipline

```bash
sha256sum <capture> >> captures.sha256      # keep next to the media
```

At 2.048 MS/s, 8-bit IQ runs ~4 MB/s — 240 MB per minute. Check free space before long captures
and delete failed attempts promptly.

## Privacy

Never commit captures containing MAC addresses, precise coordinates, message contents, or anything
identifying an individual. Findings carry aggregates and technical characterization only — see
[`../learned/us-spectrum-and-legal.md`](../learned/us-spectrum-and-legal.md).
