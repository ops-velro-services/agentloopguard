"""Example of using AgentLoopGuard with LlamaIndex."""

from __future__ import annotations

from agentloopguard import AgentLoopGuardError, LoopGuard
from agentloopguard.adapters.llamaindex import AgentLoopGuardEventHandler


def main() -> None:
    # Initialize a LoopGuard with a budget and detector policy
    guard = LoopGuard(max_iterations=10, on_alert="raise")

    # Use the official AgentLoopGuardEventHandler
    handler = AgentLoopGuardEventHandler(guard, default_model="gpt-4o")

    try:
        # Simulate LlamaIndex step callbacks entering an exact repeat loop
        for _ in range(5):
            handler.handle_tool_call(
                tool_name="vector_query",
                tool_args={"query": "agent architecture"},
                output="Identical document chunk response",
            )
    except AgentLoopGuardError as e:
        print(f"AgentLoopGuard stopped LlamaIndex execution: {e}")
    finally:
        handler.close()


if __name__ == "__main__":
    main()
