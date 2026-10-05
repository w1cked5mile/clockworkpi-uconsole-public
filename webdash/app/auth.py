"""Password + TOTP session auth.

Secret store (password hash, TOTP secret) lives in the bind-mounted /auth volume — outside the
repo, outside git (see docs/reference/webdash-architecture.md's Auth section and this repo's own
no-secrets convention, CLAUDE.md). First boot with no store present runs an unauthenticated
one-time /setup flow; once a store exists, /setup is closed.
"""
import base64
import hashlib
import io
import json
import os
import secrets
import time
from pathlib import Path

import pyotp
import segno
from fastapi import Cookie, HTTPException
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

AUTH_DIR = Path(os.environ.get("WEBDASH_AUTH_DIR", "/auth"))
STORE_PATH = AUTH_DIR / "auth.json"
SESSION_COOKIE = "uconsole_webdash_session"
SESSION_MAX_AGE_S = 12 * 3600

_SECRET_KEY_PATH = AUTH_DIR / "session_secret"


def _session_secret() -> str:
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    if not _SECRET_KEY_PATH.exists():
        _SECRET_KEY_PATH.write_text(secrets.token_hex(32))
        _SECRET_KEY_PATH.chmod(0o600)
    return _SECRET_KEY_PATH.read_text().strip()


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(_session_secret(), salt="uconsole-webdash-session")


def is_configured() -> bool:
    return STORE_PATH.exists()


def _hash_password(password: str, salt: bytes | None = None) -> str:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 200_000)
    return f"{salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored: str) -> bool:
    salt_hex, _ = stored.split("$", 1)
    return secrets.compare_digest(_hash_password(password, bytes.fromhex(salt_hex)), stored)


def create_account(username: str, password: str) -> str:
    """Writes the store and returns the TOTP provisioning URI (for the setup QR)."""
    if is_configured():
        raise RuntimeError("auth store already exists")
    totp_secret = pyotp.random_base32()
    AUTH_DIR.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(
        json.dumps(
            {
                "username": username,
                "password_hash": _hash_password(password),
                "totp_secret": totp_secret,
                "created_at": time.time(),
            }
        )
    )
    STORE_PATH.chmod(0o600)
    return pyotp.TOTP(totp_secret).provisioning_uri(name=username, issuer_name="Fancy Dashboard")


def setup_qr_svg(uri: str) -> str:
    """Returns base64-encoded SVG bytes (no data-URI prefix — the template adds that).

    Not segno's own `svg_data_uri()`: its default output is percent-encoded
    (`data:image/svg+xml;charset=utf-8,...`), not base64, despite the method's name suggesting
    otherwise — confirmed 2026-09-21 after the QR code rendered as a broken image (setup_done.html
    prepends its own `;base64,` prefix, so the percent-encoded string got wrapped in a second,
    invalid data URI). Encoding the raw SVG bytes ourselves avoids relying on that assumption.
    """
    buf = io.BytesIO()
    segno.make(uri).save(buf, kind="svg", scale=4)
    return base64.b64encode(buf.getvalue()).decode()


def verify_login(username: str, password: str, totp_code: str) -> bool:
    if not is_configured():
        return False
    store = json.loads(STORE_PATH.read_text())
    if not secrets.compare_digest(username, store["username"]):
        return False
    if not _verify_password(password, store["password_hash"]):
        return False
    return pyotp.TOTP(store["totp_secret"]).verify(totp_code, valid_window=1)


def make_session_cookie() -> str:
    return _serializer().dumps({"at": time.time()})


def _session_valid(token: str | None) -> bool:
    if not token:
        return False
    try:
        _serializer().loads(token, max_age=SESSION_MAX_AGE_S)
    except (BadSignature, SignatureExpired):
        return False
    return True


def session_ok(session: str | None) -> bool:
    return is_configured() and _session_valid(session)


async def require_session(session: str | None = Cookie(default=None, alias=SESSION_COOKIE)):
    """FastAPI dependency for API routes — 401 JSON, not a redirect. Page routes in main.py check
    session_ok() directly so they can redirect to /login or /setup instead."""
    if not session_ok(session):
        raise HTTPException(status_code=401, detail="not authenticated")
