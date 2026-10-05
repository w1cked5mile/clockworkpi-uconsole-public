# uConsole webdash — aarch64. Runs with network_mode: host (see docker-compose.yml) to reach
# gpsd/Kismet/meshtasticd/tar1090 and the aiov2_ctl host bridge on localhost — no device
# passthrough needed for this app; see docs/reference/webdash-architecture.md.
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY app ./app

# Runs as uid/gid 1000 (matches the host build user) so files it writes into the bind-mounted
# /auth volume are host-readable/removable, not root-owned — this app touches no device or
# system path that needs root.
RUN groupadd -g 1000 webdash && useradd -u 1000 -g 1000 -M webdash
USER webdash

# Bound to loopback only, not 0.0.0.0 — with network_mode: host that means reachable from this
# device alone, not the LAN. This app shows live GPS position and RF-survey state behind a login
# that's still v1-grade (no rate limiting, no lockout) — deliberately conservative until wider
# access (e.g. Tailscale) is a decision someone makes, not a default. See
# docs/reference/webdash-architecture.md.
EXPOSE 8090
CMD ["uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8090"]
