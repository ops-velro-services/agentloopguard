"""LlamaIndex event adapter for AgentLoopGuard."""

from __future__ import annotations

import logging
from typing import Any

from agentloopguard.guard import GuardSession, LoopGuard

logger = logging.getLogger(__name__)


class AgentLoopGuardEventHandler:
    """LlamaIndex event handler adapter that records steps in AgentLoopGuard.

    Can be initialized with a `GuardSession` or a `LoopGuard`.
    """

    def __init__(
        self,
        guard_or_session: LoopGuard | GuardSession,
        default_model: str = "gpt-4o",
    ) -> None:
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

    def on_event(
        self,
        event_type: str,
        payload: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Process a LlamaIndex event and record it in the guard session."""
        payload = payload or {}
        tool_name = str(
            payload.get("tool_name") or payload.get("name") or event_type or "llamaindex_event"
        )
        tool_args = payload.get("tool_kwargs") or payload.get("input") or payload.get("args") or {}
        output = payload.get("output") or payload.get("response") or payload.get("result") or ""
        model_name = str(payload.get("model") or payload.get("model_name") or self.default_model)

        prompt_tokens = int(payload.get("prompt_tokens") or payload.get("input_tokens") or 0)
        completion_tokens = int(
            payload.get("completion_tokens") or payload.get("output_tokens") or 0
        )

        step_data: dict[str, Any] = {
            "tool_name": tool_name,
            "tool_args": tool_args,
            "output": str(output),
            "model": model_name,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
        }
        self.session.record(step_data)

    def handle_tool_call(
        self,
        tool_name: str,
        tool_args: dict[str, Any] | None = None,
        output: Any = None,
        **kwargs: Any,
    ) -> None:
        """Convenience method for directly recording a LlamaIndex tool execution step."""
        self.on_event(
            event_type="tool_call",
            payload={
                "tool_name": tool_name,
                "tool_kwargs": tool_args or {},
                "output": output,
                **kwargs,
            },
        )
