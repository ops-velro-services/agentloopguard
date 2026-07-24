"""Example of using AgentLoopGuard with CrewAI."""

from __future__ import annotations

from agentloopguard import AgentLoopGuardError, LoopGuard
from agentloopguard.adapters.crewai import AgentLoopGuardCrewCallback


class MockCrewStep:
    """Mock CrewAI step object simulating an agent tool execution step."""

    def __init__(self, tool: str, tool_input: dict[str, str], output: str) -> None:
        self.action = type("Action", (), {"tool": tool, "tool_input": tool_input})()
        self.output = output


def main() -> None:
    # Initialize LoopGuard with iteration limit and alert policy
    guard = LoopGuard(max_iterations=10, on_alert="raise")

    # Initialize the CrewAI callback adapter
    cb = AgentLoopGuardCrewCallback(guard, default_model="gpt-4o")

    try:
        # Simulate CrewAI agent step_callback invocations entering a loop
        repeated_step = MockCrewStep(
            tool="web_search",
            tool_input={"query": "agentic loop guard"},
            output="No new results found",
        )

        for i in range(5):
            print(f"Executing CrewAI agent step {i + 1}...")
            cb(repeated_step)

    except AgentLoopGuardError as e:
        print(f"AgentLoopGuard stopped CrewAI execution: {e}")
    finally:
        cb.close()


if __name__ == "__main__":
    main()
