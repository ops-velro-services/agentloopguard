# AgentLoopGuard — Status Review

Review date: 2026-07-23 · Reviewer: automated project review · Version: 0.1.0

## 1. Project overview

**Stated objective** (README, DESIGN.md, PROJECT_REVIEW.md): a lightweight, dependency-free
**local Python circuit breaker** that caps agent runs (iterations, tokens, time, cost) and
detects a small set of well-defined repetition patterns before an agent runs away and burns
API budget. It is deliberately positioned as complementary to observability — "stop a
known-bad execution pattern while it is happening," not a cloud monitoring platform.

**Intended output**: a source-available (PolyForm Noncommercial 1.0.0) PyPI package
(`agentloopguard-sdk`, import `agentloopguard`) with four detectors (Exact Repeat, Lexical
Similarity, Cost Velocity, Oscillation), context-manager + decorator interfaces, a typed
event schema, optional OpenTelemetry-compatible export, a detector benchmark, honest docs, a
dark-mode landing page, and release-quality CI.

The work is governed by three living documents: `PROJECT_REVIEW.md` (the original audit that
defined the problems), `BUILD_QUEUE.md` (prioritized engineering queue ALG-001…ALG-019), and
`OWNER_ACTIONS.md` (decisions only the owner can make, OWN-001…OWN-009).

## 2. Completed work vs. intended output

The original audit (`PROJECT_REVIEW.md`) found the MVP was a credible proof of concept whose
public claims did not match the implementation. Since then the P0 hardening queue has been
worked through. I verified the current source behavior directly (the SDK is dependency-free,
so it runs without installing anything):

| Original critical finding | Queue item | Verified state today |
|---|---|---|
| Budgets shared across sessions | ALG-002 | **Fixed** — two sessions from one guard are independent (2nd session `iterations == 1`). |
| Decorator drops positional args → false loops | ALG-003 | **Fixed** — `f(1); f(2); f(3)` does not false-positive. |
| `@guard.watch` syntax invalid / async unsupported | ALG-003 | **Fixed** — `@guard.watch()` documented; async result recorded after `await`. |
| `json.dumps` crashes on bytes/sets/objects | ALG-004 | **Fixed** — sets and bytes args record without crashing (safe fingerprint fallback). |
| "Semantic" detector is really lexical | ALG-005 | **Fixed** — renamed `LexicalSimilarityDetector`; confidence reports measured similarity; alias kept. |
| Unbounded history growth | ALG-007 | **Fixed** — bounded detector window by default; `full_history=True` opt-in; monotonic clock. |
| No typed schema / stable event IDs | ALG-008 | **Fixed** — `SCHEMA_VERSION=1`, `StepEvent`, stable `detector_id`s, `to_dict()`/`to_legacy_dict()`. |
| No OpenTelemetry story | ALG-012 | **Fixed** — dependency-free `TelemetryEvent` exporter fires `agentloopguard.step`/`.detection`. |
| No benchmark / evidence | ALG-010 | **Done** — benchmark runs; all 4 detectors show precision 1.0, recall 1.0, FP-rate 0 on synthetic fixtures. |
| Landing/README contradictions (install cmd, URLs, fake cloud/Slack/webhook/`max_repeats`) | ALG-001 | **Fixed** — landing page now uses `pip install agentloopguard-sdk`, one repo URL (`ops-velro-services`), no cloud/Slack/webhook/credits claims. |
| Ambiguous alert config | ALG-004 | **Fixed** — config validated at construction; `on_alert="callback"` requires a callable. |

Documentation (ALG-014) is thorough: README covers quickstart, concepts, custom detectors,
async/concurrency, migration, and troubleshooting. Distribution artifacts (`dist/*.whl`,
`*.tar.gz`) and CI config (`.github/workflows/quality.yml`) exist.

Completed queue items: **ALG-001 through ALG-008, ALG-010, ALG-012, ALG-014** plus owner
decisions **OWN-001, OWN-003, OWN-004, OWN-006**.

**Assessment: the core objective — a trustworthy, honest, local circuit-breaker SDK — is
substantially met.** The critical correctness bugs from the audit are resolved and verified.

## 3. Gaps against the objective

1. **Unknown-model cost fails *open*, not closed.** `estimate_cost()` (`utils.py:150`) returns
   `0.0` for any model not in a small hardcoded price table, even when `max_cost_usd` is set.
   I verified an unknown model with a $1 cap records `$0.00` and never triggers. This
   contradicts the owner-approved OWN-004 policy (unknown models must fail closed when a cost
   limit is configured) and silently disables cost protection for aliased/fine-tuned/misspelled
   IDs. This is the single most important open correctness gap. (Tracked as ALG-009, blocked.)
2. **Static price snapshot with no source/date.** The price table has no source URL, effective
   date, custom price-provider hook, or user-supplied actual-cost override — all required by
   OWN-004/ALG-009.
3. **Duration limit is inter-step only.** A hung tool/model call can't be interrupted; the
   check only runs on `record()`. Documented as such, but no watchdog exists.
4. **CI is unverified in this environment.** `pytest`, `mypy`, and `ruff` could not run here
   (no network to install them; sandbox is offline). The audit previously reported 10 passing
   tests but **8 mypy errors and 153 ruff findings** — I could not confirm those are now clean.
   The test suite has since grown (5 test files, ~760 test LOC) but the green-CI claim is
   unverified from here.
5. **All hardening work is uncommitted.** `git log` shows only 2 commits (MVP + a docs tweak).
   Every ALG-002…ALG-014 change sits in the working tree as modified/untracked files. Per
   queue rule 7 this is intentional (leave uncommitted until the owner authorizes), but it
   means none of the fixes are yet in version history or released.

## 4. Recommendations

**High priority**
- Resolve the unknown-model cost policy (ALG-009). At minimum, make cost fail closed when
  `max_cost_usd` is set and the model is unknown, with an explicit opt-in for zero-cost use.
  This is a safety property of the product's core promise, and the owner decision (OWN-004)
  already exists — it's implementation, not a pending decision.
- Run the CI gate for real and record results: `pytest` (+coverage), `mypy src`, `ruff check .`,
  and a clean-env wheel install/import smoke test. Confirm the earlier 8 mypy / 153 ruff
  findings are cleared before any promotion.
- Decide on committing the P0/P1 work. The fixes are verified-good; leaving them uncommitted
  risks loss and blocks a tagged release. This needs an explicit owner go-ahead per rule 7.

**Medium priority**
- Fill in `benchmarks/report_template.md` with the actual measured numbers (they're currently
  blank) so the evidence is captured, and unblock ALG-011 (publish p50/p95 latency + memory on
  documented hardware).
- Complete the owner actions that gate trust/launch: OWN-002 (verify PyPI/GitHub control +
  MFA + backup maintainer) and then ALG-015 (SECURITY.md, trusted publishing, branch
  protection).
- Document the duration-check limitation more prominently, or scope a cooperative
  watchdog/cancellation design.

**Lower priority / sequencing**
- Start OWN-005 (interview ≥10 agent developers) — it's the dependency blocking framework
  adapters (ALG-013), performance-evidence framing, and the commercial-product decision
  (ALG-018). It can run in parallel with engineering.
- Keep cloud/pricing/second-language-SDK (ALG-016/018/019) parked until interview evidence
  exists, as the audit recommends. Don't build ahead of demand.

## 5. Pending tasks (checklist)

Engineering — unblocked, can proceed now:
- [ ] ALG-009 — implement unknown-model fail-closed cost policy, price-provider hook,
      actual-cost override, snapshot source/date, exact-alias matching (owner policy OWN-004 done).
- [ ] Verify & green the CI gate (pytest/coverage/mypy/ruff/build smoke) and record output.
- [ ] Fill `benchmarks/report_template.md` with measured precision/recall/FP + latency.

Engineering — blocked on an owner action:
- [ ] ALG-011 — publish measured latency/memory evidence (needs ALG-010 ✓ + hardware sign-off).
- [ ] ALG-015 — security & release hygiene: SECURITY.md, trusted publishing, branch protection
      (blocked on OWN-002).
- [ ] ALG-013 — ship first two framework adapters (blocked on OWN-005 interviews).

Owner actions still open:
- [ ] OWN-002 — verify PyPI + GitHub admin control, enable MFA, name a backup maintainer.
- [ ] OWN-005 — recruit design partners; interview ≥10 users; pick top-2 adapter priorities.
- [ ] OWN-007 — verify/remove the "$400 surprise bill" story and all claims; build a claims register.
- [ ] OWN-008 — legal/privacy basics (name/trademark, license headers, third-party notices).
- [ ] OWN-009 — support & maintenance policy (response targets, supported versions, ownership).
- [ ] Decision: authorize committing/tagging the completed P0/P1 work (queue rule 7).

Growth — parked until evidence exists (per audit):
- [ ] ALG-016 (design-partner CTA), ALG-017 (launch assets), ALG-018 (commercial decision),
      ALG-019 (evaluate TypeScript SDK).

## Verification performed for this review
- Read DESIGN, README, PROJECT_REVIEW, BUILD_QUEUE, OWNER_ACTIONS, CHANGELOG, BUILD_LOG.
- Ran live behavior probes (session isolation, positional-arg dedup, async await, non-JSON
  args, unknown-model cost, schema version, telemetry export) — results in section 2/3.
- Ran the detector benchmark: 4 detectors, precision/recall 1.0, FP-rate 0 on fixtures.
- Inspected `utils.estimate_cost` and `budget.py` to confirm the unknown-model gap.
- Checked landing-page consistency and `git status`.
- **Could not run** pytest/mypy/ruff or a clean-env package build (sandbox has no network to
  install them) — flagged as an open verification item, not a pass.
