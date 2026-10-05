---
id: M5.discipline
title: Capture discipline — a capture you can trust later
est_minutes: 15
---

A capture nobody can reproduce is a story, not evidence. Discipline is a habit: a filename that
carries its own parameters, a checksum that pins the exact bytes, and a finding that records where,
when and how. Start with the filename convention — everything the capture is, in its name:

@ref knowledge/rf-fundamentals/configs/capture-metadata-conventions.md#filename

And the storage rule that keeps the repo clean and honest: raw IQ never gets committed — it lives in
`~/labs/`, referenced from a finding by its sha256, not pasted into git:

@ref knowledge/rf-fundamentals/configs/capture-metadata-conventions.md#storage-discipline

In LAB-11 you produce one capture that follows all of this: named to convention, checksummed, and
recorded in a finding that holds the sha256 while the raw `.cu8` (the 8-bit IQ file) stays out of the
repo.
