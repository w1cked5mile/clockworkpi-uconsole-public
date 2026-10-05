---
id: fix-mode
term: Fix mode
tooltip: 'What kind of position the GPS has: none, 2D (no altitude) or 3D.'
good_bad: 3D is the normal outdoor state; none or searching is normal indoors.
try_this: Watch the GPS station while you move from a room's middle to a window.
learn_more: '#/learn/m/M3'
---

gpsd reports mode 0 (unknown, e.g. no data — webdash shows this with the rail off), 1 (no fix), 2 (2D) or 3 (3D). A 3D fix needs at least four satellites.
