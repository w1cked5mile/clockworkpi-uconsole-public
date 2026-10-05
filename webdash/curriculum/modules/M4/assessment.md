---
id: M4.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: negative-snr
    concept_tags: [C25, C14]
    type: single
    prompt: A LONG_FAST packet arrives at −10 dB SNR. What happens?
    choices:
      - "It can't be decoded — SNR must be positive"
      - "It decodes — LONG_FAST (SF11) works down to about −17.5 dB"
      - "It decodes only if RSSI is above −50 dBm"
    answer: 1
    explanation: Spreading gain lets LoRa decode below the noise floor.
  - id: sf-trade
    concept_tags: [C25]
    type: single
    prompt: Moving from spreading factor 11 to 12 roughly…
    choices:
      - "Halves airtime and costs 2.5 dB of link budget"
      - "Doubles airtime and adds about 2.5 dB of link budget"
      - "Changes nothing that matters"
    answer: 1
    explanation: Each SF step doubles airtime for about 2.5 dB more reach.
  - id: nothing-heard
    concept_tags: [C27, C28]
    type: single
    prompt: A nearby node's packets never show up at all — no RSSI, nothing. First suspect?
    choices:
      - "A different channel key"
      - "A different frequency slot or preset"
      - "The other node is too close"
    answer: 1
    explanation: A key mismatch still demodulates (you'd see RSSI); a slot or preset mismatch shows nothing.
  - id: slot
    concept_tags: [C27]
    type: single
    prompt: What decides the frequency a Meshtastic node uses in the US band?
    choices:
      - "The node's long name"
      - "The primary channel's name"
      - "The hop limit"
    answer: 1
    explanation: The primary channel name hashes to a slot; SCMesh is index 88, 924.125 MHz.
  - id: nodes-seen
    concept_tags: [C26]
    type: single
    prompt: webdash's nodes_seen reads 3. How many other nodes have you definitely heard since webdash started?
    choices:
      - "Three"
      - "Can't tell — the NodeDB includes this node and stale entries"
      - "Two"
    answer: 1
    explanation: Use rx_packets and rx_nodes for what was actually heard since webdash started.
  - id: range
    concept_tags: [C01, C25]
    type: single
    required: true
    prompt: You want more mesh range. What may you do?
    choices:
      - "Raise the transmit power or change the region setting"
      - "Keep the region and power settings, and put the antenna higher"
      - "Pick a quieter frequency outside the band"
    answer: 1
    explanation: Settings stay as they are; height and a clear path are the legal way to more range.
  - id: who-reads
    concept_tags: [C26, C02]
    type: single
    required: true
    prompt: "Before you send: a message on SCMesh with the default key can be read by…"
    choices:
      - "Only nodes you've paired with"
      - "Anyone in range who sets up SCMesh with the public default key — which anyone can"
      - "Nobody without your private key"
    answer: 1
    explanation: The default key is public. Never put location or anything private in a message.
---

Six of seven to pass, and both questions about range and privacy must be right.
