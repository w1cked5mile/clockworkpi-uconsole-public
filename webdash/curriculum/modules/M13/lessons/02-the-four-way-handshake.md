---
id: M13.handshake
title: The four-way handshake
est_minutes: 20
glossary: [four-way-handshake, deauthentication, pmkid]
---

WPA2-PSK proves both sides know the passphrase without ever sending it. When a client joins, the
access point and the client run a **four-way handshake**: four EAPOL frames that carry random
numbers (nonces) and message-integrity codes that only the passphrase can reproduce (not every frame
carries a MIC). Anyone listening on the channel can record them. They do not contain the passphrase —
but the key frames (the AP's nonce, and the client's nonce-plus-MIC) contain enough to *test a guess*
offline: hash a candidate the way WPA2 does, and see if it reproduces the MIC in the captured
handshake. A partial capture is useless, so you always confirm a complete handshake was caught before
relying on it.

That is the whole game, and it explains every step of the lab:

| You need | Because |
|---|---|
| To be tuned to the AP's channel, in monitor mode | The handshake is four ordinary frames on one channel; miss the channel, miss them |
| A client that connects (or reconnects) while you listen | The handshake only happens at join time |
| A way to *make* a client reconnect | Otherwise you wait for one to join on its own |
| A wordlist | The attack tests candidates you supply; it does not invent them |

On Fancy this runs on the AC1200 as `wlan1mon` (MT7921, 2.4/5/6 GHz — a 5 GHz AP you own works
too); `wlan0` stays your managed network link and is never touched, exactly as in Passage 7. The
first passive surveys there saw Wi-Fi management and control frames but **no EAPOL frames** — the
four-way handshake is precisely the EAPOL exchange this module goes after.

## Why deauth, and what it costs

A **deauthentication** frame is a management frame that says "you are disconnected." On a WPA2
network *without* 802.11w (Protected Management Frames), these frames are unauthenticated, so a
forged one is accepted and the client dutifully reconnects — running a fresh four-way handshake you
can capture. **If the AP has 802.11w/PMF enabled** — increasingly the default, and mandatory under
WPA3 — forged deauths are rejected and this trick does nothing; then you wait for a client to join
on its own, or use the clientless PMKID path below. That is why the lab sends a *few* deauths at a
*specific* client you own, not a flood and not a broadcast: a broadcast deauth knocks every client
off the network, which is disruptive and is exactly the interference the law in the last lesson is
about — it drops a real person's connection without their consent. On your own AP, nudging your own
phone is fine. Nowhere else.

## PMKID — sometimes you don't need a client at all

Some access points hand out a **PMKID** in the first handshake message, derived from the same
passphrase. If yours does, a tool like `hcxdumptool` (not installed on Fancy by default) can capture
it without deauthing anyone and without waiting for a client — a "clientless" capture. It cracks the
same way: it only tells you the passphrase if the passphrase is in your wordlist. Not every AP
exposes a PMKID; the handshake path always works, so LAB-22 uses it as the baseline and does not
exercise the PMKID path.

## What the capture proves — and what it doesn't

A crack that succeeds proves the passphrase was weak enough to be in a wordlist: rotate it, lengthen
it, make it random. A crack that fails proves only that it was not in *your* list — not that it is
unbreakable. And a captured handshake that WPA3/SAE negotiated is not crackable this way at all;
getting a workable WPA2 handshake tells you the network is still on the old scheme (WPA3 *transition*
mode still runs a crackable WPA2 handshake for clients that join the old way). The exercise is an
audit of your own passphrase strength, run the way an attacker would, on gear you may attack.

**Fancy captures; a bigger machine cracks.** The handshake file is tiny, but the crack is a
deliberately slow PBKDF2 grind and the CM4 has only its CPU — on the order of a few hundred to
low-thousands of candidates a second (measure it with `aircrack-ng -S`). So Fancy is capture-only:
you copy the capture to a GPU host on the tailnet — `gpu-host` or `homeserver` — and run the
wordlist there. And because a capture holds a real network's frames, and on success its real
passphrase, **it never goes in the repo**: it lives in `~/labs/wpa/`, moves to storage you control,
and the finding you file records only the result in words.

The hands-on version, with exact commands and the crack-offload steps, is the runbook
`docs/runbooks/wifi-wpa2-handshake-audit.md`; LAB-22 walks it on Fancy against your own AP.
