"""Main Guard module for AgentLoopGuard."""
import time
import threading
import logging
from typing import Optional, List, Callable, Any, Dict
from functools import wraps

from agentloopguard.budget import BudgetTracker
from agentloopguard.detectors import (
    BaseDetector, ExactRepeatDetector, SemanticSimilarityDetector, 
    CostVelocityDetector, OscillationDetector, DetectionResult
)
from agentloopguard.exceptions import LoopDetectedError
from agentloopguard.utils import estimate_cost

logger = logging.getLogger(__name__)

class GuardSession:
    def __init__(self, guard: 'LoopGuard'):
        self.guard = guard
        self.call_history: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
    def record(self, step: Dict[str, Any]) -> None:
        """Record a step, run detectors, and update budget."""
        with self._lock:
            # Enforce required keys or populate defaults
            step.setdefault("timestamp", time.time())
            
            model = step.get("model", "unknown")
            in_tokens = step.get("input_tokens", 0)
            out_tokens = step.get("output_tokens", 0)
            step["cost_usd"] = estimate_cost(model, in_tokens, out_tokens)
            
            self.call_history.append(step)
            
            # Update Budget
            if self.guard.budget:
                self.guard.budget.record(model, in_tokens, out_tokens)
                
            # Run Detectors
            for detector in self.guard.detectors:
                result = detector.check(self.call_history)
                if result:
                    self.guard._handle_alert(result)

    def summary(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "history_length": len(self.call_history),
                "budget": self.guard.budget.summary() if self.guard.budget else None
            }
            
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class LoopGuard:
    def __init__(
        self,
        max_iterations: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_duration_seconds: Optional[int] = None,
        on_alert: str = "raise",
        alert_callback: Optional[Callable[[DetectionResult], None]] = None,
        detectors: Optional[List[BaseDetector]] = None
    ):
        self.on_alert = on_alert
        self.alert_callback = alert_callback
        
        self.budget = BudgetTracker(
            max_iterations=max_iterations,
            max_cost_usd=max_cost_usd,
            max_tokens=max_tokens,
            max_duration_seconds=max_duration_seconds
        )
        
        if detectors is None:
            self.detectors = [
                ExactRepeatDetector(),
                SemanticSimilarityDetector(),
                CostVelocityDetector(),
                OscillationDetector()
            ]
        else:
            self.detectors = detectors

    def _handle_alert(self, result: DetectionResult):
        if self.alert_callback:
            self.alert_callback(result)
            
        if self.on_alert == "log":
            logger.warning(f"LoopGuard Alert: {result.description} ({result.detector_name})")
        elif self.on_alert == "raise":
            raise LoopDetectedError(
                f"Loop detected by {result.detector_name}: {result.description}",
                loop_type=result.detector_name,
                iteration_count=self.budget.iterations if self.budget else 0,
                pattern_description=result.description
            )

    def session(self) -> GuardSession:
        return GuardSession(self)

    def watch(self, model: str = "unknown"):
        """Decorator to watch a function call.

        Uses a persistent session so that loop detection works across
        multiple invocations of the decorated function.
        """
        def decorator(func):
            _session = self.session()

            @wraps(func)
            def wrapper(*args, **kwargs):
                res = func(*args, **kwargs)
                _session.record({
                    "tool_name": func.__name__,
                    "tool_args": kwargs,
                    "model": model,
                    "output": str(res),
                })
                return res
            wrapper._guard_session = _session  # expose for testing
            return wrapper
        return decorator
