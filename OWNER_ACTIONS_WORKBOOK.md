# Owner Action Workbook

This workbook prepares the open items in `OWNER_ACTIONS.md`. It is not a
policy, approval, confirmation, or authorization. An owner must review each
section, replace the proposed defaults where needed, and then explicitly record
the decision in `OWNER_ACTIONS.md` before a dependent build item can proceed.

## OWN-002 — Package and repository control

### Owner confirmation checklist

- [ ] Confirmed GitHub organization and repository administrator access.
- [ ] Confirmed PyPI project owner or maintainer access for
  `agentloopguard-sdk`.
- [ ] Enabled multi-factor authentication on every privileged GitHub and PyPI
  account.
- [ ] Stored recovery codes in an owner-controlled secure location outside this
  repository and tested the recovery path.
- [ ] Named at least one backup maintainer with the minimum required GitHub and
  PyPI access, and tested that access.
- [ ] Confirmed no credentials, recovery codes, or personal access tokens are
  stored in this repository or its issue tracker.

### Evidence to record (do not add secrets)

Record the confirmation date, roles tested, backup-maintainer role (not private
contact details), and where recovery materials are held. Do not record account
passwords, tokens, recovery codes, or screenshots containing them.

## OWN-005 — Design-partner research

### Interview plan

Recruit at least ten people who actively build Python agents or operate an AI
platform. Seek a mix of individual developers and platform owners; do not
collect unnecessary personal data or add anyone to a mailing list without
consent.

Use this neutral interview guide:

1. Tell me about the last agent workflow that repeated work, ran too long, or
   consumed more model budget than expected.
2. What safeguards do you use today, and where do they fail?
3. Which false positives would be unacceptable, and which would be tolerable?
4. Which Python agent frameworks and model SDKs are in production or planned?
5. Where would a useful alert or stop signal need to appear?
6. Who evaluates or approves developer tooling like this?
7. How important are local-only operation, audit events, and budget estimates?
8. What evidence would make you trust a loop detector?
9. What, if anything, would you be willing to pay for—and only after which
   capabilities exist?

### Anonymized evidence template

| Interview | Role segment | Observed problem | Current safeguard | False-positive tolerance | Frameworks | Preferred alert path | Purchase signal | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 01 | | | | | | | | |

After ten interviews, summarize recurring problems, disconfirming evidence,
and the two framework adapters with the strongest evidence. Do not claim that
an adapter is supported until its implementation and integration coverage land.

## OWN-006 — Security and release ownership

### Decision record

| Decision | Proposed starting point — not approved | Owner decision | Approved date |
| --- | --- | --- | --- |
| Private vulnerability-reporting channel | A dedicated, access-controlled email alias; do not use public GitHub Issues for embargoed reports. | | |
| Acknowledgement target | Acknowledge reports within 3 business days. | | |
| Initial assessment target | Provide a triage/update within 7 calendar days. | | |
| Release approval | Require two named maintainers, or one maintainer plus a documented emergency exception. | | |
| PyPI publishing | Use PyPI trusted publishing via GitHub Actions; never long-lived API tokens. | | |
| Tag/release authority | Restrict tags and GitHub Releases to named release approvers. | | |
| Main-branch protection | Require pull requests, one approving review, passing `quality` workflow, and no force-pushes/deletions. | | |
| Emergency process | Document the approver, exception reason, and follow-up review in the release notes or incident record. | | |

Before recording approval, confirm that the reporting channel and every named
approver actually exists and accepts the responsibility. ALG-015 can turn the
approved decisions into `SECURITY.md`, release controls, and CI configuration;
this workbook does not establish those controls.

## OWN-007 — Claims and publishing

### Claims register

Every public quantitative, customer, compatibility, savings, speed, or
reliability claim needs evidence, an approver, and a recheck date. Remove the
claim if evidence is unavailable or becomes stale. The current repository must
not restore the unverified “$400 surprise bill” story.

| Claim text | Surface | Evidence link or artifact | Owner approver | Approved date | Recheck date | Status |
| --- | --- | --- | --- | --- | --- | --- |
| | | | | | | Draft |

For a launch post, community submission, testimonial, or case study, add a row
before publication. Approval of one claim does not approve future posts or
different wording.

## OWN-008 — Legal and privacy basics

### Owner checklist

- [ ] Reviewed name and trademark risk for “AgentLoopGuard” in intended
  jurisdictions and recorded whether professional counsel is required.
- [ ] Confirmed the repository license is the intended PolyForm Noncommercial
  1.0.0 license and identified any files that need license headers.
- [ ] Reviewed direct and transitive third-party notices required for a release.
- [ ] Confirmed that the current local SDK does not collect product analytics,
  waitlist information, or other user contact data.
- [ ] Before any future data collection, approved a privacy notice, consent
  flow, data-retention period, access controls, and deletion process.
- [ ] Before any hosted or paid service, approved terms, support commitments,
  incident handling, data processing, and whether legal counsel is needed.

### Decision record

| Topic | Owner decision | Evidence/reference | Decision date | Revisit by |
| --- | --- | --- | --- | --- |
| Trademark/name | | | | |
| License/headers | | | | |
| Third-party notices | | | | |
| Current data collection | None approved | Current local-SDK scope | | |
| Future analytics/waitlist | | | | |
| Future hosted service | | | | |
| Counsel | | | | |

## OWN-009 — Support and maintenance capacity

### Decision record

| Area | Proposed starting point — not approved | Owner decision | Approved date |
| --- | --- | --- | --- |
| Supported Python versions | Python 3.9 through 3.13, matching the current CI matrix. | | |
| Supported integrations | No framework adapter is supported until OWN-005 evidence and ALG-013 integration tests exist. | | |
| Issue labels | `bug`, `security`, `documentation`, `question`, `good first issue`, `needs reproduction`, `wontfix`. | | |
| Public issue response target | Best effort only; do not promise production support until capacity is approved. | | |
| Release cadence | Release when reviewed fixes/features are ready; no fixed schedule promised. | | |
| Deprecation window | Announce a deprecation in a minor release and retain it for at least one subsequent minor release when feasible. | | |
| Pricing snapshot owner | A named maintainer updates snapshots only in a reviewed release, as approved in OWN-004. | | |
| Adapter owner | A named maintainer owns each supported adapter and its integration CI. | | |

Once approved, turn this into a concise public maintenance policy. Do not imply
service levels, framework support, or commercial support that the owner has not
explicitly approved.

## Recording approvals

For each completed action, update its `Status` and decision text in
`OWNER_ACTIONS.md`, include the approval date and non-sensitive evidence, and
append an owner entry to `BUILD_LOG.md`. Keep unapproved rows open. This
workbook is an aid to that review, not evidence that any owner action occurred.
