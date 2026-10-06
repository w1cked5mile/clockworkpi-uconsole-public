# Packet capture — the troubleshooting tap

How webdash's passive capture tap works, and how to read what it reports, written for the
hang/dropout investigation. The dashboard drives a bounded, **receive-only** `dumpcap` through a
host bridge and reads the newest segment back with `tshark`; the panel shows an **address-free**
summary while the on-disk `.pcapng` keeps the detail for a Wireshark deep-dive. Written 2026-10-06
(gap: packet-capture fundamentals). Architecture lives in
[`../webdash-architecture.md`](../webdash-architecture.md); the wrapper is
[`../../../webdash/host-helpers/tshark-capture.sh`](../../../webdash/host-helpers/tshark-capture.sh)
and the collector is [`../../../webdash/app/collectors/tshark.py`](../../../webdash/app/collectors/tshark.py).

This is a diagnostic tap, not an auditing tool. It only listens — there is no transmit path, no
injection, no deauth, no association, no probing. It captures on Fancy's **own** interfaces to find
out why a link stutters, and it sits inside the repo's passive-only legal posture
([`../../../knowledge/README.md`](../../../knowledge/README.md) §Responsible use).

## What a capture is

A capture is a recording of the frames that cross one network interface, in the order they
arrived, each stamped with the time it was seen and its length. Nothing is sent to make it happen:
the interface already receives these frames to do its job, and the capture simply copies them as
they go past. On Fancy the recorder is `dumpcap` (the small capture engine that ships with
Wireshark), and the interface is one of Fancy's own — `wlan0` (the onboard Wi-Fi link), `eth0`,
`tailscale0`, `docker0`, or `any` to watch them all at once.

Two tools read what `dumpcap` wrote. `tshark` is the command-line reader webdash uses to count
things up; Wireshark is the graphical reader you open on a workstation when a count tells you
*where* to look and you need to see the individual packets. The dashboard never shows you a
packet — it shows you aggregates, and points you at the file.

## Capture filters and display filters

There are two different filters, applied at two different times, and mixing them up is the most
common beginner mistake.

A **capture filter** is decided *before* recording and limits what is written to disk at all. It
uses BPF syntax (`host 192.0.2.1`, `port 53`, `tcp`, `not arp`) and it is cheap, because the kernel
drops the rest before it ever reaches the recorder. What a capture filter discards is gone — it was
never saved.

A **display filter** is applied *after* recording, when you read the file back. It uses Wireshark's
own much richer syntax (`tcp.analysis.retransmission`, `ip.addr == …`, `dns.flags.rcode != 0`) and
it only hides packets from view — everything is still in the file, so you can widen the filter and
see more without re-capturing.

| | Capture filter | Display filter |
|---|---|---|
| When | before recording | after recording |
| Syntax | BPF (`port 53`) | Wireshark (`dns.flags.rcode != 0`) |
| Effect | decides what is saved | decides what is shown |
| Reversible | no — unsaved is gone | yes — just widen it |
| Where on Fancy | the dashboard's "filter" box → `dumpcap -f` | in Wireshark on the `.pcapng` |

Rule of thumb: capture broadly and filter narrowly on display, unless the link is so busy that an
unfiltered capture would churn the ring too fast to hold the moment you care about. For the
dropout hunt a narrow capture filter — the gateway's address, or just `tcp` — keeps the ring
pointed at the traffic that stalls.

## The ring buffer

A capture left running would eventually fill the disk. A **ring buffer** stops that: it writes a
fixed number of fixed-size files and, once they are all full, overwrites the oldest. Disk use is
therefore bounded by `file size × file count`, no matter how long the capture runs.

Fancy's tap defaults to **10 files of about 10 MB each**, so roughly **100 MB** at most, in
`~/labs/tshark` — it can never fill the SD card. The trade is history: the ring only holds the most
recent ~100 MB, so on a busy link that may be only the last minute or two. Make the files bigger,
or the filter narrower, when you need to keep more of the window around a rare event. The tap reads
only the **newest** segment to build its summary, which keeps the cost on the Pi low even on a long
capture.

An intermittent fault and a ring buffer are a good match: you leave it running, and when the stall
happens you stop it, and the moment is still in the newest segment, in full, for Wireshark.

## Reading the protocol mix

The first thing a capture tells you is *what kind of traffic* is on the link — the protocol mix (in
Wireshark, the "protocol hierarchy"). The tap reports the top protocols by packet count. You read
it for shape, not for exact numbers:

- A healthy idle link is mostly background: ARP, DNS, mDNS/SSDP, a little TCP keepalive, some TLS.
- A link doing real work shows bulk TCP (or QUIC/UDP) dominating, which is normal under load.
- A mix that is *all* retransmission and ARP with little payload is a link that is trying and
  failing — the signature of the weak-signal stall, not of real traffic.

The mix also sanity-checks the capture itself: if you filtered to `port 53` and see anything but
DNS, your filter is not doing what you thought.

## TCP retransmits, dup-acks and resets

TCP is designed to hide packet loss from the application, so a link can be dropping badly while a
download still (slowly) completes. The capture is where that hidden loss becomes visible. The tap
counts four signals:

- **Retransmission** — the sender sent the same data again because it was not acknowledged in time.
  A few are normal on any link; a rising count during a stall means packets are being lost in
  flight and TCP is resending them. This is the headline symptom of a marginal Wi-Fi link.
- **Duplicate ACK** — the receiver got a later segment but is still missing an earlier one, and
  says so by re-acknowledging the last in-order byte. Three dup-acks in a row trigger a fast
  retransmit. Lots of dup-acks mean out-of-order or lost segments — again, loss, seen from the
  receiver's side.
- **Reset (RST)** — one end abruptly tore the connection down instead of closing it cleanly. A
  burst of resets points at something actively refusing or killing connections (a service that
  died, a firewall, a port with nothing listening) rather than at radio loss.

Read them together. Retransmits and dup-acks that climb while the link is associated but slow are
the fingerprint of **loss on a weak link** — exactly what was measured on Fancy's `wlan0` on a
−71 dBm 2.4 GHz link (20–30% ping loss, tx rate collapsed to 5.5 Mbit/s), before Wi-Fi power-save
was disabled (see `docs/logs/known-issues.md`). Resets without a climb in retransmits point the
other way, at an endpoint, not the air. **Zero of all three is the healthy baseline** — a clean
capture is supposed to be boring.

## ICMP unreachable

An **ICMP unreachable** (type 3) is a router or host saying "I can't deliver that" — no route to
the network, no host at that address, or no service on that port (the port-unreachable that answers
a UDP probe to a closed port). A scatter of port-unreachables is ordinary. A steady stream of
network- or host-unreachables while you are trying to reach something means the path is broken
upstream of the radio, and no amount of re-seating an antenna will fix it. It separates a *link*
problem (retransmits, weak signal) from a *routing* problem (unreachables).

## Address-free by design

Everything the dashboard shows is address-free: packet and byte counts, rates, protocol names, and
the four anomaly counts — never a MAC or IP. That is the same rule the other collectors follow
(see [`../../../webdash/app/collectors/net.py`](../../../webdash/app/collectors/net.py)), so the
status payload a browser receives can never carry who was talking to whom. The addresses do exist —
in the `.pcapng` on disk, which is the whole point of keeping it — so treat that file the way you
treat any capture: it stays on Fancy, it never goes in the repo, and you delete it when you are done
([`../../../CLAUDE.md`](../../../CLAUDE.md) §Conventions — no secrets, no precise locations).
