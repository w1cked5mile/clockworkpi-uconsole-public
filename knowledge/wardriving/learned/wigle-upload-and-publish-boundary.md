---
title: WiGLE upload — what publishing means and when it's allowed
discipline: wardriving
date: 2026-10-04        # UTC
---

# WiGLE upload — what publishing means and when it's allowed

Durable reasoning behind this build's WiGLE workflow. The operational steps live in
[`../../../software/kismet.md`](../../../software/kismet.md) §WiGLE export; this file is the *why*,
so the two don't drift and the near-home rule and the auto-upload path aren't read as contradicting
each other.

## Uploading is publishing, and it is irreversible

A `.wiglecsv` row carries **BSSID (MAC), SSID, precise lat/lon, and timestamp**. Uploading it to
wigle.net publishes those permanently: the data is indexed, searchable by anyone, and mirrored by
third parties. "Delete later" is not a real control — treat every upload as public forever. This is
why `*.wiglecsv` is gitignored and never committed, and why the capture file itself is treated as
sensitive, not as a throwaway artifact.

## The decision boundary (resolves the "never upload" vs "auto-upload" tension)

Two docs in this repo look like they disagree:

- `runbooks/passive-survey-session.md` says **never** upload the survey log.
- `software/kismet.md` sets up **automatic** WiGLE upload.

Both are correct because the rule is not about the activity, it's about **whether a row can tie back
to the owner's home or household**:

| Capture | Upload? | Why |
|---|---|---|
| Near-home / passive household survey | **No** | Rows map the owner's own and neighbours' networks to where they live. Publishing them is self-doxxing and exposes third parties who never consented. |
| Drive capture away from home | **Yes**, after the home-radius filter | Rows are of networks seen in public from a moving vehicle, far from the owner; this is the WiGLE-style survey the discipline is built around. |

The technical enforcement of that line is the **home-radius filter** in `wigle-upload.py`: every row
within `WIGLE_HOME_RADIUS_M` of the stored home point is dropped before upload, and so is every
row without a GPS fix. The filter *is* the boundary made mechanical — not a convenience.

## Design principles that should survive any rewrite

- **Fail closed.** With no home position set, the uploader sends **nothing** (exit 0). A safety
  control that defaults to "allow" is not a control. Any future change must keep this: unknown home
  → no upload.
- **Over-broad by default, narrow deliberately.** Home here is stored as the **town centre with an
  8 km radius**, because the owner gave a town rather than an address. That holds back the whole
  town — survey done there is simply never uploaded. Shrinking the radius is a deliberate,
  per-use decision in `~/.config/wigle/env`, not the default.
- **Credentials and home live outside the repo** — `~/.config/wigle/env`, mode 600, dir 700. API
  name/token and the home coordinate are both sensitive (the home point reveals where the owner
  lives); neither is ever committed.
- **Idempotent, hands-off.** The hourly timer uploads each finished file once, skips files touched
  in the last 10 min (still being written), and records what it sent in
  `~/.local/state/wigle-upload/state.json`. Re-runs send nothing new.

## WiGLE API gotcha (file/upload)

The `POST /api/v2/file/upload` response shape is not stable/documented enough to rely on — the first
real upload logged `transid None` even though it was accepted. Recover the transaction id by
**searching the response body for `transid`/`transId`**, and if it's absent, read it back from
`GET /api/v2/file/transactions`. Don't assume a fixed JSON key. First verified upload:
229 rows, 0 dropped, transaction `20261004-01348`.

## See also

- Operational steps + setup: [`../../../software/kismet.md`](../../../software/kismet.md) §WiGLE export
- Near-home rule in context: [`../runbooks/passive-survey-session.md`](../runbooks/passive-survey-session.md)
- Legal/ethical frame: [`../../rf-fundamentals/learned/us-spectrum-and-legal.md`](../../rf-fundamentals/learned/us-spectrum-and-legal.md)
