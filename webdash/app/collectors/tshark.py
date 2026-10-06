"""Passive packet-capture summary, via the host-side bridge (127.0.0.1:8768).

A troubleshooting tap for the hang/dropout investigation: the host bridge drives a bounded,
receive-only `dumpcap` ring buffer and reads the newest segment back with `tshark` to produce
aggregate counts. See docs/reference/webdash-architecture.md for why capture lives in a host bridge
(it needs capture privilege and a persistent process) rather than inside this container.

Everything surfaced here is ADDRESS-FREE — packet/byte counts, rates, protocol names, and TCP/ICMP
anomaly counts — matching the status-payload rule in net.py: the payload never carries a MAC or IP.
The on-disk pcap does contain addresses and is kept in ~/labs/tshark for a Wireshark deep-dive; the
summary lists its filename and size only, never its contents.
"""
import httpx

BRIDGE_BASE = "http://127.0.0.1:8768"


async def collect() -> dict:
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            r = await client.get(f"{BRIDGE_BASE}/capture/status")
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"state": "unavailable", "error": str(exc)}
    return {"state": "ok", **data}


async def start(req: dict) -> dict:
    """Starts a bounded, receive-only capture. The bridge re-validates the interface and clamps the
    ring/duration limits; the route (main.py) owns the auth gate. Passes interface, optional BPF
    capture filter, and ring/duration overrides straight through."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{BRIDGE_BASE}/capture", json=req)
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}


async def cancel() -> dict:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.post(f"{BRIDGE_BASE}/capture/cancel", json={})
            return r.json()
    except (httpx.HTTPError, ValueError) as exc:
        return {"ok": False, "error": str(exc)}
