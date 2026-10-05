---
id: deauthentication
term: Deauthentication
tooltip: A forged Wi-Fi management frame that disconnects a client so it reconnects — used, on your own network, to force a capturable handshake.
learn_more: "#/learn/m/M13"
---

On a WPA2 network without 802.11w (Protected Management Frames), management frames are unauthenticated,
so a client accepts a forged "you are disconnected" frame and reconnects — running a fresh
[four-way handshake](#/learn/m/M13) you can capture. With 802.11w/PMF enabled (default on many modern
APs, mandatory under WPA3) the forged frame is rejected and this does nothing. Sent as a few targeted
frames at a client you own, it is a legitimate way to audit your own network. Sent as a broadcast, or
at anyone else's devices, it is interference (47 U.S.C. §333) — the thing the FCC's 2014 Marriott case
was about. Targeted, on your own gear, only.
