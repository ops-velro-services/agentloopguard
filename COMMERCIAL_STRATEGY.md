# AgentLoopGuard Commercial & Product Strategy

**Approved Date**: 2026-07-24  
**Author / Approver**: Owner (Mohammed Rizwan) & AgentLoopGuard Maintainers  
**Status**: Approved Decision Memo  

---

## 1. Executive Summary

This document records the official commercial strategy and product roadmap decision for **AgentLoopGuard** (ALG-018). Following initial alpha releases and user feedback synthesis, AgentLoopGuard will follow a **developer-first, open-core product strategy**.

---

## 2. Product Roadmap & Strategic Choices

### Decision 1: Core SDK Licensing — Open Source Transition (Completed in ALG-025)
- **Decision**: Re-licensed the local Python SDK (`agentloopguard`) to **MIT / Apache 2.0 dual-license** (transitioned from PolyForm Noncommercial 1.0.0).
- **Rationale**: Maximizes developer adoption, community trust, and frictionless integration into commercial agent platforms and open-source frameworks. Zero telemetry and 100% local operation will remain core promises of the SDK.

### Decision 2: Near-Term Engineering Priority — Framework Adapter Expansion
- **Decision**: Prioritize expanding local framework adapters (e.g., CrewAI, AutoGen, Semantic Kernel, LangGraph) before commencing Phase 2 Cloud SaaS infrastructure.
- **Rationale**: Deep integration across the primary Python agent ecosystems drives user retention and establishes AgentLoopGuard as the universal standard for loop prevention across all major agent orchestrators.

### Decision 3: Commercial Tiering & Monetization Model
- **Decision**: Approved 2-tier commercial structure:
  - **Tier 1: Free Open Source Core (SDK)**: Full local detection capabilities (exact repeat, lexical similarity, cost velocity, oscillation, duration checks, OTel exporter, framework adapters).
  - **Tier 2: AgentLoopGuard Control Plane (Paid Cloud / Enterprise SaaS)**:
    - Centralized policy enforcement (dynamic rule updates without redeploying code).
    - Aggregated multi-agent team budget caps & FinOps controls.
    - Managed webhook alerts (Slack, PagerDuty, Datadog).
    - Immutable audit vault & compliance logs.
    - Hosted analytics dashboard & false-positive monitoring.

---

## 3. Immediate Action Items & Follow-ups

1. **ALG-019 Evaluation**: Evaluate TypeScript / JavaScript SDK demand based on framework adoption signals (CrewAI, AutoGen, LangChain JS).
2. **Framework Adapters (Phase 1.5)**: Track requests for CrewAI and AutoGen adapters in upcoming build cycles.
3. **Public Announcement**: Include licensing updates and ecosystem adapter plans in the public launch documentation.

---
