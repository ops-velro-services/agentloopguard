"""Unit tests for AgentLoopGuard CrewAI adapter."""

from __future__ import annotations

from typing import Any

import pytest

from agentloopguard import LoopDetectedError, LoopGuard
from agentloopguard.adapters.crewai import AgentLoopGuardCrewCallback


class MockAgentAction:
    def __init__(self, tool: str, tool_input: Any) -> None:
        self.tool = tool
        self.tool_input = tool_input


class MockAgentStep:
    def __init__(self, tool: str, tool_input: Any, output: str) -> None:
        self.action = MockAgentAction(tool, tool_input)
        self.output = output


def test_crewai_adapter_session_initialization() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    with guard.session() as session:
        cb = AgentLoopGuardCrewCallback(session, default_model="gpt-4o")
        cb.on_tool_end(
            output="Search results for CrewAI",
            tool_name="web_search",
            tool_args={"query": "agentic AI"},
        )
        assert session.budget.iterations == 1
        assert session.call_history[0]["tool_name"] == "web_search"
        assert session.call_history[0]["tool_args"] == {"query": "agentic AI"}


def test_crewai_adapter_guard_initialization_and_close() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    cb = AgentLoopGuardCrewCallback(guard, default_model="gpt-4o-mini")
    cb.on_task_end(output="Task output", task_name="research_task")
    assert cb.session.budget.iterations == 1
    assert cb.session.call_history[0]["tool_name"] == "research_task"
    cb.close()


def test_crewai_adapter_invalid_init() -> None:
    with pytest.raises(TypeError, match="must be an instance of LoopGuard or GuardSession"):
        AgentLoopGuardCrewCallback("invalid_target")  # type: ignore[arg-type]


def test_crewai_adapter_callable_step_callback() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    cb = AgentLoopGuardCrewCallback(guard)

    step_obj = MockAgentStep("search", {"q": "test"}, "found 10 items")
    cb(step_obj)

    assert cb.session.budget.iterations == 1
    assert cb.session.call_history[0]["tool_name"] == "search"
    assert cb.session.call_history[0]["tool_args"] == {"q": "test"}
    assert cb.session.call_history[0]["output"] == "found 10 items"
    cb.close()


def test_crewai_adapter_tuple_and_dict_steps() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    cb = AgentLoopGuardCrewCallback(guard)

    # Tuple format (action, output)
    action = MockAgentAction("scraper", {"url": "https://example.com"})
    cb((action, "page content"))
    assert cb.session.budget.iterations == 1
    assert cb.session.call_history[0]["tool_name"] == "scraper"

    # Dict format
    cb({"tool": "analyzer", "tool_input": {"data": "raw"}, "output": "processed"})
    assert cb.session.budget.iterations == 2
    assert cb.session.call_history[1]["tool_name"] == "analyzer"

    cb.close()


def test_crewai_adapter_triggers_loop_detected() -> None:
    guard = LoopGuard(max_iterations=3, on_alert="raise")
    cb = AgentLoopGuardCrewCallback(guard)

    step = MockAgentStep("repeated_tool", {"arg": "val"}, "repetitive output")
    cb(step)
    cb(step)
    with pytest.raises(LoopDetectedError):
        cb(step)
    cb.close()
