"""Exceptions for AgentLoopGuard."""

class AgentLoopGuardError(Exception):
    """Base exception for AgentLoopGuard."""
    pass

class LoopDetectedError(AgentLoopGuardError):
    """Raised when a loop pattern is detected."""
    def __init__(self, message: str, loop_type: str, iteration_count: int, pattern_description: str):
        super().__init__(message)
        self.loop_type = loop_type
        self.iteration_count = iteration_count
        self.pattern_description = pattern_description

class BudgetExceededError(AgentLoopGuardError):
    """Raised when cost/token budget is exceeded."""
    def __init__(self, message: str, budget_type: str, limit: float, actual: float):
        super().__init__(message)
        self.budget_type = budget_type
        self.limit = limit
        self.actual = actual

class DurationExceededError(AgentLoopGuardError):
    """Raised when max duration is exceeded."""
    pass
