# Contributing to AgentLoopGuard

Thank you for your interest in contributing to `AgentLoopGuard`! We welcome contributions that improve guard reliability, performance, detector accuracy, documentation, and framework integrations.

## Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please report any unacceptable behavior to `shaikmohammedrizwanfaisal@gmail.com`.

## Getting Started

### Prerequisites

- Python 3.9 through 3.13 supported.
- `pip` or `uv` for dependency management.

### Development Environment Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ops-velro-services/agentloopguard.git
   cd agentloopguard
   ```

2. **Create a virtual environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow & Quality Gates

Before submitting a Pull Request, verify that all quality gates pass locally:

### 1. Run Unit Tests & Coverage
```bash
pytest --cov=agentloopguard --cov-report=term-missing
```
All tests must pass, and test coverage must meet the required threshold (100% on core logic).

### 2. Static Type Checking
```bash
mypy src
```
Zero type errors are allowed.

### 3. Code Formatting & Linting
```bash
ruff check .
ruff format --check .
```
Fix lint or formatting issues automatically:
```bash
ruff check --fix .
ruff format .
```

### 4. Detector Benchmark Regression Test
```bash
python3 benchmarks/run_detector_benchmark.py
```
Benchmark classification accuracy must remain at 100% precision and recall on synthetic benchmark traces.

## Pull Request Process

1. **Branch Naming:** Use descriptive branch names like `feature/add-detector-name` or `fix/budget-reset`.
2. **Atomic Commits:** Keep commits logical, atomic, and well-described.
3. **Tests:** Include unit tests for every new feature or bug fix.
4. **Documentation:** Update README, docstrings, or docs whenever public interfaces or configurations change.
5. **Review:** Ensure CI checks pass green before requesting review.

## License

By contributing to `AgentLoopGuard`, you agree that your contributions will be licensed under the project's dual [MIT License](LICENSE) or [Apache License 2.0](LICENSE).
