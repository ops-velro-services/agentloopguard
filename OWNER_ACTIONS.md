# AgentLoopGuard Owner Actions

These actions require authority, credentials, business judgment, personal verification, or external communication. Automated build runs must not complete them on the owner's behalf.

Preparation workbook: see [`OWNER_ACTIONS_WORKBOOK.md`](OWNER_ACTIONS_WORKBOOK.md).
It contains non-binding checklists and proposed defaults; it does not change an
action's status or record an owner decision.

## Immediate — before public promotion

### OWN-001 — Choose canonical identity and URLs

- Status: done
- Approved 2026-07-21: canonical repository is `https://github.com/ops-velro-services/agentloopguard`; PyPI distribution is `agentloopguard-sdk`; Python import name is `agentloopguard`; documentation is the repository README; issues are the repository Issues tracker; no project domain is approved yet; public support contact is `shaikmohammedrizwanfaisal@gmail.com`.
- Prior conflict: the git remote is `ops-velro-services/agentloopguard`, while repository files point to other GitHub owners; the package is `agentloopguard-sdk`, while the landing page tells users to install `agentloopguard`.
- Deliverable: approved identity map recorded above. Apply it consistently in ALG-001.
- Unblocks: ALG-001.

### OWN-002 — Verify package and repository control

- Status: done
- Approved 2026-07-23: verified admin access for GitHub organization `ops-velro-services` and PyPI project `agentloopguard-sdk`. MFA enabled on maintainer accounts; recovery credentials held securely outside this repository. Primary maintainer: Mohammed Rizwan; backup maintainer/release approver: Mohammed Irfan. Zero credentials or tokens stored in repository.
- Deliverable: owner confirmation recorded.
- Unblocks: ALG-015.

### OWN-003 — Decide what to say about cloud and pricing

- Status: done
- Approved 2026-07-21: remove all cloud, credits, pricing, and paid-service claims until a service, economics, terms, support plan, and owner-approved CTA destination exist. Position the shipped product only as a local Python SDK source-available under PolyForm Noncommercial 1.0.0. Do not add a waitlist or collect contact data at this stage.
- Claim boundary: use factual wording such as “local Python SDK, source-available under PolyForm Noncommercial 1.0.0”; do not imply that commercial use is permitted, or that a future cloud service, pricing, dashboard, alerts, team feature, or third-party model-price estimate is available or guaranteed.
- Deliverable: approved landing-page offer is the local source-available SDK; its CTA must point only to a real installation or repository destination.
- Unblocks: ALG-001, ALG-016.

### OWN-004 — Approve pricing-data policy

- Status: done
- Approved 2026-07-21: resolve a step's cost source in this order: user-reported actual cost, then a user-supplied price provider, then the versioned built-in price snapshot. The effective source and snapshot version/effective date must be observable in the resulting event or summary.
- Unknown model policy: when a cost limit is configured, unknown model IDs fail closed rather than silently recording zero cost. A caller may explicitly opt into zero-cost treatment only for non-cost-tracking use cases.
- Snapshot maintenance: each built-in rate snapshot must record its source URL and effective date; maintainers update it only through a reviewed release.
- Aliases: normalize model IDs and match exact aliases only; do not use substring matching.
- Deliverable: policy approved. Implement in ALG-009 with custom/actual-cost overrides, source metadata, and pricing fixtures.
- Unblocks: ALG-009.

### OWN-005 — Recruit design partners and interview users

- Status: done
- Approved 2026-07-23: owner decided not to conduct pre-release structured user interviews; feedback will be captured directly from live organic SDK users upon release. Framework adapter development (ALG-013) will be prioritized based on live incoming issues and user requests.
- Deliverable: strategy decided and recorded above.
- Unblocks: ALG-013, ALG-018.

## Trust and launch

### OWN-006 — Set security and release ownership

- Status: done
- Approved 2026-07-21: use a dedicated access-controlled private reporting channel (not public Issues); acknowledge reports within 3 business days and provide an initial assessment or update within 7 calendar days. Require two release approvers, except for a documented emergency exception. Use PyPI trusted publishing rather than long-lived API tokens; restrict tags and GitHub Releases to release approvers; and protect the main branch with pull requests, one approving review, a passing `quality` workflow, and no force-pushes or deletions.
- Approved reporting channel: `shaikmohammedrizwanfaisal@gmail.com`; security reports are submitted privately by email, not through public Issues.
- Approved normal-release approvers: Mohammed Rizwan and Mohammed Irfan.
- Completion 2026-07-21: the reporting channel and two normal-release approvers are now recorded. Repository protections and trusted-publishing setup remain implementation work within ALG-015; no external configuration was changed by this owner decision.
- Choose the private vulnerability-reporting channel, response expectations, release approvers, signing/trusted-publishing policy, and branch-protection rules.
- Deliverable: owner-approved security and release policy.
- Unblocks: ALG-015.

### OWN-007 — Approve claims and publishing

- Status: done
- Approved 2026-07-23: approved claims register. All unverified marketing claims (including the "$400 surprise bill" story) are excluded. The product is positioned strictly as a local Python SDK source-available under PolyForm Noncommercial 1.0.0. No external launch posts, blog posts, community submissions, or marketing campaigns are approved without explicit prior review.
- Deliverable: approved claim boundary recorded.
- Unblocks: ALG-017.

### OWN-008 — Review legal and privacy basics

- Status: done
- Approved 2026-07-23: confirmed PolyForm Noncommercial 1.0.0 license for the repository and future SDK distributions. The current local SDK collects zero product analytics, telemetry, waitlist info, or personal user data. Trademark risk for "AgentLoopGuard" accepted for local SDK alpha; no external legal counsel required at this stage.
- Deliverable: recorded owner decisions above.
- Unblocks: public data collection or paid service launch.

### OWN-009 — Establish support and maintenance capacity

- Status: done
- Approved 2026-07-23: approved maintenance policy. Supported Python versions: 3.9 through 3.13. Public issues answered on a best-effort basis. Releases published on-demand when reviewed fixes/features land. Model pricing snapshots and framework adapters maintained by Mohammed Rizwan and Mohammed Irfan via reviewed releases.
- Deliverable: lightweight maintenance policy approved.
- Unblocks: production-readiness messaging.

### OWN-010 — Approve duration-enforcement watchdog architecture

- Status: done
- Approved 2026-07-24: owner approved Option B (opt-in cooperative watchdog timer / cancellation thread pattern for preemptive in-step duration enforcement). In-step cancellation will be designed as an opt-in watchdog without altering the default zero-side-effect inter-step duration check.
- Deliverable: recorded architecture approval.
- Unblocks: ALG-022.

## Suggested owner work order

1. OWN-001 and OWN-003 today; they directly affect truthful documentation.
2. OWN-002, OWN-004, and OWN-006 before the next release.
3. Start OWN-005 in parallel with P0 engineering.
4. Complete OWN-007 and OWN-008 before a coordinated launch or data-collection campaign.
5. Complete OWN-009 before promising production support.
