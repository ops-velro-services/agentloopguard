"""
Example of using AgentLoopGuard with OpenAI.
"""
from agentloopguard import LoopGuard
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import openai

def main():
    try:
        from openai import OpenAI
    except ImportError:
        print("Please install openai to run this example")
        return
        
    client = OpenAI(api_key="dummy")
    
    # Initialize Guard with limits
    guard = LoopGuard(max_iterations=10, max_cost_usd=1.0)
    
    # 1. Decorator usage
    @guard.watch(model="gpt-4o")
    def call_tool(name, **kwargs):
        # In a real app, this would execute the tool and return the output
        return "Simulated output"

    print("Running decorated function...")
    try:
        for _ in range(5):
            call_tool("search", query="agentloopguard")
    except Exception as e:
        print(f"Caught: {e}")

    # 2. Context Manager usage
    print("\nRunning in context manager...")
    with guard.session() as sess:
        try:
            for i in range(15):  # This will exceed max_iterations
                sess.record({
                    "tool_name": "generate",
                    "tool_args": {"prompt": "hello"},
                    "model": "gpt-4o",
                    "input_tokens": 10,
                    "output_tokens": 20
                })
        except Exception as e:
            print(f"Caught: {e}")

if __name__ == "__main__":
    main()
