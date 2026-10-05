---
id: M1b.configs
title: Staged versus installed configs
est_minutes: 15
---

Every file this build copies onto the device lives first in the repo's `configs/` folder. Each
one starts with a header saying how to **apply** it, how to **verify** it and how to **roll it
back**. The copy on the device can drift from the repo — someone edits `/etc` by hand, or a
package upgrade replaces a file — so you check them against each other.

A worked example, from the repo folder on Fancy:

```bash
cd ~/clockworkpi-uconsole
diff configs/gpsd/gpsd.default /etc/default/gpsd && echo same
diff configs/modprobe.d/blacklist-rtl-dvb.conf /etc/modprobe.d/blacklist-rtl-dvb.conf && echo same
```

No output from `diff` followed by `same` means the installed file matches the repo. Any lines it
prints are the drift — decide which copy is right, then fix the other one and note it in the
build log.
