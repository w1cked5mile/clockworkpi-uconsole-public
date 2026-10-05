---
id: frequency-slot
term: Frequency slot
tooltip: Which of the band's channels a Meshtastic node uses — set by hashing the primary channel's name, unless a slot is set by hand.
good_bad: SCMesh is index 88 in the journal (slot 89 in the app), 924.125 MHz.
try_this: journalctl -u meshtasticd | grep "Set radio"
learn_more: '#/learn/m/M4'
---

Nodes on different slots can't hear each other at all, whatever their keys.
