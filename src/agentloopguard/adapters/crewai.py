"""CrewAI framework adapter for AgentLoopGuard."""

from __future__ import annotations

import logging
from typing import Any

from agentloopguard.guard import GuardSession, LoopGuard

logger = logging.getLogger(__name__)


class AgentLoopGuardCrewCallback:
    """CrewAI callback adapter that records agent tool and step execution in AgentLoopGuard.

    Can be passed directly as a `step_callback` or `task_callback` to CrewAI Agents, Tasks,
    or Crews, or invoked directly.

    Can be initialized with a `GuardSession` or a `LoopGuard`. If a `LoopGuard` is provided,
    the callback will open and manage a session automatically.
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

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        """Callable interface for CrewAI step_callback or task_callback."""
        self.on_step(*args, **kwargs)

    def on_step(self, step: Any = None, **kwargs: Any) -> None:
        """Process a CrewAI agent step or callback invocation and record it in the guard session."""
        tool_name = "crewai_step"
        tool_args: Any = {}
        output = ""
        model_name = self.default_model
        prompt_tokens = 0
        completion_tokens = 0

        if step is not None:
            action = getattr(step, "action", None)
            if action is not None:
                tool_name = str(getattr(action, "tool", tool_name))
                tool_args = getattr(action, "tool_input", {})
                output = str(getattr(step, "output", step))
            elif isinstance(step, (list, tuple)) and len(step) >= 2:
                act, out = step[0], step[1]
                tool_name = str(getattr(act, "tool", getattr(act, "name", "crewai_tool")))
                tool_args = getattr(act, "tool_input", getattr(act, "args", {}))
                output = str(out)
            elif isinstance(step, dict):
                tool_name = str(
                    step.get("tool") or step.get("tool_name") or step.get("name") or tool_name
                )
                tool_args = (
                    step.get("tool_input") or step.get("tool_args") or step.get("input") or {}
                )
                output = str(step.get("output") or step.get("result") or "")
            elif hasattr(step, "output"):
                output = str(step.output)
                if hasattr(step, "name"):
                    tool_name = str(step.name)
            else:
                output = str(step)

        if "tool_name" in kwargs:
            tool_name = str(kwargs["tool_name"])
        elif "name" in kwargs:
            tool_name = str(kwargs["name"])

        if "tool_args" in kwargs:
            tool_args = kwargs["tool_args"]
        elif "inputs" in kwargs or "tool_input" in kwargs:
            tool_args = kwargs.get("inputs") or kwargs.get("tool_input")

        if "output" in kwargs:
            output = str(kwargs["output"])
        elif "result" in kwargs:
            output = str(kwargs["result"])

        if "model" in kwargs:
            model_name = str(kwargs["model"])

        prompt_tokens = int(
            kwargs.get("prompt_tokens") or kwargs.get("input_tokens") or prompt_tokens
        )
        completion_tokens = int(
            kwargs.get("completion_tokens") or kwargs.get("output_tokens") or completion_tokens
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

    def on_tool_end(
        self,
        output: Any,
        tool_name: str = "crewai_tool",
        tool_args: Any = None,
        **kwargs: Any,
    ) -> None:
        """Record a completed CrewAI tool invocation in the guard session."""
        self.on_step(
            output=output,
            tool_name=tool_name,
            tool_args=tool_args or {},
            **kwargs,
        )

    def on_task_end(
        self,
        output: Any,
        task_name: str = "crewai_task",
        **kwargs: Any,
    ) -> None:
        """Record a completed CrewAI task execution in the guard session."""
        self.on_step(
            output=output,
            tool_name=task_name,
            **kwargs,
        )
