"""Render the Detect contact log as CSV, JSON or Markdown. Pure stdlib.

Exports carry the grid square and the operator's place label, never lat/lon. They do carry
hardware addresses and SSIDs, so they're for the owner's own devices — not for WiGLE or any map.
"""
import csv
import io
import json
import time

COLUMNS = ["first_seen_utc", "last_seen_utc", "class", "confidence", "rule", "name", "address",
           "address_type", "ssids", "radio", "channel", "rssi_first", "rssi_peak", "rssi_last",
           "sightings", "grid_first", "grid_last", "place", "source", "detail"]


def utc(ts) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(ts)) if ts else ""


def _row(r: dict) -> dict:
    return {
        "first_seen_utc": utc(r.get("first_seen")), "last_seen_utc": utc(r.get("last_seen")),
        "class": r.get("cls"), "confidence": r.get("confidence"), "rule": r.get("rule_text") or r.get("rule_id"),
        "name": r.get("name") or "", "address": r.get("ident") or "", "address_type": r.get("addr_type") or "",
        "ssids": "; ".join(r.get("ssids") or []), "radio": r.get("radio"), "channel": r.get("channel") or "",
        "rssi_first": r.get("rssi_first"), "rssi_peak": r.get("rssi_peak"), "rssi_last": r.get("rssi_last"),
        "sightings": r.get("sightings"), "grid_first": r.get("grid_first") or "",
        "grid_last": r.get("grid_last") or "", "place": r.get("place") or "",
        "source": r.get("source"), "detail": r.get("detail") or "",
    }


def _csv_safe(v):
    # A cell starting with = + - @ is a formula to a spreadsheet. Names and SSIDs come off the air,
    # so neutralise them (RSSI is numeric and stays as is).
    if isinstance(v, str) and v[:1] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + v
    return v


def to_csv(records: list[dict]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS)
    w.writeheader()
    for r in records:
        w.writerow({k: _csv_safe(v) for k, v in _row(r).items()})
    return buf.getvalue()


def to_json(records: list[dict]) -> str:
    return json.dumps({"generated_utc": utc(time.time()), "count": len(records),
                       "contacts": [_row(r) for r in records]}, indent=1)


def _md(v) -> str:
    return str(v if v not in (None, "") else "—").replace("|", "\\|").replace("\n", " ")


def to_markdown(records: list[dict]) -> str:
    lines = [f"# Detect contact log — exported {utc(time.time())}", "",
             f"{len(records)} contact(s). Passive, receive-only observation. Addresses are hardware, "
             "not people; many devices rotate them. Grid squares only — no coordinates.", "",
             "| Last seen (UTC) | Class | Confidence | Name | Address | Radio · ch | RSSI last/peak | Sightings | Grid | Rule |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        x = _row(r)
        lines.append("| " + " | ".join(_md(v) for v in (
            x["last_seen_utc"], x["class"], x["confidence"], x["name"],
            f"{x['address']} ({x['address_type']})" if x["address"] else "",
            f"{x['radio']} {x['channel']}".strip(), f"{x['rssi_last']} / {x['rssi_peak']}",
            x["sightings"], x["grid_last"] + (f" · {x['place']}" if x["place"] else ""), x["rule"])) + " |")
    return "\n".join(lines) + "\n"
