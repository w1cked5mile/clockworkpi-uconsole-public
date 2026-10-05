# Headless access runbook

Reach the uConsole from another machine — for flashing, log collection, and running the Qt GUIs
when the 5" screen is inconvenient.

## 1. SSH on the LAN

> **Not used on this build (decision 2026-09-24):** remote shell access is **tailnet-only** through
> Tailscale SSH (§2, `--ssh`). No `sshd` runs, so nothing listens on :22 on the LAN. Keep this
> section for reference if LAN SSH is ever wanted. See [`../logs/decisions.md`](../logs/decisions.md).

```bash
sudo systemctl enable --now ssh
hostnamectl set-hostname uconsole      # optional, makes mDNS predictable
ip -br a                               # note the address
```

From the client:

```bash
ssh pi@uconsole.local        # mDNS; fall back to the IP if it fails
```

Harden once it works:

```bash
ssh-copy-id pi@uconsole.local
sudo sed -i 's/^#\?PasswordAuthentication .*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh
```

## 2. Tailscale (off-LAN)

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
tailscale status
```

Useful flags once it works: `--ssh` for tailnet SSH, `--advertise-exit-node` only if you actually
want to route traffic through the device.

## 3. GUI apps over the network

The AIO companion apps (SDR++, PyGPSClient, meshtastic-mui) are Qt/GTK desktop apps.

| Approach | Command | Notes |
|---|---|---|
| X11 forwarding | `ssh -X pi@uconsole.local sdrpp` | Simplest; laggy waterfalls over Wi-Fi |
| VNC | `sudo apt install -y realvnc-vnc-server` or `wayvnc` | Full desktop; check which display stack the image uses |
| Web UIs | tar1090 in a browser | No forwarding needed |

Check the session type before choosing: `echo $XDG_SESSION_TYPE` (`x11` vs `wayland`) — X11
forwarding only helps on X11.

## 4. Serial console — deliberately unavailable

The primary UART is given to the **GNSS receiver** on this build (`console=serial0` removed from
`cmdline.txt`). Do not re-enable the serial console for debugging without accepting that GPS stops
working while it is enabled.

Recovery path when the network is down is therefore: the built-in screen and keyboard, or pulling
the storage and mounting it elsewhere.

## 5. File transfer

```bash
scp file pi@uconsole.local:~/          # ad hoc
rsync -avz --progress dir/ pi@uconsole.local:~/dir/   # bulk, resumable
```

## Verification

- [x] ~~`ssh` works from the LAN with keys, password auth disabled~~ — not applicable: tailnet-only by design (2026-09-24)
- [x] Tailscale SSH works from another host — `gpu-host`, 2026-09-24
- [ ] `tailscale status` shows the node online from off-LAN
- [ ] One GUI app renders remotely
- [ ] Access details (hostname, user, method) recorded in [`../logs/build-log.md`](../logs/build-log.md) — **never the keys or passwords**
