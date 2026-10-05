---
id: crash-loop
term: Crash loop
tooltip: A service that fails to start, and systemd keeps retrying it.
good_bad: "If you start ADS-B while the SDR rail is off, readsb crash-loops until the rail is on (or you stop it). Anything crash-looping on its own is a fault."
try_this: "Check it yourself: systemctl status readsb"
learn_more: "#/learn/m/M1b"
---

systemd restarts a failed service after a short wait when its unit says `Restart=`. If the cause
doesn't go away — readsb can't find an SDR because its rail is off — it fails again. The
dashboard calls it crash-looping when systemd reports `activating` / `auto-restart`; the restart
counter shows how long it has been going on. readsb is `systemctl-disabled` on this build, so it
only runs when you pick ADS-B in the SDR view — it no longer crash-loops by itself with the rail
off; you'd only see this if you start ADS-B before turning the rail on.
