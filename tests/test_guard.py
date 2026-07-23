import asyncio
import inspect
import math
import re
import threading
from pathlib import Path

import pytest

from agentloopguard.detectors import BaseDetector, ExactRepeatDetector
from agentloopguard.exceptions import LoopDetectedError
from agentloopguard.guard import LoopGuard
from agentloopguard.schema import SCHEMA_VERSION, StepEvent, TelemetryEvent


def test_guard_session():
    guard = LoopGuard(max_iterations=5)
    with guard.session() as sess:
        for i in range(3):
            sess.record({"tool_name": "test", "tool_args": {"i": i}})

        summary = sess.summary()
        assert summary["history_length"] == 3
        assert summary["budget"]["iterations"] == 3


def test_guard_detects_loop():
    guard = LoopGuard(on_alert="raise")
    with guard.session() as sess:
        with pytest.raises(LoopDetectedError) as exc:
            for _i in range(4):
                sess.record(
                    {"tool_name": "test", "tool_args": {"fixed": True}, "output": "same output"}
                )

        assert "ExactRepeatDetector" in str(exc.value)


def test_guard_decorator():
    guard = LoopGuard(on_alert="raise")

    @guard.watch(model="gpt-3.5-turbo")
    def do_work(x):
        return x

    with pytest.raises(LoopDetectedError):
        for _ in range(4):
            do_work(1)


def test_decorator_distinguishes_positional_arguments_and_detects_repeats():
    guard = LoopGuard(on_alert="raise", detectors=[ExactRepeatDetector(n=3)])

    @guard.watch()
    def do_work(value, *, prefix=""):
        return f"{prefix}{value}"

    assert [do_work(value) for value in (1, 2, 3)] == ["1", "2", "3"]
    assert do_work._guard_session.summary()["history_length"] == 3

    with pytest.raises(LoopDetectedError):
        for _ in range(3):
            do_work(4, prefix="item-")


def test_async_decorator_records_completed_result_and_preserves_metadata():
    guard = LoopGuard(detectors=[])

    @guard.watch(model="gpt-4o")
    async def fetch(value):
        """Return a completed async result."""
        return {"value": value}

    assert inspect.iscoroutinefunction(fetch)
    assert fetch.__name__ == "fetch"
    assert fetch.__doc__ == "Return a completed async result."
    assert asyncio.run(fetch("complete")) == {"value": "complete"}
    recorded = fetch._guard_session.call_history[0]
    assert recorded["tool_name"] == "fetch"
    assert recorded["tool_args"] == {"args": ("complete",), "kwargs": {}}
    assert recorded["model"] == "gpt-4o"
    assert recorded["output"] == "{'value': 'complete'}"


def test_decorator_records_exceptions_then_reraises_them():
    guard = LoopGuard(detectors=[])

    @guard.watch()
    def failing_work(value):
        raise ValueError(f"bad value: {value}")

    with pytest.raises(ValueError, match="bad value: 7"):
        failing_work(7)

    recorded = failing_work._guard_session.call_history[0]
    assert recorded["tool_args"] == {"args": (7,), "kwargs": {}}
    assert recorded["output"] == "bad value: 7"
    assert recorded["exception"] == {"type": "ValueError", "message": "bad value: 7"}


def test_readme_decorator_examples_execute():
    readme = Path(__file__).parents[1] / "README.md"
    decorator_section = readme.read_text().split("### As a Decorator", 1)[1]
    examples = decorator_section.split("```python")[1:3]

    namespace = {}
    exec(examples[0].split("```", 1)[0], namespace)
    exec(examples[1].split("```", 1)[0], namespace)


def test_all_readme_python_examples_execute():
    readme = Path(__file__).parents[1] / "README.md"
    examples = re.findall(r"```python\n(.*?)```", readme.read_text(), flags=re.DOTALL)

    for example in examples:
        exec(example, {})


def test_readme_documents_required_developer_guidance():
    readme = (Path(__file__).parents[1] / "README.md").read_text()

    for heading in (
        "## Quickstart: stop a repeated tool call",
        "## Concepts",
        "### Custom detectors",
        "## Exceptions and alert modes",
        "## Concurrency and async behavior",
        "## Migration and compatibility",
        "## Troubleshooting",
    ):
        assert heading in readme


def test_sessions_have_independent_budget_state():
    guard = LoopGuard(max_iterations=3)
    first = guard.session()
    second = guard.session()

    first.record({"tool_name": "first", "tool_args": {}, "input_tokens": 10, "output_tokens": 5})
    second.record({"tool_name": "second", "tool_args": {}, "input_tokens": 2, "output_tokens": 1})

    assert first.summary()["budget"]["iterations"] == 1
    assert first.summary()["budget"]["total_tokens"] == 15
    assert second.summary()["budget"]["iterations"] == 1
    assert second.summary()["budget"]["total_tokens"] == 3
    assert not hasattr(guard, "budget")


def test_concurrent_sessions_do_not_share_accounting():
    guard = LoopGuard(max_iterations=20, on_alert="log")
    sessions = [guard.session(), guard.session()]
    failures = []

    def record_steps(session, prefix):
        try:
            for index in range(20):
                session.record({"tool_name": prefix, "tool_args": {"index": index}})
        except Exception as exc:
            failures.append(exc)

    threads = [
        threading.Thread(target=record_steps, args=(sessions[0], "first")),
        threading.Thread(target=record_steps, args=(sessions[1], "second")),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert failures == []
    assert [session.summary()["budget"]["iterations"] for session in sessions] == [20, 20]


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_iterations": 0}, "max_iterations"),
        ({"max_iterations": True}, "max_iterations"),
        ({"max_tokens": -1}, "max_tokens"),
        ({"max_cost_usd": math.inf}, "max_cost_usd"),
        ({"max_duration_seconds": 0}, "max_duration_seconds"),
        ({"on_alert": "email"}, "on_alert"),
        ({"on_alert": "callback"}, "alert_callback"),
        ({"alert_callback": "not callable"}, "alert_callback"),
    ],
)
def test_guard_rejects_invalid_configuration_immediately(kwargs, message):
    with pytest.raises((TypeError, ValueError), match=message):
        LoopGuard(**kwargs)


def test_record_validates_step_without_mutating_caller_input():
    guard = LoopGuard(detectors=[])
    session = guard.session()
    step = {"tool_name": "search", "tool_args": {"query": "safe"}, "input_tokens": 2}

    session.record(step)

    assert step == {"tool_name": "search", "tool_args": {"query": "safe"}, "input_tokens": 2}
    assert session.call_history[0]["timestamp"] > 0
    assert session.call_history[0]["cost_usd"] == 0


@pytest.mark.parametrize(
    "step",
    [
        {"input_tokens": -1},
        {"input_tokens": 1.5},
        {"output_tokens": True},
        {"model": ""},
        {"timestamp": math.nan},
        {"timestamp": "soon"},
    ],
)
def test_record_rejects_invalid_step_fields(step):
    session = LoopGuard(detectors=[]).session()
    with pytest.raises((TypeError, ValueError)):
        session.record(step)
    assert session.call_history == []


def test_decorator_fingerprints_non_json_and_cyclic_arguments_safely():
    guard = LoopGuard(on_alert="raise", detectors=[ExactRepeatDetector(n=2)])
    cyclic = []
    cyclic.append(cyclic)

    @guard.watch()
    def work(value):
        return "ok"

    assert work({"values": {3, 1}, "cycle": cyclic}) == "ok"
    with pytest.raises(LoopDetectedError):
        work({"cycle": cyclic, "values": {1, 3}})


def test_session_retains_only_the_largest_detector_window_by_default():
    guard = LoopGuard(detectors=[ExactRepeatDetector(n=3)])
    session = guard.session()

    for index in range(10):
        session.record({"tool_name": "work", "tool_args": {"index": index}})

    assert len(session.call_history) == 3
    assert [step["tool_args"]["index"] for step in session.call_history] == [7, 8, 9]
    assert session.summary()["budget"]["iterations"] == 10


def test_full_history_is_an_explicit_opt_in():
    guard = LoopGuard(detectors=[ExactRepeatDetector(n=3)], full_history=True)
    session = guard.session()

    for index in range(4):
        session.record({"tool_name": "work", "tool_args": {"index": index}})

    assert len(session.call_history) == 4


def test_custom_detectors_without_a_window_require_full_history():
    class UnboundedDetector(BaseDetector):
        def check(self, call_history):
            return None

    with pytest.raises(ValueError, match="full_history"):
        LoopGuard(detectors=[UnboundedDetector()])


def test_guard_passes_its_injectable_clock_to_each_session():
    clock = [1.0]
    guard = LoopGuard(max_duration_seconds=2, detectors=[], clock=lambda: clock[0])
    session = guard.session()

    clock[0] = 2.5
    assert session.summary()["budget"]["elapsed_seconds"] == 1.5


def test_recorded_steps_have_a_versioned_schema_and_accept_typed_input():
    session = LoopGuard(detectors=[]).session()
    typed_step = StepEvent(
        session_id="caller-session",
        timestamp=123.0,
        model="unknown",
        input_tokens=1,
        output_tokens=2,
        cost_usd=999.0,
        tool_name="search",
        tool_args={"query": "guard"},
        extra={"request_id": "req-1"},
    )

    session.record(typed_step)

    assert session.call_history[0] == {
        "schema_version": SCHEMA_VERSION,
        "session_id": session.session_id,
        "timestamp": 123.0,
        "model": "unknown",
        "input_tokens": 1,
        "output_tokens": 2,
        "cost_usd": 0,
        "tool_name": "search",
        "tool_args": {"query": "guard"},
        "request_id": "req-1",
    }


def test_detection_events_include_stable_context_and_legacy_adapter():
    captured = []
    guard = LoopGuard(
        detectors=[ExactRepeatDetector(n=2)], on_alert="callback", alert_callback=captured.append
    )
    session = guard.session()
    for _ in range(2):
        session.record({"timestamp": 42.0, "tool_name": "search", "tool_args": {"query": "guard"}})

    event = session.events[0]
    assert captured == [event]
    assert event.to_dict() == {
        "schema_version": SCHEMA_VERSION,
        "session_id": session.session_id,
        "timestamp": 42.0,
        "detector_id": "exact_repeat",
        "detector_name": "ExactRepeatDetector",
        "confidence": 1.0,
        "description": "Exact same tool call repeated 2 times.",
        "measured_values": {"repeats": 2},
        "recommended_action": "stop",
        "pattern_details": {"tool_name": "search", "repeats": 2},
    }
    assert event.to_legacy_dict() == {
        "detector_name": "ExactRepeatDetector",
        "confidence": 1.0,
        "description": "Exact same tool call repeated 2 times.",
        "pattern_details": {"tool_name": "search", "repeats": 2},
    }


def test_event_exporter_emits_otel_compatible_step_and_detection_events():
    exported: list[TelemetryEvent] = []
    guard = LoopGuard(
        detectors=[ExactRepeatDetector(n=2)],
        on_alert="log",
        event_exporter=exported.append,
    )
    session = guard.session()

    for _ in range(2):
        session.record(
            {
                "timestamp": 42.0,
                "tool_name": "search",
                "tool_args": {"query": "guard"},
                "model": "gpt-4o",
                "input_tokens": 2,
                "output_tokens": 3,
            }
        )

    assert [(event.name, event.timestamp) for event in exported] == [
        ("agentloopguard.step", 42.0),
        ("agentloopguard.step", 42.0),
        ("agentloopguard.detection", 42.0),
    ]
    assert exported[0].attributes == {
        "agentloopguard.schema.version": SCHEMA_VERSION,
        "agentloopguard.session.id": session.session_id,
        "agentloopguard.model": "gpt-4o",
        "agentloopguard.input_tokens": 2,
        "agentloopguard.output_tokens": 3,
        "agentloopguard.cost_usd": pytest.approx(0.000055),
        "agentloopguard.tool.name": "search",
    }
    assert exported[-1].attributes == {
        "agentloopguard.schema.version": SCHEMA_VERSION,
        "agentloopguard.session.id": session.session_id,
        "agentloopguard.detector.id": "exact_repeat",
        "agentloopguard.detector.name": "ExactRepeatDetector",
        "agentloopguard.confidence": 1.0,
        "agentloopguard.recommended_action": "stop",
    }


def test_event_exporter_failure_does_not_break_guard_recording():
    def broken_exporter(_event):
        raise RuntimeError("export unavailable")

    session = LoopGuard(detectors=[], event_exporter=broken_exporter).session()
    session.record({"tool_name": "search", "tool_args": {}})

    assert session.summary()["budget"]["iterations"] == 1


def test_guard_rejects_invalid_event_exporter():
    with pytest.raises(TypeError, match="event_exporter"):
        LoopGuard(event_exporter="not callable")
