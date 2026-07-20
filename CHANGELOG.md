# Changelog

All notable changes to AgentLoopGuard will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## v0.1.0 — 2026-07-21

### Added
- Core `LoopGuard` class with decorator and context manager interfaces
- Four detection engines: Exact Repeat, Semantic Similarity, Cost Velocity, Oscillation
- `BudgetTracker` with configurable limits for cost, tokens, iterations, and duration
- Warning callbacks at 50%, 75%, 90% of budget thresholds
- Built-in pricing table for OpenAI, Anthropic, and Google models
- Custom exceptions: `LoopDetectedError`, `BudgetExceededError`, `DurationExceededError`
- Usage examples for OpenAI, Anthropic, and LangChain integrations
- Landing page with animated terminal demo
- Prepaid credit pricing model (Starter $10, Pro $25, Team $50)
