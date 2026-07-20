"""
Example of using AgentLoopGuard with LangChain.
"""
from agentloopguard import LoopGuard
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import langchain

def main():
    try:
        import langchain
    except ImportError:
        print("Please install langchain to run this example")
        return
        
    guard = LoopGuard(max_iterations=5, on_alert="raise")
    
    # You would typically inject this via a LangChain CallbackHandler
    class GuardCallback:
        def __init__(self, session):
            self.session = session
            
        def on_tool_end(self, output, **kwargs):
            self.session.record({
                "tool_name": kwargs.get("name", "unknown"),
                "tool_args": kwargs.get("inputs", {}),
                "output": str(output),
                "model": "gpt-3.5-turbo" # Defaulting for example
            })

    with guard.session() as sess:
        cb = GuardCallback(sess)
        
        try:
            # Simulate tool calls that trigger an oscillation loop
            for _ in range(6):
                cb.on_tool_end("output A", name="tool_A")
                cb.on_tool_end("output B", name="tool_B")
        except Exception as e:
            print(f"Guard stopped execution: {e}")

if __name__ == "__main__":
    main()
