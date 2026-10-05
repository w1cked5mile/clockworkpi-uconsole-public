---
id: M8.confidence
title: Confidence, and rejecting false positives
est_minutes: 20
---

An identification is only as good as its honesty. The signal-ID worksheet grades every entry
**unidentified -> candidate -> identified**, and a good analyst says out loud what would move it up a
grade (a clean decode, a second observation, a matching reference). "Probably DMR (Digital Mobile
Radio)" with the reasons is worth more than a confident wrong name.

Half the skill is *not* naming things that were never signals. The waterfall is full of artefacts
that look like transmissions until you test them:

@ref knowledge/rf-fundamentals/learned/signal-identification-workflow.md#common-false-positives

The tell for most of them is behaviour under a change: images and aliases move when you retune, the
DC spike sits dead-centre wherever you tune, harmonics land at exact integer multiples of a strong
local source, and self-noise vanishes when you power the culprit off. In LAB-17 you classify three
real signals - and part of the grade is not logging an artefact as one of them.
