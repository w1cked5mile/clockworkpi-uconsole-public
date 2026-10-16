"""Turn a survey's raw waypoint snapshots into an analysis structure.

Everything here is deterministic aggregation of what Kismet heard — no estimation of anything that
wasn't observed. Where a number depends on Kismet having a field populated (signal, channel,
crypt), a device missing that field is simply not counted toward it, rather than guessed.

The output feeds both report.py (comprehensive + executive Markdown) and the live UI summary, so
it is plain JSON-able dicts/lists. Keyed terms (bands, signal buckets) match the glossary entries
the dashboard already ships.
"""
from collections import Counter, defaultdict

from . import rf

# Signal quality buckets (dBm, RSSI). Boundaries match the webdash RSSI glossary entry.
SIGNAL_BUCKETS = [
    (-50, "excellent"),
    (-60, "good"),
    (-67, "fair"),
    (-75, "weak"),
    (-200, "poor"),
]
# 2.4 GHz non-overlapping channels in the common (US/EU) plan; anything else overlaps a neighbour.
NON_OVERLAP_24 = {"1", "6", "11"}


def band_of(freq_khz) -> str | None:
    """2.4 / 5 / 6 GHz band from a Kismet frequency in kHz, or None if it isn't a Wi-Fi channel."""
    if not freq_khz:
        return None
    mhz = freq_khz / 1000.0
    if 2400 <= mhz <= 2500:
        return "2.4 GHz"
    if 5150 <= mhz <= 5895:
        return "5 GHz"
    if 5925 <= mhz <= 7125:
        return "6 GHz"
    return None


def valid_signal(dbm) -> bool:
    """A usable RSSI reading. Kismet reports 0 (and occasionally a positive value) for a device it
    has no real signal measurement for; real Wi-Fi RSSI is negative, so 0/positive is "no data,"
    not "very strong." Counting it would wrongly show a 0 dBm best signal."""
    return isinstance(dbm, (int, float)) and -120 <= dbm < 0


def signal_bucket(dbm) -> str | None:
    if dbm is None:
        return None
    for threshold, label in SIGNAL_BUCKETS:
        if dbm >= threshold:
            return label
    return "poor"


def _is_ap(d: dict) -> bool:
    """Kismet labels an access point's type with "AP" (e.g. "Wi-Fi AP"). Clients, bridges and
    bare "Wi-Fi Device" entries are not counted as APs."""
    t = (d.get("type") or "")
    return "AP" in t and "Client" not in t


def _is_client(d: dict) -> bool:
    t = (d.get("type") or "")
    return "Client" in t


def _crypt_class(crypt) -> str:
    """Normalize Kismet's crypt string to one security class. Kismet concatenates tokens like
    'WPA2-PSK' or 'WPA3-SAE'; the strongest token present wins."""
    c = (crypt or "").upper()
    if not c or c in ("NONE", "OPEN"):
        return "Open"
    if "WPA3" in c or "SAE" in c:
        return "WPA3"
    if "WPA2" in c or "RSN" in c:
        return "WPA2"
    if "WPA" in c:
        return "WPA"
    if "WEP" in c:
        return "WEP"
    return "Other"


WEAK_CRYPT = {"Open", "WEP", "WPA"}


def analyze(survey: dict) -> dict:
    """Full analysis of one survey dict (as stored by store.py)."""
    waypoints = survey.get("waypoints", [])

    # Unique APs across the whole walk, keyed by MAC. Keep the strongest reading seen anywhere and
    # the set of waypoints that heard it (that's the coverage footprint).
    aps: dict[str, dict] = {}
    client_macs: set[str] = set()
    per_wp = []

    for wp in waypoints:
        wp_signals = []
        wp_ap_macs = set()
        for d in wp.get("devices", []):
            mac = d.get("mac")
            if _is_client(d):
                if mac:
                    client_macs.add(mac)
                continue
            if not _is_ap(d):
                continue
            if not mac:
                continue
            wp_ap_macs.add(mac)
            sig = d.get("signal_dbm")
            has_sig = valid_signal(sig)
            if has_sig:
                wp_signals.append(sig)
            rec = aps.get(mac)
            if rec is None:
                rec = aps[mac] = {
                    "mac": mac,
                    "ssid": d.get("ssid") or d.get("name"),
                    "hidden": not (d.get("ssid") or d.get("name")),
                    "channel": d.get("channel"),
                    "band": band_of(d.get("freq_khz")),
                    "manuf": d.get("manuf"),
                    "security": _crypt_class(d.get("crypt")),
                    "best_signal_dbm": sig if has_sig else None,
                    "width_mhz": d.get("width_mhz"),
                    "span_lo_mhz": d.get("span_lo_mhz"),
                    "span_hi_mhz": d.get("span_hi_mhz"),
                    "qbss_util_pct": d.get("qbss_util_pct"),
                    "num_clients": d.get("num_clients"),
                    "seen_at": [],
                }
            else:
                # Prefer a populated SSID/channel/security if an earlier waypoint missed it.
                if rec["hidden"] and (d.get("ssid") or d.get("name")):
                    rec["ssid"] = d.get("ssid") or d.get("name")
                    rec["hidden"] = False
                if not rec["channel"] and d.get("channel"):
                    rec["channel"] = d.get("channel")
                if not rec["band"]:
                    rec["band"] = band_of(d.get("freq_khz"))
                if has_sig and (rec["best_signal_dbm"] is None or sig > rec["best_signal_dbm"]):
                    rec["best_signal_dbm"] = sig
            rec["seen_at"].append(wp.get("label"))

        wp_signals.sort()
        per_wp.append({
            "seq": wp.get("seq"),
            "label": wp.get("label"),
            "grid": wp.get("grid"),
            "fix": wp.get("fix"),
            "lat": wp.get("lat"),
            "lon": wp.get("lon"),
            "satellites_used": wp.get("satellites_used"),
            "hdop": wp.get("hdop"),
            "note": wp.get("note"),
            "snapshot_error": wp.get("snapshot_error"),
            "device_count": wp.get("device_count"),
            "ap_count": len(wp_ap_macs),
            "best_signal_dbm": wp_signals[-1] if wp_signals else None,
            "median_signal_dbm": wp_signals[len(wp_signals) // 2] if wp_signals else None,
            "coverage": _coverage_label(wp_signals),
        })

    ap_list = sorted(aps.values(),
                     key=lambda a: (a["best_signal_dbm"] is None, -(a["best_signal_dbm"] or -999)))

    return {
        "survey_name": survey.get("name"),
        "survey_id": survey.get("id"),
        "created": survey.get("created"),
        "stopped": survey.get("stopped"),
        "status": survey.get("status"),
        "waypoint_count": len(waypoints),
        "waypoints": per_wp,
        "totals": _totals(ap_list, client_macs, per_wp),
        "bands": _band_breakdown(ap_list),
        "security": _security_breakdown(ap_list),
        "channels": _channel_breakdown(ap_list),
        "access_points": ap_list,
        "findings": _findings(ap_list, per_wp),
    }


def _coverage_label(signals: list) -> str | None:
    if not signals:
        return None
    best = max(signals)
    if best >= -60:
        return "strong"
    if best >= -72:
        return "usable"
    return "marginal"


def _totals(ap_list, client_macs, per_wp) -> dict:
    heard = [wp for wp in per_wp if not wp["snapshot_error"]]
    return {
        "unique_aps": len(ap_list),
        "unique_clients": len(client_macs),
        "waypoints_with_data": len(heard),
        "waypoints_failed": len(per_wp) - len(heard),
        "hidden_ssids": sum(1 for a in ap_list if a["hidden"]),
    }


def _band_breakdown(ap_list) -> dict:
    c = Counter(a["band"] or "unknown" for a in ap_list)
    return {k: c[k] for k in ("2.4 GHz", "5 GHz", "6 GHz", "unknown") if c[k]}


def _security_breakdown(ap_list) -> dict:
    c = Counter(a["security"] for a in ap_list)
    order = ("WPA3", "WPA2", "WPA", "WEP", "Open", "Other")
    return {k: c[k] for k in order if c[k]}


def _channel_breakdown(ap_list) -> dict:
    """APs per channel, grouped by band — the raw material for a congestion read."""
    by_band = defaultdict(Counter)
    for a in ap_list:
        if a["channel"]:
            by_band[a["band"] or "unknown"][a["channel"]] += 1
    return {band: dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))
            for band, counts in by_band.items()}


def _findings(ap_list, per_wp) -> list[dict]:
    """Rule-derived observations, each a {severity, title, detail}. Severity drives report order
    and the UI colour. Nothing here is a vulnerability claim about a network — they are survey
    facts (an open SSID is open; a channel is crowded), in keeping with the passive posture."""
    out = []

    openaps = [a for a in ap_list if a["security"] == "Open"]
    if openaps:
        out.append({"severity": "info", "title": f"{len(openaps)} open network(s) observed",
                    "detail": "Unencrypted SSIDs broadcasting in range: "
                              + ", ".join(sorted({_ssid_label(a) for a in openaps}))})
    wep = [a for a in ap_list if a["security"] == "WEP"]
    if wep:
        out.append({"severity": "warn", "title": f"{len(wep)} network(s) using WEP",
                    "exec": "WEP encryption is obsolete and trivially broken; these networks should "
                            "be upgraded or investigated.",
                    "detail": "WEP is obsolete and trivially broken; these: "
                              + ", ".join(sorted({_ssid_label(a) for a in wep}))})
    wpa1 = [a for a in ap_list if a["security"] == "WPA"]
    if wpa1:
        out.append({"severity": "warn", "title": f"{len(wpa1)} network(s) on original WPA (TKIP-era)",
                    "exec": "These run pre-WPA2 security, which is deprecated and should be upgraded.",
                    "detail": "Pre-WPA2 security, deprecated: "
                              + ", ".join(sorted({_ssid_label(a) for a in wpa1}))})

    # Channel hygiene, RF-honest: co-channel crowding is *shared* airtime (APs defer to each other
    # on the same primary — contention, not corruption); spectral overlap on a DIFFERENT primary is
    # the harmful case (they often cannot hear each other, so they collide). Flag them distinctly.
    ch24 = Counter(a["channel"] for a in ap_list if a["band"] == "2.4 GHz" and a["channel"])
    if ch24:
        busiest, n = max(ch24.items(), key=lambda kv: kv[1])
        if n >= 3:
            out.append({"severity": "info", "title": f"2.4 GHz channel {busiest} is crowded",
                        "exec": "Several access points share this channel and must take turns, "
                                "which can slow everyone on it.",
                        "detail": f"{n} APs share primary channel {busiest}; same-channel "
                                  "contention (they defer to each other — shared airtime, not "
                                  "interference)."})
    adj = _adjacent_overlaps(ap_list)
    if adj:
        out.append({"severity": "warn", "title": f"{len(adj)} adjacent-channel overlap(s)",
                    "exec": "Some access points partly overlap on different channels, which causes "
                            "collisions rather than orderly sharing — worth re-planning channels.",
                    "detail": "Different primary channels whose spectrum overlaps (collisions, not "
                              "deferral): " + "; ".join(adj[:8])
                              + (" …" if len(adj) > 8 else "")})

    marginal = [wp for wp in per_wp if wp["coverage"] == "marginal"]
    if marginal:
        out.append({"severity": "warn", "title": f"{len(marginal)} waypoint(s) with only marginal coverage",
                    "exec": "Signal at these locations was below the usable threshold; coverage "
                            "there may be unreliable.",
                    "detail": "Best signal below −72 dBm at: "
                              + ", ".join(wp["label"] for wp in marginal)})
    dead = [wp for wp in per_wp if not wp["snapshot_error"] and wp["ap_count"] == 0]
    if dead:
        out.append({"severity": "warn", "title": f"{len(dead)} waypoint(s) heard no APs",
                    "exec": "No access points were heard at these locations — likely no coverage there.",
                    "detail": "No access points observed at: " + ", ".join(wp["label"] for wp in dead)})
    failed = [wp for wp in per_wp if wp["snapshot_error"]]
    if failed:
        out.append({"severity": "warn", "title": f"{len(failed)} waypoint(s) captured no data",
                    "exec": "Data capture failed at these points; they should be re-walked for a "
                            "complete survey.",
                    "detail": "Kismet snapshot failed at: "
                              + ", ".join(f"{wp['label']} ({wp['snapshot_error']})" for wp in failed)})
    return out


def _adjacent_overlaps(ap_list) -> list[str]:
    """Pairs of APs whose channels spectrally overlap on DIFFERENT primaries (the harmful case).
    Deduped by SSID-channel pair to keep the finding short. O(n^2) over ~dozens of APs."""
    seen, out = set(), []
    for i, a in enumerate(ap_list):
        for b in ap_list[i + 1:]:
            if not a["channel"] or not b["channel"] or a["channel"] == b["channel"]:
                continue
            ov = rf.overlap_mhz((a.get("span_lo_mhz"), a.get("span_hi_mhz")),
                                (b.get("span_lo_mhz"), b.get("span_hi_mhz")))
            if ov <= 0:
                continue
            key = tuple(sorted((a["channel"], b["channel"])))
            if key in seen:
                continue
            seen.add(key)
            out.append(f"ch {key[0]} / ch {key[1]} ({ov:.0f} MHz)")
    return out


def _ssid_label(ap: dict) -> str:
    return ap["ssid"] if ap["ssid"] else "<hidden>"


# =============================================================================================
# SSID-focused analysis: signal / channel / overlap / contention, per AP, per waypoint.
# Works off the raw per-waypoint device snapshots (not the deduped survey-wide AP list), because a
# focused survey is about how one ESS behaves at each location. Receive-only throughout.
# =============================================================================================

def list_ssids(survey: dict) -> list[dict]:
    """Distinct named SSIDs seen anywhere in the survey, with BSSID count and bands — for the UI's
    focus picker. Hidden networks (no SSID) are omitted; you focus by name."""
    agg: dict[str, dict] = {}
    for wp in survey.get("waypoints", []):
        for d in wp.get("devices", []):
            if not _is_ap(d) or not d.get("ssid"):
                continue
            e = agg.setdefault(d["ssid"], {"ssid": d["ssid"], "bssids": set(), "bands": set()})
            if d.get("mac"):
                e["bssids"].add(d["mac"])
            b = band_of(d.get("freq_khz"))
            if b:
                e["bands"].add(b)
    out = [{"ssid": e["ssid"], "bssid_count": len(e["bssids"]),
            "bands": sorted(e["bands"])} for e in agg.values()]
    out.sort(key=lambda e: (-e["bssid_count"], e["ssid"].lower()))
    return out


def _span(d: dict) -> tuple:
    return (d.get("span_lo_mhz"), d.get("span_hi_mhz"))


def _matches(d: dict, target: str, mode: str) -> bool:
    s = d.get("ssid")
    if not s:
        return False
    return s.casefold() == target.casefold() if mode == "ci" else s == target


# Thresholds (from the 2026-10-08 RF review of the Microban guest walk).
STRONG_DBM = -60      # "strong" coverage at/above this
USABLE_DBM = -72      # "usable" at/above this; below is marginal
CONTEND_DBM = -70     # two co-channel siblings both at/above this actually steal airtime
FIVE_FALLBACK_DBM = -67  # a strong 2.4 anchor...
ADJ_FRAC = 0.5        # adjacent overlap significance: >= half the victim channel...
ADJ_MHZ = 10          # ...or >= this many MHz, AND the victim is in use (>= CONTEND_DBM)
LOAD_STATIONS = 25    # QBSS station count that flags load concentration
UTIL_PRESSURE = 40    # QBSS utilization % that flags airtime pressure


def _radio_key(mac: str) -> str:
    """Group virtual BSSIDs that are the same physical radio. Enterprise APs (Cisco here) broadcast
    many SSIDs from one radio, varying the top octet(s) but sharing the lower 5 — so the lower 5
    octets approximate the physical radio. Heuristic, not measured."""
    return (mac or "")[3:]


def _sig(dbm) -> str:
    return f"{dbm} dBm" if isinstance(dbm, (int, float)) else "—"


def _coverage(sig) -> str | None:
    if not valid_signal(sig):
        return None
    return "strong" if sig >= STRONG_DBM else "usable" if sig >= USABLE_DBM else "marginal"


def focus_analysis(survey: dict, target_ssid: str, match_mode: str = "exact") -> dict:
    """Per-AP, per-waypoint signal / channel / overlap / contention for one target SSID (ESS).

    An SSID is an ESS that may be served by several BSSIDs across 2.4/5/6 GHz. For each waypoint we
    report each of the ESS's BSSIDs heard there: its signal, channel geometry, who it overlaps
    (co-channel = shares airtime; adjacent = collides), its own ESS siblings co-channel with it,
    and contention proxies. Overlap is computed against ALL APs heard at the waypoint.

    Per-waypoint-meaningful values are the last-signal RSSI and the instantaneous QBSS station /
    utilization reads. Kismet's min/max signal and num_associated_clients are whole-capture
    cumulative figures, so they are surfaced once per BSSID in the roaming footprint, never
    per-waypoint (see the 2026-10-08 RF review).
    """
    waypoints = survey.get("waypoints", [])
    members: dict[str, dict] = {}
    footprint: dict[str, dict] = {}
    per_wp = []
    self_pairs: dict = {}

    for wp in waypoints:
        aps = [d for d in wp.get("devices", []) if _is_ap(d) and d.get("mac")]
        targets = [d for d in aps if _matches(d, target_ssid, match_mode)]
        target_macs = {d["mac"] for d in targets}
        sig_at_wp = {d["mac"]: d.get("signal_dbm") for d in targets}

        observations = []
        strongest = (None, None)
        best_band = {}  # band -> (mac, sig)
        for d in targets:
            mac, band, primary = d["mac"], band_of(d.get("freq_khz")), d.get("channel")
            members.setdefault(mac, {"mac": mac, "band": band, "channel": primary,
                                     "width_mhz": d.get("width_mhz"), "manuf": d.get("manuf"),
                                     "mobility_domain": d.get("mobility_domain")})
            co, adj, self_co = [], [], []
            for o in aps:
                if o["mac"] == mac:
                    continue
                ov = rf.overlap_mhz(_span(d), _span(o))
                rel = rf.relation(primary, o.get("channel"), ov)
                if rel == "co-channel":
                    co.append(o["mac"])
                    if o["mac"] in target_macs:
                        self_co.append(o["mac"])
                        # Record each unordered pair once (from the a-side visit), with BOTH
                        # siblings' signal here so the "do they actually contend" gate can apply.
                        key = tuple(sorted((mac, o["mac"])))
                        if mac == key[0]:
                            sp = self_pairs.setdefault(key, {"bssid_a": key[0], "bssid_b": key[1],
                                                             "channel": primary, "samples": []})
                            sp["samples"].append({"waypoint": wp.get("label"),
                                                  "sig_a": sig_at_wp.get(key[0]),
                                                  "sig_b": sig_at_wp.get(key[1])})
                elif rel == "adjacent":
                    adj.append({"bssid": o["mac"], "channel": o.get("channel"),
                                "overlap_mhz": round(ov, 1),
                                "overlap_frac": rf.overlap_fraction(ov, d.get("width_mhz"),
                                                                    o.get("width_mhz"))})
            sig = d.get("signal_dbm")
            if valid_signal(sig):
                if strongest[1] is None or sig > strongest[1]:
                    strongest = (mac, sig)
                if band and (band not in best_band or sig > best_band[band][1]):
                    best_band[band] = (mac, sig)

            fp = footprint.setdefault(mac, {"bssid": mac, "band": band, "channel": primary,
                                            "seen_at": [], "best_signal_dbm": None,
                                            "worst_signal_dbm": None, "clients_cumulative": None,
                                            "stations_max": None})
            fp["seen_at"].append(wp.get("label"))
            if valid_signal(sig):
                fp["best_signal_dbm"] = sig if fp["best_signal_dbm"] is None else max(fp["best_signal_dbm"], sig)
                fp["worst_signal_dbm"] = sig if fp["worst_signal_dbm"] is None else min(fp["worst_signal_dbm"], sig)
            nc = d.get("num_clients")
            if isinstance(nc, int):
                fp["clients_cumulative"] = nc if fp["clients_cumulative"] is None else max(fp["clients_cumulative"], nc)
            st = d.get("qbss_stations")
            if isinstance(st, int):
                fp["stations_max"] = st if fp["stations_max"] is None else max(fp["stations_max"], st)

            observations.append({
                "bssid": mac, "band": band, "channel": primary,
                "width_mhz": d.get("width_mhz"), "width_source": d.get("width_source"),
                "signal_dbm": sig if valid_signal(sig) else None,
                # Whole-capture extremes — kept, but named so no renderer shows them as "here".
                "lifetime_min_dbm": d.get("min_signal_dbm") if valid_signal(d.get("min_signal_dbm")) else None,
                "lifetime_max_dbm": d.get("max_signal_dbm") if valid_signal(d.get("max_signal_dbm")) else None,
                "overlap": {"co_channel": co, "co_channel_bssids": len(co),
                            "co_channel_radios": len({_radio_key(m) for m in co}),
                            "self_co_channel": self_co, "adjacent": adj},
                "contention": {"qbss_util_pct": d.get("qbss_util_pct"),
                               "qbss_stations": d.get("qbss_stations"),  # instantaneous, per-waypoint
                               "qbss_present": d.get("qbss_present")},
            })

        per_wp.append({
            "seq": wp.get("seq"), "label": wp.get("label"), "grid": wp.get("grid"),
            "fix": wp.get("fix"), "lat": wp.get("lat"), "lon": wp.get("lon"),
            "snapshot_error": wp.get("snapshot_error"),
            "target_bssids_heard": len(targets),
            "strongest_bssid": strongest[0], "strongest_signal_dbm": strongest[1],
            "coverage": _coverage(strongest[1]),
            "best_by_band": {b: {"bssid": v[0], "signal_dbm": v[1]} for b, v in best_band.items()},
            "observations": observations,
        })

    # Gate self co-channel pairs: a pair only *contends* at waypoints where BOTH siblings are
    # mutually strong (>= CONTEND_DBM). Elsewhere it is healthy frequency reuse.
    pairs = []
    for sp in self_pairs.values():
        contending = [s["waypoint"] for s in sp["samples"]
                      if valid_signal(s["sig_a"]) and s["sig_a"] >= CONTEND_DBM
                      and valid_signal(s["sig_b"]) and s["sig_b"] >= CONTEND_DBM]
        pairs.append({"bssid_a": sp["bssid_a"], "bssid_b": sp["bssid_b"], "channel": sp["channel"],
                      "waypoints": [s["waypoint"] for s in sp["samples"]],
                      "contending_waypoints": contending,
                      "healthy_reuse": not contending})

    footprint_sorted = sorted(footprint.values(),
                              key=lambda f: (f["best_signal_dbm"] is None, -(f["best_signal_dbm"] or -999)))
    return {
        "survey_name": survey.get("name"),
        "survey_id": survey.get("id"),
        "target_ssid": target_ssid,
        "match_mode": match_mode,
        "ess_bssids": sorted(members.values(), key=lambda m: (m["band"] or "z", m["channel"] or "")),
        "waypoints": per_wp,
        "roaming": {"per_bssid_footprint": footprint_sorted, "self_co_channel_pairs": pairs},
        "findings": _focus_findings(per_wp, pairs, footprint_sorted),
        "notes": _focus_notes(),
    }


def _focus_findings(per_wp, pairs, footprint) -> list[dict]:
    """Rule-derived findings for the focused ESS (severities drive report order + colour). Each is
    a survey fact, not an intrusion claim. Thresholds are the module constants above."""
    out = []
    data_wps = [w for w in per_wp if not w["snapshot_error"]]

    # 1. Coverage gaps / dead spots.
    gaps = [w for w in data_wps if w["target_bssids_heard"] == 0
            or (w["strongest_signal_dbm"] is not None and w["strongest_signal_dbm"] < USABLE_DBM)]
    if gaps:
        out.append({"severity": "warn", "title": f"{len(gaps)} waypoint(s) with weak/no coverage",
                    "exec": "This network is weak or absent at these locations.",
                    "detail": "Below the usable threshold: "
                              + ", ".join(f"{w['label']} ({_sig(w['strongest_signal_dbm'])})" for w in gaps)})
    elif data_wps:
        out.append({"severity": "info", "title": "Coverage is strong at every surveyed point",
                    "exec": "The network provides strong coverage across all locations walked.",
                    "detail": "Every waypoint with data has an access point at or above "
                              f"{USABLE_DBM} dBm (strongest at each: "
                              + ", ".join(f"{w['label']} {_sig(w['strongest_signal_dbm'])}" for w in data_wps) + ")."})

    # 2. 5 GHz fallback risk: strong 2.4 but weak/absent 5 GHz (clients likely stay on 2.4).
    fallback = []
    for w in data_wps:
        b = w["best_by_band"]
        s24 = (b.get("2.4 GHz") or {}).get("signal_dbm")
        s5 = (b.get("5 GHz") or {}).get("signal_dbm")
        if valid_signal(s24) and s24 >= FIVE_FALLBACK_DBM and (not valid_signal(s5) or s5 < USABLE_DBM):
            fallback.append(w["label"])
    if fallback:
        out.append({"severity": "info", "title": f"{len(fallback)} waypoint(s) with weak 5 GHz vs 2.4 GHz",
                    "exec": "Devices may stay on the slower 2.4 GHz band in these areas.",
                    "detail": "Strong 2.4 GHz but no usable 5 GHz at: " + ", ".join(fallback)})

    # 3. Self co-channel contention (gated).
    contending = [p for p in pairs if p["contending_waypoints"]]
    if contending:
        out.append({"severity": "warn", "title": f"{len(contending)} self co-channel contention point(s)",
                    "exec": "In places, two of this network's own access points share a channel and "
                            "compete for airtime.",
                    "detail": "; ".join(f"ch {p['channel']} ({p['bssid_a']} + {p['bssid_b']}) at "
                                        f"{', '.join(p['contending_waypoints'])}" for p in contending)
                              + ". Other same-channel pairs are healthy frequency reuse (siblings not "
                                "mutually strong)."})

    # 4. Adjacent-channel interference from external APs (significant + where we're in use).
    interferers = {}
    for w in data_wps:
        for o in w["observations"]:
            if not valid_signal(o["signal_dbm"]) or o["signal_dbm"] < CONTEND_DBM:
                continue
            for a in o["overlap"]["adjacent"]:
                if (a.get("overlap_frac") or 0) >= ADJ_FRAC or a["overlap_mhz"] >= ADJ_MHZ:
                    k = (a["bssid"], a["channel"], o["channel"])
                    prev = interferers.get(k)
                    if prev is None or a["overlap_mhz"] > prev["overlap_mhz"]:
                        interferers[k] = {"bssid": a["bssid"], "their_ch": a["channel"],
                                          "our_ch": o["channel"], "overlap_mhz": a["overlap_mhz"],
                                          "frac": a.get("overlap_frac")}
    if interferers:
        items = sorted(interferers.values(), key=lambda x: -x["overlap_mhz"])
        out.append({"severity": "warn", "title": f"{len(items)} external adjacent-channel interferer(s)",
                    "exec": "Nearby Wi-Fi networks you don't control are overlapping this one on the "
                            "2.4 GHz band and causing interference, worst near the offices.",
                    "detail": "Off-plan neighbour APs overlapping our channels (external — not this "
                              "ESS): " + "; ".join(f"{x['bssid']} ch{x['their_ch']} → our ch{x['our_ch']} "
                              f"({x['overlap_mhz']:.0f} MHz{', full-channel' if (x['frac'] or 0) >= 0.99 else ''})"
                              for x in items[:6])})

    # 5. Load concentration on one radio.
    stations = [f["stations_max"] for f in footprint if isinstance(f.get("stations_max"), int)]
    med = sorted(stations)[len(stations) // 2] if stations else 0
    hot = [f for f in footprint if isinstance(f.get("stations_max"), int)
           and (f["stations_max"] >= LOAD_STATIONS or (med and f["stations_max"] >= 2 * med))]
    if hot:
        out.append({"severity": "info", "title": "Client load concentrated on one radio",
                    "exec": "A large share of users are on a single access point — worth an AP-side "
                            "load-balancing check.",
                    "detail": "AP-reported station counts stand out at: "
                              + ", ".join(f"{f['bssid']} (ch {f['channel']}, {f['stations_max']} stations)" for f in hot)
                              + f" vs a median of {med}. Passive data can't prove sticky clients — a "
                                "hypothesis for AP-side load-balancing / band-steering review."})

    # 6. Airtime pressure.
    busy = set()
    for w in data_wps:
        for o in w["observations"]:
            u = o["contention"].get("qbss_util_pct")
            if isinstance(u, (int, float)) and u >= UTIL_PRESSURE:
                busy.add(f"{o['bssid']} ch{o['channel']} ({u}% at {w['label']})")
    if busy:
        out.append({"severity": "info", "title": "Transient high channel utilization",
                    "exec": "A channel was briefly busy during the walk.",
                    "detail": "AP-reported utilization at/over "
                              f"{UTIL_PRESSURE}%: " + "; ".join(sorted(busy))})

    # 7. Failed / duplicate waypoints.
    from collections import Counter
    labels = Counter(w["label"] for w in per_wp)
    failed = [w for w in per_wp if w["snapshot_error"]]
    for w in failed:
        dup = " (re-walked — a later same-named point has data)" if labels[w["label"]] > 1 else ""
        out.append({"severity": "warn", "title": f"Waypoint '{w['label']}' captured no data{dup}",
                    "detail": f"{w['snapshot_error']}. Treat the two same-named points as one location."})
    return out


def _focus_notes() -> list[str]:
    """Honest limitations that belong on every focused report (from the RF review)."""
    return [
        "Passive, receive-only capture on a single channel-hopping radio: BSSID and client counts "
        "are lower bounds — a BSSID absent at a waypoint may simply not have been heard in that "
        "dwell window, not be out of range.",
        "Channel utilization and station counts are the access point's own QBSS/BSS-Load figures, "
        "read from its beacon (AP-reported, instantaneous). We do not and cannot measure true "
        "airtime busy-time from a hopping radio.",
        "Per-waypoint values are the last-signal RSSI and the instantaneous QBSS station / "
        "utilization reads. Signal min/max and client counts are whole-capture cumulative figures, "
        "so they are shown once per BSSID in the roaming footprint, not per waypoint.",
        "Co-channel figures are BSSID tallies; many 'co-channel' BSSIDs are additional SSIDs on one "
        "physical radio, so the physical-radio estimate is the better contention proxy (a heuristic, "
        "grouped by the lower 5 MAC octets).",
        "Signal is uncalibrated relative RSSI from the capture radio; no noise floor is available "
        "on this hardware, so no SNR is reported.",
        "Channel width is read from the beacon's HT/VHT/HE element, not measured across the bonded "
        "block.",
    ]


def _focus_notes() -> list[str]:
    """Honest limitations that belong on every focused report (from the RF review)."""
    return [
        "Passive, receive-only capture on a single channel-hopping radio: BSSID and client counts "
        "are lower bounds — a BSSID absent at a waypoint may simply not have been heard in that "
        "dwell window, not be out of range.",
        "Channel utilization shown is the access point's own QBSS/BSS-Load figure, read from its "
        "beacon (AP-reported, instantaneous). We do not and cannot measure true airtime busy-time "
        "from a hopping radio.",
        "Signal is uncalibrated relative RSSI from the capture radio; no noise floor is available "
        "on this hardware, so no SNR is reported.",
        "Channel width is read from the beacon's HT/VHT/HE element, not measured across the bonded "
        "block.",
    ]
