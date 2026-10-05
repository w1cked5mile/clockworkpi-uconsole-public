---
id: hops
term: Hops
tooltip: How many relays a packet went through; 0 means heard directly.
good_bad: The default hop limit is 3; each relay spends one.
try_this: Look at hops away for each node in the Meshtastic app.
learn_more: '#/learn/m/M4'
---

Each rebroadcast decrements the packet's hop limit; at 0 it is not relayed further.
