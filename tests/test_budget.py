import pytest
import time
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
