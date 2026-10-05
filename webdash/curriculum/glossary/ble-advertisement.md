---
id: ble-advertisement
term: BLE advertisement
tooltip: A short packet a Bluetooth LE device broadcasts on channels 37, 38 and 39 so others can find it.
good_bad: "Hearing advertisements is passive. Asking for more (a scan request) is active and transmits."
try_this: "Do LAB-21 and count unique advertising addresses over one minute."
learn_more: "#/learn/m/M7"
---

Bluetooth LE devices advertise every 20 ms to 10.24 s, plus a small random delay, on three fixed
channels (2402, 2426 and 2480 MHz). A legacy advertisement carries up to 31 bytes. The address it
comes from is usually random and rotates, so one device over time looks like several.
