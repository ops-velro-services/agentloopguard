"""Unit tests for AgentLoopGuard framework adapters (LangChain & LlamaIndex)."""

from __future__ import annotations

import pytest

from agentloopguard import LoopDetectedError, LoopGuard
from agentloopguard.adapters.langchain import AgentLoopGuardCallbackHandler
from agentloopguard.adapters.llamaindex import AgentLoopGuardEventHandler


def test_langchain_adapter_session_initialization() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    with guard.session() as session:
        handler = AgentLoopGuardCallbackHandler(session, default_model="gpt-4o")
        handler.on_tool_end(
            "Search results for query",
            name="search_tool",
            inputs={"query": "python"},
        )
        assert session.budget.iterations == 1
        assert session.call_history[0]["tool_name"] == "search_tool"
        assert session.call_history[0]["tool_args"] == {"query": "python"}


def test_langchain_adapter_guard_initialization_and_close() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    handler = AgentLoopGuardCallbackHandler(guard, default_model="gpt-4o-mini")
    handler.on_tool_end("Output 1", name="tool_a")
    assert handler.session.budget.iterations == 1
    handler.close()


def test_langchain_adapter_invalid_init() -> None:
    with pytest.raises(TypeError, match="must be an instance of LoopGuard or GuardSession"):
        AgentLoopGuardCallbackHandler("invalid_target")  # type: ignore[arg-type]


def test_langchain_adapter_llm_end_and_loop_detection() -> None:
    guard = LoopGuard(max_iterations=3, on_alert="raise")
    handler = AgentLoopGuardCallbackHandler(guard, default_model="gpt-4o")

    class MockLLMResponse:
        def __init__(self) -> None:
            self.llm_output = {
                "token_usage": {"prompt_tokens": 100, "completion_tokens": 50},
                "model_name": "gpt-4o",
            }

        def __str__(self) -> str:
            return "Model output string"

    handler.on_llm_end(MockLLMResponse())
    assert handler.session.budget.iterations == 1
    assert handler.session.budget.total_input_tokens == 100
    assert handler.session.budget.total_output_tokens == 50
    handler.close()


def test_langchain_adapter_triggers_loop_detected() -> None:
    guard = LoopGuard(max_iterations=3, on_alert="raise")
    handler = AgentLoopGuardCallbackHandler(guard)

    handler.on_tool_end("repetitive output", name="search")
    handler.on_tool_end("repetitive output", name="search")
    with pytest.raises(LoopDetectedError):
        handler.on_tool_end("repetitive output", name="search")
    handler.close()


def test_llamaindex_adapter_session_initialization() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    with guard.session() as session:
        handler = AgentLoopGuardEventHandler(session, default_model="gpt-4o")
        handler.on_event(
            event_type="query_step",
            payload={
                "tool_name": "index_query",
                "input": {"query": "vector search"},
                "output": "retrieved 5 nodes",
                "prompt_tokens": 200,
                "completion_tokens": 80,
            },
        )
        assert session.budget.iterations == 1
        assert session.call_history[0]["tool_name"] == "index_query"
        assert session.budget.total_input_tokens == 200
        assert session.budget.total_output_tokens == 80


def test_llamaindex_adapter_handle_tool_call_and_close() -> None:
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    handler = AgentLoopGuardEventHandler(guard, default_model="gpt-4o")
    handler.handle_tool_call(tool_name="calculator", tool_args={"expr": "2 + 2"}, output="4")
    assert handler.session.budget.iterations == 1
    assert handler.session.call_history[0]["tool_name"] == "calculator"
    handler.close()


def test_llamaindex_adapter_invalid_init() -> None:
    with pytest.raises(TypeError, match="must be an instance of LoopGuard or GuardSession"):
        AgentLoopGuardEventHandler(123)  # type: ignore[arg-type]


def test_llamaindex_adapter_triggers_loop_detected() -> None:
    guard = LoopGuard(max_iterations=3, on_alert="raise")
    handler = AgentLoopGuardEventHandler(guard)

    handler.handle_tool_call("fetch_data", {"id": 1}, "response data")
    handler.handle_tool_call("fetch_data", {"id": 1}, "response data")
    with pytest.raises(LoopDetectedError):
        handler.handle_tool_call("fetch_data", {"id": 1}, "response data")
    handler.close()
