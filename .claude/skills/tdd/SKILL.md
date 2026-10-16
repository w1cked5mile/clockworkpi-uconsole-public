---
name: tdd
description: Test-driven development. Use when the user wants to build features or fix bugs test-first, mentions "red-green-refactor", or wants integration tests.
---

# Test-Driven Development

TDD is the red → green loop. This skill is the reference that makes that loop produce tests worth keeping: what a good test is, where tests go, the anti-patterns, and the rules of the loop. Every section applies on every cycle: consult them before and during the loop, not after.

When exploring the codebase, match test names and interface vocabulary to the project's domain language (the curriculum [`glossary`](../../../webdash/curriculum/glossary/) and the docs the code cites), and respect [`decisions.md`](../../../docs/logs/decisions.md) in the area you're touching.

## What a good test is

Tests verify behavior through public interfaces, not implementation details. Code can change entirely; tests shouldn't. A good test reads like a specification: "user can checkout with valid cart" tells you exactly what capability exists, and it survives refactors because it doesn't care about internal structure.

See [tests.md](tests.md) for examples and [mocking.md](mocking.md) for mocking guidelines.

## Seams: where tests go

A **seam** is the public boundary you test at: the interface where you observe behavior without reaching inside. Tests live at seams, never against internals.

**Test only at pre-agreed seams.** Before writing any test, write down the seams under test and confirm them with the user. No test is written at an unconfirmed seam. You can't test everything, so agreeing the seams up front is how testing effort lands on the critical paths and complex logic instead of every edge case.

Ask: "What's the public interface, and which seams should we test?" Give each proposed seam a one-line note on what it catches and what it misses.

When the shape of that interface is itself in question (how deep the module is, where the seam belongs, what the interface should expose), settle it with the user before writing the test: prefer a deep module with a small interface, whose logic is pure and testable without the hardware.

## Anti-patterns

- **Implementation-coupled**: mocks internal collaborators, tests private methods, or verifies through a side channel (querying the database instead of using the interface). The tell: the test breaks when you refactor but behavior hasn't changed.
- **Tautological**: the assertion recomputes the expected value the way the code does (`expect(add(a, b)).toBe(a + b)`, a snapshot derived by hand the same way, a constant asserted equal to itself), so it passes by construction and can never disagree with the code. Expected values must come from an independent source of truth: a known-good literal, a worked example, the spec.
- **Horizontal slicing**: writing all tests first, then all implementation. Bulk tests verify _imagined_ behavior: you test the _shape_ of things rather than user-facing behavior, the tests go insensitive to real changes, and you commit to test structure before understanding the implementation. Work in **vertical slices** instead: one test → one implementation → repeat, each test a **tracer bullet** that responds to what the last cycle taught you.

## Rules of the loop

- **Red before green.** Write the failing test first, then only enough code to pass it. Don't anticipate future tests or add speculative features.
- **One slice at a time.** One seam, one test, one minimal implementation per cycle.
- **Refactoring is not part of the loop.** It belongs to the review stage (the `web-ui-engineer` agent for UI code, `repo-audit` before a batch is committed), not the red → green implementation cycle.

## In this repo

The tests are webdash's: Python stdlib `unittest` (no pytest), one suite per area in
[`webdash/tests/`](../../../webdash/tests/). The examples in [tests.md](tests.md) and
[mocking.md](mocking.md) are TypeScript; the rules carry over unchanged.

- **Seams already in use.** Pure modules with no I/O (the `collectors/*` logic that turns radio
  config or survey data into a model) are the deepest seam: feed literal inputs, assert on the
  returned dict. HTTP routes are the next seam out. The rendered page is checked by the
  headless-chromium harnesses in [`webdash/tools/render-check/`](../../../webdash/tools/render-check/README.md),
  driven with fixture models.
- **System boundaries here** are the hardware and the daemons: `meshtasticd`, `gpsd`, Kismet, the
  AIO V2 bridge, the clock. Fake those at the boundary with a small stand-in object; never let a
  test key the radio. Skip a test cleanly (`unittest.skipUnless`) when an optional library such as
  `meshtastic` is absent on the host.
- **Expected values come from an independent source**: a datasheet, a firmware source file, or a
  reading taken on Fancy, cited in a comment, never recomputed the way the code does it.
- **Run red and green in the container** —
  `sg docker -c 'docker exec -i uconsole-webdash python -' < webdash/tests/<suite>.py` — after
  rebuilding the image (`cd webdash && sg docker -c 'docker compose up -d --build'`), since app
  code is baked in. A host run (`cd webdash && PYTHONPATH=. python3 tests/<suite>.py`) is a quick
  check only.
