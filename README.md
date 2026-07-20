# 🛡️ AgentLoopGuard

**Detect and kill infinite AI agent loops before they burn your API budget.**

[![PyPI version](https://img.shields.io/pypi/v/agentloopguard-sdk.svg)](https://pypi.org/project/agentloopguard-sdk/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## The Problem

AI agents get stuck in loops. Your agent calls the same tool 50 times. Or it generates nearly identical outputs over and over. Or it oscillates between two states forever.

Meanwhile, your API bill climbs: $0.12... $1.50... $15.00... $47.00... **$412.00**.

You wake up to a surprise bill because your agent ran all night doing nothing useful.

## The Solution

```python
from agentloopguard import LoopGuard

guard = LoopGuard(
    max_iterations=50,
    max_cost_usd=10.00,
    max_duration_seconds=300,
)

with guard.session() as session:
    for step in my_agent.run():
        session.record({
            "tool_name": step.tool,
            "tool_args": step.args,
            "output": step.result,
            "model": "gpt-4o",
            "input_tokens": step.input_tokens,
            "output_tokens": step.output_tokens,
        })
        # LoopGuard watches every call.
        # Loops die. Your budget lives.
```

## Installation

```bash
pip install agentloopguard-sdk
```

## Four Detection Engines

| Engine | What It Catches | Default Threshold |
|--------|----------------|-------------------|
| **Exact Repeat** | Same tool call repeated consecutively | 3 repeats |
| **Semantic Similarity** | Near-identical outputs (TF-IDF cosine sim) | 92% similarity, 3 calls |
| **Cost Velocity** | Spending money too fast | $2/minute |
| **Oscillation** | A→B→A→B going nowhere | 3 cycles |

All four run automatically on every `session.record()` call. Zero configuration needed.

## Usage

### As a Context Manager

```python
from agentloopguard import LoopGuard

guard = LoopGuard(max_iterations=100, max_cost_usd=5.00)

with guard.session() as session:
    for i in range(200):  # Will be killed at iteration 100
        session.record({
            "tool_name": "search",
            "tool_args": {"query": "same thing"},
            "output": "same result",
            "model": "gpt-4o",
            "input_tokens": 100,
            "output_tokens": 50,
        })
```

### As a Decorator

```python
from agentloopguard import LoopGuard

guard = LoopGuard(max_cost_usd=10.00)

@guard.watch
def run_agent(prompt: str) -> str:
    # Your agent logic here
    ...
```

### Custom Alert Handling

```python
def my_alert_handler(detection_result):
    send_slack_notification(f"Loop detected: {detection_result.description}")

guard = LoopGuard(
    max_iterations=50,
    on_alert="callback",
    alert_callback=my_alert_handler,
)
```

### Budget Tracking Only

```python
from agentloopguard import BudgetTracker

tracker = BudgetTracker(max_cost_usd=20.00, max_tokens=1_000_000)

tracker.record(model="gpt-4o", input_tokens=500, output_tokens=200)
print(tracker.summary())
# {'total_cost_usd': 0.0055, 'total_tokens': 700, 'iterations': 1, ...}
```

## Supported Models

Built-in pricing for:
- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3.5-sonnet, claude-3-haiku, claude-3-opus
- **Google**: gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_iterations` | `int` | `None` | Maximum number of agent steps |
| `max_cost_usd` | `float` | `None` | Maximum total cost in USD |
| `max_tokens` | `int` | `None` | Maximum total tokens (input + output) |
| `max_duration_seconds` | `float` | `None` | Maximum wall-clock time |
| `on_alert` | `str` | `"raise"` | Action on detection: `"raise"`, `"log"`, `"callback"` |
| `alert_callback` | `callable` | `None` | Custom function called on detection |
| `detectors` | `list` | all four | Which detection engines to use |

## Performance

- **<1ms overhead** per `record()` call
- **Zero external dependencies** — stdlib only
- **Thread-safe** — works in async and multi-threaded agents
- **No network calls** — everything runs locally

## License

MIT — free forever. Use it in production. Use it in your startup. Use it everywhere.

## Links

- [GitHub](https://github.com/mohammedshaik/agentloopguard)
- [PyPI](https://pypi.org/project/agentloopguard/)
- [Changelog](CHANGELOG.md)

---

*Built by developers who got a $400 surprise API bill.*
