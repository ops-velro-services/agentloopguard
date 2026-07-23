# Changelog

All notable changes to AgentLoopGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

### Changed
- Future releases are source-available under PolyForm Noncommercial 1.0.0; previously released MIT versions retain their original terms.
- Removed unsupported cloud-service and prepaid-credit claims from public materials.

## v0.1.0 — 2026-07-21

### Added
- Core `LoopGuard` class with decorator and context manager interfaces
- Four detection engines: Exact Repeat, Lexical Similarity, Cost Velocity, Oscillation
- `BudgetTracker` with configurable limits for cost, tokens, iterations, and duration
- Custom exceptions: `LoopDetectedError`, `BudgetExceededError`, `DurationExceededError`
- Landing page with animated terminal demo
