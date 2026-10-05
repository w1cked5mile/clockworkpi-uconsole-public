---
id: LAB-01
title: Staged versus applied
themed_title: Sea trial · Check the charts
mode: observe
est_minutes: 15
requires: {rails: [], services: []}
transmits: false
steps:
  - id: nodes
    text: "Run ls -l /dev/serial0 /dev/spidev1.0 /dev/rtc0 and paste the output: the GPS, LoRa and clock device nodes."
    check: {type: paste, parser: regex, pattern: '(serial0|spidev1\.0|rtc0)', min_matches: 3, reject: 'cannot access|No such file'}
  - id: gpsd
    text: "Compare gpsd's options: run diff configs/gpsd/gpsd.default /etc/default/gpsd from the repo folder. The server checks the same pair."
    check: {type: file, op: sha256_equal, path: "~/clockworkpi-uconsole/configs/gpsd/gpsd.default", other: "/etc/default/gpsd"}
  - id: kismet
    text: "Compare Kismet's site overrides: run diff configs/kismet/kismet_site.conf /etc/kismet/kismet_site.conf from the repo folder. The server checks the same pair."
    check: {type: file, op: sha256_equal, path: "~/clockworkpi-uconsole/configs/kismet/kismet_site.conf", other: "/etc/kismet/kismet_site.conf"}
  - id: dvb
    text: "Compare the DVB-T driver blacklist: run diff configs/modprobe.d/blacklist-rtl-dvb.conf /etc/modprobe.d/blacklist-rtl-dvb.conf from the repo folder. The server checks the same pair."
    check: {type: file, op: sha256_equal, path: "~/clockworkpi-uconsole/configs/modprobe.d/blacklist-rtl-dvb.conf", other: "/etc/modprobe.d/blacklist-rtl-dvb.conf"}
  - id: banner
    text: "Compare the login banner: run diff configs/profile.d/fancy-banner.sh /etc/profile.d/fancy-banner.sh from the repo folder. The server checks the same pair."
    check: {type: file, op: sha256_equal, path: "~/clockworkpi-uconsole/configs/profile.d/fancy-banner.sh", other: "/etc/profile.d/fancy-banner.sh"}
  - id: udev
    text: "Compare the fixed nRF51822 udev rule: run diff configs/udev/99-kismet-nrf51822.rules /etc/udev/rules.d/99-kismet-nrf51822.rules from the repo folder. The server checks the same pair."
    check: {type: file, op: sha256_equal, path: "~/clockworkpi-uconsole/configs/udev/99-kismet-nrf51822.rules", other: "/etc/udev/rules.d/99-kismet-nrf51822.rules"}
  - id: why
    text: "Read the header of configs/kismet/kismet_site.conf. Why does this build add a site file instead of editing kismet.conf?"
    check: {type: attest, prompt: "Package upgrades overwrite kismet.conf but leave kismet_site.conf alone."}
restore: []
evidence: []
---

Read-only. The server compares checksums of each pair and returns only "same" or "different";
it never sends the files' contents to the browser. The polkit rule is left out because
`/etc/polkit-1/rules.d` is readable only by root.
