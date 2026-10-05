---
id: four-way-handshake
term: Four-way handshake
tooltip: The four EAPOL frames a WPA2 client and access point exchange at join time to prove both know the passphrase — without sending it.
learn_more: "#/learn/m/M13"
---

WPA2-PSK never sends the passphrase. Instead, at connection time the access point and client trade
four EAPOL frames carrying random nonces and a message-integrity code that only the passphrase can
reproduce. Capturing the key frames (the AP's nonce, and the client's nonce-plus-MIC) lets an
attacker *test guesses* offline — hash a candidate the WPA2 way and check it against the captured
MIC — but only guesses from a wordlist, and only for WPA2, not WPA3/SAE.
Forcing a client to reconnect (a [deauthentication](#/learn/m/M13)) is how you make a fresh
handshake happen on demand. Audit your own network with it; nothing else.
