"""Reverse-proxies tar1090 (readsb's map UI) at /apps/tar1090/ — the only app proxied *through*
this app rather than linked to via its own tailscale serve mapping (see main.py and
software/webdash.md's "Other apps" section for why: tar1090 already uses paths relative to
whatever prefix it's served under — confirmed by grepping its shipped HTML for absolute hrefs —
so a straight passthrough proxy works without HTML/JS rewriting. Kismet and meshtasticd's web UI
assume they own the URL root, so those get their own tailscale serve port instead of fighting
that assumption here.

tar1090 itself has no login of its own (lighttpd serves it to anyone who can reach :80) — putting
it behind this app's TOTP session is a real access-control improvement, not just convenience.
"""
import httpx
from fastapi import Request
from fastapi.responses import Response

UPSTREAM_BASE = "http://127.0.0.1/tar1090"

# Forwarded as-is; everything else (content-encoding, content-length, transfer-encoding) is
# dropped because httpx already decompresses the upstream response body into `.content` — passing
# the original content-encoding header along with already-decoded bytes would mismatch and the
# browser would fail to render the page.
PASSTHROUGH_HEADERS = {"content-type", "cache-control", "etag", "last-modified"}


async def fetch(path: str, request: Request) -> Response:
    url = f"{UPSTREAM_BASE}/{path}"
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
        try:
            upstream = await client.get(url, params=request.query_params)
        except httpx.HTTPError as exc:
            return Response(content=f"tar1090 unreachable: {exc}", status_code=502)

    headers = {k: v for k, v in upstream.headers.items() if k.lower() in PASSTHROUGH_HEADERS}
    return Response(content=upstream.content, status_code=upstream.status_code, headers=headers)
