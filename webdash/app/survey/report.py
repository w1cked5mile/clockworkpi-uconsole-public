"""Render an analysis (analysis.py) into human documents.

Three outputs, all Markdown:

  comprehensive  — the full technical write-up: per-waypoint coverage, the AP inventory, channel
                   and security breakdowns, and every finding. For the operator / RF engineer.
  executive      — a one-page leadership summary: what was surveyed, the headline numbers, the
                   handful of findings that matter to a decision, and plain-language next steps.
  claude_brief   — a compact, structured prompt the operator can hand to Claude (claude.ai or a
                   Claude Code session) for a narrative pass or a client-specific rewrite. This is
                   the "Claude-assisted" path, kept honest: the reports above are generated on the
                   device with no LLM; this brief is what you give an LLM when you want one. The
                   CM4 runs no model locally and this app holds no API key.

Reports contain SSIDs and BSSIDs, so they are treated like the survey data itself — shown in the
authenticated UI and downloadable, never written anywhere that reaches git. The executive summary
redacts BSSIDs to their OUI (first three octets, the manufacturer prefix) since leadership needs
the vendor and the count, not the full radio address.
"""


def _oui(mac: str | None) -> str:
    if not mac or len(mac) < 8:
        return "??:??:??"
    return mac[:8].upper()


def _ssid(ap: dict) -> str:
    return ap["ssid"] if ap.get("ssid") else "_(hidden)_"


def _sig(dbm) -> str:
    return f"{dbm} dBm" if isinstance(dbm, (int, float)) else "—"


def _header(a: dict, title: str) -> list[str]:
    span = a.get("created") or "?"
    if a.get("stopped"):
        span += f" → {a['stopped']}"
    return [
        f"# {title}",
        "",
        f"**Survey:** {a.get('survey_name') or '(unnamed)'}  ",
        f"**Period (UTC):** {span}  ",
        f"**Waypoints:** {a.get('waypoint_count', 0)}  ",
        f"**Method:** passive observation (Kismet, receive-only) — no networks were connected to, "
        "deauthenticated, or decrypted.",
        "",
    ]


def comprehensive(a: dict) -> str:
    t = a["totals"]
    L = _header(a, f"Wi-Fi survey — {a.get('survey_name') or 'report'}")

    L += ["## 1. Summary", "",
          f"- **Unique access points heard:** {t['unique_aps']}",
          f"- **Unique client devices heard:** {t['unique_clients']}",
          f"- **Hidden SSIDs:** {t['hidden_ssids']}",
          f"- **Waypoints with data / failed:** {t['waypoints_with_data']} / {t['waypoints_failed']}",
          ""]

    L += ["## 2. Coverage by waypoint", "",
          "| # | Waypoint | Grid | Fix | APs heard | Best signal | Median | Coverage | Note |",
          "|---|----------|------|-----|-----------|-------------|--------|----------|------|"]
    for wp in a["waypoints"]:
        if wp["snapshot_error"]:
            L.append(f"| {wp['seq']} | {wp['label']} | {wp['grid'] or '—'} | {wp['fix'] or '—'} "
                     f"| — | — | — | _no data_ | {wp['snapshot_error']} |")
        else:
            L.append(f"| {wp['seq']} | {wp['label']} | {wp['grid'] or '—'} | {wp['fix'] or '—'} "
                     f"| {wp['ap_count']} | {_sig(wp['best_signal_dbm'])} | {_sig(wp['median_signal_dbm'])} "
                     f"| {wp['coverage'] or '—'} | {wp['note'] or ''} |")
    L.append("")

    L += ["## 2b. GPS fixes by waypoint", "",
          "| # | Waypoint | Grid | Fix | Sats | HDOP | Position |",
          "|---|----------|------|-----|------|------|----------|"]
    any_pos = False
    for wp in a["waypoints"]:
        pos = "—"
        if isinstance(wp.get("lat"), (int, float)) and isinstance(wp.get("lon"), (int, float)):
            pos = f"{wp['lat']:.5f}, {wp['lon']:.5f}"
            any_pos = True
        L.append(f"| {wp['seq']} | {wp['label']} | {wp.get('grid') or '—'} | {wp.get('fix') or '—'} "
                 f"| {wp.get('satellites_used') if wp.get('satellites_used') is not None else '—'} "
                 f"| {wp.get('hdop') if wp.get('hdop') is not None else '—'} | {pos} |")
    L.append("")
    if not any_pos:
        L.append("_No precise GPS positions were recorded (no fix during the walk — typical indoors); "
                 "locations are the operator's waypoint labels._")
        L.append("")

    L += ["## 3. Spectrum", "", "**By band:**", ""]
    bands = a["bands"]
    if bands:
        for band, n in bands.items():
            L.append(f"- {band}: {n} AP(s)")
    else:
        L.append("- (none)")
    L += ["", "**Channel occupancy (APs per channel):**", ""]
    for band, counts in a["channels"].items():
        chans = ", ".join(f"ch {ch} ({n})" for ch, n in counts.items())
        L.append(f"- **{band}:** {chans}")
    if not a["channels"]:
        L.append("- (no channel data)")
    L.append("")

    L += ["## 4. Security posture", "",
          "| Security | Networks |", "|----------|----------|"]
    for sec, n in a["security"].items():
        L.append(f"| {sec} | {n} |")
    if not a["security"]:
        L.append("| (none) | 0 |")
    L.append("")

    L += ["## 5. Access point inventory", "",
          "Sorted by strongest signal observed anywhere on the walk. BSSIDs included (operator "
          "tool, behind login); redact before external distribution if required.", "",
          "| SSID | BSSID | Band | Ch | Width | Security | Best signal | Util | Vendor | Seen at |",
          "|------|-------|------|----|-------|----------|-------------|------|--------|---------|"]
    for ap in a["access_points"]:
        seen = ", ".join(dict.fromkeys(x for x in ap["seen_at"] if x))
        util = f"{ap['qbss_util_pct']}%" if ap.get("qbss_util_pct") is not None else "—"
        L.append(f"| {_ssid(ap)} | {ap['mac'] or '—'} | {ap['band'] or '—'} | {ap['channel'] or '—'} "
                 f"| {_w(ap.get('width_mhz'))} | {ap['security']} | {_sig(ap['best_signal_dbm'])} | {util} "
                 f"| {ap['manuf'] or '—'} | {seen} |")
    if not a["access_points"]:
        L.append("| (no access points heard) | | | | | | | | | |")
    L.append("")

    L += ["## 6. Findings", ""]
    L += _findings_block(a["findings"])

    L += ["## 7. Method & limitations", "",
          "- Data is whatever Kismet heard while channel-hopping during the walk; a network that "
          "did not beacon in that window, or sat on a channel Kismet was not dwelling on, may be "
          "under-represented or absent.",
          "- Signal readings are the strongest RSSI seen at any waypoint, as reported by the "
          "capture radio (AC1200 / MT7921). They are relative, not calibrated field strength.",
          "- Positions are Maidenhead grid squares plus operator labels; this survey stores no "
          "precise coordinates.",
          "- Receive-only throughout. No association, no deauthentication, no decryption.",
          ""]
    return "\n".join(L)


def executive(a: dict) -> str:
    t = a["totals"]
    L = _header(a, f"Wi-Fi site survey — executive summary")

    weak = sum(a["security"].get(k, 0) for k in ("Open", "WEP", "WPA"))
    marginal = sum(1 for wp in a["waypoints"] if wp.get("coverage") == "marginal")

    L += ["## What we did", "",
          f"We walked {a.get('waypoint_count', 0)} location(s) and passively recorded the Wi-Fi "
          "environment at each — which networks are present, how strong they are, and how the "
          "airtime is being used. Nothing was connected to or interfered with; this is a listen-only "
          "measurement.",
          "",
          "## Headline numbers", "",
          f"- **{t['unique_aps']}** distinct wireless networks (access points) in range across the walk",
          f"- **{t['unique_clients']}** client devices observed",
          f"- **{_band_phrase(a['bands'])}**",
          f"- **{weak}** network(s) using weak or no encryption (open / WEP / original WPA)",
          f"- **{marginal}** survey point(s) with only marginal coverage",
          ""]

    L += ["## What matters", ""]
    decision = [f for f in a["findings"] if f["severity"] in ("warn", "crit")]
    if decision:
        for f in decision:
            L.append(f"- **{f['title']}.** {f.get('exec', '')}".rstrip())
    else:
        L.append("- No coverage gaps or weak-security networks of concern were flagged by the "
                 "automated checks. See the technical report for the full detail.")
    L.append("")

    L += ["## Recommended next steps", ""]
    L += _recommendations(a, weak, marginal)
    L += ["",
          "---",
          "_Passive survey, receive-only. Figures are what was observed during the walk and are "
          "indicative of conditions at that time. Full detail, per-location breakdown and the "
          "network inventory are in the accompanying technical report._"]
    return "\n".join(L)


def claude_brief(a: dict) -> str:
    """A structured, paste-ready prompt for a Claude narrative/leadership rewrite. Compact: the AP
    inventory is summarised, not dumped, so it fits comfortably in a chat. BSSIDs are reduced to
    OUI here — the narrative pass does not need full radio addresses."""
    t = a["totals"]
    lines = [
        "You are helping write up a passive Wi-Fi site survey for a client's leadership. The survey "
        "was receive-only (Kismet) — no networks were connected to, deauthenticated, or decrypted. "
        "Using ONLY the facts below, write (1) a short executive narrative for non-technical "
        "leadership and (2) a prioritised recommendations list. Do not invent networks, signal "
        "figures, or vulnerabilities beyond what is stated. Flag anything the data cannot support.",
        "",
        "## Survey facts",
        f"- Name: {a.get('survey_name')}",
        f"- Waypoints: {a.get('waypoint_count', 0)} "
        f"({t['waypoints_with_data']} with data, {t['waypoints_failed']} failed)",
        f"- Unique APs: {t['unique_aps']}; unique clients: {t['unique_clients']}; "
        f"hidden SSIDs: {t['hidden_ssids']}",
        f"- Bands: {a['bands'] or 'none'}",
        f"- Security mix: {a['security'] or 'none'}",
        "",
        "## Per-waypoint coverage",
    ]
    for wp in a["waypoints"]:
        if wp["snapshot_error"]:
            lines.append(f"- {wp['label']} ({wp['grid'] or 'no grid'}): NO DATA — {wp['snapshot_error']}")
        else:
            lines.append(f"- {wp['label']} ({wp['grid'] or 'no grid'}): {wp['ap_count']} APs, "
                         f"best {_sig(wp['best_signal_dbm'])}, coverage {wp['coverage'] or 'n/a'}"
                         + (f", note: {wp['note']}" if wp['note'] else ""))
    lines += ["", "## Strongest networks (top 10, OUI only)"]
    for ap in a["access_points"][:10]:
        lines.append(f"- {_ssid(ap)} [{_oui(ap['mac'])}] {ap['band'] or '?'} ch{ap['channel'] or '?'} "
                     f"{ap['security']} {_sig(ap['best_signal_dbm'])}")
    lines += ["", "## Automated findings"]
    for f in a["findings"]:
        lines.append(f"- [{f['severity']}] {f['title']}: {f['detail']}")
    if not a["findings"]:
        lines.append("- (none flagged)")
    return "\n".join(lines)


# --- helpers ---------------------------------------------------------------------------------

def focus_markdown(focus: dict) -> str:
    """Technical report for one focused SSID: ESS membership, then per-waypoint per-BSSID signal,
    channel, overlap and contention, roaming footprint, self co-channel, and the honest caveats."""
    L = [
        f"# Wi-Fi survey — focused SSID: {focus.get('target_ssid')}",
        "",
        f"**Survey:** {focus.get('survey_name') or '(unnamed)'}  ",
        f"**Target SSID (ESS):** `{focus.get('target_ssid')}` (match: {focus.get('match_mode')})  ",
        f"**Waypoints:** {len(focus.get('waypoints', []))}  ",
        "**Method:** passive observation (Kismet, receive-only).",
        "",
        "## ESS membership (BSSIDs advertising this SSID)",
        "",
        "| BSSID | Band | Channel | Width | Vendor | Mobility domain |",
        "|-------|------|---------|-------|--------|-----------------|",
    ]
    for m in focus.get("ess_bssids", []):
        L.append(f"| {m['mac']} | {m['band'] or '—'} | {m['channel'] or '—'} | "
                 f"{_w(m['width_mhz'])} | {m['manuf'] or '—'} | "
                 f"{m.get('mobility_domain') if m.get('mobility_domain') not in (None, 0) else '—'} |")
    if not focus.get("ess_bssids"):
        L.append("| _(no BSSIDs heard for this SSID)_ | | | | | |")
    L.append("")

    # Findings first — the interpreted summary a reader wants before the raw tables.
    L += ["## Findings", ""]
    L += _findings_block(focus.get("findings", []))

    # Best server per band, per waypoint — the roaming candidate set at a glance.
    L += ["## Best server per band, by waypoint", "",
          "| Waypoint | Coverage | Best 2.4 GHz | Best 5 GHz |",
          "|----------|----------|--------------|------------|"]
    for wp in focus["waypoints"]:
        if wp["snapshot_error"]:
            L.append(f"| {wp['label']} | _no data_ | — | — |")
            continue
        b = wp.get("best_by_band", {})
        b24 = b.get("2.4 GHz"); b5 = b.get("5 GHz")
        s24 = f"{b24['bssid']} {_sig(b24['signal_dbm'])}" if b24 else "—"
        s5 = f"{b5['bssid']} {_sig(b5['signal_dbm'])}" if b5 else "—"
        L.append(f"| {wp['label']} | {wp.get('coverage') or '—'} | {s24} | {s5} |")
    L.append("")

    L += ["## Per-waypoint — signal, channel, overlap, contention", "",
          "_Signal is the last reading at the waypoint; QBSS stations/util are instantaneous. "
          "Co-ch shows BSSIDs then distinct physical radios (≈). Lifetime signal range and "
          "cumulative client counts are in the roaming footprint._", ""]
    for wp in focus["waypoints"]:
        gps = _gps_line(wp)
        L.append(f"### {wp['label']}  {gps}")
        if wp["snapshot_error"]:
            L += [f"_No data: {wp['snapshot_error']}_", ""]
            continue
        if not wp["observations"]:
            L += ["_This SSID was not heard at this waypoint._", ""]
            continue
        verdict = f" — coverage **{wp['coverage']}**" if wp.get("coverage") else ""
        if wp["strongest_bssid"]:
            L.append(f"Strongest BSSID here: **{wp['strongest_bssid']}** "
                     f"({_sig(wp['strongest_signal_dbm'])}){verdict}.")
        L += ["",
              "| BSSID | Band | Ch | Width | Signal | Co-ch (BSSIDs/radios) | Self | Adjacent overlaps | Util | Stations |",
              "|-------|------|----|-------|--------|----------------------|------|-------------------|------|----------|"]
        for o in wp["observations"]:
            ov = o["overlap"]
            adj = ", ".join(f"ch{x['channel']} {x['overlap_mhz']}MHz" for x in ov["adjacent"]) or "—"
            c = o["contention"]
            util = f"{c['qbss_util_pct']}%" if c.get("qbss_util_pct") is not None else "—"
            sta = c["qbss_stations"] if c.get("qbss_stations") is not None else "—"
            L.append(f"| {o['bssid']} | {o['band'] or '—'} | {o['channel'] or '—'} | {_w(o['width_mhz'])} "
                     f"| {_sig(o['signal_dbm'])} | {ov['co_channel_bssids']}/{ov['co_channel_radios']} "
                     f"| {len(ov['self_co_channel'])} | {adj} | {util} | {sta} |")
        L.append("")

    # Roaming — this is where the cumulative figures (lifetime range, total clients) belong.
    L += ["## Roaming footprint (per BSSID across the walk)", "",
          "_Best/worst are across waypoints; clients are cumulative distinct clients seen (lower "
          "bound); stations is the peak QBSS count._", "",
          "| BSSID | Band | Ch | Best | Worst | Clients (cum.) | Peak stations | Seen at |",
          "|-------|------|----|----|----|--------------|--------------|---------|"]
    for f in focus["roaming"]["per_bssid_footprint"]:
        seen = ", ".join(dict.fromkeys(x for x in f["seen_at"] if x))
        cl = f.get("clients_cumulative"); st = f.get("stations_max")
        L.append(f"| {f['bssid']} | {f['band'] or '—'} | {f['channel'] or '—'} | "
                 f"{_sig(f['best_signal_dbm'])} | {_sig(f['worst_signal_dbm'])} | "
                 f"{cl if cl is not None else '—'} | {st if st is not None else '—'} | {seen} |")
    L.append("")
    pairs = focus["roaming"]["self_co_channel_pairs"]
    contending = [p for p in pairs if p["contending_waypoints"]]
    healthy = [p for p in pairs if not p["contending_waypoints"]]
    if pairs:
        L += ["### Same-channel sibling APs (frequency reuse)", ""]
        if contending:
            L.append("**Actual self-contention** (both APs mutually strong — they steal airtime):")
            for p in contending:
                L.append(f"- ch {p['channel']}: {p['bssid_a']} + {p['bssid_b']} at "
                         f"{', '.join(p['contending_waypoints'])}")
        if healthy:
            L.append("")
            L.append("_Healthy reuse (same channel but the siblings are never mutually strong, so "
                     "they don't contend):_ "
                     + ", ".join(f"ch {p['channel']}" for p in healthy) + ".")
        L.append("")

    L += ["## Method & limitations", ""]
    for n in focus.get("notes", []):
        L.append(f"- {n}")
    L.append("")
    return "\n".join(L)


def _w(width):
    return f"{width} MHz" if width else "—"


def _gps_line(wp: dict) -> str:
    bits = []
    if wp.get("grid"):
        bits.append(f"grid {wp['grid']}")
    if wp.get("fix"):
        bits.append(f"{wp['fix']} fix")
    if isinstance(wp.get("lat"), (int, float)) and isinstance(wp.get("lon"), (int, float)):
        bits.append(f"{wp['lat']:.5f}, {wp['lon']:.5f}")
    return f"_( {' · '.join(bits)} )_" if bits else "_(no GPS)_"


def _findings_block(findings: list[dict]) -> list[str]:
    if not findings:
        return ["_No findings flagged by the automated checks._", ""]
    icon = {"crit": "🔴", "warn": "🟠", "info": "🔵"}
    order = {"crit": 0, "warn": 1, "info": 2}
    out = []
    for f in sorted(findings, key=lambda x: order.get(x["severity"], 3)):
        out.append(f"- {icon.get(f['severity'], '•')} **{f['title']}** — {f['detail']}")
    out.append("")
    return out


def _band_phrase(bands: dict) -> str:
    if not bands:
        return "no band data"
    return "band split: " + ", ".join(f"{n} on {b}" for b, n in bands.items())


def _recommendations(a: dict, weak: int, marginal: int) -> list[str]:
    recs = []
    if weak:
        recs.append("- Identify and remediate the open / WEP / legacy-WPA networks — move any "
                    "that are ours to WPA2 or WPA3, and investigate any that are not.")
    if marginal:
        recs.append("- Review coverage at the marginal location(s); consider AP placement or an "
                    "additional access point if those areas need reliable Wi-Fi.")
    ch24 = a["channels"].get("2.4 GHz", {})
    if any(ch not in {"1", "6", "11"} for ch in ch24):
        recs.append("- Re-plan 2.4 GHz channels onto 1 / 6 / 11 to cut overlap and improve "
                    "throughput for older devices.")
    if a["totals"]["waypoints_failed"]:
        recs.append("- Re-walk the point(s) where capture failed so the survey is complete.")
    if not recs:
        recs.append("- No action required from this survey; retain as a baseline for comparison "
                    "against future walks.")
    return recs
