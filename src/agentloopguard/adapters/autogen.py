"""AutoGen framework adapter for AgentLoopGuard."""

from __future__ import annotations

import logging
from typing import Any

from agentloopguard.guard import GuardSession, LoopGuard

logger = logging.getLogger(__name__)


class AgentLoopGuardAutoGenHook:
    """AutoGen framework adapter that intercepts message exchanges and tool calls in AgentLoopGuard.

    Can be registered with AutoGen agents via `agent.register_hook(hookable_method, hook_fn)`
    or invoked directly as a message processing hook / callback.

    Can be initialized with a `GuardSession` or a `LoopGuard`. If a `LoopGuard` is provided,
    the hook will open and manage a session automatically.
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

    def attach_to_agent(
        self,
        agent: Any,
        hookable_method: str = "process_message_before_send",
    ) -> None:
        """Attach this hook to an AutoGen agent using its `register_hook` interface."""
        if hasattr(agent, "register_hook") and callable(agent.register_hook):
            agent.register_hook(
                hookable_method=hookable_method,
                hook=self.process_message_before_send,
            )
        else:
            logger.warning("Target agent does not support `register_hook` interface.")

    def process_message_before_send(
        self,
        sender: Any = None,
        recipient: Any = None,
        message: Any = None,
        silent: bool = False,
        **kwargs: Any,
    ) -> Any:
        """Hook method signature compatible with AutoGen `process_message_before_send`.

        Intercepts the message, records it in the guard session, and returns the message.
        """
        self.on_message(message=message, sender=sender, recipient=recipient, **kwargs)
        return message

    def on_message(
        self,
        message: Any = None,
        sender: Any = None,
        recipient: Any = None,
        **kwargs: Any,
    ) -> Any:
        """Process an AutoGen message or tool invocation and record it in the guard session."""
        tool_name = "autogen_message"
        tool_args: Any = {}
        output = ""
        model_name = self.default_model
        prompt_tokens = 0
        completion_tokens = 0

        sender_name = getattr(sender, "name", str(sender)) if sender is not None else "agent"
        recipient_name = (
            getattr(recipient, "name", str(recipient)) if recipient is not None else "agent"
        )

        if sender is not None or recipient is not None:
            tool_name = f"{sender_name}->{recipient_name}"
            tool_args = {"sender": sender_name, "recipient": recipient_name}

        if message is not None:
            if isinstance(message, dict):
                output = str(message.get("content") or "")

                if "tool_calls" in message and isinstance(message["tool_calls"], list):
                    for tc in message["tool_calls"]:
                        if isinstance(tc, dict):
                            fn = tc.get("function", {})
                            if isinstance(fn, dict) and "name" in fn:
                                tool_name = str(fn["name"])
                                tool_args = fn.get("arguments", {})
                elif "function_call" in message and isinstance(message["function_call"], dict):
                    fc = message["function_call"]
                    if "name" in fc:
                        tool_name = str(fc["name"])
                        tool_args = fc.get("arguments", {})
                elif "name" in message:
                    tool_name = str(message["name"])

                if "model" in message:
                    model_name = str(message["model"])

                if "usage" in message and isinstance(message["usage"], dict):
                    u = message["usage"]
                    prompt_tokens = int(u.get("prompt_tokens") or u.get("input_tokens") or 0)
                    completion_tokens = int(
                        u.get("completion_tokens") or u.get("output_tokens") or 0
                    )

            elif isinstance(message, (list, tuple)):
                output = str([str(m) for m in message])
            elif hasattr(message, "content"):
                output = str(getattr(message, "content", message))
                if hasattr(message, "name"):
                    tool_name = str(message.name)
            else:
                output = str(message)

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
        elif "content" in kwargs and output == "":
            output = str(kwargs["content"])

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
            "output": output,
            "model": model_name,
            "input_tokens": prompt_tokens,
            "output_tokens": completion_tokens,
        }
        self.session.record(step_data)
        return message

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Callable interface for AutoGen message hooks or callbacks."""
        msg = kwargs.pop("message", None)
        sender = kwargs.pop("sender", None)
        recipient = kwargs.pop("recipient", None)

        if len(args) == 1:
            msg = args[0]
        elif len(args) == 2:
            sender, recipient = args[0], args[1]
        elif len(args) >= 3:
            if isinstance(args[0], (dict, str)) or hasattr(args[0], "content"):
                msg, sender, recipient = args[0], args[1], args[2]
            else:
                sender, recipient, msg = args[0], args[1], args[2]

        self.on_message(message=msg, sender=sender, recipient=recipient, **kwargs)
        return msg if msg is not None else (args[0] if args else None)
