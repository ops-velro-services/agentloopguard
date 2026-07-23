# AgentLoopGuard Build Queue

This is the canonical prioritized queue. The scheduler may execute only rows marked `auto-eligible: yes` whose dependencies are complete and that do not require an owner decision or external side effect.

Statuses: `ready`, `blocked`, `in-progress`, `done`, `cancelled`.

## P0 — truthful, reliable alpha

### ALG-001 — Align the public contract

- Status: done
- Auto-eligible: no
- Depends on: OWN-001, OWN-003
- Scope: make README, landing page, examples, package metadata, badges, install command, API names, thresholds, repository URLs, and feature claims agree with the shipped SDK. Remove unimplemented paid/cloud claims and unsupported performance/concurrency claims.
- Acceptance: every copied code sample executes; one canonical repo URL and one package name are used everywhere; no feature is advertised without a test or linked implementation.
- Verification: link scan, README snippet tests, landing-page text scan, `pytest`.

### ALG-002 — Make budget state session-local

- Status: done
- Auto-eligible: yes
- Depends on: none
- Scope: treat `LoopGuard` as immutable configuration and create a new tracker for each session/decorated run policy. Define deliberate behavior for persistent decorated histories.
- Acceptance: two sessions created from one guard have independent cost, token, duration, iteration, warnings, and summaries; concurrent sessions do not share mutable accounting.
- Verification: isolation and concurrency tests.

### ALG-003 — Correct sync and async decorators

- Status: done
- Auto-eligible: yes
- Depends on: ALG-002
- Scope: include positional and keyword arguments in a stable call representation; add an await-aware wrapper; define whether exceptions are recorded; make documented invocation syntax exact.
- Acceptance: distinct positional calls do not false-positive; repeated equivalent calls do; async results are recorded after awaiting; function metadata is preserved.
- Verification: sync/async unit tests and executable README examples.

### ALG-004 — Validate configuration and input safely

- Status: done
- Auto-eligible: yes
- Depends on: ALG-002
- Scope: reject invalid limits, thresholds, alert modes, token counts, timestamps, and missing callback requirements. Copy input rather than mutating caller dictionaries. Canonicalize or safely fingerprint non-JSON arguments with documented fallback behavior.
- Acceptance: invalid configuration fails immediately with actionable errors; common Python/SDK argument types cannot crash the guard; caller inputs remain unchanged.
- Verification: parameterized boundary and property-style tests.

### ALG-005 — Make detector names and math truthful

- Status: done
- Auto-eligible: yes
- Depends on: ALG-004
- Scope: rename the current output detector to lexical similarity or implement genuine documented TF-IDF/embedding semantics. Report measured similarity rather than the configured threshold as confidence. Define empty-output and retry behavior. Correct cost-velocity window math.
- Acceptance: names and docs reflect algorithms; result details include measured values and sample/window size; synthetic positive and negative cases pass.
- Verification: detector fixtures including legitimate retry sequences and timestamp boundaries.

### ALG-006 — Add release-quality CI gates

- Status: done
- Auto-eligible: yes
- Depends on: ALG-003, ALG-004, ALG-005
- Scope: GitHub Actions for Python 3.9–3.13, unit tests, coverage threshold, Ruff, MyPy, package build, wheel install/import smoke test, and README snippet tests.
- Acceptance: all configured Python versions pass; artifacts install into a clean environment; branch protection can require the workflow.
- Verification: green CI run.

### ALG-007 — Bound memory and use monotonic time

- Status: done
- Auto-eligible: yes
- Depends on: ALG-002
- Scope: store only the maximum detector window unless full history is explicitly enabled; use a monotonic clock for elapsed time and injectable clocks for tests.
- Acceptance: default memory is bounded; wall-clock changes do not break duration checks; tests do not sleep.
- Verification: long-run memory/window tests and fake-clock tests.

### ALG-020 — Verify and enforce a clean CI/lint/type baseline

- Status: done
- Auto-eligible: yes
- Depends on: ALG-006
- Added 2026-07-23 (status review): ALG-006 wired up the CI gates, but the green state was not re-verified after the P0/P1 changes. The original audit reported 8 MyPy errors and 153 Ruff findings; these must be confirmed cleared so the "release-quality CI" claim is truthful.
- Scope: run `pytest` with the coverage threshold, `mypy src`, `ruff check .`, and a clean-environment wheel install + import smoke test; fix any remaining failures; capture raw output.
- Acceptance: all four checks pass on every configured Python version (3.9–3.13); zero MyPy errors and zero Ruff findings (or explicitly justified, minimal, documented ignores); wheel installs and imports in a clean env.
- Verification: green CI run with archived logs; results recorded in `BUILD_LOG.md`.

## P1 — useful, measurable developer product

### ALG-008 — Introduce a typed step and event schema

- Status: done
- Auto-eligible: yes
- Depends on: ALG-004, ALG-005
- Scope: typed input/result models with stable detector IDs, schema version, run/session ID, timestamps, measured values, and recommended action. Preserve a backwards-compatible dictionary adapter.
- Acceptance: events serialize predictably; public fields are documented; compatibility tests cover legacy dictionaries.
- Verification: schema snapshot and round-trip tests.

### ALG-009 — Add pricing-provider abstraction

- Status: ready
- Auto-eligible: no
- Depends on: ALG-008 (done), OWN-004 (done)
- Unblocked 2026-07-23: both dependencies are complete (ALG-008 done; OWN-004 pricing policy approved 2026-07-21). Dependency-based blocker cleared; auto-eligible remains `no` pending owner confirmation that implementing the approved policy needs no further pricing decision.
- Current-state note (verified 2026-07-23): `estimate_cost()` in `utils.py` returns `0.0` for any model outside the small hardcoded table, so unknown models fail **open** even when `max_cost_usd` is set — this violates the approved OWN-004 fail-closed policy and is the top open correctness gap.
- Scope: custom price provider, explicit unknown-model policy, versioned built-in snapshot with source date, user-supplied actual cost, and model alias matching without substring collisions.
- Acceptance: unknown models never silently appear free unless explicitly configured; price source and effective date are visible; custom/actual cost overrides work.
- Verification: pricing fixtures and alias tests.

### ALG-010 — Build the detector benchmark

- Status: done
- Auto-eligible: yes
- Depends on: ALG-005, ALG-008
- Scope: checked-in labeled traces for exact repeats, oscillations, lexical repeats, legitimate retries, progressive refinement, and non-looping tool sequences; benchmark script and report template.
- Acceptance: deterministic per-detector precision, recall, false-positive rate, and latency report; fixtures are anonymized/synthetic and reviewable.
- Verification: benchmark runs in CI with regression tolerances.

### ALG-011 — Publish measured performance evidence

- Status: ready
- Auto-eligible: no
- Depends on: ALG-007 (done), ALG-010 (done)
- Unblocked 2026-07-23: both dependencies are complete. Dependency-based blocker cleared; auto-eligible remains `no` because it requires documented hardware and owner-approved public claims. `benchmarks/report_template.md` is still blank and should be filled with measured precision/recall/FP-rate and p50/p95 latency.
- Scope: benchmark p50/p95 latency and memory across event sizes and enabled detectors on documented hardware; replace unsupported claims with results.
- Acceptance: reproducible command, raw output, environment details, and conservative README statements.
- Verification: independent rerun within an agreed tolerance.

### ALG-012 — Add OpenTelemetry-compatible emission

- Status: done
- Auto-eligible: yes
- Depends on: ALG-008
- Scope: optional event hook/exporter aligned with current GenAI conventions where applicable, without adding a required runtime dependency.
- Acceptance: structured guard events can be attached to a trace or exported through a documented callback; local-only use remains zero-dependency.
- Verification: exporter tests with no live backend.

### ALG-013 — Ship maintained framework adapters

- Status: blocked
- Auto-eligible: no
- Depends on: ALG-003, ALG-008, OWN-005
- Scope: select and implement the first two adapters based on user interviews; pin a supported-version matrix and run integration tests.
- Acceptance: two real end-to-end examples execute against current supported versions; unsupported behaviors are explicit.
- Verification: scheduled integration CI.

### ALG-014 — Improve developer documentation

- Status: done
- Auto-eligible: yes
- Depends on: ALG-001, ALG-003, ALG-008
- Scope: quickstart, concepts, configuration reference, custom detector guide, exception handling, concurrency/async behavior, limitations, migration policy, and troubleshooting.
- Acceptance: a new user can install and trigger a controlled detection in under five minutes using only documented commands.
- Verification: clean-environment docs walkthrough.

### ALG-015 — Establish security and release hygiene

- Status: blocked
- Auto-eligible: no
- Depends on: ALG-006, OWN-002, OWN-006
- Scope: `SECURITY.md`, contribution guide, code of conduct, changelog/release checklist, trusted publishing, provenance/attestations, dependency review, and secret scanning.
- Acceptance: documented disclosure route and repeatable tagged release with owner-approved credentials and controls.
- Verification: test release or dry run, then owner-approved production release.

### ALG-021 — Define and document duration-enforcement behavior

- Status: ready
- Auto-eligible: yes
- Depends on: ALG-007
- Added 2026-07-23 (status review): the duration limit is only checked when a step is recorded, so a hung tool or model call cannot be interrupted mid-call. This is a real behavioral limitation that must not be overstated.
- Scope: document the current limit prominently as an inter-step check (README limitations + docstrings); optionally design a cooperative cancellation/watchdog approach and record it as a follow-up item rather than implementing silently.
- Acceptance: README and API docs state the inter-step nature of the duration check explicitly; any watchdog work is scoped as a separate proposed item with an owner decision noted.
- Verification: docs walkthrough; test asserting a between-steps duration breach raises `DurationExceededError` while an in-step hang is documented as out of scope.

## P2 — growth experiments, not assumptions

### ALG-016 — Replace pricing cards with design-partner validation

- Status: blocked
- Auto-eligible: no
- Depends on: ALG-001, OWN-003
- Scope: waitlist/design-partner CTA, analytics with consent, concise use-case questions, and no promise of unavailable cloud functionality.
- Acceptance: CTA has a real destination, privacy disclosure, event definitions, and an owner-reviewed follow-up process.
- Verification: form and analytics test without collecting production data during automation.

### ALG-017 — Create launch assets

- Status: blocked
- Auto-eligible: no
- Depends on: ALG-010, ALG-011, ALG-014, OWN-007
- Scope: technical launch post, demo GIF/video, benchmark summary, incident simulator, social copy, and framework-community posts.
- Acceptance: every quantitative claim links to evidence; all links and commands are tested; owner approves publishing.
- Verification: preflight checklist and link checker.

### ALG-018 — Run customer discovery and decide the commercial product

- Status: blocked
- Auto-eligible: no
- Depends on: OWN-005
- Scope: synthesize interviews around centralized policy, team budgets, alerting, audit events, and hosted analytics; recommend build/no-build and packaging.
- Acceptance: at least ten relevant interviews, problem-frequency evidence, willingness-to-pay signals, and a written decision memo.
- Verification: owner reviews anonymized notes and decision.

### ALG-019 — Evaluate additional language SDKs

- Status: blocked
- Auto-eligible: no
- Depends on: ALG-010, ALG-018
- Scope: decide whether TypeScript demand justifies a second SDK after Python retention and integration signals exist.
- Acceptance: evidence-based language decision with maintenance cost and parity plan.
- Verification: owner-approved decision memo; no implementation before approval.

## Queue operating rules

1. One queue item per branch and pull request unless the item explicitly permits decomposition.
2. Change a status to `in-progress` before editing and add a `BUILD_LOG.md` start entry.
3. Never start a blocked item, skip dependencies, publish externally, spend money, handle secrets, or make product/legal/pricing decisions autonomously.
4. Preserve backwards compatibility unless the queue item explicitly authorizes a breaking change.
5. Tests and acceptance criteria are part of the task, not optional follow-up.
6. If scope expands materially, stop, record the blocker, and add a proposed queue item instead of silently broadening the task.
7. On completion, record commands and results in `BUILD_LOG.md`, update this file to `done`, and leave the work uncommitted unless the owner or execution environment explicitly authorizes commit/push/PR actions.
