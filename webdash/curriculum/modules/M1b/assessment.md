---
id: M1b.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: error6
    concept_tags: [C08]
    type: single
    prompt: "rtl_test prints usb_claim_interface error -6. The most likely cause on this build is…"
    choices:
      - "The SDR is broken"
      - "readsb already holds the dongle"
      - "The DVB driver is loaded"
    answer: 1
    explanation: The DVB driver is blacklisted here; readsb is the usual owner. Stop it first.
  - id: autorestart
    concept_tags: [C09]
    type: single
    prompt: "With the SDR rail off, systemctl status readsb says activating (auto-restart). That means…"
    choices:
      - "readsb is broken and needs reinstalling"
      - "readsb can't find an SDR and systemd keeps retrying — normal here"
      - "readsb is decoding normally"
    answer: 1
    explanation: A crash loop is the resting state for readsb while its rail is off.
  - id: serial
    concept_tags: [C08]
    type: single
    prompt: Who owns /dev/serial0, and how should you look at the raw GPS sentences?
    choices:
      - "meshtasticd; read it with cat"
      - "gpsd; read it through gpsd with gpspipe -r"
      - "Nobody; read it with stty and cat"
    answer: 1
    explanation: Reading the port directly interleaves with gpsd.
  - id: cli
    concept_tags: [C08, C10]
    type: single
    prompt: Running meshtastic --host localhost --info while webdash is up…
    choices:
      - "Works alongside webdash"
      - "Drops webdash's mesh connection — meshtasticd serves one client at a time"
      - "Transmits a packet"
    answer: 1
    explanation: Port 4403 serves a single client.
  - id: reboot
    concept_tags: [C09]
    type: single
    prompt: You run sudo systemctl stop readsb, then reboot with the SDR rail on. Is readsb running?
    choices:
      - "No — stop is permanent"
      - "Yes — it is still enabled, so it starts at boot"
      - "Only if you start it by hand"
    answer: 1
    explanation: stop is about now; enable is about boot.
  - id: spi
    concept_tags: [C07]
    type: single
    prompt: Which device node does the LoRa chip (SX1262) sit behind?
    choices: ["/dev/serial0", "/dev/spidev1.0", "/dev/rtc0", "A USB device"]
    answer: 1
    explanation: The SX1262 is on SPI1; meshtasticd drives it through /dev/spidev1.0.
---

Five of six to pass.
