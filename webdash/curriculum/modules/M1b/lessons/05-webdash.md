---
id: M1b.webdash
title: How the dashboard gets its numbers
est_minutes: 10
---

webdash never owns a radio. It asks the services that do, every 3 seconds, and shows what they
say:

@ref docs/reference/webdash-architecture.md#what-maps-to-what

That is why webdash holds meshtasticd's single client slot (lesson 3), and why a service that is
stopped shows up on the dashboard as "stopped" rather than an error.
