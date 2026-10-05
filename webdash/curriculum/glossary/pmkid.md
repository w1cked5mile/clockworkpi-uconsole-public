---
id: pmkid
term: PMKID
tooltip: A key identifier some access points include in the first handshake message, letting a capture proceed without deauthing any client.
learn_more: "#/learn/m/M13"
---

The PMKID is derived from the same passphrase as the [four-way handshake](#/learn/m/M13) and is sent
by some access points in the first EAPOL message. When present, a tool like `hcxdumptool` (not
installed on Fancy by default) can grab it without a connected client and without a
[deauthentication](#/learn/m/M13) — a "clientless"
capture. It cracks the same way and with the same limit: it yields the passphrase only if the
passphrase is in your wordlist. Not every AP exposes one, so the handshake path stays the baseline.
