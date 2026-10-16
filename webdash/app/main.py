"""uConsole webdash — FastAPI app. See docs/reference/webdash-architecture.md."""
import asyncio
import os
import time
from collections import deque
from typing import Literal

from fastapi import Cookie, Depends, FastAPI, Form, Header, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field
from starlette.websockets import WebSocket, WebSocketDisconnect

from . import auth, proxy, widget
from .collectors import adsb, aiov2, gps, kismet, mesh, net, services, system, tshark
from .sdr import hunt as sdr_hunt
from .sdr import listen as sdr_listen
from .wpa import allowlist as wpa_allowlist
from .wpa import capture as wpa_capture
from .wpa import crack as wpa_crack
from .learn import labs as learn_labs
from .learn import routes as learn_routes
from .survey import analysis as survey_analysis
from .survey import pdf as survey_pdf
from .survey import report as survey_report
from .survey import sitemap as survey_sitemap
from .survey import snapshot as survey_snapshot
from .survey import store as survey_store
from .detect import engine as detect_engine
from .detect import export as detect_export
from .detect import rules as detect_rules
from .detect import store as detect_store

app = FastAPI(title="Fancy Dashboard")


class RevalidatedStaticFiles(StaticFiles):
    """Static files the browser must revalidate (cheap: ETag → 304), so a rebuilt image's CSS/JS
    shows up on the next reload instead of after a heuristic cache lifetime."""

    def file_response(self, *args, **kwargs):
        resp = super().file_response(*args, **kwargs)
        resp.headers["Cache-Control"] = "no-cache"
        return resp


app.mount("/static", RevalidatedStaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/static")
app.include_router(learn_routes.router)

START_TIME = time.time()

# This device's tailnet FQDN — Kismet and meshtasticd's web UI get their own `tailscale serve`
# port mapping rather than being proxied through this app (see proxy.py's docstring for why).
# Override via env if this is ever reused on a different device.
TAILNET_FQDN = os.environ.get("WEBDASH_TAILNET_FQDN", "fancy.example-tailnet.ts.net")


COLLECT_INTERVAL_S = 3.0
HISTORY_INTERVAL_S = 30.0
HISTORY_LEN = 240  # 2 h at 30 s

# One collection loop for the whole app: every WebSocket client and /api/status get the same
# cached snapshot, instead of each client triggering its own gpsd/Kismet/bridge round-trips every
# 3 s. It also keeps meshtasticd's TCP interface connected with no dashboard open, so incoming
# text messages reach mesh.py's buffer rather than only while someone is watching.
_latest: dict | None = None
_history: deque = deque(maxlen=HISTORY_LEN)


def _avg_temp_1h() -> float | None:
    """Mean CPU temp over the last hour from the in-memory history (one sample / 30 s).
    None until the first sample lands; a true 1 h mean only once an hour of history exists."""
    cutoff = time.time() - 3600
    temps = [s["temp_c"] for s in _history if s["ts"] >= cutoff and s.get("temp_c") is not None]
    return round(sum(temps) / len(temps), 1) if temps else None


def _history_sample(st: dict) -> dict:
    p = (st.get("aiov2") or {}).get("power_num") or {}
    g, m = st.get("gps") or {}, st.get("mesh") or {}
    return {
        "ts": st["generated_at"],
        "cpu_percent": st["system"]["cpu_percent"],
        "temp_c": st["system"]["temp_c"],
        "voltage_v": p.get("voltage_v"),
        "power_w": p.get("power_w"),
        "gps_sats_used": g.get("satellites_used"),
        "mesh_nodes": m.get("nodes_seen"),
    }


async def _collect_loop():
    global _latest
    next_history = 0.0
    while True:
        try:
            _latest = await build_status()
            if _latest["generated_at"] >= next_history:
                _history.append(_history_sample(_latest))
                next_history = _latest["generated_at"] + HISTORY_INTERVAL_S
            # Derived from history, so it lives on the loop, not in system.collect(): every
            # WebSocket push and /api/status sees it via the shared _latest snapshot.
            _latest["system"]["temp_avg_1h_c"] = _avg_temp_1h()
            try:
                learn_labs.tick(_latest)
            except Exception as exc:  # noqa: BLE001 — learning must never stop status collection
                print(f"learn: tick failed: {exc!r}", flush=True)
        except Exception as exc:  # noqa: BLE001 — one bad cycle must never kill the loop
            print(f"status collection failed: {exc!r}", flush=True)
        await asyncio.sleep(COLLECT_INTERVAL_S)


@app.on_event("startup")
async def _start_background():
    learn_routes.set_status_source(lambda: _latest)
    try:
        learn_labs.recover()
    except Exception as exc:  # noqa: BLE001 — e.g. /data missing or not writable
        print(f"learning disabled: {exc!r} (check ~/.local/share/uconsole-webdash/data)", flush=True)
    app.state.collector = asyncio.create_task(_collect_loop())
    app.state.detect = asyncio.create_task(detect_engine.run(lambda: _latest))


async def current_status() -> dict:
    return _latest if _latest is not None else await build_status()


async def build_status() -> dict:
    aiov2_r, kismet_r, gps_r, adsb_r, mesh_r, services_r, tshark_r = await asyncio.gather(
        aiov2.collect(), kismet.collect(), gps.collect(), adsb.collect(), mesh.collect(),
        services.collect(), tshark.collect(),
    )
    status = {
        "system": system.collect(),
        "aiov2": aiov2_r,
        "kismet": kismet_r,
        "gps": gps_r,
        "adsb": adsb_r,
        "mesh": mesh.with_tx(mesh_r, aiov2_r, services_r),
        "services": services_r,
        "net": net.collect(),
        "tshark": tshark_r,
        "generated_at": time.time(),
    }
    try:
        status["detect"] = detect_engine.status_summary(status)
    except Exception as exc:  # noqa: BLE001 — a bad log file must never stop status collection
        status["detect"] = {"error": f"detect unavailable: {exc!r}"}
    return status


# ---------------------------------------------------------------------------
# Auth pages
# ---------------------------------------------------------------------------


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    if auth.is_configured():
        return RedirectResponse("/login")
    return templates.TemplateResponse("setup.html", {"request": request, "error": None})


@app.post("/setup", response_class=HTMLResponse)
async def setup_submit(
    request: Request, username: str = Form(...), password: str = Form(...)
):
    if auth.is_configured():
        return RedirectResponse("/login")
    if len(password) < 8:
        return templates.TemplateResponse(
            "setup.html",
            {"request": request, "error": "Password must be at least 8 characters."},
        )
    uri = auth.create_account(username, password)
    qr = auth.setup_qr_svg(uri)
    return templates.TemplateResponse("setup_done.html", {"request": request, "qr_svg": qr})


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    if not auth.is_configured():
        return RedirectResponse("/setup")
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login")
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    totp_code: str = Form(...),
):
    if not auth.verify_login(username, password, totp_code):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username, password, or code."},
            status_code=401,
        )
    resp = RedirectResponse("/", status_code=303)
    resp.set_cookie(
        auth.SESSION_COOKIE,
        auth.make_session_cookie(),
        max_age=auth.SESSION_MAX_AGE_S,
        httponly=True,
        samesite="lax",
    )
    return resp


@app.get("/logout")
async def logout():
    resp = RedirectResponse("/login")
    resp.delete_cookie(auth.SESSION_COOKIE)
    return resp


# ---------------------------------------------------------------------------
# Dashboard page (own redirect logic — see auth.require_session's docstring)
# ---------------------------------------------------------------------------


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, uconsole_webdash_session: str | None = Cookie(default=None)):
    if not auth.is_configured():
        return RedirectResponse("/setup")
    if not auth.session_ok(uconsole_webdash_session):
        return RedirectResponse("/login")
    return templates.TemplateResponse("index.html", {"request": request})


# ---------------------------------------------------------------------------
# API — all behind auth.require_session
# ---------------------------------------------------------------------------


@app.get("/api/health")
async def health():
    return {"ok": True, "uptime_s": int(time.time() - START_TIME)}


@app.get("/api/widget")
async def api_widget(authorization: str | None = Header(default=None)):
    """Compact status for the phone widget. Bearer token, not the session cookie (a widget can't
    do TOTP); the token opens this read-only route and nothing else. See app/widget.py."""
    if not widget.token_ok(widget.bearer(authorization)):
        raise HTTPException(status_code=401, detail="not authenticated")
    return JSONResponse(widget.summary(await current_status(), list(_history)),
                        headers={"Cache-Control": "no-store"})


@app.get("/api/status", dependencies=[Depends(auth.require_session)])
async def api_status():
    return JSONResponse(await current_status())


@app.get("/api/history", dependencies=[Depends(auth.require_session)])
async def api_history():
    """Last 2 h of vitals, one sample per 30 s, in memory only (empty after a restart)."""
    return {"interval_s": HISTORY_INTERVAL_S, "samples": list(_history)}


@app.get("/api/links", dependencies=[Depends(auth.require_session)])
async def api_links():
    """URLs for the apps that get their own tailscale serve mapping instead of being proxied
    through this one (see proxy.py) — Kismet has its own login; meshtasticd's web UI does not,
    which is called out in software/webdash.md rather than silently relied on."""
    return {
        "kismet": f"https://{TAILNET_FQDN}:2501/",
        "meshtastic_ui": f"https://{TAILNET_FQDN}:9443/",
        # OpenWebRX — web-native SDR receiver, its own admin login, tailscale serve on :8073.
        "openwebrx": f"https://{TAILNET_FQDN}:8073/",
    }


class RailRequest(BaseModel):
    feature: Literal["GPS", "LORA", "SDR", "USB"]
    state: Literal["on", "off"]


@app.post("/api/aiov2/rail", dependencies=[Depends(auth.require_session)])
async def api_set_rail(body: RailRequest):
    # Cutting the SDR rail while readsb holds the tuner makes readsb crash-loop: systemd restarts it
    # straight into a missing dongle (~340 restarts on 2026-10-09). Stop ADS-B first, so the rail
    # powers down an idle tuner. Best-effort — set_adsb returns an error dict rather than raising if
    # the SDR bridge is unreachable, and we cut the rail regardless. (OpenWebRX is restart:"no", so
    # it errors but never thrashes; the user stops it from the Receiver tab.) This covers rail-off
    # from the dashboard; a CLI `aiov2_ctl SDR off` still bypasses it — see TODO.md.
    if body.feature == "SDR" and body.state == "off":
        await sdr_hunt.set_adsb("stop")
    result = await aiov2.set_rail(body.feature, body.state)
    return JSONResponse(result, status_code=200 if result.get("ok") else 502)


class KismetRequest(BaseModel):
    action: Literal["start", "stop"]


@app.post("/api/kismet/control", dependencies=[Depends(auth.require_session)])
async def api_kismet_control(body: KismetRequest):
    """Start/stop Kismet via the host bridge (a user systemd service). Receive-only survey tool;
    see software/kismet.md for the legal posture. Same auth gate as the rail/mesh write paths."""
    result = await kismet.control(body.action)
    return JSONResponse(result, status_code=200 if result.get("ok") else 502)


# --- SDR broadcast/airband hunt (receive-only) ---------------------------------------------
# One-shot rtl_power sweep via the host SDR bridge; brackets readsb (shared tuner). See
# software/sdr-stack.md. Listening (audio stream) is a later phase.
class SdrHuntRequest(BaseModel):
    band: Literal["fm", "airband"]


@app.post("/api/sdr/hunt", dependencies=[Depends(auth.require_session)])
async def api_sdr_hunt(body: SdrHuntRequest):
    result = await sdr_hunt.start(body.band)
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


@app.get("/api/sdr/hunt/status", dependencies=[Depends(auth.require_session)])
async def api_sdr_hunt_status():
    return await sdr_hunt.status()


@app.get("/api/sdr/scan/status", dependencies=[Depends(auth.require_session)])
async def api_sdr_scan_status():
    """Live airband-scanner state (the frequency it's parked on, or None while sweeping)."""
    return await sdr_hunt.scan_status()


class SdrAdsbRequest(BaseModel):
    action: Literal["start", "stop"]


@app.post("/api/sdr/adsb", dependencies=[Depends(auth.require_session)])
async def api_sdr_adsb(body: SdrAdsbRequest):
    """Start/stop ADS-B (readsb) as a chosen SDR application — the rail toggle no longer implies it.
    Mutually exclusive with hunt/listen on the single tuner; the bridge enforces it."""
    result = await sdr_hunt.set_adsb(body.action)
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


class SdrOwrxRequest(BaseModel):
    action: Literal["start", "stop"]


@app.post("/api/sdr/owrx", dependencies=[Depends(auth.require_session)])
async def api_sdr_owrx(body: SdrOwrxRequest):
    """Start/stop OpenWebRX (the web-native receiver) as a chosen SDR application. It owns the tuner
    continuously while up, so it is mutually exclusive with ADS-B/hunt/listen; the bridge enforces
    it and runs the container. The UI opens the receiver at the /api/links openwebrx URL."""
    result = await sdr_hunt.set_owrx(body.action)
    err = result.get("error", "")
    status = 200 if result.get("ok") else 409 if "busy" in err or "USB rail" in err else 400
    return JSONResponse(result, status_code=status)


@app.get("/api/sdr/listen", dependencies=[Depends(auth.require_session)])
async def api_sdr_listen(mode: str = "am", freq: int = 0, scan: str = "", squelch: int = 80):
    """Relay a live receive-only audio stream from the SDR bridge to the browser <audio>. Either a
    single channel (mode+freq) or the airband scanner (scan=<comma freqs>|"airband" + squelch),
    which pauses on traffic and resumes. Same-origin session cookie authenticates it; see
    software/sdr-stack.md."""
    return await sdr_listen.stream(mode, freq, scan, squelch)


# --- Passive packet capture (troubleshooting tap, receive-only) ----------------------------
# A bounded dumpcap ring buffer on a chosen interface, summarized address-free for the dash. For
# the hang/dropout investigation; no transmit path. The host bridge re-validates the interface and
# clamps the ring/duration limits. Same auth gate as the other write paths.
class TsharkCaptureRequest(BaseModel):
    iface: str = Field(min_length=1, max_length=15)
    filter: str = Field(default="", max_length=200)
    ringsize: int | None = None          # KB per ring file
    ringfiles: int | None = None         # ring files kept
    duration: int | None = None          # overall cap in seconds, 0 = until cancelled
    stats_interval: int | None = None


@app.post("/api/tshark/capture", dependencies=[Depends(auth.require_session)])
async def api_tshark_capture(body: TsharkCaptureRequest):
    result = await tshark.start(body.model_dump(exclude_none=True))
    return JSONResponse(result, status_code=200 if result.get("ok")
                        else 409 if "already" in result.get("error", "") else 400)


@app.post("/api/tshark/capture/cancel", dependencies=[Depends(auth.require_session)])
async def api_tshark_cancel():
    result = await tshark.cancel()
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


# --- WPA audit (authorized equipment only) -------------------------------------------------
# The BSSID allowlist gate. Active auditing (deauth/capture, added in a later phase) runs only
# against a BSSID added here; the host-side helper re-enforces this list. See
# docs/reference/webdash-architecture.md and software/aircrack-ng.md.
class WpaAllowlistAdd(BaseModel):
    bssid: str = Field(min_length=17, max_length=17)
    basis: str = Field(min_length=1, max_length=128)
    ssid_label: str = Field("", max_length=64)


@app.get("/api/wpa/allowlist", dependencies=[Depends(auth.require_session)])
async def api_wpa_allowlist():
    return {"entries": wpa_allowlist.load()}


@app.post("/api/wpa/allowlist", dependencies=[Depends(auth.require_session)])
async def api_wpa_allowlist_add(body: WpaAllowlistAdd):
    result = wpa_allowlist.add(body.bssid, body.basis, body.ssid_label)
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


@app.delete("/api/wpa/allowlist/{bssid}", dependencies=[Depends(auth.require_session)])
async def api_wpa_allowlist_remove(bssid: str):
    result = wpa_allowlist.remove(bssid)
    return JSONResponse(result, status_code=200 if result.get("ok") else 404)


class WpaCaptureStart(BaseModel):
    bssid: str = Field(min_length=17, max_length=17)
    channel: int | None = Field(None, ge=1, le=196)


@app.post("/api/wpa/capture", dependencies=[Depends(auth.require_session)])
async def api_wpa_capture_start(body: WpaCaptureStart):
    """Start an authorized WPA handshake capture against an allowlisted BSSID (deauth + capture via
    the host bridge). Transmits bounded deauth; authorized equipment only — the bridge and the root
    script both re-enforce the allowlist. Same session gate as every other write path."""
    result = await wpa_capture.start(body.bssid, body.channel)
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


@app.get("/api/wpa/capture/status", dependencies=[Depends(auth.require_session)])
async def api_wpa_capture_status():
    return await wpa_capture.status()


@app.post("/api/wpa/capture/cancel", dependencies=[Depends(auth.require_session)])
async def api_wpa_capture_cancel():
    result = await wpa_capture.cancel()
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


class WpaCrackStart(BaseModel):
    cap: str = Field(min_length=1, max_length=512)


@app.post("/api/wpa/crack", dependencies=[Depends(auth.require_session)])
async def api_wpa_crack_start(body: WpaCrackStart):
    """Offload a captured handshake to the GPU host (gpu-host) to recover the PSK. The cap must
    be one this webdash captured (bridge re-validates). Authorized-audit use; the PSK is returned to
    this session only and not persisted. See software/aircrack-ng.md."""
    result = await wpa_crack.start(body.cap)
    return JSONResponse(result, status_code=200 if result.get("ok") else 400)


@app.get("/api/wpa/crack/status", dependencies=[Depends(auth.require_session)])
async def api_wpa_crack_status():
    return await wpa_crack.status()


# --- Claude-assisted Wi-Fi survey (passive) ------------------------------------------------
# A site-survey workflow over the passive Kismet collector: start a survey, drop a waypoint at
# each location (each captures a Kismet device snapshot tagged with the GPS grid square), stop,
# then generate a comprehensive technical report and a leadership executive summary. Receive-only
# throughout — see app/survey/ and docs/reference/webdash-architecture.md. Same session gate as
# every other route.

def _active_survey_brief() -> dict | None:
    """The active survey without the heavy per-waypoint device lists — for the status poll."""
    s = survey_store.get_active()
    if not s:
        return None
    return {
        "id": s["id"], "name": s["name"], "created": s["created"],
        "status": s["status"],
        "waypoints": [{"seq": w["seq"], "label": w["label"], "grid": w["grid"], "fix": w["fix"],
                       "device_count": w["device_count"], "note": w["note"],
                       "snapshot_error": w["snapshot_error"]} for w in s["waypoints"]],
    }


@app.get("/api/survey/active", dependencies=[Depends(auth.require_session)])
async def api_survey_active():
    return {"active": _active_survey_brief()}


@app.get("/api/survey/list", dependencies=[Depends(auth.require_session)])
async def api_survey_list():
    return {"surveys": survey_store.list_surveys()}


class SurveyStart(BaseModel):
    name: str = Field("", max_length=survey_store.MAX_NAME)


@app.post("/api/survey/start", dependencies=[Depends(auth.require_session)])
async def api_survey_start(body: SurveyStart):
    result = survey_store.start(body.name)
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


class SurveyWaypoint(BaseModel):
    label: str = Field("", max_length=survey_store.MAX_LABEL)
    note: str = Field("", max_length=survey_store.MAX_NOTE)


@app.post("/api/survey/waypoint", dependencies=[Depends(auth.require_session)])
async def api_survey_waypoint(body: SurveyWaypoint):
    """Capture a waypoint: a passive Kismet device snapshot + the current GPS grid/fix. If Kismet
    is down the waypoint is still recorded, with the snapshot error noted, so the position isn't
    lost."""
    snap, loc = await asyncio.gather(survey_snapshot.capture(), gps.collect())
    result = survey_store.add_waypoint(body.label, loc, snap, body.note)
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


@app.post("/api/survey/waypoint/undo", dependencies=[Depends(auth.require_session)])
async def api_survey_waypoint_undo():
    result = survey_store.delete_last_waypoint()
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


@app.post("/api/survey/stop", dependencies=[Depends(auth.require_session)])
async def api_survey_stop():
    result = survey_store.stop()
    return JSONResponse(result, status_code=200 if result.get("ok") else 409)


@app.get("/api/survey/{survey_id}", dependencies=[Depends(auth.require_session)])
async def api_survey_get(survey_id: str):
    s = survey_store.get(survey_id)
    if not s:
        return JSONResponse({"ok": False, "error": "no such survey"}, status_code=404)
    return survey_analysis.analyze(s)


@app.get("/api/survey/{survey_id}/ssids", dependencies=[Depends(auth.require_session)])
async def api_survey_ssids(survey_id: str):
    """Distinct named SSIDs in the survey (with BSSID count + bands) for the focus picker."""
    s = survey_store.get(survey_id)
    if not s:
        return JSONResponse({"ok": False, "error": "no such survey"}, status_code=404)
    return {"ssids": survey_analysis.list_ssids(s)}


@app.get("/api/survey/{survey_id}/focus", dependencies=[Depends(auth.require_session)])
async def api_survey_focus(survey_id: str, ssid: str, mode: str = "exact"):
    """Per-AP, per-waypoint signal/channel/overlap/contention for one SSID (ESS), plus the site-map
    SVG when the waypoints carry GPS positions (null otherwise)."""
    s = survey_store.get(survey_id)
    if not s:
        return JSONResponse({"ok": False, "error": "no such survey"}, status_code=404)
    if not ssid:
        return JSONResponse({"ok": False, "error": "ssid is required"}, status_code=400)
    focus = survey_analysis.focus_analysis(s, ssid, "ci" if mode == "ci" else "exact")
    svg = survey_sitemap.build(focus["waypoints"], "strongest_signal_dbm",
                               f"{ssid} — strongest signal by waypoint")
    return {"focus": focus, "map_svg": svg}


@app.get("/api/survey/{survey_id}/report", dependencies=[Depends(auth.require_session)])
async def api_survey_report(survey_id: str, kind: str = "comprehensive", fmt: str = "md",
                            ssid: str = "", mode: str = "exact"):
    """Render a survey. kind = comprehensive | executive | brief | focus; fmt = md | pdf.
    `focus` needs `ssid` (the ESS to narrow to) and reports signal/channel/overlap/contention per
    AP per waypoint. `brief` is a prompt, so it stays Markdown. Served as a download."""
    s = survey_store.get(survey_id)
    if not s:
        return JSONResponse({"ok": False, "error": "no such survey"}, status_code=404)
    safe = "".join(c for c in (s.get("name") or "survey") if c.isalnum() or c in " -_").strip() or "survey"
    base = f"{safe.replace(' ', '-')}-{kind}"

    if kind == "focus":
        if not ssid:
            return JSONResponse({"ok": False, "error": "focus needs an ssid"}, status_code=400)
        focus = survey_analysis.focus_analysis(s, ssid, "ci" if mode == "ci" else "exact")
        ssid_safe = "".join(c for c in ssid if c.isalnum() or c in "-_") or "ssid"
        base = f"{safe.replace(' ', '-')}-focus-{ssid_safe}"
        if fmt == "pdf":
            return Response(survey_pdf.focus_pdf(focus), media_type="application/pdf",
                            headers={"Content-Disposition": f'attachment; filename="{base}.pdf"'})
        return PlainTextResponse(survey_report.focus_markdown(focus),
                                 media_type="text/markdown; charset=utf-8",
                                 headers={"Content-Disposition": f'attachment; filename="{base}.md"'})

    a = survey_analysis.analyze(s)
    if fmt == "pdf":
        build = {"comprehensive": survey_pdf.comprehensive_pdf,
                 "executive": survey_pdf.executive_pdf}.get(kind)
        if not build:
            return JSONResponse({"ok": False, "error": "PDF is available for comprehensive, executive or focus"},
                                status_code=400)
        return Response(build(a), media_type="application/pdf",
                        headers={"Content-Disposition": f'attachment; filename="{base}.pdf"'})

    render = {"comprehensive": survey_report.comprehensive,
              "executive": survey_report.executive,
              "brief": survey_report.claude_brief}.get(kind)
    if not render:
        return JSONResponse({"ok": False, "error": "kind must be comprehensive, executive, brief or focus"},
                            status_code=400)
    return PlainTextResponse(render(a), media_type="text/markdown; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="{base}.md"'})


@app.delete("/api/survey/{survey_id}", dependencies=[Depends(auth.require_session)])
async def api_survey_delete(survey_id: str):
    result = survey_store.delete(survey_id)
    return JSONResponse(result, status_code=200 if result.get("ok") else 404)


# --- Detect: offensive-device detection (passive) --------------------------------------------
# Reads what Kismet has heard, matches it against the owner's rules file and keeps a contact log
# under WEBDASH_DATA_DIR. Receive-only: nothing here transmits or touches a detected device, and
# no route offers any action on one beyond annotating or deleting its log record. See app/detect/.

class DetectWatch(BaseModel):
    action: Literal["start", "stop"]


class DetectPlace(BaseModel):
    place: str = Field("", max_length=detect_store.MAX_PLACE)


class DetectClear(BaseModel):
    confirm: Literal[True]


def _detect_filter(cls: str, conf: str, hours: float) -> list[dict]:
    since = time.time() - hours * 3600 if hours and hours > 0 else 0.0
    return detect_store.filtered(cls if cls in detect_rules.CLASSES else "",
                                 conf if conf in detect_rules.CONFIDENCES else "", since)


@app.get("/api/detect/records", dependencies=[Depends(auth.require_session)])
async def api_detect_records(cls: str = "", conf: str = "", hours: float = 0):
    recs = _detect_filter(cls, conf, hours)
    since = time.time() - (hours * 3600 if hours and hours > 0 else 86400)
    return {"records": recs[:1000], "shown": len(recs), "total": len(detect_store.records()),
            "coverage": detect_store.coverage(since), "coverage_since": since}


@app.get("/api/detect/rules", dependencies=[Depends(auth.require_session)])
async def api_detect_rules():
    rules, errors = detect_rules.load()
    return {"path": detect_rules.RULES_PATH.name, "rules": [detect_rules.public(r) for r in rules],
            "errors": errors}


@app.post("/api/detect/watch", dependencies=[Depends(auth.require_session)])
async def api_detect_watch(body: DetectWatch):
    return {"ok": True, **detect_store.set_armed(body.action == "start")}


@app.post("/api/detect/seen", dependencies=[Depends(auth.require_session)])
async def api_detect_seen():
    return {"ok": True, "seen_marker": detect_store.mark_seen()}


@app.post("/api/detect/record/{rid}/place", dependencies=[Depends(auth.require_session)])
async def api_detect_place(rid: str, body: DetectPlace):
    result = detect_store.set_place(rid, body.place)
    return JSONResponse(result, status_code=200 if result.get("ok") else 404)


@app.delete("/api/detect/record/{rid}", dependencies=[Depends(auth.require_session)])
async def api_detect_delete(rid: str):
    result = detect_store.delete(rid)
    return JSONResponse(result, status_code=200 if result.get("ok") else 404)


@app.post("/api/detect/clear", dependencies=[Depends(auth.require_session)])
async def api_detect_clear(body: DetectClear):
    return detect_store.clear()


@app.get("/api/detect/export", dependencies=[Depends(auth.require_session)])
async def api_detect_export(fmt: Literal["csv", "json", "md"] = "csv", cls: str = "", conf: str = "",
                            hours: float = 0):
    recs = _detect_filter(cls, conf, hours)
    body = {"csv": detect_export.to_csv, "json": detect_export.to_json,
            "md": detect_export.to_markdown}[fmt](recs)
    stamp = time.strftime("%Y%m%dT%H%MZ", time.gmtime())
    media = {"csv": "text/csv", "json": "application/json", "md": "text/markdown"}[fmt]
    return PlainTextResponse(body, media_type=f"{media}; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="detect-log-{stamp}.{fmt}"'})


@app.get("/api/mesh/messages", dependencies=[Depends(auth.require_session)])
async def api_mesh_messages():
    return mesh.messages()


class MeshSendRequest(BaseModel):
    # A coarse character cap only; the real limit is mesh.MAX_TEXT_BYTES in UTF-8 bytes, checked in
    # mesh.send_text so every over-length message gets the same error.
    text: str = Field(min_length=1, max_length=4 * mesh.MAX_TEXT_BYTES)
    channel: int = Field(0, ge=0, le=7)
    # wantAck: the radio reports a heard relay and re-sends up to twice if none is heard.
    want_ack: bool = True


@app.post("/api/mesh/send", dependencies=[Depends(auth.require_session)])
async def api_mesh_send(body: MeshSendRequest):
    """Broadcast a text message over LoRa — the app's second write path, after the rail toggle.
    Transmits for real; see software/webdash.md. The server checks readiness itself (rail, daemon,
    region, tx_enabled, ham mode) against current status, so a stale or crafted client can't
    transmit when the dashboard would show the control as blocked."""
    st = await current_status()
    m = mesh.with_tx(st.get("mesh"), st.get("aiov2"), st.get("services"))
    tx = m["tx"]
    if not tx["can_send"]:
        return JSONResponse({"ok": False, "code": tx["code"], "error": tx["reason"]},
                            status_code=409)
    if body.channel not in {c["index"] for c in m.get("channel_detail") or []}:
        return JSONResponse({"ok": False, "code": "bad_channel",
                             "error": "That channel isn't enabled on the radio."}, status_code=400)
    result = await mesh.send_text(body.text, body.channel, body.want_ack)
    return JSONResponse(result, status_code=200 if result.get("ok") else 502)


class MeshMqttRequest(BaseModel):
    enabled: bool


@app.post("/api/mesh/mqtt", dependencies=[Depends(auth.require_session)])
async def api_mesh_mqtt(body: MeshMqttRequest):
    """Turn the Meshtastic MQTT module on or off. A config write, not a transmission, but the
    firmware restarts meshtasticd to apply it and the node announces itself when it comes back;
    see software/webdash.md. Checked against current status like a send."""
    st = await current_status()
    m = mesh.with_tx(st.get("mesh"), st.get("aiov2"), st.get("services"))
    ready = m["mqtt"]["ready"]
    if not ready["can_send"]:
        return JSONResponse({"ok": False, "code": ready["code"], "error": ready["reason"]},
                            status_code=409)
    result = await mesh.set_mqtt(body.enabled)
    return JSONResponse(result, status_code=200 if result.get("ok") else 502)


@app.api_route("/apps/tar1090", methods=["GET"])
async def tar1090_root_redirect():
    return RedirectResponse("/apps/tar1090/")


@app.api_route("/apps/tar1090/{path:path}", methods=["GET"], dependencies=[Depends(auth.require_session)])
async def tar1090_proxy(path: str, request: Request):
    return await proxy.fetch(path or "index.html", request)


@app.websocket("/ws/status")
async def ws_status(websocket: WebSocket):
    session = websocket.cookies.get(auth.SESSION_COOKIE)
    if not auth.session_ok(session):
        # accept() first: closing before accept() rejects the opening handshake itself (the
        # client sees a plain HTTP 403, no WS close frame — app.js's onclose never sees code
        # 4401, so the "session expired, reload" path never fires). Accepting then immediately
        # closing with 4401 completes the handshake so the close code actually reaches the client.
        await websocket.accept()
        await websocket.close(code=4401)
        return
    await websocket.accept()
    try:
        while True:
            await websocket.send_json(await current_status())
            await asyncio.sleep(COLLECT_INTERVAL_S)
    except WebSocketDisconnect:
        pass
