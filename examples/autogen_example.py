"""Example of using AgentLoopGuard with AutoGen."""

from __future__ import annotations

from typing import Any

from agentloopguard import AgentLoopGuardError, LoopGuard
from agentloopguard.adapters.autogen import AgentLoopGuardAutoGenHook


class MockConversableAgent:
    """Mock AutoGen ConversableAgent demonstrating hook registration and message interception."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.hooks: list[Any] = []

    def register_hook(self, hookable_method: str, hook: Any) -> None:
        if hookable_method == "process_message_before_send":
            self.hooks.append(hook)

    def send(self, recipient: MockConversableAgent, message: dict[str, Any]) -> None:
        for hook in self.hooks:
            message = hook(sender=self, recipient=recipient, message=message)


def main() -> None:
    # Initialize LoopGuard with iteration limit and alert policy
    guard = LoopGuard(max_iterations=10, on_alert="raise")

    # Initialize the AutoGen hook adapter
    hook = AgentLoopGuardAutoGenHook(guard, default_model="gpt-4o")

    # Create mock AutoGen agents
    user_proxy = MockConversableAgent("UserProxy")
    assistant = MockConversableAgent("AssistantAgent")

    # Register the guard hook on the sending agent
    hook.attach_to_agent(user_proxy)

    try:
        # Simulate repeating AutoGen multi-agent message exchanges
        looping_message = {
            "content": "Searching database for record ID 404...",
            "tool_calls": [
                {
                    "function": {
                        "name": "db_search",
                        "arguments": {"id": 404},
                    }
                }
            ],
        }

        for i in range(5):
            print(f"Simulating AutoGen message exchange {i + 1}...")
            user_proxy.send(recipient=assistant, message=looping_message)

    except AgentLoopGuardError as e:
        print(f"AgentLoopGuard stopped AutoGen message loop: {e}")
    finally:
        hook.close()


if __name__ == "__main__":
    main()
