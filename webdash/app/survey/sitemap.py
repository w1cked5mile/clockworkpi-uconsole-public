"""Site map: an SVG scatter of the survey's waypoints positioned by GPS, coloured by signal.

"If available" by design — a positional map needs real coordinates, and an indoor survey often has
no GPS fix (as the 2026-10-08 test walk did: fix "none", no lat/lon). `build()` returns None when
fewer than two waypoints carry coordinates, and the UI/report then shows a short "no GPS positions"
note instead (an operator-supplied floor plan backdrop is a noted follow-up, not built here).

Pure string-built SVG — no plotting dependency — so it renders in the browser preview and embeds
into the PDF (via fpdf2's SVG support). Projection is a simple local equirectangular fit: at a
single site the area is tiny and latitude distortion is negligible; this is a relative layout of
where the operator stood, not a georeferenced map.
"""
from . import analysis

W, H = 620, 430
MARGIN = 54
# Signal buckets → colour (dark-theme friendly, matches the dashboard palette).
_BUCKET_COLOR = {
    "excellent": "#4ade80", "good": "#86efac", "fair": "#facc15",
    "weak": "#fb923c", "poor": "#f87171", None: "#64748b",
}


def _positioned(waypoints: list[dict]) -> list[dict]:
    return [wp for wp in waypoints
            if isinstance(wp.get("lat"), (int, float)) and isinstance(wp.get("lon"), (int, float))]


def build(waypoints: list[dict], value_key: str = "best_signal_dbm", title: str = "Site map") -> str | None:
    """SVG string, or None if there aren't at least two positioned waypoints.

    `value_key` is the per-waypoint field used to colour each point by signal bucket
    (`best_signal_dbm` for a general survey, `strongest_signal_dbm` for a focused one)."""
    pts = _positioned(waypoints)
    if len(pts) < 2:
        return None

    lats = [p["lat"] for p in pts]
    lons = [p["lon"] for p in pts]
    lat0, lat1, lon0, lon1 = min(lats), max(lats), min(lons), max(lons)
    # Pad degenerate extents (all points nearly colinear or coincident) so nothing divides by zero
    # and the markers aren't jammed on an edge.
    dlat = (lat1 - lat0) or 1e-5
    dlon = (lon1 - lon0) or 1e-5
    plot_w, plot_h = W - 2 * MARGIN, H - 2 * MARGIN

    def xy(p):
        x = MARGIN + (p["lon"] - lon0) / dlon * plot_w
        y = MARGIN + (1 - (p["lat"] - lat0) / dlat) * plot_h  # north up
        return x, y

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
        'font-family="system-ui, sans-serif">',
        f'<rect x="0" y="0" width="{W}" height="{H}" fill="#0e130e"/>',
        f'<text x="{MARGIN}" y="26" fill="#d7f5d7" font-size="15" font-weight="bold">{_esc(title)}</text>',
        f'<rect x="{MARGIN}" y="{MARGIN - 8}" width="{plot_w}" height="{plot_h + 8}" '
        'fill="none" stroke="#223022"/>',
    ]
    # Connect waypoints in walk order (seq) as a faint path.
    ordered = sorted(pts, key=lambda p: p.get("seq") or 0)
    path = " ".join(f"{'M' if i == 0 else 'L'}{x:.1f},{y:.1f}"
                    for i, (x, y) in enumerate(xy(p) for p in ordered))
    parts.append(f'<path d="{path}" fill="none" stroke="#3f5f3f" stroke-width="1.5" '
                 'stroke-dasharray="4 3"/>')
    for p in pts:
        x, y = xy(p)
        val = p.get(value_key)
        color = _BUCKET_COLOR[analysis.signal_bucket(val)]
        label = _esc(str(p.get("label") or f"WP{p.get('seq', '')}"))
        vtxt = f"{val} dBm" if isinstance(val, (int, float)) else "no signal"
        parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="8" fill="{color}" '
                     'stroke="#0e130e" stroke-width="1.5"/>')
        parts.append(f'<text x="{x + 11:.1f}" y="{y + 4:.1f}" fill="#d7f5d7" font-size="11">'
                     f'{label} <tspan fill="#7fa87f">({vtxt})</tspan></text>')
    # Legend.
    lx, ly = MARGIN, H - 16
    parts.append(f'<text x="{lx}" y="{ly}" fill="#7fa87f" font-size="10">Signal:</text>')
    for i, (name, col) in enumerate([("excellent", _BUCKET_COLOR["excellent"]),
                                     ("good", _BUCKET_COLOR["good"]), ("fair", _BUCKET_COLOR["fair"]),
                                     ("weak", _BUCKET_COLOR["weak"]), ("poor", _BUCKET_COLOR["poor"])]):
        cx = lx + 52 + i * 92
        parts.append(f'<circle cx="{cx}" cy="{ly - 4}" r="5" fill="{col}"/>')
        parts.append(f'<text x="{cx + 9}" y="{ly}" fill="#7fa87f" font-size="10">{name}</text>')
    parts.append("</svg>")
    return "".join(parts)


def available(waypoints: list[dict]) -> bool:
    return len(_positioned(waypoints)) >= 2


def _esc(s: str) -> str:
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))
