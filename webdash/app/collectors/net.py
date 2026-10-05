"""Wireless interface modes from sysfs — which radios exist and whether any is in monitor mode.

The container runs with `network_mode: host`, so /sys/class/net inside it is the host's. Each
interface's `type` file is its ARPHRD link type: 1 (ARPHRD_ETHER) for Ethernet and for a Wi-Fi
interface in managed mode, 803 (ARPHRD_IEEE80211_RADIOTAP) for a Wi-Fi interface in monitor mode.
A `wireless/` or `phy80211` entry tells a Wi-Fi interface from wired Ethernet with the same type.

Reports booleans, counts and mode names only. It never reads `address`: learning content and the
status payload carry no MAC addresses (see docs/reference/webdash-architecture.md).

  monitor_ifaces   count of every interface with type 803, whatever it is called
  wlan0 / wlan1    present: bool; mode: "managed" (type 1, wireless), "monitor" (803),
                   "other" (anything else, including type 1 without a wireless entry), or None
                   when the interface is absent

Kismet puts a card into monitor mode by adding a separate monitor vif, `wlan1mon`, alongside
`wlan1`, which stays managed (seen 2026-09-25: monitor_ifaces=1, wlan1 managed, throughout the
LAB-15 run), and it can leave `wlan1mon` up after it exits (removed with `iw dev wlan1mon del`).
With both present, wlan1 reports its own mode and wlan1mon counts toward monitor_ifaces. An older
reading of the 2026-09-21 test was a rename (wlan1 -> wlan1mon -> wlan1), so if `wlan1` is ever
absent while `wlan1mon` is present, wlan1 is still reported present with wlan1mon's mode (normally
"monitor"); it is the same radio. The same rule applies to wlan0/wlan0mon for
symmetry, although wlan0 (brcmfmac) has no monitor mode on this build.

Never raises: an unreadable interface is skipped, and a failure to list the directory at all
reports state "error" with every value None.
"""
import os

SYS_CLASS_NET = "/sys/class/net"
ARPHRD_ETHER = 1
ARPHRD_IEEE80211_RADIOTAP = 803
NAMED = ("wlan0", "wlan1")


def _type(root: str, iface: str) -> int | None:
    try:
        with open(os.path.join(root, iface, "type")) as f:
            return int(f.read().strip())
    except (OSError, ValueError):
        return None  # vanished between listdir and read, or not an interface directory


def _mode(root: str, iface: str, t: int | None) -> str | None:
    if t is None:
        return None
    if t == ARPHRD_IEEE80211_RADIOTAP:
        return "monitor"
    if t == ARPHRD_ETHER and (os.path.isdir(os.path.join(root, iface, "wireless"))
                              or os.path.exists(os.path.join(root, iface, "phy80211"))):
        return "managed"
    return "other"


def collect(root: str = SYS_CLASS_NET) -> dict:
    try:
        types = {i: _type(root, i) for i in os.listdir(root)}
        types = {i: t for i, t in types.items() if t is not None}
        out = {
            "state": "ok",
            "monitor_ifaces": sum(1 for t in types.values() if t == ARPHRD_IEEE80211_RADIOTAP),
        }
        for name in NAMED:
            iface = name if name in types else f"{name}mon" if f"{name}mon" in types else None
            out[name] = {"present": iface is not None,
                         "mode": _mode(root, iface, types[iface]) if iface else None}
        return out
    except Exception:  # noqa: BLE001 — a status collector must never raise
        return {"state": "error", "monitor_ifaces": None,
                **{name: {"present": None, "mode": None} for name in NAMED}}
