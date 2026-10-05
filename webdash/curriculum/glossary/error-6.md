---
id: error-6
term: usb_claim_interface error -6
tooltip: The SDR is already claimed by another program — on this build almost always readsb.
good_bad: 'Known fault, not your mistake: stop readsb first, start it after.'
try_this: sudo systemctl stop readsb; rtl_test -t; sudo systemctl start readsb
learn_more: '#/learn/m/M1b'
---

The DVB-T TV driver could also claim it, but it is blacklisted here.
