---
id: M1b
title: Who owns what — buses, daemons, dashboard
themed_title: Passage 1b · Who holds the lines
discipline: platform
station: system
prerequisites:
  - {id: M1, soft: false}
sources:
  - docs/reference/platform-basics/buses-and-rails.md
  - docs/reference/platform-basics/systemd.md
  - docs/reference/webdash-architecture.md
  - docs/reference/platform-basics/device-tree.md
  - docs/reference/platform-basics/drivers-and-udev.md
  - configs/sdr/sdr-swap.sh
  - configs/README.md
  - docs/logs/known-issues.md
objectives:
  - "**Verify** which bus and device node each chip uses."
  - "**Interpret** a service's systemd state, including a normal crash loop."
  - "**Diagnose** `usb_claim_interface error -6` and fix it."
  - "**Explain** why gpsd and a direct read can't share `/dev/serial0`, and why the meshtastic CLI drops webdash's mesh connection."
  - "**Verify** that the configs staged in the repo are the ones installed on the device."
est_minutes: 115
today:
  state: ready
  reason: Everything here uses hardware already fitted.
---

Most of the confusing failures on this build are two programs wanting the same device. This
module is the map of who owns what.
