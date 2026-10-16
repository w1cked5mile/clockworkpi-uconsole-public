"""Offensive-device detection ("Detect" tab, Wi-Fi view) — passive, receive-only.

Reads what Kismet has already heard (its device table and its own alerts), matches it against an
owner-supplied rules file, and keeps a durable log of contacts under WEBDASH_DATA_DIR. Nothing in
this package transmits, scans actively, connects to, or responds to a detected device. See
docs/reference/webdash-architecture.md, "Detect".

  rules.py   load + validate the owner's rules file; pure matching functions
  store.py   the contact log, seen marker, watch state and coverage intervals (JSON, atomic)
  export.py  CSV / JSON / Markdown renderers of the log
  observe.py Kismet device/alert → log observation, and folding a poll into the store
  engine.py  the background poll of Kismet (only while the watch is on)
"""
