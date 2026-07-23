# AgentLoopGuard Project Review

Review date: 2026-07-21

## Executive assessment

AgentLoopGuard addresses a real and understandable failure mode: autonomous agents can repeat actions, oscillate between states, or consume more time and money than intended. The strongest product wedge is **a local, framework-neutral circuit breaker for agent runs**. That is narrower, clearer, and more defensible than presenting the current alpha as a complete agent-safety or cloud-monitoring platform.

The repository is a credible proof of concept, not yet a production-ready release. The core is small, readable, dependency-free, and covered by ten passing unit tests. However, important public claims do not match the implementation, several common integrations behave incorrectly, and the release and landing-page surfaces disagree about install commands, APIs, repository ownership, and available commercial features.

Recommended release posture: keep the package at alpha, correct the public contract first, then harden the runtime and publish measurable detector-quality and overhead evidence before broader promotion.

## Intended purpose and product fit

### What the product should be

AgentLoopGuard should be the last-line, in-process circuit breaker between an agent runtime and runaway execution. Its job is to:

1. accept normalized agent-step events;
2. enforce deterministic limits for iterations, tokens, time, and known cost;
3. detect a small number of well-defined repetition patterns;
4. emit an actionable event and stop, log, or delegate the decision according to policy;
5. integrate with existing tracing systems rather than trying to replace them.

This is complementary to observability and content guardrails. Observability explains what happened; AgentLoopGuard should stop a known-bad execution pattern while it is happening. Content and authorization guardrails solve different risks.

### Best initial customer

The best initial user is a Python developer or small platform team running tool-using agents in batch jobs, background workers, CI, or internal automation, where an unbounded run has a direct cost or operational consequence. The initial buyer is likely a lead developer or AI platform engineer, not a general business user.

### Product promise to use now

> A lightweight Python circuit breaker that caps agent runs and detects repeated tool-call patterns before they run away.

Avoid claiming “semantic” detection, universal framework compatibility, async support, thread safety, sub-millisecond overhead, webhook/cloud features, or savings figures until each is implemented and evidenced.

## Accuracy and implementation review

### Critical findings

1. **Budgets are shared across sessions.** `LoopGuard` creates one `BudgetTracker`, while every `GuardSession` references it. A second session inherits the first session's iteration, cost, duration, and token totals. This contradicts the natural meaning of `guard.session()` and can stop unrelated runs. The same shared mutable tracker also makes the thread-safety claim unsafe.

2. **The decorator loses positional arguments.** `LoopGuard.watch()` records only `kwargs`; calls with different positional arguments hash as the same tool invocation. Three distinct calls can therefore be classified as an exact-repeat loop.

3. **The documented decorator form is invalid.** The README shows `@guard.watch` while the implementation requires `@guard.watch()` or `@guard.watch(model=...)`.

4. **Async functions are not supported correctly.** Decorating an async function records the coroutine object before it is awaited, so it neither observes the actual output nor detects failures correctly. The public “works in async” claim should be removed until an async-aware wrapper is tested.

5. **“Semantic similarity” is actually lexical cosine similarity.** The helper named `tfidf_vector` applies term frequency with a constant multiplier; it does not compute inverse document frequency and has no semantic model. The detector can be useful, but its name, documentation, confidence, and thresholds currently overstate its behavior.

6. **Exact-call hashing can crash on legitimate arguments.** `json.dumps()` fails on bytes, sets, paths, datetimes, custom objects, and many SDK request types. A guardrail should degrade predictably rather than become a new failure source.

7. **History grows without a bound.** Each session retains every step, although current detectors need only a limited window. Long-running processes can accumulate unnecessary memory.

8. **Alert configuration is ambiguous and not validated.** A callback runs whenever supplied, regardless of `on_alert`; `on_alert="callback"` with no callback silently does nothing; unsupported values also silently do nothing. The README mentions webhook handling that does not exist.

9. **Unknown models are priced at zero.** This silently disables cost protection for current, aliased, fine-tuned, or misspelled model IDs. Static prices also age quickly. Unknown-price behavior needs an explicit policy and users need a custom price-provider hook.

10. **Elapsed-time enforcement only happens when a step is recorded.** A hung tool or model call cannot be interrupted by the current duration check. Describe the current limit as an inter-step check, or add a cooperative cancellation/watchdog design.

### Public-surface inconsistencies

- Package metadata and README use `agentloopguard-sdk`; the landing page copies `pip install agentloopguard`.
- The landing page uses nonexistent `max_repeats` and `@guard.monitor` APIs.
- Metadata and README link to `github.com/mohammedshaik/agentloopguard`; the configured remote is `github.com/ops-velro-services/agentloopguard`; landing-page links point to another GitHub organization.
- The README PyPI badge targets `agentloopguard-sdk`, while its Links section targets `agentloopguard`.
- README says the default similarity threshold is 92%; the landing page says 95%.
- The landing page sells a cloud dashboard, cloud runs, email alerts, Slack integration, team budgets, and prepaid credits, none of which exist in this repository.
- The landing page says webhook is configurable; the SDK has log, raise, and Python callback paths only.
- “One-line SDK,” “zero configuration,” “framework-agnostic,” “thread-safe,” “works in async,” and “<1ms overhead” need precise scope or evidence.
- The origin remote is live, while the public links embedded in the product point elsewhere. Canonical ownership must be decided before promotion.

### Verification performed

- `python3 -m pytest -q`: **10 passed**.
- `python3 -m mypy src`: **8 errors**.
- `python3 -m ruff check .`: **153 findings** (many formatting/import issues, plus unused code and typing hygiene).
- Isolated package build: not verified because the sandbox could not download `hatchling`; add a CI build-and-install smoke test in a clean environment.
- PyPI JSON endpoint confirms `agentloopguard-sdk` exists; `agentloopguard` does not currently resolve as a PyPI project.
- The repository's configured origin is `ops-velro-services/agentloopguard`.

### What is already good

- The problem statement is easy to understand and has a strong “seatbelt” mental model.
- The implementation is intentionally small and has no runtime dependencies.
- Detector classes are modular and accept custom detector lists.
- Exceptions carry useful structured fields.
- A context manager and decorator are sensible integration primitives.
- The visual identity is coherent and developer-oriented.
- MIT licensing reduces adoption friction.

## Market assessment

### Positioning

Do not compete as another broad observability, evaluation, policy, or AI-safety suite. The sharper position is:

> **The local circuit breaker for runaway Python agents.** Deterministic budgets plus repeat-pattern detection, with no hosted dependency.

Differentiate on predictable enforcement, local operation, framework adapters, clear false-positive behavior, and portable event output. [OpenTelemetry has active generative-AI semantic conventions](https://opentelemetry.io/docs/specs/semconv/), so emitting compatible events is strategically better than inventing a closed telemetry system.

### Proof required before growth

Marketing should be built around reproducible proof:

- a public corpus of looping and non-looping agent traces;
- precision/recall and false-positive rates per detector and threshold;
- p50/p95 overhead and memory growth at multiple history sizes;
- known limitations, especially hung calls and unknown model pricing;
- copy-paste integrations that execute in CI against supported framework versions;
- one real case study with a verifiable before/after outcome.

### Go-to-market sequence

1. **Credibility:** align names, links, examples, claims, CI, packaging, and security policy.
2. **Developer adoption:** publish three excellent integration recipes (plain Python/OpenAI Agents, LangGraph/LangChain, and one additional high-demand runtime selected from interviews).
3. **Evidence:** release a loop-trace benchmark and a technical article explaining detection tradeoffs.
4. **Distribution:** launch to Python and agent-framework communities, submit framework integration examples, and invite trace fixtures as open-source contributions.
5. **Conversion discovery:** use an email waitlist or design-partner form for team policy, centralized analytics, and alerts. Do not publish paid tiers until the service and economics exist.

### Content and campaign ideas

- “Five ways production agents get stuck—and which circuit breaker catches each one.”
- A runnable incident simulator showing exact repeats, oscillation, and a legitimate retry sequence.
- A benchmark leaderboard for detector configurations.
- “Observability vs runtime enforcement” with OpenTelemetry export examples.
- Framework-specific guides and starter repositories.
- A lightweight “runaway-risk review” checklist that naturally leads to the SDK.

### Success measures

Track: successful installs, example completion rate, weekly active guarded runs (opt-in only), GitHub stars as a secondary measure, issues-to-resolution time, integration recipe traffic, design-partner interviews, benchmark fixture contributions, and false-positive reports. Do not use download count alone as product validation.

## Recommended decision

Proceed, but keep the scope disciplined. First make the local SDK trustworthy and measurable. Validate demand for shared policy and centralized event aggregation before building a paid cloud product. The build order and execution rules are maintained in `BUILD_QUEUE.md`; owner-only decisions are in `OWNER_ACTIONS.md`.
