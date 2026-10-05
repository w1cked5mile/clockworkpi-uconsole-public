---
id: oui
term: OUI
tooltip: The first three bytes of a real hardware address, registered to the manufacturer.
good_bad: "An OUI names who registered the prefix — not what the device is. A random address has no OUI."
try_this: "Check the locally administered bit before reading anything into an address's first bytes."
learn_more: "#/learn/m/M7"
---

The IEEE sells address blocks to manufacturers; the Organizationally Unique Identifier is the
prefix. A match tells you whose block it came from, and makers sell chips to many products, so
it can't prove what the device is. Matches on randomised addresses are pure coincidence.
