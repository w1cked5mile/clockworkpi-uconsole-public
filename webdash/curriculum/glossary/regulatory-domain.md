---
id: regulatory-domain
term: Regulatory domain
tooltip: The country rule table that decides which Wi-Fi channels and powers a radio may use.
good_bad: "Fancy's global domain is US. phy#0 says country 99 — brcmfmac's own built-in table, applied to that radio instead of the global one; what the chip's firmware enforces is unverified."
try_this: "Run iw reg get and find both the global block and the phy#0 block."
learn_more: "#/learn/m/M7"
---

Linux keeps a regulatory database and a global country setting (here US, from the kernel command
line). Some drivers apply their own table to their radio and report it as a separate phy# block —
the onboard brcmfmac does. A USB adapter is expected to follow the global US table: check that no
new phy# block appears when you plug it in. The domain also marks which 5 GHz channels need DFS radar detection.
