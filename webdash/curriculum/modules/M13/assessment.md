---
id: M13.quiz
kind: quiz
pass_threshold: 0.85
items:
  - id: the-one-rule
    concept_tags: [C01, C39]
    type: single
    required: true
    prompt: Against which networks may you run the capture-and-deauth workflow in this module?
    choices:
      - "Any network, now that this account is approved into the Cyber Verification Program"
      - "Only a network you own, or one you hold written authorization to test"
      - "Any open network, since open networks have no protection to break"
      - "Any network whose owner probably wouldn't mind"
    answer: 1
    explanation: One rule, no exceptions — your own network or documented written authorization. Approval, an open network, and a guess about the owner are none of them.
  - id: approval-scope
    concept_tags: [C39]
    type: single
    required: true
    prompt: What does the Cyber Verification Program approval on this account actually change?
    choices:
      - "It authorizes you to test networks you don't own"
      - "It lifts the default block on dual-use security work; it does not authorize you against any particular network"
      - "It unblocks command-and-control and ransomware work"
      - "It means being installed equals being allowed"
    answer: 1
    explanation: Approval removes a default block on dual-use work. Authorization for a specific target is still something you establish and document; C2, mass exfiltration and ransomware stay prohibited.
  - id: still-prohibited
    concept_tags: [C39]
    type: multi
    required: true
    prompt: Which of these stay prohibited regardless of the approval?
    choices:
      - "Command-and-control (C2) infrastructure"
      - "Auditing your own AP's passphrase"
      - "Mass data exfiltration"
      - "Ransomware development"
    answer: [0, 2, 3]
    explanation: C2, mass exfiltration and ransomware are prohibited-use and never in scope. Auditing your own AP is the authorized case this module teaches.
  - id: deauth-target
    concept_tags: [C39, C40]
    type: single
    required: true
    prompt: To force a handshake on your own network, which is acceptable?
    choices:
      - "Broadcast a deauth so every client reconnects at once"
      - "Send a few deauths at one client you own"
      - "Deauth a neighbour's client that happens to be in range"
    answer: 1
    explanation: A few targeted deauths at your own client. A broadcast knocks everyone off — disruptive — and a neighbour's client is not yours to touch.
  - id: captures-handling
    concept_tags: [C02]
    type: single
    required: true
    prompt: Where do capture files and any recovered passphrase belong?
    choices:
      - "Committed to the repo so the finding has evidence"
      - "Outside the repo, on storage you control, and deleted when no longer needed"
      - "Uploaded to a public cracking service"
    answer: 1
    explanation: Captures hold the network's real frames and, on success, its real passphrase. They never go in the repo; a finding records the result in words only.
  - id: where-cracking-runs
    concept_tags: [C40]
    type: single
    required: true
    prompt: Why does the real cracking run on a GPU host on the tailnet rather than on Fancy?
    choices:
      - "Fancy is not allowed to run hashcat"
      - "The CM4 is CPU-only and slow; a GPU host makes a large wordlist practical, so Fancy captures and offloads"
      - "The capture file can only be read on Windows"
    answer: 1
    explanation: Fancy captures fine but cracks slowly on its CPU. The handshake is small, so you transfer it to a beefier host (gpu-host or homeserver) for the GPU run.
  - id: wpa3
    concept_tags: [C40]
    type: single
    prompt: You capture a handshake and it will not crack from any wordlist. What can you conclude?
    choices:
      - "The passphrase is definitely unbreakable"
      - "Only that it was not in your wordlist — a bigger list or a different network scheme may change that"
      - "The capture must be corrupt"
    answer: 1
    explanation: A failed crack proves only that the passphrase was not in your list. It is not proof of strength, and WPA3/SAE would not yield a crackable handshake at all.
  - id: authorization-is-recorded
    concept_tags: [C39]
    type: single
    required: true
    prompt: How is authorization handled in this module?
    choices:
      - "Assumed, since the tools are installed"
      - "Established and recorded each time — your own network, or a cited written authorization — and attested before the lab runs"
      - "Granted automatically by passing this quiz"
    answer: 1
    explanation: Authorization is something you establish and document every time. Passing this quiz unlocks the lab; it does not authorize you against anything.
---

Seven of eight to pass, and every required question — the one rule, what approval means, what stays
prohibited, deauth targeting, capture handling, and recording authorization — must be right. This
quiz is the gate: LAB-22 stays locked until you pass it.
