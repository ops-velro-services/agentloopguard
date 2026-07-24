# AgentLoopGuard Language & Multi-SDK Strategy

**Approved Date**: 2026-07-24  
**Author / Approver**: Owner (Mohammed Rizwan) & AgentLoopGuard Maintainers  
**Task Reference**: ALG-019  
**Status**: Approved Decision Memo  

---

## 1. Executive Summary & Strategic Decision

This document records the official evaluation and language strategy for expanding **AgentLoopGuard** beyond Python to additional programming ecosystems, specifically TypeScript/JavaScript (`agentloopguard-ts`).

### Strategic Recommendation: **Defer TypeScript SDK (Phase 1.5 Python-First Focus)**
- **Primary Decision**: **Defer** full development of a TypeScript SDK (`agentloopguard-ts`) until the core Python SDK (`agentloopguard-sdk`) reaches v1.0.0 stability, 500+ GitHub stars, and at least 15 verified community/user feature requests for JS/TS support.
- **Immediate Focus**: Prioritize Python ecosystem depth — specifically expanding framework adapters (CrewAI, AutoGen, LangGraph, LlamaIndex, Semantic Kernel) and solidifying local detector performance.
- **Rationale**: ~85% of active autonomous agent development (especially complex multi-turn tool-calling agents) currently takes place in Python. Splitting core engineering focus across dual SDKs at this stage would double maintenance burden, duplicate detector/schema sync work, and slow down Python feature velocity without proportional market gain.

---

## 2. Ecosystem & Market Landscape Analysis

| Metric / Dimension | Python Agent Ecosystem | TypeScript / JavaScript Agent Ecosystem |
| :--- | :--- | :--- |
| **Primary Orchestrators** | LangChain, CrewAI, AutoGen, LlamaIndex, Semantic Kernel | Vercel AI SDK, LangChain.js, AutoGen TS, LlamaIndex.TS |
| **Market Share (Est.)** | ~80–85% of enterprise & open-source agents | ~15–20% (primarily web frontends & Next.js API routes) |
| **Loop Vulnerability Risk** | High (multi-step autonomous loops, custom tool pipelines) | High (Vercel AI SDK tool loops, agentic UI chatbots) |
| **Primary Deployment** | Backend microservices, Async workers, Python CLIs | Serverless functions (Vercel, AWS Lambda), Node.js services |
| **Integration Pattern** | Decorators, event hooks, middleware handlers | Async wrappers, Vercel AI SDK `wrapLanguageModel` middleware |

---

## 3. Quantitative Activation Triggers for TypeScript SDK

Development of `agentloopguard-ts` will automatically trigger when **any two** of the following quantitative conditions are met:

1. **Community Demand**: $\ge 15$ distinct user issues/discussions requesting TypeScript / Node.js support on GitHub.
2. **Python SDK Adoption**: Python package (`agentloopguard-sdk`) reaches $\ge 1,000$ monthly PyPI downloads and $\ge 500$ GitHub stars.
3. **Framework Signals**: Widespread adoption of Vercel AI SDK v4+ tool-calling agents requiring explicit loop mitigation.
4. **Stable Spec**: Python SDK schema and detector interface remain stable for $\ge 60$ consecutive days post-v1.0 release without breaking schema revisions.

---

## 4. Feature Parity & Architecture Specification (For Future TS SDK)

When activation triggers are met, `agentloopguard-ts` must maintain **100% functional and mathematical parity** with the Python SDK:

### 4.1 Detector & Accounting Parity
- **Core Detectors**:
  - `ExactRepeatDetector`: SHA-256 step signature matching over normalized JSON inputs/outputs.
  - `LexicalSimilarityDetector`: SequenceMatcher / Levenshtein distance similarity reporting measured confidence.
  - `CostVelocityDetector`: Sliding window cost-per-time tracking using injectable monotonic clocks.
  - `OscillationDetector`: Alternating step state pattern matching ($A \rightarrow B \rightarrow A \rightarrow B$).
- **Session Accounting**:
  - `LoopGuard` configuration object remains immutable.
  - `SessionBudgetTracker` creates independent session instances tracking total tokens, USD cost, duration, and step counts.

### 4.2 Ecosystem Adapters (TypeScript)
- **Vercel AI SDK Middleware**: `wrapLanguageModel()` middleware interceptor for `ai` package.
- **LangChain.js Handler**: `BaseCallbackHandler` subclass overriding `handleModelStart` and `handleModelEnd`.
- **Async Interceptor**: Higher-order function / Promise wrapper (`withLoopGuard(fn, options)`).

### 4.3 Schema & Telemetry Standard
- Shared JSON Schema definitions for `StepEvent` and `GuardSummary`.
- Zero required runtime dependencies for core TS SDK; optional `@opentelemetry/api` integration.

---

## 5. Dual-SDK Maintenance Cost & Risk Analysis

| Cost Factor | Python Only (Current) | Dual-SDK (Python + TypeScript) | Mitigation Strategy |
| :--- | :--- | :--- | :--- |
| **Maintenance Burden** | 1.0x baseline | ~1.6x baseline | Shared JSON benchmark trace fixtures for cross-suite testing |
| **Pricing Snapshot Sync** | Single `pricing.py` update | Dual update (`pricing.py` & `pricing.ts`) | Generated canonical `pricing.json` compiled at build time |
| **CI / CD Pipeline** | Pytest, MyPy, Ruff | Pytest + Vitest/Jest, ESLint, TSDoc | Combined GitHub Actions workflow with shared matrix |
| **Release Coordination** | Single PyPI release | PyPI + npm synchronized semantic versioning | Automated release tagging via GitHub Workflows |

---

## 6. Action Plan & Roadmap Integration

1. **Immediate (P1/P2 Current Phase)**: Complete Python core release, publish release-quality CI gates, and launch Python framework adapters (CrewAI, AutoGen).
2. **Monitoring (Post-Launch)**: Track incoming GitHub Issues and Discussions under the "Language Requests" label.
3. **Trigger Review**: Re-evaluate activation criteria quarterly or upon reaching 500 Python stars.
