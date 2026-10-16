# netexec — authorized AD/network service auditing

Upstream: https://github.com/Pennyw0rth/NetExec · wiki https://netexec.wiki/ · the maintained
successor to CrackMapExec. Installed from the project's Git repo via `pipx` (there is no PyPI
package — `pip install netexec` fails), and verified on this hardware 2026-10-13:
`nxc` **1.5.1** ("Yippie-Ki-Yay", commit `28e58512`, build 1011), on Python 3.13.5.

> **Scope: own networks, documented engagements, and CTFs — nothing else.** NetExec is an active
> network-attack tool: it authenticates, sprays credentials, relays auth, enumerates AD, and runs
> commands against SMB/LDAP/MSSQL/WINRM/WMI/SSH/FTP/NFS/VNC/RDP hosts. That is the opposite of this
> repo's passive-only wardriving posture (see [`../CLAUDE.md`](../CLAUDE.md) and
> [`../knowledge/README.md`](../knowledge/README.md)'s responsible-use section). Like
> [`aircrack-ng`](aircrack-ng.md), it is a deliberate, gated exception — only against hosts you
> own, a network you hold written authorization to test, or a CTF whose rules permit it. If you're
> not sure a target is in scope, it isn't. Authorization recorded by the owner 2026-10-13:
> self-owned networks, documented engagements, and CTFs.

## Install

NetExec needs a Rust compiler to build its `aardwolf` (RDP) dependency, plus the usual C build
headers. On Debian 13 (trixie), which this build runs:

```bash
sudo apt install -y pipx git rustc cargo build-essential python3-dev libffi-dev libssl-dev
pipx ensurepath                                    # puts ~/.local/bin on PATH (new shell to pick up)
pipx install git+https://github.com/Pennyw0rth/NetExec
```

The Rust build of `aardwolf` is slow on the CM4 (a few minutes). On success pipx reports the four
console scripts it links into `~/.local/bin`: `NetExec`, `netexec`, `nxc`, `nxcdb`.

Update later with `pipx upgrade netexec`, or `pipx reinstall netexec` to pull the latest commits.

## Verify

```bash
nxc --version          # expect: 1.5.1 - Yippie-Ki-Yay - 28e58512 - 1011  (as installed 2026-10-13)
nxc smb --version      # confirms a protocol subcommand loads
```

First run prints `[*] First time use detected` and creates `~/.nxc/` (see below). That is normal and
happens once.

## What it writes

NetExec keeps all state under **`~/.nxc/`**, created on first run — **not** inside this repo's
working tree, and it must stay that way:

| Path | Holds |
|---|---|
| `~/.nxc/nxc.conf` | Config (workspace, logging, options) |
| `~/.nxc/workspaces/` | Per-protocol SQLite databases of hosts/creds/shares enumerated |
| `~/.nxc/logs/` | Run logs, plus `logs/{sam,lsa,ntds,dpapi}/` — **dumped credential material** |
| `~/.nxc/modules/`, `obfuscated_scripts/`, `screenshots/`, `tmp/` | Module data, payloads, loot |

`logs/sam`, `logs/lsa`, `logs/ntds` and `logs/dpapi` collect secrets (password hashes, domain
credentials) from authorized targets. Treat everything under `~/.nxc/` as sensitive: it never goes
in git (it lives in `$HOME`, outside the tree, so there is nothing to `.gitignore`), and loot from
an engagement should be moved to storage you control and wiped from the device when the engagement
ends. No secrets from it go in this repo — per [`../CLAUDE.md`](../CLAUDE.md).

`nxcdb` opens the workspace database for review (`nxc`-enumerated hosts, users, shares, creds).

## Typical authorized workflow

Only against in-scope hosts (own, authorized, or CTF). Protocol-first; `-u`/`-p` take users and
passwords (or hashes, files, `-k` for Kerberos). A null/enumeration sweep of your own subnet:

```bash
nxc smb 192.0.2.0/24                                 # host discovery + SMB signing/OS/domain
nxc smb 192.0.2.0/24 -u user -p 'pass' --shares      # authenticated share enumeration
nxc ldap dc.lab.local -u user -p 'pass' --users      # AD user enumeration over LDAP
nxc winrm 192.0.2.5 -u user -p 'pass' -x whoami      # command exec where you're authorized
```

`nxc <protocol> --help` lists that protocol's flags and modules; `nxc <protocol> -L` lists modules.

## This device as the attack host

Fancy is CPU-only and modest; NetExec is network-bound, not compute-bound, so it runs fine for
enumeration and auth from here over Wi-Fi, Ethernet, or the tailnet. For anything that then needs a
GPU (cracking hashes NetExec dumps), offload to the GPU host on the tailnet the same way the WPA
workflow does — see [`aircrack-ng.md`](aircrack-ng.md)'s GPU crack-offload section and
[`../docs/reference/gpu-crack-offload-host.md`](../docs/reference/gpu-crack-offload-host.md).
