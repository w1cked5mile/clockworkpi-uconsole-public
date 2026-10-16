"""Claude-assisted Wi-Fi survey.

A passive site-survey workflow layered on the Kismet collector: start a survey, drop a waypoint
at each location you walk to (each waypoint captures a snapshot of what Kismet has heard, tagged
with the GPS grid square and an operator label), then stop and generate reports — a comprehensive
technical write-up and a leadership executive summary.

Receive-only by design. Every device record comes from Kismet, which only listens; nothing in
this package transmits, associates, deauthenticates, or decodes protected traffic. It stays
inside the repo's legal posture (see knowledge/README.md). The one active capability in the
Wi-Fi view, authorized WPA auditing, lives in app/wpa/ and is deliberately separate from this.

Survey data (SSIDs, BSSIDs, signal readings) is stored in the read-write data dir, outside the
repo and git — the same boundary the WPA allowlist and captures sit behind.
"""
