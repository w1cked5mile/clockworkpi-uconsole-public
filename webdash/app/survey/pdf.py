"""PDF rendering of a survey analysis, built directly from the analysis dict (the same structure
report.py's Markdown uses) with fpdf2 — a pure-Python generator with no native/system
dependencies, so it stays inside the slim image (reportlab would pull pillow + chardet).

Two documents: the comprehensive technical report (landscape, to fit the AP inventory) and the
executive summary (portrait, narrative). The Claude brief stays Markdown-only — it is a prompt to
feed a model, not a document to read, so a PDF of it makes no sense.

fpdf2's core fonts are latin-1. `_s()` maps the few non-latin-1 glyphs our own text uses, then
drops anything still outside latin-1 (e.g. a CJK or emoji SSID) to "?" rather than crash — SSIDs
are untrusted bytes from the air. Accented latin names (é, ñ, …) are in latin-1 and render fine;
full-Unicode SSIDs would need an embedded TTF (noted as a follow-up, not needed for v1).
"""
from fpdf import FPDF
from fpdf.fonts import FontFace

from . import analysis

# Signal bucket → RGB for the native PDF site map (mirrors sitemap.py's SVG palette).
_BUCKET_RGB = {
    "excellent": (74, 222, 128), "good": (134, 239, 172), "fair": (250, 204, 21),
    "weak": (251, 146, 60), "poor": (248, 113, 113), None: (120, 130, 140),
}

_REPL = {
    "−": "-",   # minus sign → hyphen
    "–": "-",   # en dash
    "—": " - ",  # em dash
    "•": "*",   # bullet
    "→": "->",  # arrow
    "✓": "[ok]",
}


def _s(x) -> str:
    s = str(x if x is not None else "")
    for k, v in _REPL.items():
        s = s.replace(k, v)
    return s.encode("latin-1", "replace").decode("latin-1")


class _Doc(FPDF):
    def __init__(self, orientation="P"):
        super().__init__(orientation=orientation, unit="mm", format="A4")
        self.set_auto_page_break(auto=True, margin=15)
        self.set_title("Wi-Fi survey")

    def footer(self):
        self.set_y(-12)
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(120)
        self.cell(0, 6, _s("Passive survey, receive-only - observed conditions at survey time."),
                  align="L")
        self.cell(0, 6, f"Page {self.page_no()}/{{nb}}", align="R")
        self.set_text_color(0)

    # --- small building blocks ---------------------------------------------------------------
    def h1(self, text):
        self.set_font("Helvetica", "B", 16)
        self.multi_cell(0, 8, _s(text), new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def h2(self, text):
        self.ln(2)
        self.set_font("Helvetica", "B", 12)
        self.multi_cell(0, 7, _s(text), new_x="LMARGIN", new_y="NEXT")

    def meta(self, lines):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(90)
        for ln in lines:
            self.multi_cell(0, 5, _s(ln), new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0)
        self.ln(1)

    def body(self, text):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5, _s(text), new_x="LMARGIN", new_y="NEXT")

    def bullet(self, text, bold_prefix=None):
        self.set_font("Helvetica", "", 10)
        x = self.get_x()
        self.cell(5, 5, _s("*"))
        if bold_prefix:
            self.set_font("Helvetica", "B", 10)
            self.multi_cell(0, 5, _s(bold_prefix), new_x="LMARGIN", new_y="NEXT")
            self.set_x(x + 5)
            self.set_font("Helvetica", "", 10)
            if text:
                self.multi_cell(0, 5, _s(text), new_x="LMARGIN", new_y="NEXT")
        else:
            self.multi_cell(0, 5, _s(text), new_x="LMARGIN", new_y="NEXT")


def _sig(dbm):
    return f"{dbm} dBm" if isinstance(dbm, (int, float)) else "-"


def _ssid(ap):
    return ap["ssid"] if ap.get("ssid") else "(hidden)"


def _meta_lines(a):
    span = a.get("created") or "?"
    if a.get("stopped"):
        span += f"  ->  {a['stopped']}"
    return [
        f"Survey: {a.get('survey_name') or '(unnamed)'}",
        f"Period (UTC): {span}",
        f"Waypoints: {a.get('waypoint_count', 0)}",
        "Method: passive observation (Kismet, receive-only) - no networks were connected to, "
        "deauthenticated, or decrypted.",
    ]


def executive_pdf(a: dict) -> bytes:
    t = a["totals"]
    weak = sum(a["security"].get(k, 0) for k in ("Open", "WEP", "WPA"))
    marginal = sum(1 for wp in a["waypoints"] if wp.get("coverage") == "marginal")
    d = _Doc("P")
    d.add_page()
    d.h1("Wi-Fi site survey - executive summary")
    d.meta(_meta_lines(a))

    d.h2("What we did")
    d.body(f"We walked {a.get('waypoint_count', 0)} location(s) and passively recorded the Wi-Fi "
           "environment at each - which networks are present, how strong they are, and how the "
           "airtime is being used. Nothing was connected to or interfered with; this is a "
           "listen-only measurement.")

    d.h2("Headline numbers")
    for b in [
        f"{t['unique_aps']} distinct wireless networks (access points) in range across the walk",
        f"{t['unique_clients']} client devices observed",
        _band_phrase(a["bands"]),
        f"{weak} network(s) using weak or no encryption (open / WEP / original WPA)",
        f"{marginal} survey point(s) with only marginal coverage",
    ]:
        d.bullet(b)

    d.h2("What matters")
    decision = [f for f in a["findings"] if f["severity"] in ("warn", "crit")]
    if decision:
        for f in decision:
            d.bullet(f.get("exec", ""), bold_prefix=f["title"] + ".")
    else:
        d.bullet("No coverage gaps or weak-security networks of concern were flagged by the "
                 "automated checks. See the technical report for the full detail.")

    d.h2("Recommended next steps")
    for r in _recommendations(a, weak, marginal):
        d.bullet(r)
    return bytes(d.output())


def comprehensive_pdf(a: dict) -> bytes:
    t = a["totals"]
    d = _Doc("L")
    d.add_page()
    d.h1(f"Wi-Fi survey - {a.get('survey_name') or 'report'}")
    d.meta(_meta_lines(a))

    d.h2("1. Summary")
    for b in [
        f"Unique access points heard: {t['unique_aps']}",
        f"Unique client devices heard: {t['unique_clients']}",
        f"Hidden SSIDs: {t['hidden_ssids']}",
        f"Waypoints with data / failed: {t['waypoints_with_data']} / {t['waypoints_failed']}",
    ]:
        d.bullet(b)

    d.h2("2. Coverage by waypoint")
    d.set_font("Helvetica", "", 8)
    with d.table(col_widths=(8, 55, 24, 16, 20, 26, 24, 24, 80), text_align="LEFT",
                 headings_style=_HEAD) as table:
        table.row(["#", "Waypoint", "Grid", "Fix", "APs", "Best signal", "Median", "Coverage", "Note"])
        for wp in a["waypoints"]:
            if wp["snapshot_error"]:
                table.row([str(wp["seq"]), _s(wp["label"]), _s(wp["grid"] or "-"), _s(wp["fix"] or "-"),
                           "-", "-", "-", "no data", _s(wp["snapshot_error"])])
            else:
                table.row([str(wp["seq"]), _s(wp["label"]), _s(wp["grid"] or "-"), _s(wp["fix"] or "-"),
                           str(wp["ap_count"]), _sig(wp["best_signal_dbm"]), _sig(wp["median_signal_dbm"]),
                           _s(wp["coverage"] or "-"), _s(wp["note"] or "")])

    d.h2("2b. GPS fixes by waypoint")
    d.set_font("Helvetica", "", 8)
    any_pos = False
    with d.table(col_widths=(8, 55, 24, 16, 14, 16, 40), text_align="LEFT", headings_style=_HEAD) as t:
        t.row(["#", "Waypoint", "Grid", "Fix", "Sats", "HDOP", "Position"])
        for wp in a["waypoints"]:
            pos = "-"
            if isinstance(wp.get("lat"), (int, float)) and isinstance(wp.get("lon"), (int, float)):
                pos = f"{wp['lat']:.5f}, {wp['lon']:.5f}"; any_pos = True
            t.row([str(wp["seq"]), _s(wp["label"]), _s(wp.get("grid") or "-"), _s(wp.get("fix") or "-"),
                   str(wp.get("satellites_used") if wp.get("satellites_used") is not None else "-"),
                   str(wp.get("hdop") if wp.get("hdop") is not None else "-"), _s(pos)])
    if not any_pos:
        d.body("No precise GPS positions were recorded (no fix during the walk - typical indoors); "
               "locations are the operator's waypoint labels.")

    d.h2("3. Spectrum")
    d.body("By band: " + (", ".join(f"{b}: {n}" for b, n in a["bands"].items()) or "(none)"))
    for band, counts in a["channels"].items():
        d.body(f"{band} channels: " + ", ".join(f"ch {ch} ({n})" for ch, n in counts.items()))

    d.h2("4. Security posture")
    d.set_font("Helvetica", "", 9)
    with d.table(col_widths=(60, 40), text_align="LEFT", headings_style=_HEAD,
                 width=100) as table:
        table.row(["Security", "Networks"])
        for sec, n in (a["security"].items() or []):
            table.row([sec, str(n)])
        if not a["security"]:
            table.row(["(none)", "0"])

    d.h2("5. Access point inventory")
    d.body("Sorted by strongest signal observed anywhere on the walk. BSSIDs included (operator "
           "tool, behind login); redact before external distribution if required.")
    d.set_font("Helvetica", "", 8)
    with d.table(col_widths=(46, 38, 18, 12, 18, 26, 22, 16, 42, 39), text_align="LEFT",
                 headings_style=_HEAD) as table:
        table.row(["SSID", "BSSID", "Band", "Ch", "Width", "Security", "Best signal", "Util",
                   "Vendor", "Seen at"])
        for ap in a["access_points"]:
            seen = ", ".join(dict.fromkeys(x for x in ap["seen_at"] if x))
            util = f"{ap['qbss_util_pct']}%" if ap.get("qbss_util_pct") is not None else "-"
            table.row([_s(_ssid(ap)), _s(ap["mac"] or "-"), _s(ap["band"] or "-"),
                       _s(ap["channel"] or "-"), _w(ap.get("width_mhz")), _s(ap["security"]),
                       _sig(ap["best_signal_dbm"]), util, _s(ap["manuf"] or "-"), _s(seen)])
        if not a["access_points"]:
            table.row(["(no access points heard)", "", "", "", "", "", "", "", "", ""])

    d.h2("6. Findings")
    if a["findings"]:
        order = {"crit": 0, "warn": 1, "info": 2}
        for f in sorted(a["findings"], key=lambda x: order.get(x["severity"], 3)):
            d.bullet(f"[{f['severity']}] {f['detail']}", bold_prefix=f["title"])
    else:
        d.body("No findings flagged by the automated checks.")

    d.h2("7. Method & limitations")
    for b in [
        "Data is whatever Kismet heard while channel-hopping during the walk; a network that did "
        "not beacon in that window may be under-represented or absent.",
        "Signal readings are the strongest RSSI seen at any waypoint, as reported by the capture "
        "radio. They are relative, not calibrated field strength.",
        "Positions are Maidenhead grid squares plus operator labels; no precise coordinates.",
        "Receive-only throughout. No association, no deauthentication, no decryption.",
    ]:
        d.bullet(b)
    return bytes(d.output())


_HEAD = FontFace(emphasis="BOLD", color=(215, 245, 215), fill_color=(34, 40, 34))


def _w(width):
    return f"{width} MHz" if width else "-"


def _gps(wp):
    bits = []
    if wp.get("grid"):
        bits.append(f"grid {wp['grid']}")
    if wp.get("fix"):
        bits.append(f"{wp['fix']} fix")
    if isinstance(wp.get("lat"), (int, float)) and isinstance(wp.get("lon"), (int, float)):
        bits.append(f"{wp['lat']:.5f}, {wp['lon']:.5f}")
    return " · ".join(bits) if bits else "no GPS"


def focus_pdf(focus: dict) -> bytes:
    """Focused-SSID technical report: ESS membership, per-waypoint per-BSSID signal/channel/overlap/
    contention, the site map when GPS positions exist, roaming footprint and self co-channel."""
    from . import sitemap
    d = _Doc("L")
    d.add_page()
    d.h1(_s(f"Wi-Fi survey - focused SSID: {focus.get('target_ssid')}"))
    d.meta([f"Survey: {focus.get('survey_name') or '(unnamed)'}",
            f"Target SSID (ESS): {focus.get('target_ssid')}  (match: {focus.get('match_mode')})",
            f"Waypoints: {len(focus.get('waypoints', []))}",
            "Method: passive observation (Kismet, receive-only)."])

    d.h2("ESS membership (BSSIDs advertising this SSID)")
    d.set_font("Helvetica", "", 9)
    with d.table(col_widths=(42, 18, 18, 18, 55, 30), text_align="LEFT", headings_style=_HEAD) as t:
        t.row(["BSSID", "Band", "Channel", "Width", "Vendor", "Mobility domain"])
        for m in focus.get("ess_bssids", []):
            md = m.get("mobility_domain")
            t.row([_s(m["mac"]), _s(m["band"] or "-"), _s(m["channel"] or "-"), _w(m["width_mhz"]),
                   _s(m["manuf"] or "-"), _s(str(md) if md not in (None, 0) else "-")])
        if not focus.get("ess_bssids"):
            t.row(["(none heard)", "", "", "", "", ""])

    wps = focus["waypoints"]

    # Findings first.
    d.h2("Findings")
    _findings_pdf(d, focus.get("findings", []))

    # Site map, if GPS positions exist.
    if sitemap.available(wps):
        d.h2("Site map (waypoints by GPS position, coloured by strongest signal)")
        _draw_sitemap(d, wps, "strongest_signal_dbm")

    # Best server per band, per waypoint.
    d.h2("Best server per band, by waypoint")
    d.set_font("Helvetica", "", 9)
    with d.table(col_widths=(44, 24, 85, 85), text_align="LEFT", headings_style=_HEAD) as t:
        t.row(["Waypoint", "Coverage", "Best 2.4 GHz", "Best 5 GHz"])
        for wp in wps:
            if wp["snapshot_error"]:
                t.row([_s(wp["label"]), "no data", "-", "-"]); continue
            b = wp.get("best_by_band", {}); b24 = b.get("2.4 GHz"); b5 = b.get("5 GHz")
            s24 = f"{b24['bssid']} {_sig(b24['signal_dbm'])}" if b24 else "-"
            s5 = f"{b5['bssid']} {_sig(b5['signal_dbm'])}" if b5 else "-"
            t.row([_s(wp["label"]), _s(wp.get("coverage") or "-"), _s(s24), _s(s5)])

    d.h2("Per-waypoint - signal, channel, overlap, contention")
    d.body("Signal is the last reading at the waypoint; QBSS stations/util are instantaneous. "
           "Co-ch = BSSIDs / distinct physical radios. Lifetime range and cumulative clients are in "
           "the roaming footprint.")
    for wp in wps:
        d.set_font("Helvetica", "B", 10)
        verdict = f"  - coverage {wp['coverage']}" if wp.get("coverage") else ""
        d.multi_cell(0, 6, _s(f"{wp['label']}   ({_gps(wp)}){verdict}"), new_x="LMARGIN", new_y="NEXT")
        if wp["snapshot_error"]:
            d.body(f"No data: {wp['snapshot_error']}"); continue
        if not wp["observations"]:
            d.body("This SSID was not heard at this waypoint."); continue
        d.set_font("Helvetica", "", 8)
        with d.table(col_widths=(40, 16, 12, 16, 20, 24, 12, 50, 18, 20), text_align="LEFT",
                     headings_style=_HEAD) as t:
            t.row(["BSSID", "Band", "Ch", "Width", "Signal", "Co-ch B/R", "Self",
                   "Adjacent overlaps", "Util", "Stations"])
            for o in wp["observations"]:
                ov = o["overlap"]; c = o["contention"]
                adj = ", ".join(f"ch{x['channel']} {x['overlap_mhz']}MHz" for x in ov["adjacent"]) or "-"
                util = f"{c['qbss_util_pct']}%" if c.get("qbss_util_pct") is not None else "-"
                sta = str(c["qbss_stations"]) if c.get("qbss_stations") is not None else "-"
                t.row([_s(o["bssid"]), _s(o["band"] or "-"), _s(o["channel"] or "-"), _w(o["width_mhz"]),
                       _sig(o["signal_dbm"]), f"{ov['co_channel_bssids']}/{ov['co_channel_radios']}",
                       str(len(ov["self_co_channel"])), _s(adj), util, sta])

    d.h2("Roaming footprint (per BSSID across the walk)")
    d.body("Best/worst across waypoints; clients are cumulative distinct clients (lower bound); "
           "stations is the peak QBSS count.")
    d.set_font("Helvetica", "", 8)
    with d.table(col_widths=(42, 16, 12, 18, 18, 22, 22, 78), text_align="LEFT", headings_style=_HEAD) as t:
        t.row(["BSSID", "Band", "Ch", "Best", "Worst", "Clients", "Peak sta", "Seen at"])
        for f in focus["roaming"]["per_bssid_footprint"]:
            seen = ", ".join(dict.fromkeys(x for x in f["seen_at"] if x))
            cl = f.get("clients_cumulative"); st = f.get("stations_max")
            t.row([_s(f["bssid"]), _s(f["band"] or "-"), _s(f["channel"] or "-"),
                   _sig(f["best_signal_dbm"]), _sig(f["worst_signal_dbm"]),
                   str(cl) if cl is not None else "-", str(st) if st is not None else "-", _s(seen)])

    pairs = focus["roaming"]["self_co_channel_pairs"]
    contending = [p for p in pairs if p["contending_waypoints"]]
    healthy = [p for p in pairs if not p["contending_waypoints"]]
    if pairs:
        d.h2("Same-channel sibling APs (frequency reuse)")
        if contending:
            d.body("Actual self-contention (both APs mutually strong - they steal airtime):")
            for p in contending:
                d.bullet(f"ch {p['channel']}: {p['bssid_a']} + {p['bssid_b']} at "
                         f"{', '.join(p['contending_waypoints'])}")
        if healthy:
            d.body("Healthy reuse (same channel but siblings never mutually strong): "
                   + ", ".join(f"ch {p['channel']}" for p in healthy) + ".")

    d.h2("Method & limitations")
    for n in focus.get("notes", []):
        d.bullet(n)
    return bytes(d.output())


def _findings_pdf(d: "_Doc", findings):
    if not findings:
        d.body("No findings flagged by the automated checks.")
        return
    order = {"crit": 0, "warn": 1, "info": 2}
    tag = {"crit": "[!]", "warn": "[warn]", "info": "[info]"}
    for f in sorted(findings, key=lambda x: order.get(x["severity"], 3)):
        d.bullet(f["detail"], bold_prefix=f"{tag.get(f['severity'], '-')} {f['title']}")


def _draw_sitemap(d: "_Doc", waypoints, value_key):
    """Draw the waypoint scatter natively (fpdf2 primitives — more reliable than embedding SVG text).
    Local equirectangular fit; relative layout of where the operator stood, north up."""
    pts = [w for w in waypoints
           if isinstance(w.get("lat"), (int, float)) and isinstance(w.get("lon"), (int, float))]
    if len(pts) < 2:
        return
    x0 = d.get_x(); y0 = d.get_y() + 2
    width_mm, height_mm = 170, 95
    lats = [p["lat"] for p in pts]; lons = [p["lon"] for p in pts]
    dlat = (max(lats) - min(lats)) or 1e-5; dlon = (max(lons) - min(lons)) or 1e-5
    pad = 12
    d.set_draw_color(34, 48, 34); d.set_line_width(0.2)
    d.rect(x0, y0, width_mm, height_mm)

    def xy(p):
        x = x0 + pad + (p["lon"] - min(lons)) / dlon * (width_mm - 2 * pad)
        y = y0 + pad + (1 - (p["lat"] - min(lats)) / dlat) * (height_mm - 2 * pad)
        return x, y

    ordered = sorted(pts, key=lambda p: p.get("seq") or 0)
    d.set_draw_color(63, 95, 63); d.set_line_width(0.3)
    prev = None
    for p in ordered:
        x, y = xy(p)
        if prev:
            d.line(prev[0], prev[1], x, y)
        prev = (x, y)
    for p in pts:
        x, y = xy(p)
        r, g, b = _BUCKET_RGB[analysis.signal_bucket(p.get(value_key))]
        d.set_fill_color(r, g, b)
        d.ellipse(x - 1.6, y - 1.6, 3.2, 3.2, style="F")
        d.set_xy(x + 2.4, y - 2)
        d.set_font("Helvetica", "", 7)
        d.set_text_color(60)
        d.cell(0, 4, _s(str(p.get("label") or "")))
    d.set_text_color(0)
    d.set_xy(x0, y0 + height_mm + 1)
    d.ln(height_mm + 4)


def _band_phrase(bands: dict) -> str:
    if not bands:
        return "no band data"
    return "band split: " + ", ".join(f"{n} on {b}" for b, n in bands.items())


def _recommendations(a, weak, marginal):
    recs = []
    if weak:
        recs.append("Identify and remediate the open / WEP / legacy-WPA networks - move any that "
                    "are ours to WPA2 or WPA3, and investigate any that are not.")
    if marginal:
        recs.append("Review coverage at the marginal location(s); consider AP placement or an "
                    "additional access point if those areas need reliable Wi-Fi.")
    ch24 = a["channels"].get("2.4 GHz", {})
    if any(ch not in {"1", "6", "11"} for ch in ch24):
        recs.append("Re-plan 2.4 GHz channels onto 1 / 6 / 11 to cut overlap and improve "
                    "throughput for older devices.")
    if a["totals"]["waypoints_failed"]:
        recs.append("Re-walk the point(s) where capture failed so the survey is complete.")
    if not recs:
        recs.append("No action required from this survey; retain as a baseline for comparison "
                    "against future walks.")
    return recs
