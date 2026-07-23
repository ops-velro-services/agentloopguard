"""
Example of using AgentLoopGuard with Anthropic.
"""

from typing import TYPE_CHECKING

from agentloopguard import LoopGuard

if TYPE_CHECKING:
    pass


def main():
    try:
        from anthropic import Anthropic
    except ImportError:
        print("Please install anthropic to run this example")
        return

    Anthropic(api_key="dummy")

    guard = LoopGuard(
        max_cost_usd=5.0,
        max_tokens=100_000,
        on_alert="log",  # Log instead of raising exceptions
    )

    with guard.session() as sess:
        # Simulate agent steps
        for step in range(5):
            # E.g. client.messages.create(...)

            # Record the step
            sess.record(
                {
                    "tool_name": "claude_message",
                    "tool_args": {"step": step},
                    "model": "claude-3-opus",
                    "input_tokens": 500,
                    "output_tokens": 200,
                    "output": "Simulated claude response",
                }
            )

        print("Session Summary:", sess.summary())


if __name__ == "__main__":
    main()
