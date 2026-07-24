"""Unit tests for AgentLoopGuard AutoGen adapter."""

from __future__ import annotations

from typing import Any

import pytest

from agentloopguard import LoopDetectedError, LoopGuard
from agentloopguard.adapters.autogen import AgentLoopGuardAutoGenHook
from agentloopguard.detectors import ExactRepeatDetector, LexicalSimilarityDetector


class MockAutoGenAgent:
    def __init__(self, name: str) -> None:
        self.name = name
        self.hooks: dict[str, list[Any]] = {}

    def register_hook(self, hookable_method: str, hook: Any) -> None:
        if hookable_method not in self.hooks:
            self.hooks[hookable_method] = []
        self.hooks[hookable_method].append(hook)


def test_autogen_adapter_session_initialization() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    with guard.session() as session:
        hook = AgentLoopGuardAutoGenHook(session, default_model="gpt-4o")
        res = hook.on_message(
            message="Hello world",
            sender="User",
            recipient="Assistant",
        )
        assert res == "Hello world"
        assert session.budget.iterations == 1
        assert session.call_history[0]["tool_name"] == "User->Assistant"
        assert session.call_history[0]["output"] == "Hello world"


def test_autogen_adapter_guard_initialization_and_close() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    hook = AgentLoopGuardAutoGenHook(guard, default_model="gpt-4o-mini")
    res = hook.process_message_before_send(
        sender="UserProxy",
        recipient="AssistantAgent",
        message="Calculate 2+2",
    )
    assert res == "Calculate 2+2"
    assert hook.session.budget.iterations == 1
    assert hook.session.call_history[0]["tool_name"] == "UserProxy->AssistantAgent"
    hook.close()


def test_autogen_adapter_invalid_init() -> None:
    with pytest.raises(TypeError, match="must be an instance of LoopGuard or GuardSession"):
        AgentLoopGuardAutoGenHook("invalid_target")  # type: ignore[arg-type]


def test_autogen_adapter_attach_to_agent() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    hook = AgentLoopGuardAutoGenHook(guard)
    agent = MockAutoGenAgent("Assistant")

    hook.attach_to_agent(agent)

    assert "process_message_before_send" in agent.hooks
    assert len(agent.hooks["process_message_before_send"]) == 1

    registered_fn = agent.hooks["process_message_before_send"][0]
    out = registered_fn(sender=agent, recipient="User", message="Hook attached test")
    assert out == "Hook attached test"
    assert hook.session.budget.iterations == 1
    hook.close()


def test_autogen_adapter_dict_and_tool_calls() -> None:
    guard = LoopGuard(
        max_iterations=5,
        detectors=[ExactRepeatDetector(), LexicalSimilarityDetector()],
        on_alert="raise",
    )
    hook = AgentLoopGuardAutoGenHook(guard)

    # Dictionary message with tool_calls
    msg_dict = {
        "content": "Executing python script",
        "tool_calls": [
            {
                "function": {
                    "name": "python_interpreter",
                    "arguments": {"code": "print(42)"},
                }
            }
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    hook.on_message(msg_dict)
    assert hook.session.budget.iterations == 1
    assert hook.session.call_history[0]["tool_name"] == "python_interpreter"
    assert hook.session.call_history[0]["input_tokens"] == 100
    assert hook.session.call_history[0]["output_tokens"] == 50

    # Function call format
    msg_func = {
        "content": "Running SQL query",
        "function_call": {
            "name": "sql_query",
            "arguments": {"query": "SELECT * FROM users;"},
        },
    }
    hook.on_message(msg_func)
    assert hook.session.budget.iterations == 2
    assert hook.session.call_history[1]["tool_name"] == "sql_query"

    hook.close()


def test_autogen_adapter_callable_interface() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    hook = AgentLoopGuardAutoGenHook(guard)

    msg = {"content": "Callable test message"}
    ret = hook(msg, sender="AgentA", recipient="AgentB")

    assert ret == msg
    assert hook.session.budget.iterations == 1
    assert hook.session.call_history[0]["tool_name"] == "AgentA->AgentB"
    hook.close()


def test_autogen_adapter_triggers_loop_detected() -> None:
    guard = LoopGuard(max_iterations=3, on_alert="raise")
    hook = AgentLoopGuardAutoGenHook(guard)

    msg = {"content": "Same repetitive AutoGen message"}
    hook(msg, sender="User", recipient="Assistant")
    hook(msg, sender="User", recipient="Assistant")
    with pytest.raises(LoopDetectedError):
        hook(msg, sender="User", recipient="Assistant")
    hook.close()
