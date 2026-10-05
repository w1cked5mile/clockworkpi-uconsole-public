# GPU crack-offload host (Kali WSL as a tailnet node)

Fancy (a CM4) captures WPA handshakes but is CPU-only and slow; the actual cracking offloads to a
GPU host on the tailnet. This documents the standing host — **`gpu-host-wsl`** — and how it
was set up, so the [`§5b` step of the WPA audit runbook](../runbooks/wifi-wpa2-handshake-audit.md)
and [`software/crack-offload.sh`](../../software/crack-offload.sh) have somewhere to land.

**Authorized-audit use only** — you crack your own captures (own network or a documented
engagement). Being able to offload is not permission; see [`../../CLAUDE.md`](../../CLAUDE.md).

## The host

`gpu-host` is a Windows 11 laptop (i9-12900H, **NVIDIA RTX 3070 Ti Laptop GPU**) already on the
tailnet. The crack runs in its **Kali WSL2** instance, which joins the tailnet as its **own node**,
`gpu-host-wsl`, separate from the Windows host. Fancy SSHes straight into Kali; Windows isn't
in the path.

## One-time setup (in the Kali WSL)

1. **Tools.** `sudo apt install -y hcxtools hashcat` (hashcat ships with Kali; `hcxtools` provides
   `hcxpcapngtool`, the `.cap` → `.hc22000` converter).

2. **systemd + Tailscale as its own node.** WSL had no systemd, so `tailscaled` wouldn't stay up and
   Tailscale SSH wouldn't run. Enable systemd — `/etc/wsl.conf`:
   ```
   [boot]
   systemd=true

   [user]
   default=wicked5mile
   ```
   then `wsl --shutdown` from Windows and reopen. Now:
   ```
   sudo systemctl enable --now tailscaled
   sudo tailscale up --ssh --hostname=gpu-host-wsl
   ```
   **Kernel mode matters:** `tailscaled` must run in kernel-TUN mode (the packaged service does).
   The earlier `--tun=userspace-networking` attempt let the control plane and even the TCP handshake
   through, but **Tailscale SSH does not serve in userspace mode** — SSH negotiation just hangs. WSL2
   ships `/dev/net/tun`, so kernel mode works.

3. **A non-interactive SSH ACL.** The default tailnet SSH rule was `action: "check"`, which demands a
   browser re-auth per session and so blocks automation. For your own devices, change it to
   `accept` (admin console → Access Controls → `ssh`):
   ```json
   "ssh": [
     { "action": "accept", "src": ["autogroup:member"], "dst": ["autogroup:self"], "users": ["autogroup:nonroot", "root"] }
   ]
   ```
   (To keep `check` elsewhere, tag just this node and add an `accept` rule for the tag, above the
   `check` rule.)

4. **CUDA for hashcat (GPU).** The NVIDIA GPU is passed through from Windows (`nvidia-smi` works, and
   `libcuda.so` is mounted at `/usr/lib/wsl/lib`), but hashcat's CUDA backend also needs **NVRTC**,
   which the Windows driver does not provide. Install the **driverless** CUDA toolkit inside WSL —
   **never a Linux NVIDIA driver in WSL**, it breaks the passthrough:
   ```
   cd /tmp
   wget https://developer.download.nvidia.com/compute/cuda/repos/wsl-ubuntu/x86_64/cuda-keyring_1.1-1_all.deb
   sudo dpkg -i cuda-keyring_1.1-1_all.deb
   ```
   Kali's Sequoia-based apt (`sqv`) rejects NVIDIA's repo because its signing key uses a **SHA-1**
   self-signature (disallowed since 2026-02-01), so the repo shows as unsigned. Mark that one repo
   trusted (still HTTPS to NVIDIA's host):
   ```
   REPO=$(grep -rl 'compute/cuda/repos/wsl-ubuntu' /etc/apt/sources.list.d/)
   sudo sed -i 's/\[signed-by=[^]]*\]/[trusted=yes]/' "$REPO"
   sudo apt update
   sudo apt install -y cuda-nvrtc-12-6        # NVRTC is all hashcat needs; cuda-toolkit-12-6 for the full kit
   echo 'export LD_LIBRARY_PATH=/usr/local/cuda/lib64:/usr/lib/wsl/lib:$LD_LIBRARY_PATH' >> ~/.bashrc
   source ~/.bashrc
   ```
   Verify: `hashcat -I | grep -iE 'CUDA|Backend Device|Name'` should list the RTX 3070 Ti.

## Using it from Fancy

```bash
CRACK_HOST=gpu-host-wsl ~/labs/wpa/crack-offload.sh ~/labs/wpa/handshake-01.cap
# repo copy: software/crack-offload.sh
```
The script checks reachability, ensures the wordlist exists (expanding `rockyou.txt.gz` if needed),
copies the capture, converts with `hcxpcapngtool`, and runs `hashcat -m 22000 -O -w 3`.

## Gotchas

- **The node is only online while the WSL distro is running.** Windows tears the WSL VM down when no
  session is active. Keep a Kali window open (or `wsl` a keep-alive) before offloading; it rejoins
  the tailnet within a couple seconds of starting. The script's step 1 reports if it's down.
- **Tailnet path is DERP-relayed** (WSL NAT), so it's a bit slower to connect — fine for a small
  `.cap` and a local crack.
- **Two tailnet devices now** (`gpu-host` + `gpu-host-wsl`); ACLs must allow `fancy → kali`.

## Validated

2026-09-26 on this host: full `rockyou` (14.3M) ran in **~46 s** on the RTX 3070 Ti (`-O -w 3`,
~210 kH/s — `-w 4` goes faster) vs ~14 min CPU-only on Fancy. The test capture (own AP) was
**not** cracked — the passphrase isn't in `rockyou`. Pipeline end-to-end confirmed.
