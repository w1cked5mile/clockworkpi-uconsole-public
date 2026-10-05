# Docker and Compose, as webdash uses them

Written 2026-09-25 (gap P5). References: Docker's overview and Compose docs (linked in
[`../../../knowledge/README.md`](../../../knowledge/README.md) §Platform references).

## Four words

| Word | Meaning | webdash's |
|---|---|---|
| Image | a packaged filesystem plus the command to run — built once | `uconsole-webdash:latest`, built from [`../../../webdash/Dockerfile`](../../../webdash/Dockerfile) |
| Container | a running instance of an image, isolated from the host | `uconsole-webdash` |
| Bind mount | a host folder made visible inside the container | `/hostfs` (host `/`, read-only), `/sys/class/thermal` (read-only), `/auth`, `/learn` (read-only), `/data` |
| Compose file | the recipe that says how to run it | [`../../../webdash/docker-compose.yml`](../../../webdash/docker-compose.yml) |

The app's code is baked into the image, so editing files on disk changes nothing until you
rebuild: `sg docker -c 'docker compose up -d --build'` in `webdash/`.

## Host networking and the bridge

webdash runs with `network_mode: host`, so `127.0.0.1` inside the container is the host's. That's
how it reaches gpsd, meshtasticd, Kismet, tar1090 and the aiov2 bridge without port mapping. It
never gets hardware (`/dev`) itself: anything that needs GPIO goes through the small host-side
bridge ([`../webdash-architecture.md`](../webdash-architecture.md)).

## The uid-1000 detail

The container runs as uid 1000 — the same number as the owner on the host — so files it writes
into `/data` and `/auth` belong to the owner and can be read or removed without sudo. Being in the
`docker` group is root-equivalent on the host, which is one reason webdash never gets the Docker
socket.

## Read-only checks

```bash
sg docker -c 'docker ps'
sg docker -c 'docker compose -f ~/clockworkpi-uconsole/webdash/docker-compose.yml logs --tail 20'
```
