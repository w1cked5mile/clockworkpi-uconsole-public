---
id: tcp-dup-ack
term: Duplicate ACK
tooltip: The receiver re-acknowledges the last in-order byte because it is still missing an earlier segment.
good_bad: "Read alongside retransmissions: lots of dup-acks mean out-of-order or lost segments, seen from the receiver's side. Three in a row trigger a fast retransmit."
try_this: "Compare the dup-ack count with the retransmit count — they usually climb together on a lossy link."
learn_more: "#/learn/m/M14"
---

A duplicate ACK is the receiver's way of saying "I got something later, but I am still waiting on an
earlier piece." It re-acknowledges the last byte it received in order. Three dup-acks in a row tell
the sender to resend immediately (fast retransmit) rather than wait for a timeout. A stream of them
is the same story as retransmissions — loss — told from the other end of the connection.
