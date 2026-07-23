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

- Status: open
- Confirm admin access, enable multi-factor authentication, protect recovery methods, and identify at least one backup maintainer for the GitHub organization and PyPI project.
- Deliverable: owner confirmation that access and recovery are tested; do not store credentials in this repository.
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

- Status: open
- Interview at least ten Python agent developers or AI platform owners. Ask about real runaway incidents, current safeguards, tolerated false positives, runtime frameworks, alert destinations, procurement, and willingness to pay.
- Deliverable: anonymized evidence summary plus the top two framework-adapter priorities.
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

- Status: open
- Personally verify or remove the “$400 surprise bill” story and any customer, savings, speed, compatibility, or reliability claim. Approve public posts, community submissions, testimonials, and case studies before publication.
- Deliverable: claims register with evidence link, approver, and expiration/recheck date.
- Unblocks: ALG-017.

### OWN-008 — Review legal and privacy basics

- Status: open
- Confirm name/trademark risk, license headers, third-party notices, privacy disclosures for any analytics/waitlist, terms for a future hosted service, and whether professional counsel is needed.
- Deliverable: recorded owner decisions and any required policy pages.
- Unblocks: public data collection or paid service launch.

### OWN-009 — Establish support and maintenance capacity

- Status: open
- Set response targets, issue labels, release cadence, supported Python/framework versions, deprecation window, and who maintains model pricing and adapters.
- Deliverable: lightweight maintenance policy visible to contributors and users.
- Unblocks: production-readiness messaging.

## Suggested owner work order

1. OWN-001 and OWN-003 today; they directly affect truthful documentation.
2. OWN-002, OWN-004, and OWN-006 before the next release.
3. Start OWN-005 in parallel with P0 engineering.
4. Complete OWN-007 and OWN-008 before a coordinated launch or data-collection campaign.
5. Complete OWN-009 before promising production support.
