"""LangChain callback adapter for AgentLoopGuard."""

from __future__ import annotations

import logging
from typing import Any

from agentloopguard.guard import GuardSession, LoopGuard

logger = logging.getLogger(__name__)

try:
    from langchain_core.callbacks import BaseCallbackHandler  # type: ignore[import-not-found]
except ImportError:  # pragma: no cover
    try:
        from langchain.callbacks.base import BaseCallbackHandler  # type: ignore[import-not-found]
    except ImportError:

        class BaseCallbackHandler:  # type: ignore[no-redef]
            """Fallback base callback handler when LangChain is not installed."""

            pass


class AgentLoopGuardCallbackHandler(BaseCallbackHandler):  # type: ignore[misc]
    """LangChain callback handler that records agent tool and LLM execution steps in AgentLoopGuard.

    Can be initialized with a `GuardSession` or a `LoopGuard`. If a `LoopGuard` is provided,
    the callback will open and manage a session automatically.
    """

    def __init__(
        self,
        guard_or_session: LoopGuard | GuardSession,
        default_model: str = "gpt-4o",
    ) -> None:
        super().__init__()
        self.default_model = default_model
        if isinstance(guard_or_session, LoopGuard):
            self._guard: LoopGuard | None = guard_or_session
            self.session: GuardSession = guard_or_session.session()
            self.session.__enter__()
        elif isinstance(guard_or_session, GuardSession):
            self._guard = None
            self.session = guard_or_session
        else:
            raise TypeError("guard_or_session must be an instance of LoopGuard or GuardSession")

    def close(self) -> None:
        """Close the managed session if initialized from a LoopGuard instance."""
        if self._guard is not None:
            self.session.__exit__(None, None, None)
            self._guard = None

    def on_tool_end(
        self,
        output: Any,
        *,
        run_id: Any = None,
        parent_run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Record a completed tool invocation step in the guard session."""
        tool_name = kwargs.get("name") or kwargs.get("tool_name") or "unknown_tool"
        tool_args = kwargs.get("inputs") or kwargs.get("tool_input") or {}

        step_data: dict[str, Any] = {
            "tool_name": str(tool_name),
            "tool_args": tool_args,
            "output": str(output),
            "model": self.default_model,
        }

        self.session.record(step_data)

    def on_llm_end(
        self,
        response: Any,
        *,
        run_id: Any = None,
        parent_run_id: Any = None,
        **kwargs: Any,
    ) -> None:
        """Record token counts and output from an LLM response if available."""
        prompt_tokens = 0
        completion_tokens = 0
        model_name = self.default_model

        llm_output = getattr(response, "llm_output", None) or {}
        if isinstance(llm_output, dict):
            token_usage = llm_output.get("token_usage") or llm_output.get("usage") or {}
            if isinstance(token_usage, dict):
                prompt_tokens = (
                    token_usage.get("prompt_tokens") or token_usage.get("input_tokens") or 0
                )
                completion_tokens = (
                    token_usage.get("completion_tokens") or token_usage.get("output_tokens") or 0
                )
            if llm_output.get("model_name"):
                model_name = str(llm_output["model_name"])

        step_data: dict[str, Any] = {
            "tool_name": "llm_completion",
            "tool_args": {},
            "output": str(response),
            "model": model_name,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
        }
        self.session.record(step_data)
