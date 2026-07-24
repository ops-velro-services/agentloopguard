"""Framework adapters for AgentLoopGuard."""

from agentloopguard.adapters.autogen import AgentLoopGuardAutoGenHook
from agentloopguard.adapters.crewai import AgentLoopGuardCrewCallback
from agentloopguard.adapters.langchain import AgentLoopGuardCallbackHandler
from agentloopguard.adapters.llamaindex import AgentLoopGuardEventHandler

__all__ = [
    "AgentLoopGuardAutoGenHook",
    "AgentLoopGuardCrewCallback",
    "AgentLoopGuardCallbackHandler",
    "AgentLoopGuardEventHandler",
]
