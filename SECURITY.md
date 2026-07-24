# Security Policy

`AgentLoopGuard` takes the security and reliability of AI agent control loops seriously. This document outlines our security policies, reporting guidelines, and release verification standards.

## Supported Versions

Only the latest release line of `AgentLoopGuard` receives security updates.

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1.0 | :x:                |

## Reporting a Vulnerability

> [!IMPORTANT]
> Please **do not report security vulnerabilities through public GitHub Issues or Pull Requests**.

If you discover a potential security flaw, logic bypass, or safety vulnerability in `AgentLoopGuard`, please report it privately:

- **Email Contact:** `shaikmohammedrizwanfaisal@gmail.com`
- **Response Commitment:**
  - **Acknowledgment:** Within **3 business days**.
  - **Initial Assessment & Update:** Within **7 calendar days**.

### Information to Include in Your Report

To help us assess and resolve the issue quickly, please include:
1. A descriptive title and summary of the issue.
2. Step-by-step instructions or proof-of-concept script to reproduce the vulnerability.
3. Affected `AgentLoopGuard` versions and environment configuration.
4. Any potential impact or risk assessment.

## Vulnerability Handling & Disclosure Policy

1. **Triage:** Upon receipt, maintainers (`Mohammed Rizwan` and `Mohammed Irfan`) will investigate and confirm the report.
2. **Fix Development:** A fix will be developed and verified in a private working environment.
3. **Release & Advisory:** A patch release will be published to PyPI via trusted publishing. Security advisories will be published alongside the release notes.
4. **Credit:** Reporters will be credited in `CHANGELOG.md` and release notes (unless anonymity is requested).

## Security & Release Hygiene

- **Release Approvers:** All tagged releases and package distributions require review and approval from two maintainers (`Mohammed Rizwan` and `Mohammed Irfan`), except for emergency patch releases.
- **Trusted Publishing:** PyPI distributions are built and uploaded exclusively via GitHub Actions OpenID Connect (OIDC) trusted publishing. No persistent long-lived PyPI tokens are stored in repository secrets.
- **Branch Protection:** The `main` branch requires code reviews, passing CI checks (unit tests, coverage, static typing, linting), and zero unreviewed force-pushes.
- **Dependency Hygiene:** Dependencies are kept minimal to reduce the attack surface. Core `AgentLoopGuard` functionality operates with zero external required dependencies.
