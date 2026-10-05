---
id: M13
title: Authorized active Wi-Fi audit
themed_title: Passage 13 · Sounding your own hull
discipline: wardriving
station: wifi
prerequisites:
  - {id: M0, soft: false}
  - {id: M7, soft: false}
sources:
  - software/aircrack-ng.md
  - docs/runbooks/wifi-wpa2-handshake-audit.md
  - knowledge/rf-fundamentals/learned/us-spectrum-and-legal.md
  - knowledge/wardriving/learned/wifi-capture-fundamentals.md
  - knowledge/wardriving/learned/80211-identifiers-and-regdom.md
objectives:
  - "**Distinguish** authorized active testing from wardriving, and **state** the one rule that gates everything here: your own network, or a documented written authorization — nothing else."
  - "**Explain** the WPA2 four-way handshake, why a deauthentication frame forces a client to redo it, and **name** what a deauth transmits."
  - "**Capture** a handshake from your own access point, **verify** it is complete, and **recover or fail to recover** the passphrase from a wordlist."
  - "**Offload** the real crack to a GPU host on the tailnet, and **explain** why Fancy itself is capture-only."
  - "**State** what the Cyber Verification Program approval does and does not permit, and what stays prohibited regardless of it."
est_minutes: 90
today:
  state: ready
  reason: "Runs against your own AP on the AC1200 (MT7921, wlan1), which arrived 2026-09-30 and covers 2.4/5/6 GHz — so a 5 GHz AP you own works too. Fancy captures; the actual cracking offloads to a GPU host on the tailnet (the `gpu-host-wsl` Kali/WSL node). On-device aircrack-ng is a quick check against a short wordlist only. LAB-22 passed a supervised hardware dry-run on the owner's own AP on 2026-09-26 (full path: monitor → capture → targeted deauth → handshake → verify) and the GPU crack-offload was validated the same day (RTX 3070 Ti, full rockyou ~46 s, not cracked). Note: that dry-run used the now-retired RT5370; the MT7921's monitor mode is verified, but the full transmit path has not yet been re-run on it."
---

Passage 7 listened and never spoke. This one transmits — a deauthentication frame to nudge a
client, then a capture of the handshake it makes when it reconnects — and that is exactly why it is
walled off from the passive survey and gated behind a rule you agree to before the lab will run.

**One rule, no exceptions: your own network, or a network you hold written authorization to test.**
Deauthenticating a client and capturing its handshake are active acts against a specific network.
Against anything you do not own or are not authorized to test, they are unlawful in most places and
outside everything this platform stands for. If you are not certain a target is in scope, it is not.

**Being able to is not being allowed to.** `aircrack-ng` is installed on Fancy, and this module
teaches the whole capture-and-crack loop. Neither fact is permission. The Cyber Verification Program
approval on this account lifts the default block on dual-use security work — it does not authorize
you against any particular network, and it leaves command-and-control infrastructure, mass data
exfiltration and ransomware development blocked and out of scope here as everywhere.

The repo's legal summary for Wi-Fi, restated in the passive module and just as binding here:

@ref knowledge/rf-fundamentals/learned/us-spectrum-and-legal.md#wi-fi-and-bluetooth

The point of the exercise is defensive: prove your own passphrase is weak (or confirm it holds) by
trying to break it, the same way an attacker would, on gear you are allowed to attack.
