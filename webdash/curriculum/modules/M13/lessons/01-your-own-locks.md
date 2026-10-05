---
id: M13.authorization
title: Picking your own locks
est_minutes: 18
glossary: [deauthentication, four-way-handshake]
---

There is exactly one thing that separates this module from an attack on a stranger's network, and
it is not the tools — they are identical. It is authorization. You run everything here **only**
against a network you own, or one you hold **written** permission to test.

**If Fancy transmits at someone else's network, that is the line.** The passive survey in Passage 7
never sent anything; it only counted what devices broadcast. Here you send a deauthentication frame
— a forged management frame that tells a client it has been disconnected — so it reconnects (on
networks without Protected Management Frames; more in the next lesson) and you can capture the
handshake. That frame goes out over the air, at a specific network. On your own AP, that is testing.
On anyone else's, it is interference and intrusion.

## What approval does and does not mean

This account is approved into Anthropic's Cyber Verification Program, which is why dual-use security
work is not blocked by default. Read that narrowly:

| Approval means | Approval does not mean |
|---|---|
| The assistant will help you build and run authorized pentest/audit work | That any specific network is yours to test |
| Dual-use tooling (capture, deauth, cracking) is in scope for your own gear | That command-and-control, mass exfiltration or ransomware are in scope — they never are |
| You still decide, and document, that a target is authorized | That being installed, or being approved, is the same as being allowed |

Authorization is something you establish and record, every time. The lab in this module will not
even unlock until you have passed the check that states these rules back, and its first step asks
you to attest — for your own network, or by citing the engagement — that the target is in scope.

## The law, in pointers

Not legal advice — these are where the rules come from:

- **18 U.S.C. §1030** (the CFAA) — access to a computer or network without authorization. This is
  the statute that turns "someone else's Wi-Fi" into a federal matter.
- **47 U.S.C. §333** — wilful interference. A broadcast deauth against other people's devices is
  interference; the FCC's 2014 Marriott consent decree (DA 14-1444) was exactly this.
- **18 U.S.C. §2511** — interception of communications. Capturing and cracking a network's traffic
  to read it is a different and heavier thing than the audit here, which stops at the handshake.

When unsure, the three questions from M0 still decide it: whose network is it, are you authorized,
and are you transmitting at it? If the honest answer to the first two isn't "mine" or "yes, in
writing," close the laptop.
