"""webdash -> sdr-bridge audio proxy. The browser's <audio> element hits /api/sdr/listen
(same-origin, so the session cookie authenticates it) and this relays the bridge's live MP3 stream.
Receive-only. When the browser disconnects, the generator's finally closes the upstream connection,
and the bridge then kills rtl_fm/ffmpeg and restores readsb.
"""
import json

import httpx
from fastapi.responses import JSONResponse, StreamingResponse

from . import hunt  # reuse BRIDGE address

MODES = ("nfm", "wbfm", "am")


async def stream(mode: str, freq: int, scan: str = "", squelch: int = 80):
    # Two shapes, same bridge endpoint: single-channel listen (mode+freq) or the airband scanner
    # (scan=<comma freqs>|"airband" + squelch). The bridge forces AM for the scanner.
    if scan:
        params = {"scan": scan, "squelch": squelch}
    else:
        if mode not in MODES:
            return JSONResponse({"ok": False, "error": "mode must be nfm/wbfm/am"}, status_code=400)
        params = {"mode": mode, "freq": freq}
    client = httpx.AsyncClient(timeout=None)
    try:
        req = client.build_request("GET", f"{hunt.BRIDGE}/listen", params=params)
        r = await client.send(req, stream=True)
    except httpx.HTTPError as exc:
        await client.aclose()
        return JSONResponse({"ok": False, "error": f"SDR bridge unreachable: {exc}"}, status_code=502)

    if r.status_code != 200:
        body = await r.aread()
        await r.aclose()
        await client.aclose()
        try:
            return JSONResponse(json.loads(body), status_code=r.status_code)
        except ValueError:
            return JSONResponse({"ok": False, "error": f"bridge HTTP {r.status_code}"},
                                status_code=r.status_code)

    async def gen():
        try:
            async for chunk in r.aiter_bytes():
                yield chunk
        finally:
            await r.aclose()
            await client.aclose()

    return StreamingResponse(gen(), media_type="audio/mpeg")
