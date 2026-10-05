---
id: mac-randomization
term: MAC randomisation
tooltip: Phones use made-up, changing addresses when scanning or advertising, so they can't be followed.
good_bad: "Expect most client and Bluetooth addresses to be random. That's a privacy feature working, and it means counts overstate devices."
try_this: "In Kismet, note what share of client addresses are locally administered — for a unicast address, second hex digit 2, 6, A or E. Count them; don't list them."
learn_more: "#/learn/m/M7"
---

A random Wi-Fi address sets the locally administered bit (0x02 in the first byte). Bluetooth LE
has its own scheme: resolvable private addresses rotate about every 15 minutes, and only paired
devices can tell who they belong to. Never treat a random address as an identity, and never look
up its maker.
