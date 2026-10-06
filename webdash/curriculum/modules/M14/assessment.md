---
id: M14.quiz
kind: quiz
pass_threshold: 0.8
items:
  - id: passive
    concept_tags: [C41, C01]
    type: single
    prompt: Fancy's tap captures on wlan0. What does it put on the air to do that?
    choices:
      - "A probe frame, so the AP knows to mirror its traffic"
      - "Nothing — it only copies frames wlan0 already receives"
      - "A monitor-mode beacon"
    answer: 1
    explanation: Capture is passive. dumpcap copies received frames; no frame is transmitted to start it.
  - id: filters
    concept_tags: [C41]
    type: single
    prompt: You capture with no filter, then realise you only care about DNS. Which filter gets you there without re-capturing, and why?
    choices:
      - "A capture filter — it is applied before recording"
      - "A display filter — everything is still in the file, so you just narrow the view"
      - "Either one; they do the same thing at different times"
    answer: 1
    explanation: A display filter only hides packets from view. A capture filter would have had to be set before recording, and what it dropped is gone.
  - id: lost-data
    concept_tags: [C41]
    type: single
    prompt: Which filter can lose data you cannot get back?
    choices:
      - "The display filter — hidden packets are deleted"
      - "The capture filter — what it drops is never written to disk"
      - "Neither; both are reversible"
    answer: 1
    explanation: A capture filter decides what is saved; a display filter only decides what is shown.
  - id: ring
    concept_tags: [C41]
    type: single
    prompt: The tap runs a 10 MB x 10 ring buffer. What is bounded, and what is the trade?
    choices:
      - "Disk is capped at about 100 MB; the trade is history — only the most recent ~100 MB is kept"
      - "Capture time is capped at 10 minutes; there is no trade"
      - "Nothing is bounded; the ring just makes it faster"
    answer: 0
    explanation: Disk use is file size x count. The ring overwrites the oldest segment, so long runs keep only the most recent window.
  - id: retransmit-climb
    concept_tags: [C42]
    type: single
    prompt: While wlan0 is associated but slow, tcp_retransmit and tcp_dup_ack climb steadily. What does that point at?
    choices:
      - "A routing problem upstream of the radio"
      - "Packets being lost in flight on a marginal link — the weak-signal loss pattern"
      - "A service refusing connections"
    answer: 1
    explanation: Retransmits and dup-acks both mean loss; climbing while associated-but-slow is the fingerprint of a weak link — consistent with the 20–30% loss measured on wlan0 before power-save was disabled (the retransmit counts themselves were not recorded).
  - id: resets
    concept_tags: [C42]
    type: single
    prompt: You see a burst of tcp_reset but retransmits stay near zero. Best first read?
    choices:
      - "The Wi-Fi antenna needs re-seating"
      - "Something is actively tearing connections down — a dead service, a firewall, a closed port — not radio loss"
      - "The ring buffer is too small"
    answer: 1
    explanation: A reset is an abrupt teardown. Without a climb in retransmits it points at an endpoint or a filter, not at loss on the air.
  - id: baseline
    concept_tags: [C42]
    type: single
    prompt: A capture of a healthy link shows all four findings at zero. What does that mean?
    choices:
      - "The capture failed — a real link always shows anomalies"
      - "That is the healthy baseline; a clean capture is supposed to be boring"
      - "The filter is wrong"
    answer: 1
    explanation: Zero retransmits, dup-acks, resets and unreachables is exactly what a working link looks like.
  - id: pcap-privacy
    concept_tags: [C02, C41]
    type: single
    required: true
    prompt: The dashboard summary is address-free, but the .pcapng on disk is not. How do you handle that file?
    choices:
      - "Commit it to the repo so the finding is reproducible"
      - "Keep it on Fancy, never put it in the repo, and delete it when done — it holds addresses"
      - "Upload it to the dashboard so the counts match"
    answer: 1
    explanation: The pcap keeps addresses on purpose for a Wireshark deep-dive. It stays on Fancy and off the repo, like any capture.
---

Seven of eight to pass, and the question about handling the on-disk capture must be right.
