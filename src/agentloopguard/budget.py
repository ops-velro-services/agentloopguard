"""Budget tracking for AgentLoopGuard."""

import math
import time
from typing import Any, Callable, Optional

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
        warning_callback: Optional[Callable[[str, float], None]] = None,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        _validate_positive_number("max_cost_usd", max_cost_usd)
        _validate_positive_integer("max_tokens", max_tokens)
        _validate_positive_integer("max_iterations", max_iterations)
        _validate_positive_number("max_duration_seconds", max_duration_seconds)
        if warning_callback is not None and not callable(warning_callback):
            raise TypeError("warning_callback must be callable when provided")
        if not callable(clock):
            raise TypeError("clock must be callable")
        self.max_cost_usd = max_cost_usd
        self.max_tokens = max_tokens
        self.max_iterations = max_iterations
        self.max_duration_seconds = max_duration_seconds
        self.warning_callback = warning_callback
        self._clock = clock

        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_cost_usd = 0.0
        self.iterations = 0
        self.start_time = self._read_clock()

        self._warnings_emitted: dict[str, set[float]] = {
            "cost": set(),
            "tokens": set(),
            "iterations": set(),
            "duration": set(),
        }

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def elapsed_seconds(self) -> float:
        return max(0.0, self._read_clock() - self.start_time)

    def _read_clock(self) -> float:
        value = self._clock()
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError("clock must return a finite number")
        return float(value)

    def record(self, model: str, input_tokens: int, output_tokens: int) -> None:
        """Record usage for a step."""
        validate_usage_inputs(model, input_tokens, output_tokens)
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
                self.warning_callback(f"{metric_type} budget at {int(t * 100)}%", ratio)

    def check(self) -> None:
        """Check if any limits are exceeded and emit warnings if approaching limits."""
        # Cost check
        if self.max_cost_usd is not None:
            self._check_warnings("cost", self.total_cost_usd, self.max_cost_usd)
            if self.total_cost_usd > self.max_cost_usd:
                raise BudgetExceededError(
                    f"Max cost exceeded: ${self.total_cost_usd:.4f} > ${self.max_cost_usd:.4f}",
                    "cost",
                    self.max_cost_usd,
                    self.total_cost_usd,
                )

        # Token check
        if self.max_tokens is not None:
            self._check_warnings("tokens", self.total_tokens, self.max_tokens)
            if self.total_tokens > self.max_tokens:
                raise BudgetExceededError(
                    f"Max tokens exceeded: {self.total_tokens} > {self.max_tokens}",
                    "tokens",
                    self.max_tokens,
                    self.total_tokens,
                )

        # Iteration check
        if self.max_iterations is not None:
            self._check_warnings("iterations", self.iterations, self.max_iterations)
            if self.iterations > self.max_iterations:
                raise BudgetExceededError(
                    f"Max iterations exceeded: {self.iterations} > {self.max_iterations}",
                    "iterations",
                    self.max_iterations,
                    self.iterations,
                )

        # Duration check
        if self.max_duration_seconds is not None:
            elapsed = self.elapsed_seconds
            self._check_warnings("duration", elapsed, self.max_duration_seconds)
            if elapsed > self.max_duration_seconds:
                raise DurationExceededError(
                    f"Max duration exceeded: {elapsed:.1f}s > {self.max_duration_seconds}s"
                )

    def summary(self) -> dict[str, Any]:
        """Return summary of current budget."""
        return {
            "total_tokens": self.total_tokens,
            "input_tokens": self.total_input_tokens,
            "output_tokens": self.total_output_tokens,
            "total_cost_usd": self.total_cost_usd,
            "iterations": self.iterations,
            "elapsed_seconds": self.elapsed_seconds,
        }


def _validate_positive_number(name: str, value: Optional[float]) -> None:
    if value is None:
        return
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise ValueError(f"{name} must be a finite number greater than zero or None")


def _validate_positive_integer(name: str, value: Optional[int]) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer or None")


def _validate_nonnegative_integer(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def validate_usage_inputs(model: str, input_tokens: int, output_tokens: int) -> None:
    """Validate usage fields before a step is accepted into a session history."""
    if not isinstance(model, str) or not model:
        raise ValueError("model must be a non-empty string")
    _validate_nonnegative_integer("input_tokens", input_tokens)
    _validate_nonnegative_integer("output_tokens", output_tokens)
