---
id: icmp-unreachable
term: ICMP unreachable
tooltip: A router or host replying that it could not deliver a packet — no route, no host, or no service on that port.
good_bad: "A scatter of port-unreachables is ordinary. A steady stream of network- or host-unreachables while you are trying to reach something means the path is broken upstream of the radio."
try_this: "Note the icmp_unreachable count while a connection fails — it separates a routing fault from a weak link."
learn_more: "#/learn/m/M14"
---

An ICMP unreachable (type 3) is the network saying "I can't deliver that." It separates a *link*
problem (retransmissions, weak signal) from a *routing* problem (unreachables): re-seating an
antenna will not fix a path that is broken upstream. The port-unreachable variant is the normal
answer to a UDP probe sent to a closed port, so a few are expected and mean little on their own.
