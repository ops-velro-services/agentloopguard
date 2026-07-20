"""Budget tracking for AgentLoopGuard."""
import time
from typing import Dict, Optional, Callable, Any

from agentloopguard.exceptions import BudgetExceededError, DurationExceededError
from agentloopguard.utils import estimate_cost

class BudgetTracker:
    """Tracks token usage, cost, time, and iterations against limits."""
    
    def __init__(
        self,
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_iterations: Optional[int] = None,
        max_duration_seconds: Optional[int] = None,
        warning_callback: Optional[Callable[[str, float], None]] = None
    ):
        self.max_cost_usd = max_cost_usd
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations
        self.max_duration_seconds = max_duration_seconds
        self.warning_callback = warning_callback
        
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.iterations = 0
        self.start_time = time.time()
        
        self._warnings_emitted: Dict[str, set] = {
            "cost": set(),
            "tokens": set(),
            "iterations": set(),
            "duration": set()
        }

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens
        
    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.start_time

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Record usage for a step."""
        self.iterations += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_cost_usd += estimate_cost(model, input_tokens, output_tokens)
        
        self.check()

    def _check_warnings(self, metric_type: str, current: float, limit: float) -> None:
        if not self.warning_callback or limit <= 0:
            return
        
        ratio = current / limit
        thresholds = [0.5, 0.75, 0.9]
        
        for t in thresholds:
            if ratio >= t and t not in self._warnings_emitted[metric_type]:
                self._warnings_emitted[metric_type].add(t)
                self.warning_callback(f"{metric_type} budget at {int(t*100)}%", ratio)

    def check(self) -> None:
        """Check if any limits are exceeded and emit warnings if approaching limits."""
        # Cost check
        if self.max_cost_usd is not None:
            self._check_warnings("cost", self.total_cost_usd, self.max_cost_usd)
            if self.total_cost_usd > self.max_cost_usd:
                raise BudgetExceededError(
                    f"Max cost exceeded: ${self.total_cost_usd:.4f} > ${self.max_cost_usd:.4f}",
                    "cost", self.max_cost_usd, self.total_cost_usd
                )
                
        # Token check
        if self.max_tokens is not None:
            self._check_warnings("tokens", self.total_tokens, self.max_tokens)
            if self.total_tokens > self.max_tokens:
                raise BudgetExceededError(
                    f"Max tokens exceeded: {self.total_tokens} > {self.max_tokens}",
                    "tokens", self.max_tokens, self.total_tokens
                )
                
        # Iteration check
        if self.max_iterations is not None:
            self._check_warnings("iterations", self.iterations, self.max_iterations)
            if self.iterations > self.max_iterations:
                raise BudgetExceededError(
                    f"Max iterations exceeded: {self.iterations} > {self.max_iterations}",
                    "iterations", self.max_iterations, self.iterations
                )
                
        # Duration check
        if self.max_duration_seconds is not None:
            elapsed = self.elapsed_seconds
            self._check_warnings("duration", elapsed, self.max_duration_seconds)
            if elapsed > self.max_duration_seconds:
                raise DurationExceededError(
                    f"Max duration exceeded: {elapsed:.1f}s > {self.max_duration_seconds}s"
                )

    def summary(self) -> Dict[str, Any]:
        """Return summary of current budget."""
        return {
            "total_tokens": self.total_tokens,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "iterations": self.iterations,
            "elapsed_seconds": self.elapsed_seconds
        }
