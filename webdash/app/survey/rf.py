"""Pure RF helpers for the survey: channel width, center frequency, occupied span, and the
overlap between two APs' channels. No I/O, no Kismet — just the physics — so it is unit-testable
and shared by snapshot.py (per-device width/center at capture) and analysis.py (overlap between
APs at a waypoint).

Design reviewed by the senior-rf-engineer agent (2026-10-08). Key points baked in here:
- Width is read from the beacon's HT/VHT/HE operation element (Kismet `ht_mode`), NOT measured —
  the MT7921 reads it while parked on the primary 20 MHz channel; we never demodulate the full
  bonded block (and the radio is 80 MHz-capable anyway). So we can honestly *report* a neighbour's
  160 MHz width without claiming to have occupied it.
- Overlap is classified by PRIMARY channel, because 802.11 CCA/CSMA arbitrates on the primary
  20 MHz: same primary = co-channel (they defer to each other, politely sharing airtime);
  different primary but spectral overlap = adjacent-channel (they often cannot decode each other,
  so they collide — the genuinely harmful case).
- All frequencies here are MHz unless a name says kHz.
"""
import re

# 2.4 GHz non-overlapping 20 MHz channels in the common plan; everything else there overlaps.
NON_OVERLAP_24 = {"1", "6", "11"}


def width_mhz(ht_mode: str | None) -> int | None:
    """Channel width in MHz from Kismet's ht_mode string ("HT20", "HT40+", "VHT80", "VHT160",
    "VHT80+80", "HE80", …). The first integer in the string is the width; "80+80" → 80 (one 80 MHz
    segment for span purposes, the second segment is carried separately). None if unreadable."""
    if not ht_mode:
        return None
    m = re.search(r"(\d+)", str(ht_mode))
    if not m:
        return None
    w = int(m.group(1))
    return w if w in (20, 40, 80, 160, 320) else None


def channel_center_mhz(channel: str | int | None, freq_khz: int | None) -> float | None:
    """Center frequency (MHz) of the PRIMARY 20 MHz channel. Prefers Kismet's own frequency (kHz)
    when present; otherwise derives it from the channel number and band."""
    if freq_khz:
        return freq_khz / 1000.0
    try:
        ch = int(str(channel))
    except (TypeError, ValueError):
        return None
    # Band inferred from channel number ranges (2.4 GHz 1–14, else treat as 5 GHz plan). 6 GHz
    # needs the frequency, which we prefer above; this derivation is the fallback.
    if 1 <= ch <= 13:
        return 2412 + 5 * (ch - 1)
    if ch == 14:
        return 2484.0
    return 5000 + 5 * ch


def occupied_span_mhz(primary_center: float | None, width: int | None,
                      ht_center1_mhz: float | None, ht_mode: str | None) -> tuple:
    """The spectral span [lo, hi] (MHz) a channel occupies, its block center, and how we know the
    width ("beacon" or "assumed").

    Prefers Kismet's advertised block center (ht_center1, in MHz) when it is present and plausible;
    for HT40 without a center we derive the +/- offset; wider blocks without a center fall back to
    the primary center with width_source "assumed" so the report can flag it. Returns
    (lo, hi, center, width_mhz, width_source)."""
    if primary_center is None:
        return (None, None, None, None, "unknown")
    if not width:
        # No HT/VHT/HE element read → treat as a 20 MHz channel, flagged as assumed (common for a
        # 6 GHz BSSID whose HE width field we could not read).
        return (primary_center - 10, primary_center + 10, primary_center, 20, "assumed")

    center = primary_center
    source = "beacon"
    if width == 20:
        center = primary_center
    elif ht_center1_mhz and _plausible(ht_center1_mhz):
        center = float(ht_center1_mhz)          # Kismet's advertised block center (MHz)
    elif width == 40 and ht_mode:
        center = primary_center + (10 if "40+" in ht_mode or ht_mode.endswith("+") else
                                   -10 if "40-" in ht_mode or ht_mode.endswith("-") else 0)
    else:
        # Wider block but no usable advertised center: anchor on the primary and flag it.
        source = "assumed"
    half = width / 2.0
    return (center - half, center + half, center, width, source)


def _plausible(center_mhz: float) -> bool:
    """A real Wi-Fi center frequency, to reject Kismet's 0 / placeholder center fields."""
    return 2400 <= center_mhz <= 7200


def overlap_mhz(span_a: tuple, span_b: tuple) -> float:
    """Overlapping bandwidth (MHz) between two [lo, hi] spans; 0 if they don't overlap or either
    is unknown."""
    lo_a, hi_a = span_a[0], span_a[1]
    lo_b, hi_b = span_b[0], span_b[1]
    if None in (lo_a, hi_a, lo_b, hi_b):
        return 0.0
    return max(0.0, min(hi_a, hi_b) - max(lo_a, lo_b))


def overlap_fraction(ov_mhz: float, width_a: int | None, width_b: int | None) -> float | None:
    """Overlap as a fraction of the NARROWER of the two channels (0..1)."""
    widths = [w for w in (width_a, width_b) if w]
    if not widths or ov_mhz <= 0:
        return 0.0 if widths else None
    return round(ov_mhz / min(widths), 2)


def relation(primary_a: str | None, primary_b: str | None, ov_mhz: float) -> str:
    """How two APs' channels relate: 'co-channel' (same primary → they defer, shared airtime),
    'adjacent' (spectral overlap, different primary → collisions, harmful), or 'clear'."""
    if primary_a is not None and primary_a == primary_b:
        return "co-channel"
    return "adjacent" if ov_mhz > 0 else "clear"
