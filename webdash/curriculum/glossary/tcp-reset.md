---
id: tcp-reset
term: TCP reset (RST)
tooltip: One end abruptly tore a connection down instead of closing it cleanly.
good_bad: "A burst of resets without a climb in retransmits points at an endpoint — a dead service, a firewall, a closed port — not at radio loss. That distinction is the whole point of reading them together."
try_this: "If you see resets, check whether retransmits are also climbing: both means loss; resets alone means something is refusing connections."
learn_more: "#/learn/m/M14"
---

A reset (the RST flag) ends a connection immediately, unlike the orderly FIN handshake. Something
actively refused or killed the connection: a service that died, a firewall dropping it, or a port
with nothing listening (a connection attempt to a closed port is answered with a reset). On a flaky
link, resets tell you to look at the endpoints and the path, not the air.
