# 🛡️ AgentLoopGuard

**Detect and kill infinite AI agent loops before they burn your API budget.**

[![PyPI version](https://img.shields.io/pypi/v/agentloopguard-sdk.svg)](https://pypi.org/project/agentloopguard-sdk/)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: PolyForm Noncommercial](https://img.shields.io/badge/License-PolyForm%20Noncommercial-orange.svg)](https://polyformproject.org/licenses/noncommercial/1.0.0)

---

## The Problem

AI agents get stuck in loops. Your agent calls the same tool 50 times. Or it generates nearly identical outputs over and over. Or it oscillates between two states forever.

Use it to enforce local iteration, token, duration, and cost limits while
detecting repeated calls and outputs.

## The Solution

```python
from agentloopguard import LoopGuard

guard = LoopGuard(
    max_iterations=50,
    max_cost_usd=10.00,
    max_duration_seconds=300,
)

with guard.session() as session:
    session.record({
        "tool_name": "search",
        "tool_args": {"query": "agent loops"},
        "output": "recorded result",
        "model": "unknown",
    })
```

## Installation

```bash
pip install agentloopguard-sdk
```

## Quickstart: stop a repeated tool call

Create a guard, record each agent step, and choose what should happen when a
detector fires. This example deliberately records the same call three times and
handles the resulting local exception.

```python
from agentloopguard import ExactRepeatDetector, LoopDetectedError, LoopGuard

guard = LoopGuard(
    detectors=[ExactRepeatDetector(n=3)],
    on_alert="raise",
)

try:
    with guard.session() as session:
        for _ in range(3):
            session.record({"tool_name": "search", "tool_args": {"query": "status"}})
except LoopDetectedError as error:
    assert error.loop_type == "ExactRepeatDetector"
```

Use one `LoopGuard` as immutable configuration. Call `guard.session()` for each
agent run; every session has independent budget, history, warnings, and
summary state.

## Four Detection Engines

| Engine | What It Catches | Default Threshold |
|--------|----------------|-------------------|
| **Exact Repeat** | Same tool call repeated consecutively | 3 repeats |
| **Lexical Similarity** | Near-identical non-empty outputs (token-overlap cosine similarity) | 92% similarity, 3 calls |
| **Cost Velocity** | Spending money too fast | $2/minute |
| **Oscillation** | A→B→A→B going nowhere | 3 cycles |

All four run automatically on every `session.record()` call. Zero configuration needed.

## Concepts

- A **step** is one mapping passed to `session.record()`. Common fields are
  `tool_name`, `tool_args`, `output`, `model`, `input_tokens`, and
  `output_tokens`.
- A **session** owns the mutable history, detector results, and budget totals
  for one run. Read `session.summary()` for a compact run summary.
- A **detection** is a `DetectionResult` added to `session.events`. It includes
  a stable `detector_id`, measured values, a recommended action, and the
  triggering session and timestamp.
- A **budget** is checked after every accepted step. The supported local limits
  are iterations, tokens, elapsed monotonic duration (checked inter-step), and the SDK's built-in
  cost estimate.

### Stable event schema

Every recorded session step is normalized into a versioned `StepEvent` and remains
available through the existing `session.call_history` dictionaries. Each detection
is a `DetectionResult` in `session.events` (and is passed to `alert_callback`).
The stable fields are `schema_version`, `session_id`, `timestamp`, `detector_id`,
`measured_values`, and `recommended_action`; detector IDs are `exact_repeat`,
`lexical_similarity`, `cost_velocity`, and `oscillation`. Use `result.to_dict()`
for the versioned schema or `result.to_legacy_dict()` for the prior four-field
dictionary shape.
The lexical detector compares the tokens actually present in each consecutive
output; it does not provide semantic or embedding-based similarity. Its reported
confidence is the lowest measured pair similarity in the matched sample. Empty
or non-string outputs break the sample window, which lets blank retry responses
pass without triggering a lexical-loop alert.

### Optional OpenTelemetry-compatible export

Pass `event_exporter` to receive `TelemetryEvent` objects without adding an
OpenTelemetry runtime dependency. The callback receives low-cardinality,
scalar attributes only (never tool arguments or model output) and two fixed
event names: `agentloopguard.step` and `agentloopguard.detection`. This makes
it suitable for an OpenTelemetry trace or log adapter while keeping local-only
use dependency-free.

```python
from agentloopguard import LoopGuard, TelemetryEvent

class CurrentSpan:
    def add_event(self, name, attributes):
        print(name, attributes)

current_span = CurrentSpan()

def export_to_current_span(event: TelemetryEvent) -> None:
    # Import OpenTelemetry in your application, not in agentloopguard.
    current_span.add_event(event.name, attributes=event.attributes)

guard = LoopGuard(event_exporter=export_to_current_span)
```

Exporter failures are logged and do not interrupt the guarded work. The event
timestamp is available as `event.timestamp` for adapters that accept it.

## Usage

### As a Context Manager

```python
from agentloopguard import LoopGuard

guard = LoopGuard(detectors=[])

with guard.session() as session:
    session.record({"tool_name": "search", "tool_args": {"query": "one result"}})
    assert session.summary()["budget"]["iterations"] == 1
```

### As a Decorator

```python
from agentloopguard import LoopGuard

guard = LoopGuard(max_cost_usd=10.00)

@guard.watch()
def run_agent(prompt: str) -> str:
    return f"handled: {prompt}"

assert run_agent("check status") == "handled: check status"
```

The decorator preserves the function's metadata and tracks both positional and
keyword arguments. For `async def` functions, it records the returned value
only after it has been awaited. Calls that raise are recorded with their
exception type and message, then the original exception is re-raised.
Arguments that are not JSON-native are fingerprinted using a normalized
representation where possible and otherwise a safe type-and-`repr` fallback;
they never prevent a call from being recorded.

```python
import asyncio
from agentloopguard import LoopGuard

guard = LoopGuard(detectors=[])

@guard.watch()
async def fetch_status() -> str:
    return "complete"

assert asyncio.run(fetch_status()) == "complete"
```

### Custom Alert Handling

```python
from agentloopguard import LoopGuard

alerts = []

def my_alert_handler(detection_result):
    alerts.append(detection_result.to_dict())

guard = LoopGuard(
    max_iterations=50,
    on_alert="callback",
    alert_callback=my_alert_handler,
)

with guard.session() as session:
    session.record({"tool_name": "search", "tool_args": {}})
```

### Budget Tracking Only

```python
from agentloopguard import BudgetTracker

tracker = BudgetTracker(max_tokens=1_000_000)

tracker.record(model="unknown", input_tokens=500, output_tokens=200)
print(tracker.summary())
# {'total_cost_usd': 0.0, 'total_tokens': 700, 'iterations': 1, ...}
```

## Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_iterations` | `int` | `None` | Maximum number of agent steps |
| `max_cost_usd` | `float` | `None` | Maximum total cost in USD |
| `max_tokens` | `int` | `None` | Maximum total tokens (input + output) |
| `max_duration_seconds` | `float` | `None` | Maximum elapsed time in seconds, measured with a monotonic clock (checked inter-step upon `record()`) |
| `on_alert` | `str` | `"raise"` | Action on detection: `"raise"`, `"log"`, `"callback"` (the latter requires a callback) |
| `alert_callback` | `callable` | `None` | Callable custom function called on detection |
| `event_exporter` | `callable` | `None` | Callable receiving dependency-free `TelemetryEvent` step/detection events |
| `detectors` | `list` | all four | Which detection engines to use |
| `full_history` | `bool` | `False` | Retain every recorded step instead of only the largest detector window |

Sessions retain only the recent steps their configured detectors need by default.
The built-in cost-velocity detector uses a bounded 1,000-event window; pass
`full_history=True` only when a custom detector explicitly needs all prior
steps. Duration limits use `time.monotonic()` by default. Tests or specialized
runtimes can provide a finite-number-returning `clock` callable to
`LoopGuard` or `BudgetTracker`.

Duration limits (`max_duration_seconds`) are evaluated inter-step upon `record()`.
If a tool call or model invocation hangs mid-step before returning, `LoopGuard` cannot
interrupt execution mid-call; `DurationExceededError` is raised on the subsequent
step recorded after the duration limit expires. Preemptive background watchdog
cancellation is out of scope for standard inter-step budget enforcement.

Configuration is validated when the guard is created. Limits must be positive,
token counts must be non-negative integers, timestamps must be finite numbers,
and `on_alert="callback"` requires a callable `alert_callback`. Input step
mappings are copied, so recording never adds fields to the caller's dictionary.

### Custom detectors

Implement `BaseDetector.check()` and give the detector a stable ID. A detector
that needs bounded history must expose a finite `history_window`; otherwise
construct the guard with `full_history=True` explicitly.

```python
from agentloopguard import LoopGuard
from agentloopguard.detectors import BaseDetector, DetectionResult

class MissingOutputDetector(BaseDetector):
    detector_id = "missing_output"
    history_window = 1

    def check(self, call_history):
        if call_history[-1].get("output") is None:
            return DetectionResult(
                detector_name="MissingOutputDetector",
                detector_id=self.detector_id,
                confidence=1.0,
                description="The latest step has no output.",
                pattern_details={},
                measured_values={"sample_size": 1},
                recommended_action="inspect",
            )
        return None

guard = LoopGuard(detectors=[MissingOutputDetector()], on_alert="log")
with guard.session() as session:
    session.record({"tool_name": "fetch", "tool_args": {}})
```

## Exceptions and alert modes

`on_alert="raise"` (the default) raises `LoopDetectedError` for a detector
match. Budget limits raise `BudgetExceededError`, and duration limits raise
`DurationExceededError`. Use `on_alert="log"` to keep working while writing a
warning, or `on_alert="callback"` to receive each `DetectionResult` yourself.
Callbacks run synchronously during `record()`, so keep them fast and avoid
raising from them unless you intend to interrupt the guarded work.

## Concurrency and async behavior

`LoopGuard` configuration can be shared across concurrent sessions, but do not
share one `GuardSession` as a cross-run aggregate: each session represents one
run and serializes its own `record()` calls. `watch()` intentionally keeps one
persistent session per decorated function so repeated invocations can be
detected. For an `async def` target, the wrapper awaits its result before
recording it. Calls that raise are recorded with their exception type and
message before the original exception is re-raised.

## Migration and compatibility

The current schema version is available as `agentloopguard.SCHEMA_VERSION`.
`session.call_history` remains dictionary-based for compatibility, while
normalized steps include schema fields. `DetectionResult.to_dict()` returns the
versioned event shape; use `to_legacy_dict()` only when an existing consumer
requires the older four-field result. `SemanticSimilarityDetector` remains an
import-compatible alias, but new code should use the accurate
`LexicalSimilarityDetector` name.

## Troubleshooting

| Symptom | What to check |
|---------|---------------|
| No detector fires | Confirm every relevant step has the fields that detector needs, such as `tool_name` and `tool_args` for exact repeats. |
| A lexical loop does not fire | The last `n` outputs must be non-empty strings; blank, non-string, and tokenless outputs reset the candidate window. |
| History is shorter than expected | This is the default bounded-memory behavior. Set `full_history=True` only for a custom detector that truly needs every step. |
| Cost is zero or differs from a provider bill | The SDK uses local estimates; supply your own authoritative accounting when billing accuracy matters. |
| A callback guard fails at construction | Set `on_alert="callback"` only together with a callable `alert_callback`. |

## Runtime behavior

AgentLoopGuard has no required runtime dependencies and performs its guard
logic locally. Model-price estimates are implementation details, not a pricing
guarantee; provide your own accounting when accurate provider billing matters.

## License

This repository is source-available under the [PolyForm Noncommercial 1.0.0
license](LICENSE). Noncommercial use is permitted under its terms; commercial
use requires separate permission from the copyright holder. Versions previously
released under the MIT license remain available under their original terms.

## Links

- [GitHub](https://github.com/ops-velro-services/agentloopguard)
- [PyPI](https://pypi.org/project/agentloopguard-sdk/)
- [Changelog](CHANGELOG.md)
- [Support](mailto:shaikmohammedrizwanfaisal@gmail.com)

---

*Local loop and budget protection for Python agents.*
