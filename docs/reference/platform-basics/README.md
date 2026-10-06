# Platform basics

Short explainers for the Linux and hardware layer under Fancy's radios — the concepts the rest
of the repo uses without explaining. Written for the learning platform's gap modules (P1–P8 in
[`../learning-platform-plan.md`](../learning-platform-plan.md) §1.6); external references are in
[`../../../knowledge/README.md`](../../../knowledge/README.md) §Platform references.

| Doc | Covers | Used by |
|---|---|---|
| [`systemd.md`](systemd.md) | Services, enabled vs active, restart loops, the journal | M1b |
| [`buses-and-rails.md`](buses-and-rails.md) | UART, SPI, I²C, USB; what a "rail" is; who owns which device | M1, M1b |
| [`drivers-and-udev.md`](drivers-and-udev.md) | Kernel drivers, device nodes, udev rules, the DVB blacklist | M1b |
| [`device-tree.md`](device-tree.md) | Device tree, overlays, `config.txt`, the serial console | M1b |
| [`docker.md`](docker.md) | Images, containers, bind mounts, host networking, uid 1000 | M1b |
| [`packet-capture.md`](packet-capture.md) | The passive capture tap: capture vs display filters, the ring buffer, protocol mix, TCP/ICMP anomaly counts | M14 |
| [`totp.md`](totp.md) | How the login codes work, and why the clock matters | M0 |

Power for learners (P8) is a section of [`../power-budget.md`](../power-budget.md#reading-the-power-numbers).
Tailscale (P6) is the one platform gap *not written yet*.
