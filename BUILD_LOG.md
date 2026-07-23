# AgentLoopGuard Build Log

This append-only log tracks material build and review activity. Newest entries go first. Do not rewrite older entries except to correct a factual error, and label corrections.

## 2026-07-23 19:40 IST — OWNER ACTION — authorize commit of P0/P1 build baseline

- Actor: owner
- Status change: working tree uncommitted -> committed baseline
- Scope completed: owner authorized commit of all completed P0/P1 hardening items (ALG-001 through ALG-010, ALG-012, ALG-014, ALG-020, ALG-021, and ALG-009).
- Files changed: repository-wide commit.
- Verification: 76 unit tests passing with 91.86% coverage, 0 MyPy errors, 0 Ruff findings, clean wheel build (`agentloopguard_sdk-0.1.0-py3-none-any.whl`).
- Decisions: commit verified P0/P1 baseline into git main branch; do not push to remote or publish without separate authorization.
- Risks/follow-ups: none.
- Blocker/owner input: owner authorization recorded.
- Commit/PR: main branch commit.

## 2026-07-23 19:37 IST — ALG-009 — add pricing-provider abstraction

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: implemented custom price provider support (callable or dict), fail-closed unknown model policy (`UnknownModelError` when cost limit is active), versioned built-in pricing snapshot with source URL and effective date (`2026.01` / `2026-01-01`), user-supplied actual cost override (`actual_cost_usd`), exact model alias matching with zero substring collisions, observable pricing metadata (`cost_source`, `pricing_snapshot_version`, `pricing_effective_date`), and 10 unit tests in `tests/test_pricing.py`.
- Files changed: `src/agentloopguard/pricing.py`, `src/agentloopguard/exceptions.py`, `src/agentloopguard/utils.py`, `src/agentloopguard/budget.py`, `src/agentloopguard/guard.py`, `src/agentloopguard/schema.py`, `src/agentloopguard/__init__.py`, `tests/test_pricing.py`, `tests/test_guard.py`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 76 passed, 91.86% coverage; `python3 -m mypy src` -> 0 errors across 8 files; `python3 -m ruff check .` -> 0 findings; `python3 -m ruff format --check .` -> 17 files formatted; `python3 -m build --wheel --no-isolation --outdir ./dist` -> `agentloopguard_sdk-0.1.0-py3-none-any.whl`.
- Decisions: pricing resolution follows strict priority order: actual cost -> price provider -> built-in snapshot; unknown models fail closed with `UnknownModelError` when a cost limit is set (unless `unknown_model_policy="zero"` is explicitly set); alias matching requires exact key or alias map lookup without partial substring matching; 0 token steps cost $0.00 (`zero_cost`).
- Risks/follow-ups: none. ALG-009 complete. Next eligible queue items: none auto-eligible remaining (ALG-011, ALG-013, ALG-015 require owner/hardware decisions).
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-23 19:10 IST — ALG-009 — add pricing-provider abstraction

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope: started; implementing pricing-provider abstraction, unknown-model fail-closed policy, versioned built-in snapshot with source date, user-supplied actual cost, and exact model alias matching without substring collisions.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: unknown models fail closed when a cost limit is set unless zero-cost is explicitly configured; price resolution order: actual cost -> price provider -> built-in snapshot.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-23 19:07 IST — OWNER ACTIONS — record owner decisions for OWN-002, OWN-005, OWN-007, OWN-008, OWN-009, and unblock queue items

- Actor: owner
- Status change: OWN-002 open -> done; OWN-005 open -> done; OWN-007 open -> done; OWN-008 open -> done; OWN-009 open -> done; ALG-009 auto-eligible no -> yes; ALG-013 blocked -> ready; ALG-015 blocked -> ready; ALG-016 blocked -> ready; ALG-018 blocked -> ready
- Scope completed: recorded owner decisions for package/repo control (OWN-002), live user feedback strategy (OWN-005), claims boundary (OWN-007), PolyForm Noncommercial 1.0.0 license & zero data collection (OWN-008), and maintenance policy (OWN-009). Confirmed auto-eligibility for ALG-009. Updated status of unblocked build queue items ALG-013, ALG-015, ALG-016, and ALG-018 to ready.
- Files changed: `OWNER_ACTIONS.md`, `OWNER_ACTIONS_WORKBOOK.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: verified git remote (`ops-velro-services/agentloopguard`), package metadata (`pyproject.toml`), and license (`LICENSE`). All queue dependencies reconciled against completed owner actions.
- Decisions: live user feedback replaces structured pre-release interviews for framework adapter prioritization. Marketing claims exclude all unverified stories. Local SDK alpha confirmed zero-telemetry and source-available under PolyForm Noncommercial 1.0.0. Maintenance policy covers Python 3.9–3.13 on a best-effort basis.
- Risks/follow-ups: ALG-009 is now ready and auto-eligible for the next build loop run to fix fail-open cost estimation for unknown models.
- Blocker/owner input: none remaining for current P0/P1 build items.
- Commit/PR: none.

## 2026-07-23 19:01 IST — ALG-021 — define and document duration-enforcement behavior

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: documented `max_duration_seconds` as an inter-step check in `LoopGuard` and `BudgetTracker` docstrings and README concepts/configuration sections; added tests in `tests/test_guard.py` verifying that between-steps duration breaches raise `DurationExceededError` and that in-step executions complete before `DurationExceededError` is raised on recording; added proposed follow-up queue item `ALG-022` for cooperative watchdog design.
- Files changed: `src/agentloopguard/budget.py`, `src/agentloopguard/guard.py`, `README.md`, `tests/test_guard.py`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 66 passed, 93.21% coverage; `python3 -m mypy src` -> 0 errors across 7 files; `python3 -m ruff check .` -> 0 findings; `python3 -m ruff format --check .` -> 15 files formatted; `python3 -m build --wheel --no-isolation` -> `agentloopguard_sdk-0.1.0-py3-none-any.whl`.
- Decisions: duration limit is defined and documented explicitly as an inter-step check on `record()`; in-step preemptive cancellation/watchdog is scoped as follow-up item ALG-022.
- Risks/follow-ups: ALG-022 added to queue for future preemptive duration architecture evaluation.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-23 18:56 IST — ALG-021 — define and document duration-enforcement behavior

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope: started; documenting inter-step duration limit behavior in docstrings and README limitations; adding test asserting between-steps duration breach and documenting in-step hang out-of-scope behavior; scoping cooperative watchdog as a proposed follow-up item.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: duration limit remains an inter-step check evaluated on `record()`; background thread/async watchdog cancellation is deferred to a separate proposed queue item.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-23 18:51 IST — ALG-020 — verify and enforce a clean CI/lint/type baseline

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: ran full quality verification suite: pytest with coverage threshold, mypy src, ruff check ., hatchling wheel build, and clean virtual environment wheel install + import smoke test. Verified zero MyPy errors, zero Ruff findings, 64 passing tests with 93.21% coverage (>=80%), and clean wheel import producing version 0.1.0.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 64 passed, 93.21% coverage; `python3 -m mypy src` -> 0 errors across 7 files; `python3 -m ruff check .` -> 0 findings; `python3 -m build --wheel --no-isolation --outdir ./dist` -> `agentloopguard_sdk-0.1.0-py3-none-any.whl`; clean virtualenv wheel install and import -> passed (`0.1.0`).
- Decisions: verified clean baseline state; no code modifications to `src/` or `tests/` were required as all checks passed cleanly.
- Risks/follow-ups: none.
- Blocker/owner input: none.
- Commit/PR: none (uncommitted changes left in working tree per policy).

## 2026-07-23 18:48 IST — ALG-020 — verify and enforce a clean CI/lint/type baseline

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope: started; running pytest with coverage threshold, mypy src, ruff check ., and clean wheel install/import smoke test; fixing any remaining failures; capturing results.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: none yet.
- Risks/follow-ups: none.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 20:25 IST — OWN-006 — complete security and release ownership

- Actor: owner
- Status change: open -> done
- Scope completed: named Mohammed Irfan as the second normal-release approver, joining Mohammed Rizwan; the approved private reporting channel and two-approver policy are now concretely recorded.
- Files changed: `OWNER_ACTIONS.md`, `BUILD_LOG.md`.
- Verification: verified that the policy record now contains one private reporting address and two release approvers. No account, repository setting, credential, trusted-publishing configuration, publishing, or external action was performed.
- Decisions: normal releases require Mohammed Rizwan and Mohammed Irfan unless the documented emergency exception is used.
- Risks/follow-ups: ALG-015 can implement the approved documentation and local configuration, but remains blocked by OWN-002. Repository protections and PyPI trusted publishing must be configured through the appropriate owner-controlled accounts when ALG-015 is ready.
- Blocker/owner input: none for OWN-006.
- Commit/PR: none.

## 2026-07-21 20:25 IST — OWN-006 — record reporting channel and first release approver

- Actor: owner
- Status change: open -> open (partial completion recorded)
- Scope completed: designated `shaikmohammedrizwanfaisal@gmail.com` as the private email reporting channel and Mohammed Rizwan as the first normal-release approver.
- Files changed: `OWNER_ACTIONS.md`, `BUILD_LOG.md`.
- Verification: recorded owner-provided non-secret contact and approver information only; no email alias, account, repository setting, credential, trusted-publishing configuration, or external action was created or changed.
- Decisions: security reports are received privately by email rather than public Issues. The previously approved two-approver rule remains unchanged.
- Risks/follow-ups: one additional normal-release approver is still required before OWN-006 becomes operational and can unblock ALG-015.
- Blocker/owner input: needs a second release-approver name or role.
- Commit/PR: none.

## 2026-07-21 13:08 IST — OWN-006 — approve security and release-policy direction

- Actor: owner
- Status change: open -> open (partial approval recorded)
- Scope completed: approved the proposed private-reporting, response-time, two-approver, PyPI trusted-publishing, tag/release, main-branch-protection, and emergency-exception policy directions from `OWNER_ACTIONS_WORKBOOK.md`.
- Files changed: `OWNER_ACTIONS.md`, `BUILD_LOG.md`.
- Verification: reviewed the approved workbook defaults; no account, repository setting, credential, publishing, or external action was performed.
- Decisions: reports use a dedicated access-controlled private channel rather than public Issues; acknowledgement target is 3 business days; initial-assessment target is 7 calendar days; normal releases require two approvers; trusted publishing replaces long-lived PyPI tokens; main requires a pull request, one approval, and passing `quality`, with force-pushes and deletion disabled.
- Risks/follow-ups: the actual private reporting channel and named release approvers are still unspecified and must be confirmed to make the policy operational. OWN-006 and ALG-015 remain blocked until then.
- Blocker/owner input: needs the reporting-channel address/alias and release-approver names or roles.
- Commit/PR: none.

## 2026-07-21 12:58 IST — OWN-004 — approve pricing-data policy

- Actor: owner
- Status change: open -> done
- Scope completed: approved ordered cost sourcing (actual cost, custom provider, then versioned built-in snapshot); exact alias matching; observable source/version/effective-date metadata; reviewed snapshot maintenance; and fail-closed handling for unknown model IDs whenever a cost limit is active. Explicit zero-cost treatment is permitted only for non-cost-tracking use cases.
- Files changed: `OWNER_ACTIONS.md`, `BUILD_LOG.md`.
- Verification: inspected the current estimator and confirmed it currently uses substring matching and silently returns zero for unknown models; ALG-009 acceptance criteria cover replacing both behaviors.
- Decisions: no provider pricing data or external lookup was added by this decision; implementation remains scoped to ALG-009.
- Risks/follow-ups: the existing estimator remains unsafe for unknown cost-limited models until ALG-009 is implemented.
- Blocker/owner input: owner approval recorded.
- Commit/PR: none.

## 2026-07-21 12:54 IST — ALG-014 — improve developer documentation

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: added an executable under-five-minute repeated-call quickstart; documented steps, sessions, detections, and budgets; clarified configuration validation and memory behavior; added a bounded custom-detector guide; documented alert exceptions, concurrent sessions, async decorators, schema/legacy migration, and practical troubleshooting.
- Files changed: `README.md`, `tests/test_guard.py`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py -q` -> 36 passed; `python3 -m pytest -q` -> 64 passed; `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m mypy src` -> passed; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-alg014` -> passed; clean temporary-environment wheel install/import -> passed; `git diff --check` -> passed.
- Decisions: kept guidance in the README because the approved documentation destination is the repository README; documented only shipped local-SDK behavior and retained the dictionary compatibility/migration path.
- Risks/follow-ups: no ready auto-eligible queue item remains; ALG-009, ALG-011, ALG-013, and ALG-015 remain blocked by their listed owner actions.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:XX IST — ALG-014 — improve developer documentation

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope: started; inspecting the shipped SDK and existing executable README coverage to add a factual quickstart, concepts, configuration, custom-detector, exception, concurrency, migration, and troubleshooting guidance.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: documentation will describe only the local SDK behavior implemented and tested in this repository.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:51 IST — ALG-001 — align the public contract

- Actor: interactive-agent
- Status change: in-progress -> done
- Scope completed: applied the confirmed canonical repository, distribution, import, support, and no-cloud offer. Replaced the MIT license with the owner-approved PolyForm Noncommercial 1.0.0 text and required copyright notice; updated package metadata and wheel licensing; rebuilt the README and landing page around verified local SDK behavior; removed cloud, credit, dashboard, paid-service, fabricated-cost, unsupported performance, and unsupported framework claims; corrected copied commands and public links; and added a test that executes every README Python snippet.
- Files changed: `LICENSE`, `pyproject.toml`, `README.md`, `landing/index.html`, `landing/script.js`, `CHANGELOG.md`, `tests/test_guard.py`, `OWNER_ACTIONS.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py -q` -> 35 passed; `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m mypy src` -> passed; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-alg001` -> passed; `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 63 passed, 93.21% coverage; clean temporary-environment wheel install/import -> passed; wheel inspection confirmed `licenses/LICENSE` and canonical project URLs; public-claim scan found no removed claim patterns; `git diff --check` -> passed.
- Decisions: future repository releases are source-available under PolyForm Noncommercial 1.0.0, while prior MIT releases retain their original terms; commercial use requires separate permission. The package’s MIT classifier was removed and the license metadata now carries `LICENSE`.
- Risks/follow-ups: PolyForm Noncommercial is not OSI-approved open source; validate contributor copyright ownership before releasing, and obtain legal advice for commercial-license terms or enforcement.
- Blocker/owner input: none.
- Commit/PR: none.

## Correction — 2026-07-21 12:51 IST — OWN-003 — decide what to say about cloud and pricing

- Actor: owner
- Correction: the approved license wording is PolyForm Noncommercial 1.0.0, not MIT. The no-cloud, no-pricing, and no-waitlist decision remains unchanged.
- Reason: owner later clarified that commercial use by others is not permitted and approved the PolyForm Noncommercial license for future releases.

## 2026-07-21 12:XX IST — ALG-001 — align the public contract

- Actor: interactive-agent
- Status change: blocked -> in-progress
- Scope completed: started after owner completion of OWN-001 and OWN-003. Replacing the MIT license with the owner-approved PolyForm Noncommercial license and aligning public identity, installation, and shipped-feature claims.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: previously released MIT versions retain their MIT terms; this repository's future releases will use PolyForm Noncommercial 1.0.0.
- Risks/follow-ups: this change makes the project source-available rather than OSI open source; contributors and downstream users must receive the new license terms.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:33 IST — OWN-003 — decide what to say about cloud and pricing

- Actor: owner
- Status change: open -> done
- Scope completed: approved removal of all cloud, credits, pricing, paid-service, and waitlist claims until an implemented service and owner-approved CTA exist. Approved the factual positioning “MIT-licensed local Python SDK.”
- Files changed: `OWNER_ACTIONS.md`, `BUILD_LOG.md`.
- Verification: checked that `LICENSE` contains the MIT license text and that the Open Source Initiative identifies the MIT license as SPDX identifier `MIT`.
- Decisions: the landing-page offer must be only the shipped local SDK and point to real installation/repository destinations. Do not promise a future service or collect contact data.
- Risks/follow-ups: ALG-001 must replace existing unsupported marketing, package, and link text consistently; ALG-016 remains blocked pending its other prerequisites and a real consent-aware CTA.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:33 IST — OWN-001 — choose canonical identity and URLs

- Actor: owner
- Status change: open -> done
- Scope completed: approved the canonical repository as `https://github.com/ops-velro-services/agentloopguard`, PyPI distribution as `agentloopguard-sdk`, import name as `agentloopguard`, README and repository Issues as the docs/support surfaces, no project domain for now, and `shaikmohammedrizwanfaisal@gmail.com` as the public support contact.
- Files changed: `OWNER_ACTIONS.md`, `BUILD_LOG.md`.
- Verification: compared against `git remote -v`, `pyproject.toml`, and README references.
- Decisions: ALG-001 must apply this map consistently; no publication, repository-setting, account, or package-registry change was made.
- Risks/follow-ups: OWN-003 remains required before ALG-001 can begin.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:33 IST — ALG-012 — add OpenTelemetry-compatible emission

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: added a zero-dependency `TelemetryEvent` and optional `event_exporter` callback. Each recorded step emits `agentloopguard.step`; each detection emits `agentloopguard.detection`. Both use fixed names and scalar, low-cardinality attributes appropriate for a trace/log adapter, while excluding tool arguments and model output. Exporter failures are contained and logged so observability cannot interrupt guarded work.
- Files changed: `src/agentloopguard/schema.py`, `src/agentloopguard/guard.py`, `src/agentloopguard/__init__.py`, `tests/test_guard.py`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py -q` -> 34 passed; `python3 -m ruff format --check src/agentloopguard/guard.py src/agentloopguard/schema.py src/agentloopguard/__init__.py tests/test_guard.py` -> passed; `python3 -m ruff check src/agentloopguard/guard.py src/agentloopguard/schema.py src/agentloopguard/__init__.py tests/test_guard.py` -> passed; `python3 -m mypy src` -> passed; `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 62 passed, 93.21% coverage; `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-alg012` -> passed; clean temporary-environment wheel install/import -> passed (`LoopGuard`, `TelemetryEvent`); `git diff --check` -> passed.
- Decisions: used documented, fixed, domain-qualified event names and did not introduce an OpenTelemetry dependency; event attributes omit potentially sensitive tool arguments and model outputs. OpenTelemetry’s current guidance favors named event occurrences with structured, flat attributes and supports trace/log adapters.
- Risks/follow-ups: no backend export is configured by default; applications choose and own their OpenTelemetry SDK/exporter configuration.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:XX IST — ALG-012 — add OpenTelemetry-compatible emission

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting the versioned event schema, guard record path, and current OpenTelemetry event conventions before adding an optional zero-dependency exporter hook.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: the integration will remain callback-based and will not import or require an OpenTelemetry package at runtime.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:11 IST — ALG-010 — build the detector benchmark

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: added seven checked-in, synthetic/anonymized labeled traces covering exact repeats, oscillations, lexical repeats, rapid cost growth, legitimate retries, progressive refinement, and non-looping tool sequences. Added a local/CI runnable benchmark that reports each built-in detector's precision, recall, false-positive rate, and p50/p95/mean check latency, plus a report template and strict fixture-metric regression test.
- Files changed: `benchmarks/fixtures/detector_traces.json`, `benchmarks/run_detector_benchmark.py`, `benchmarks/report_template.md`, `tests/test_benchmark.py`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_benchmark.py -q` -> 1 passed; `python3 benchmarks/run_detector_benchmark.py --json` -> all four detectors precision 1.000, recall 1.000, false-positive rate 0.000 across seven fixtures; `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 59 passed, 92.79% coverage; `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m mypy src` -> passed; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-alg010` -> passed; clean temporary-environment wheel install/import -> passed (`0.1.0`); `git diff --check` -> passed.
- Decisions: fixture classifications are deterministic and require perfect precision/recall with zero false positives; latency is reported as an observational local measurement and is not thresholded across hardware.
- Risks/follow-ups: benchmark results only cover the checked-in synthetic traces; real-world performance evidence remains ALG-011 and is blocked pending its dependencies.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:07 IST — ALG-010 — build the detector benchmark

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting detector behavior and repository test/package conventions before adding synthetic labeled traces, a deterministic benchmark runner, and regression coverage.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: benchmark data will be checked-in synthetic fixtures and run entirely locally.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:04 IST — ALG-008 — introduce a typed step and event schema

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: added versioned `StepEvent` and `DetectionResult` models. Recorded steps now include a schema version and session ID while retaining caller-defined fields and the legacy dictionary history; detections include stable detector IDs, measured values, recommended action, session context, and timestamp. Added `to_dict()` and `to_legacy_dict()` adapters, public exports, README reference, and schema snapshot/round-trip coverage.
- Files changed: `src/agentloopguard/schema.py`, `src/agentloopguard/detectors.py`, `src/agentloopguard/guard.py`, `src/agentloopguard/__init__.py`, `tests/test_guard.py`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py tests/test_detectors.py -q` -> 42 passed; `python3 -m pytest -q` -> 58 passed; `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m mypy src` -> passed; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-alg008` -> passed; clean temporary-environment wheel install/import -> passed (`0.1.0`, `DetectionResult`, `StepEvent`); `git diff --check` -> passed.
- Decisions: detector IDs are `exact_repeat`, `lexical_similarity`, `cost_velocity`, and `oscillation`; alerts recommend `stop`; a caller-provided `StepEvent` is normalized to the receiving session and recalculates cost from validated usage, so session accounting remains authoritative.
- Risks/follow-ups: the standard isolated `python3 -m build` remains network-dependent for `hatchling` in this sandbox, as previously recorded; CI installs build dependencies.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 12:00 IST — ALG-008 — introduce a typed step and event schema

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting step recording and detection-result compatibility before introducing stable event models.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: preserve the existing dictionary-facing APIs with explicit adapters.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:51 IST — ALG-007 — bound memory and use monotonic time

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: bounded session history to the largest configured detector window (the built-in cost-velocity detector caps its window at 1,000 events), added explicit `full_history=True` opt-in for unbounded custom-detector history, and made duration tracking monotonic with validated injectable clocks for deterministic tests.
- Files changed: `src/agentloopguard/budget.py`, `src/agentloopguard/detectors.py`, `src/agentloopguard/guard.py`, `tests/test_budget.py`, `tests/test_guard.py`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest -q` -> 56 passed; `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m mypy src` -> passed; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-alg007-final` -> passed; clean virtual-environment wheel install/import -> passed (`0.1.0`); `git diff --check` -> passed.
- Decisions: custom detectors without a finite `history_window` must explicitly request `full_history=True`; injected clocks must return finite numbers and backward values are clamped to zero elapsed time.
- Risks/follow-ups: the standard isolated `python3 -m build` remains network-dependent for `hatchling` in this sandbox, as previously recorded; CI installs dependencies before its isolated build.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:48 IST — ALG-007 — bound memory and use monotonic time

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting session-history retention and duration-clock behavior.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: pending implementation review.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## Correction — 2026-07-21 11:39 IST — ALG-006 — add release-quality CI gates

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting package/test configuration and preparing a local-only GitHub Actions quality workflow.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: branch-protection configuration and any external CI run remain owner/repository actions and will not be performed.
- Risks/follow-ups: existing repository-wide Ruff and MyPy findings must be resolved rather than bypassed for the required gates to be green.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:42 IST — ALG-006 — add release-quality CI gates

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: added a Python 3.9–3.13 GitHub Actions quality workflow with unit/README-snippet tests, an 80% coverage floor, Ruff, MyPy, isolated package build, and clean-wheel import smoke test. Fixed existing lint and strict-type findings so the configured gates pass locally.
- Files changed: `.github/workflows/quality.yml`, `src/agentloopguard/`, `tests/`, `examples/`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m ruff format --check .` -> passed; `python3 -m ruff check .` -> passed; `python3 -m mypy src` -> passed; `python3 -m pytest --cov=agentloopguard --cov-report=term-missing --cov-fail-under=80` -> 50 passed, 90.68% coverage; `python3 -m build --wheel --no-isolation --outdir /private/tmp/agentloopguard-ci-final` -> passed; clean virtual-environment wheel install/import -> passed; `git diff --check` -> passed. The standard isolated `python3 -m build` remains unable to download `hatchling` in this sandbox; CI installs dependencies before building.
- Decisions: configured local checks as required CI gates; did not change branch protection, run external CI, commit, push, open a PR, or publish.
- Risks/follow-ups: GitHub must run the new workflow before its matrix is independently confirmed green; branch-protection enforcement remains an owner/repository setting.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:37 IST — ALG-005 — make detector names and math truthful

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: renamed the default output detector to `LexicalSimilarityDetector` while retaining `SemanticSimilarityDetector` as an import-compatible alias; replaced the misleading TF-IDF claim with explicit token-frequency cosine similarity; results now report the minimum measured pair similarity, pair measurements, and sample size. Blank, non-string, and tokenless outputs break a lexical candidate window; cost velocity now uses an inclusive, event-timestamp five-minute window and reports its sample/window size.
- Files changed: `src/agentloopguard/detectors.py`, `src/agentloopguard/guard.py`, `src/agentloopguard/__init__.py`, `tests/test_detectors.py`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_detectors.py -q` -> 11 passed; `python3 -m pytest -q` -> 50 passed; `git diff --check` -> passed. `python3 -m ruff check .` -> 144 repository-wide findings; `python3 -m mypy src` -> 7 pre-existing strict-typing errors; `python3 -m build` -> blocked because isolated build dependency installation requires unavailable network access.
- Decisions: the algorithm is explicitly lexical rather than semantic; compatibility is maintained through the legacy import alias; simultaneous timestamps produce no cost-velocity decision because elapsed time is zero.
- Risks/follow-ups: repository-wide lint, strict typing, and offline package-build issues remain outside this item.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:30 IST — ALG-005 — make detector names and math truthful

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting output-similarity naming, reported confidence, empty/retry handling, and cost-velocity window boundaries.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: pending implementation review.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:28 IST — ALG-004 — validate configuration and input safely

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: validate finite positive budget limits, positive detector limits, similarity thresholds, alert modes/callback requirements, token counts, models, and timestamps at construction or record boundaries; copy each recorded step before adding defaults; normalize/fingerprint common non-JSON argument values with a safe type-and-`repr` fallback for unsupported objects and cycles.
- Files changed: `src/agentloopguard/budget.py`, `src/agentloopguard/detectors.py`, `src/agentloopguard/guard.py`, `src/agentloopguard/utils.py`, `tests/test_budget.py`, `tests/test_detectors.py`, `tests/test_guard.py`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py tests/test_budget.py tests/test_detectors.py -q` -> 47 passed; `python3 -m pytest -q` -> 47 passed; `git diff --check` -> passed. `python3 -m ruff check .` -> 153 pre-existing findings; `python3 -m mypy src` -> 7 pre-existing strict-typing errors; `python3 -m build` -> blocked because isolated build dependency installation requires unavailable network access.
- Decisions: zero and negative budgets/limits are rejected rather than treated as disabled; alerts support only `raise`, `log`, and `callback`, with a callable callback required for callback mode; invalid records are rejected before they change session history.
- Risks/follow-ups: lint, strict typing, and offline package-build issues remain repository-wide follow-up work.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:25 IST — ALG-004 — validate configuration and input safely

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting configuration validation, mutable input handling, timestamp/token validation, and call fingerprint fallbacks.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: pending implementation review.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:21 IST — ALG-003 — correct sync and async decorators

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: decorator call records now include positional and keyword arguments; asynchronous functions are awaited before recording their result; ordinary exceptions are recorded with type/message before re-raising; README decorator examples now use the exact invocation syntax and execute in tests.
- Files changed: `src/agentloopguard/guard.py`, `tests/test_guard.py`, `README.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py -q` -> 9 passed; `python3 -m pytest -q` -> 16 passed; `git diff --check` -> passed. `python3 -m ruff check .` -> 153 pre-existing findings; `python3 -m mypy src` -> 7 pre-existing strict-typing errors; `python3 -m build` -> blocked because isolated build dependency installation requires unavailable network access.
- Decisions: decorator histories remain persistent per decorated function; successful calls are recorded only after completion, and `Exception` subclasses are recorded before the original exception is re-raised.
- Risks/follow-ups: non-JSON argument fingerprinting remains for ALG-004; lint, strict typing, and offline package-build issues remain repository-wide follow-up work.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:17 IST — ALG-003 — correct sync and async decorators

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting decorator call fingerprints, async execution, exception behavior, and README invocation syntax.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: decorator sessions remain persistent per decorated function, as established by ALG-002.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:13 IST — ALG-002 — make budget state session-local

- Actor: scheduled-agent
- Status change: in-progress -> done
- Scope completed: moved mutable budget accounting from `LoopGuard` into each `GuardSession`; retained one explicit persistent session per decorated function; made the guard's budget limits a frozen configuration; added isolation and concurrent-session regression tests.
- Files changed: `src/agentloopguard/guard.py`, `tests/test_guard.py`, `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: `python3 -m pytest tests/test_guard.py -q` -> 5 passed; `python3 -m pytest -q` -> 12 passed; `git diff --check` -> passed. `python3 -m ruff check .` -> 153 pre-existing findings (same count as prior audit); `python3 -m mypy src` -> 7 pre-existing strict-typing errors; `python3 -m build` -> blocked because isolated build dependency installation requires unavailable network access.
- Decisions: `LoopGuard` no longer owns a mutable tracker; every call to `session()` constructs a fresh `BudgetTracker`, while `watch()` keeps one intentionally persistent decorated-function session.
- Risks/follow-ups: lint, strict typing, and offline package-build issues remain repository-wide follow-up work outside ALG-002.
- Blocker/owner input: none.
- Commit/PR: none.

## 2026-07-21 11:10 IST — ALG-002 — make budget state session-local

- Actor: scheduled-agent
- Status change: ready -> in-progress
- Scope completed: started; inspecting guard/session accounting and adding isolation coverage.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: pending.
- Decisions: each `GuardSession` will own its mutable budget tracker; decorated functions retain one explicit persistent session.
- Risks/follow-ups: none identified.
- Blocker/owner input: none.
- Commit/PR: none.

## Entry template

```text
## YYYY-MM-DD HH:MM TZ — ALG-NNN — short title

- Actor: owner | scheduled-agent | interactive-agent
- Status change: previous -> new
- Scope completed: concise list
- Files changed: paths
- Verification: exact commands and outcomes
- Decisions: choices made within authorized scope
- Risks/follow-ups: remaining issues
- Blocker/owner input: none or specific OWN-NNN
- Commit/PR: none or link/hash
```

## 2026-07-21 — REVIEW — repository and product audit

- Actor: interactive-agent
- Status change: not applicable
- Scope completed: reviewed product purpose, Python implementation, tests, examples, packaging metadata, landing page, repository links, public claims, market position, and release readiness; created prioritized queue, owner actions, and scheduler-loop prompt.
- Files changed: `PROJECT_REVIEW.md`, `BUILD_QUEUE.md`, `BUILD_LOG.md`, `OWNER_ACTIONS.md`, `SCHEDULER_LOOP_PROMPT.md`.
- Verification: `python3 -m pytest -q` -> 10 passed; `python3 -m mypy src` -> 8 errors; `python3 -m ruff check .` -> 153 findings; targeted probes reproduced cross-session budget leakage, positional-argument false positives, premature async recording, and a `TypeError` for repeated non-JSON arguments; isolated `python3 -m build` could not install build requirements because sandbox network access was unavailable.
- Decisions: recommend a local Python circuit-breaker wedge; defer cloud pricing and second-language SDK work until customer evidence exists.
- Risks/follow-ups: public claims and API examples are inconsistent; critical session, decorator, async, hashing, pricing, and memory behaviors need hardening.
- Blocker/owner input: see `OWNER_ACTIONS.md`.
- Commit/PR: none.

## 2026-07-23 — QUEUE UPDATE — reconcile statuses after status review

- Actor: interactive-agent
- Status change: ALG-009 blocked -> ready; ALG-011 blocked -> ready
- Scope completed: reviewed current source behavior and reconciled BUILD_QUEUE.md with completed dependencies. ALG-009 dependencies (ALG-008 done, OWN-004 approved) and ALG-011 dependencies (ALG-007 done, ALG-010 done) are all complete, so both moved from blocked to ready. Recorded verified fail-open cost behavior on ALG-009 and blank benchmark report on ALG-011. Auto-eligibility left `no` on both pending owner confirmation.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`, `STATUS_REVIEW_2026-07-23.md`.
- Verification: live SDK probes (session isolation, positional dedup, async await, non-JSON args, unknown-model cost=0.0, schema version, telemetry export); detector benchmark precision/recall 1.0, FP-rate 0; inspected `utils.estimate_cost` (returns 0.0 for unknown models). pytest/mypy/ruff/build not run — sandbox offline.
- Decisions: only dependency-based status changes made; no auto-eligibility, scope, or ownership decisions taken autonomously.
- Risks/follow-ups: ALG-009 fail-open cost is the top open correctness gap; CI green state unverified; all P0/P1 work remains uncommitted pending owner authorization.
- Blocker/owner input: confirm whether ALG-009/ALG-011 auto-eligibility can flip to `yes`; authorize commit of completed work.
- Commit/PR: none.

## 2026-07-23 — QUEUE UPDATE — add review-recommended items

- Actor: interactive-agent
- Status change: added ALG-020 (ready), ALG-021 (ready)
- Scope completed: added two new queue items from the 2026-07-23 status review that were not covered by existing items. ALG-020 (P0) verifies/enforces a clean CI/lint/type baseline after the P0/P1 changes (original audit had 8 MyPy + 153 Ruff findings). ALG-021 (P1) defines and documents inter-step duration-enforcement behavior and scopes any watchdog work as a follow-up. Benchmark-report fill and unknown-model fail-closed cost are already tracked under ALG-011 and ALG-009 respectively; commit-authorization and remaining owner items live in OWNER_ACTIONS.md.
- Files changed: `BUILD_QUEUE.md`, `BUILD_LOG.md`.
- Verification: not applicable (planning update); no code changed.
- Decisions: only added items and set them ready where dependencies are complete; no scope, pricing, or ownership decisions taken autonomously.
- Risks/follow-ups: ALG-020 may surface unresolved lint/type findings; ALG-009 fail-open cost remains the top correctness gap.
- Blocker/owner input: none for these additions.
- Commit/PR: none.
