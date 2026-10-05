"""Host system vitals — always available, no downstream service to fail."""
import os
import time

import psutil

HOSTFS = os.environ.get("WEBDASH_HOSTFS", "/hostfs")

# cpu_percent(interval=None) measures since the previous call and returns 0.0 on the first one;
# prime it at import so the first status a client sees isn't a false 0%.
psutil.cpu_percent(interval=None)


def _cpu_temp_c() -> float | None:
    path = "/sys/class/thermal/thermal_zone0/temp"
    try:
        with open(path) as f:
            return round(int(f.read().strip()) / 1000, 1)
    except OSError:
        return None


def _undervoltage() -> bool | None:
    """Pi firmware throttle state, as the raspberrypi-hwmon 'rpi_volt' device exposes it:
    in0_lcrit_alarm == 1 while the 5 V rail is sagging (bit 0 of vcgencmd's get_throttled word).
    This is the one throttle signal readable without /dev/vcio, which the container doesn't have.
    Read via HOSTFS — only /sys/class/thermal is bind-mounted directly; hwmon isn't."""
    base = os.path.join(HOSTFS, "sys/class/hwmon")
    try:
        entries = os.listdir(base)
    except OSError:
        return None
    for entry in entries:
        d = os.path.join(base, entry)
        try:
            with open(os.path.join(d, "name")) as f:
                if f.read().strip() != "rpi_volt":
                    continue
            with open(os.path.join(d, "in0_lcrit_alarm")) as f:
                return f.read().strip() == "1"
        except OSError:
            continue
    return None


def collect() -> dict:
    disk = psutil.disk_usage(HOSTFS if os.path.isdir(HOSTFS) else "/")
    load1, load5, load15 = os.getloadavg()
    return {
        "cpu_percent": psutil.cpu_percent(interval=None),
        "cpu_count": psutil.cpu_count(),
        "load": {"1m": load1, "5m": load5, "15m": load15},
        "mem": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "percent": psutil.virtual_memory().percent,
        },
        "disk": {"total": disk.total, "used": disk.used, "free": disk.free, "percent": disk.percent},
        "temp_c": _cpu_temp_c(),
        "undervoltage": _undervoltage(),
        "uptime_s": int(time.time() - psutil.boot_time()),
    }
