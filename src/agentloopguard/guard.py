"""Main Guard module for AgentLoopGuard."""

import inspect
import logging
import math
import threading
import time
import uuid
from collections.abc import Mapping
from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable, Optional, Union

from agentloopguard.budget import BudgetTracker, validate_usage_inputs
from agentloopguard.detectors import (
    BaseDetector,
    CostVelocityDetector,
    DetectionResult,
    ExactRepeatDetector,
    LexicalSimilarityDetector,
    OscillationDetector,
)
from agentloopguard.exceptions import LoopDetectedError
from agentloopguard.pricing import PriceProviderType, resolve_cost
from agentloopguard.schema import StepEvent, TelemetryEvent

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class _BudgetConfig:
    max_iterations: Optional[int]
    max_cost_usd: Optional[float]
    max_tokens: Optional[int]
    max_duration_seconds: Optional[int]
    price_provider: Optional[PriceProviderType]
    unknown_model_policy: Optional[str]
    clock: Callable[[], float]


class GuardSession:
    def __init__(self, guard: "LoopGuard"):
        self.guard = guard
        self.session_id = str(uuid.uuid4())
        self.call_history: list[dict[str, Any]] = []
        self.events: list[DetectionResult] = []
        self.budget = BudgetTracker(
            max_iterations=guard._budget_config.max_iterations,
            max_cost_usd=guard._budget_config.max_cost_usd,
            max_tokens=guard._budget_config.max_tokens,
            max_duration_seconds=guard._budget_config.max_duration_seconds,
            price_provider=guard._budget_config.price_provider,
            unknown_model_policy=guard._budget_config.unknown_model_policy,
            clock=guard._budget_config.clock,
        )
        self._lock = threading.Lock()

    def record(self, step: Union[Mapping[str, Any], StepEvent]) -> None:
        """Record a step, run detectors, and update budget."""
        if isinstance(step, StepEvent):
            recorded_step = step.to_dict()
        elif isinstance(step, Mapping):
            recorded_step = dict(step)
        else:
            raise TypeError("step must be a mapping")
        timestamp = recorded_step.get("timestamp", time.time())
        if (
            isinstance(timestamp, bool)
            or not isinstance(timestamp, (int, float))
            or not math.isfinite(timestamp)
        ):
            raise ValueError("timestamp must be a finite number")
        recorded_step["timestamp"] = float(timestamp)

        actual_cost = recorded_step.get("actual_cost_usd")
        if (
            actual_cost is None
            and "cost_usd" in recorded_step
            and isinstance(step, Mapping)
            and not isinstance(step, StepEvent)
        ):
            actual_cost = recorded_step.get("cost_usd")

        model = recorded_step.get("model", "unknown")
        input_tokens = recorded_step.get("input_tokens", 0)
        output_tokens = recorded_step.get("output_tokens", 0)
        validate_usage_inputs(model, input_tokens, output_tokens)
        with self._lock:
            estimate = resolve_cost(
                model,
                input_tokens,
                output_tokens,
                actual_cost_usd=actual_cost,
                price_provider=self.guard.price_provider,
                unknown_model_policy=self.guard.unknown_model_policy,
            )
            cost_usd = estimate.cost_usd
            known_keys = {
                "schema_version",
                "session_id",
                "timestamp",
                "model",
                "input_tokens",
                "output_tokens",
                "cost_usd",
                "cost_source",
                "pricing_snapshot_version",
                "pricing_effective_date",
                "actual_cost_usd",
                "tool_name",
                "tool_args",
                "output",
                "exception",
            }
            event = StepEvent(
                session_id=self.session_id,
                timestamp=float(timestamp),
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=cost_usd,
                cost_source=estimate.source,
                pricing_snapshot_version=estimate.snapshot_version,
                pricing_effective_date=estimate.effective_date,
                tool_name=recorded_step.get("tool_name"),
                tool_args=recorded_step.get("tool_args"),
                output=recorded_step.get("output"),
                exception=recorded_step.get("exception"),
                extra={key: value for key, value in recorded_step.items() if key not in known_keys},
            )
            recorded_step = event.to_dict()

            self.call_history.append(recorded_step)
            if not self.guard.full_history:
                del self.call_history[: -self.guard._history_window]

            # Update Budget
            self.budget.record(model, input_tokens, output_tokens, actual_cost_usd=actual_cost)
            self.guard._emit_event(
                TelemetryEvent(
                    name="agentloopguard.step",
                    timestamp=event.timestamp,
                    attributes={
                        "agentloopguard.schema.version": event.schema_version,
                        "agentloopguard.session.id": event.session_id,
                        "agentloopguard.model": event.model,
                        "agentloopguard.input_tokens": event.input_tokens,
                        "agentloopguard.output_tokens": event.output_tokens,
                        "agentloopguard.cost_usd": event.cost_usd,
                        "agentloopguard.cost_source": event.cost_source or "",
                        "agentloopguard.tool.name": event.tool_name or "",
                    },
                )
            )

            # Run Detectors
            for detector in self.guard.detectors:
                result = detector.check(self.call_history)
                if result:
                    contextual_result = result.with_context(self.session_id, event.timestamp)
                    self.events.append(contextual_result)
                    self.guard._emit_event(
                        TelemetryEvent(
                            name="agentloopguard.detection",
                            timestamp=contextual_result.timestamp or event.timestamp,
                            attributes={
                                "agentloopguard.schema.version": contextual_result.schema_version,
                                "agentloopguard.session.id": contextual_result.session_id or "",
                                "agentloopguard.detector.id": contextual_result.detector_id,
                                "agentloopguard.detector.name": contextual_result.detector_name,
                                "agentloopguard.confidence": contextual_result.confidence,
                                "agentloopguard.recommended_action": (
                                    contextual_result.recommended_action
                                ),
                            },
                        )
                    )
                    self.guard._handle_alert(contextual_result, self.budget.iterations)

    def summary(self) -> dict[str, Any]:
        with self._lock:
            return {
                "session_id": self.session_id,
                "history_length": len(self.call_history),
                "event_count": len(self.events),
                "budget": self.budget.summary(),
            }

    def __enter__(self) -> "GuardSession":
        return self

    def __exit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Any,
    ) -> None:
        return None


class LoopGuard:
    """Main circuit-breaker guard for agent sessions.

    Note:
        `max_duration_seconds` is evaluated as an inter-step check whenever
        `record()` is called on a session. If an external model or tool call
        hangs mid-step, execution inside that call is not interrupted; a
        `DurationExceededError` is raised on the subsequent step recorded after
        the duration limit expires.
    """

    def __init__(
        self,
        max_iterations: Optional[int] = None,
        max_cost_usd: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_duration_seconds: Optional[int] = None,
        price_provider: Optional[PriceProviderType] = None,
        unknown_model_policy: Optional[str] = None,
        on_alert: str = "raise",
        alert_callback: Optional[Callable[[DetectionResult], None]] = None,
        event_exporter: Optional[Callable[[TelemetryEvent], None]] = None,
        detectors: Optional[list[BaseDetector]] = None,
        full_history: bool = False,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if on_alert not in {"raise", "log", "callback"}:
            raise ValueError("on_alert must be one of: 'raise', 'log', 'callback'")
        if alert_callback is not None and not callable(alert_callback):
            raise TypeError("alert_callback must be callable when provided")
        if event_exporter is not None and not callable(event_exporter):
            raise TypeError("event_exporter must be callable when provided")
        if on_alert == "callback" and alert_callback is None:
            raise ValueError("alert_callback is required when on_alert='callback'")
        if not isinstance(full_history, bool):
            raise TypeError("full_history must be a bool")
        if not callable(clock):
            raise TypeError("clock must be callable")
        BudgetTracker(
            max_iterations=max_iterations,
            max_cost_usd=max_cost_usd,
            max_tokens=max_tokens,
            max_duration_seconds=max_duration_seconds,
            price_provider=price_provider,
            unknown_model_policy=unknown_model_policy,
            clock=clock,
        )
        self.on_alert = on_alert
        self.alert_callback = alert_callback
        self.event_exporter = event_exporter
        self.price_provider = price_provider
        self.unknown_model_policy = (
            unknown_model_policy
            if unknown_model_policy is not None
            else ("fail_closed" if max_cost_usd is not None else "zero")
        )

        self._budget_config = _BudgetConfig(
            max_iterations=max_iterations,
            max_cost_usd=max_cost_usd,
            max_tokens=max_tokens,
            max_duration_seconds=max_duration_seconds,
            price_provider=price_provider,
            unknown_model_policy=self.unknown_model_policy,
            clock=clock,
        )

        self.detectors: tuple[BaseDetector, ...]
        if detectors is None:
            self.detectors = (
                ExactRepeatDetector(),
                LexicalSimilarityDetector(),
                CostVelocityDetector(),
                OscillationDetector(),
            )
        else:
            self.detectors = tuple(detectors)
        windows = [detector.history_window for detector in self.detectors]
        if not full_history and any(window is None for window in windows):
            raise ValueError("detectors without a finite history_window require full_history=True")
        self.full_history = full_history
        self._history_window = max((window or 1 for window in windows), default=1)

    def _handle_alert(self, result: DetectionResult, iteration_count: int) -> None:
        if self.alert_callback:
            self.alert_callback(result)

        if self.on_alert == "log":
            logger.warning(f"LoopGuard Alert: {result.description} ({result.detector_name})")
        elif self.on_alert == "raise":
            raise LoopDetectedError(
                f"Loop detected by {result.detector_name}: {result.description}",
                loop_type=result.detector_name,
                iteration_count=iteration_count,
                pattern_description=result.description,
            )

    def _emit_event(self, event: TelemetryEvent) -> None:
        """Send a structured telemetry event without making telemetry required."""
        if self.event_exporter is None:
            return
        try:
            self.event_exporter(event)
        except Exception:
            logger.exception("AgentLoopGuard event exporter failed")

    def session(self) -> GuardSession:
        return GuardSession(self)

    def watch(self, model: str = "unknown") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
        """Decorator to watch a function call.

        Uses a persistent session so that loop detection works across
        multiple invocations of the decorated function. Positional and
        keyword arguments are recorded separately. Calls that raise are
        recorded with their exception details before the exception is
        re-raised.
        """

        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            _session = self.session()

            def record_result(
                args: tuple[Any, ...],
                kwargs: dict[str, Any],
                output: Any,
                exception: Optional[Exception] = None,
            ) -> None:
                step = {
                    "tool_name": func.__name__,
                    "tool_args": {"args": args, "kwargs": kwargs},
                    "model": model,
                    "output": str(output),
                }
                if exception is not None:
                    step["exception"] = {
                        "type": type(exception).__name__,
                        "message": str(exception),
                    }
                _session.record(step)

            if inspect.iscoroutinefunction(func):

                @wraps(func)
                async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                    try:
                        result = await func(*args, **kwargs)
                    except Exception as error:
                        record_result(args, kwargs, error, error)
                        raise
                    record_result(args, kwargs, result)
                    return result

                async_wrapper._guard_session = _session  # type: ignore[attr-defined]
                return async_wrapper

            @wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    result = func(*args, **kwargs)
                except Exception as error:
                    record_result(args, kwargs, error, error)
                    raise
                record_result(args, kwargs, result)
                return result

            wrapper._guard_session = _session  # type: ignore[attr-defined]
            return wrapper

        return decorator
