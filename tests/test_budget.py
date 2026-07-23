import pytest

from agentloopguard.budget import BudgetTracker
from agentloopguard.exceptions import BudgetExceededError, DurationExceededError


def test_budget_tracker_cost_exceeded():
    tracker = BudgetTracker(max_cost_usd=0.01)
    with pytest.raises(BudgetExceededError) as exc:
        tracker.record("gpt-4o", 1000000, 1000000)
    assert exc.value.budget_type == "cost"


def test_budget_tracker_tokens_exceeded():
    tracker = BudgetTracker(max_tokens=100)
    tracker.record("gpt-3.5-turbo", 50, 40)
    with pytest.raises(BudgetExceededError) as exc:
        tracker.record("gpt-3.5-turbo", 10, 10)
    assert exc.value.budget_type == "tokens"


def test_budget_tracker_iterations():
    tracker = BudgetTracker(max_iterations=2)
    tracker.record("gpt-4o-mini", 10, 10)
    tracker.record("gpt-4o-mini", 10, 10)
    with pytest.raises(BudgetExceededError) as exc:
        tracker.record("gpt-4o-mini", 10, 10)
    assert exc.value.budget_type == "iterations"


def test_budget_warnings():
    warnings = []

    def cb(msg, ratio):
        warnings.append(msg)

    tracker = BudgetTracker(max_tokens=100, warning_callback=cb)
    tracker.record("gpt-4o", 50, 0)
    assert len(warnings) == 1
    assert "tokens budget at 50%" in warnings[0]

    tracker.record("gpt-4o", 25, 0)
    assert len(warnings) == 2
    assert "tokens budget at 75%" in warnings[1]


@pytest.mark.parametrize(
    "kwargs",
    [
        {"max_cost_usd": 0},
        {"max_cost_usd": float("nan")},
        {"max_tokens": 1.2},
        {"max_iterations": False},
        {"max_duration_seconds": -2},
        {"warning_callback": object()},
    ],
)
def test_budget_tracker_rejects_invalid_configuration(kwargs):
    with pytest.raises((TypeError, ValueError)):
        BudgetTracker(**kwargs)


@pytest.mark.parametrize("tokens", [(-1, 0), (0, -1), (True, 0), (0, 1.5)])
def test_budget_tracker_rejects_invalid_token_counts(tokens):
    with pytest.raises(ValueError):
        BudgetTracker().record("gpt-4o", *tokens)


def test_duration_uses_injectable_monotonic_clock_without_sleeping():
    clock = [100.0]
    tracker = BudgetTracker(max_duration_seconds=5, clock=lambda: clock[0])

    clock[0] = 104.5
    assert tracker.elapsed_seconds == 4.5
    tracker.record("gpt-4o", 0, 0)

    clock[0] = 106.0
    with pytest.raises(DurationExceededError):
        tracker.record("gpt-4o", 0, 0)


def test_duration_does_not_go_negative_when_an_injected_clock_moves_backwards():
    clock = [100.0]
    tracker = BudgetTracker(max_duration_seconds=1, clock=lambda: clock[0])

    clock[0] = 90.0
    assert tracker.elapsed_seconds == 0.0
    tracker.record("gpt-4o", 0, 0)
