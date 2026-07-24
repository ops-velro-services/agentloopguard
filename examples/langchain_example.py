"""Example of using AgentLoopGuard with LangChain."""

from __future__ import annotations

from agentloopguard import AgentLoopGuardError, LoopGuard
from agentloopguard.adapters.langchain import AgentLoopGuardCallbackHandler


def main() -> None:
    # Initialize a LoopGuard with an iteration limit and alert policy
    guard = LoopGuard(max_iterations=10, on_alert="raise")

    # Use the official AgentLoopGuardCallbackHandler
    cb = AgentLoopGuardCallbackHandler(guard, default_model="gpt-4o")

    try:
        # Simulate LangChain tool callbacks that enter an oscillation loop
        for _ in range(6):
            cb.on_tool_end("output A", name="tool_A", inputs={"query": "fetch"})
            cb.on_tool_end("output B", name="tool_B", inputs={"query": "process"})
    except AgentLoopGuardError as e:
        print(f"AgentLoopGuard stopped LangChain execution: {e}")
    finally:
        cb.close()


if __name__ == "__main__":
    main()
