"""AgentLoopGuard SDK."""
from agentloopguard.guard import LoopGuard, GuardSession
from agentloopguard.budget import BudgetTracker
from agentloopguard.detectors import (
    ExactRepeatDetector,
    SemanticSimilarityDetector,
    CostVelocityDetector,
    OscillationDetector,
    DetectionResult,
)
from agentloopguard.exceptions import (
    AgentLoopGuardError,
    LoopDetectedError,
    BudgetExceededError,
    DurationExceededError,
)

__version__ = "0.1.0"
