# Changelog

All notable changes to AgentLoopGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Security policy (`SECURITY.md`), contribution guidelines (`CONTRIBUTING.md`), and Contributor Covenant Code of Conduct (`CODE_OF_CONDUCT.md`) (ALG-015).
- Framework adapters for LangChain (`AgentLoopGuardCallbackHandler`) and LlamaIndex (`AgentLoopGuardEventHandler`) in `agentloopguard.adapters` (ALG-013).
- Populated benchmark results and performance evidence report in `benchmarks/report_template.md` (ALG-011).

## [0.1.0] - 2026-07-23

### Added
- Core `LoopGuard` with immutable configuration and session-local accounting (`GuardSession`) (ALG-002).
- Built-in detection algorithms: `ExactRepeatDetector`, `LexicalSimilarityDetector`, `CostVelocityDetector`, and `OscillationDetector` (ALG-005).
- Pricing provider abstraction (`PricingSnapshot`, `ModelRates`, `resolve_cost`) with fail-closed unknown model support (ALG-009).
- Bounded memory window option and monotonic clock for duration enforcement (ALG-007, ALG-021).
- Typed schema events (`StepEvent`, `TelemetryEvent`, `SCHEMA_VERSION`) (ALG-008).
- Release-quality CI matrix for Python 3.9–3.13 with 100% test coverage and zero MyPy/Ruff findings (ALG-006, ALG-020).
- OpenTelemetry exporter hook integration (ALG-012).
- Comprehensive benchmark runner and synthetic trace suite in `benchmarks/` (ALG-010).

### Changed
- Truthful documentation and identity alignment: package `agentloopguard-sdk`, module `agentloopguard`, source-available under PolyForm Noncommercial 1.0.0 (ALG-001, OWN-001, OWN-003).
