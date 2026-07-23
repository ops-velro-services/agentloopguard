"""Tests for pricing provider abstraction, exact alias matching, and unknown model policies."""

import pytest

from agentloopguard import (
    BudgetExceededError,
    BudgetTracker,
    LoopGuard,
    ModelRates,
    PricingSnapshot,
    UnknownModelError,
    resolve_cost,
)
from agentloopguard.pricing import DEFAULT_PRICING_SNAPSHOT


def test_builtin_snapshot_exact_alias_matching():
    """Verify built-in snapshot matches exact model names and aliases without collisions."""
    # gpt-4o: input 5.0, output 15.0 per million
    res_gpt4o = resolve_cost("gpt-4o", 1_000_000, 1_000_000)
    assert res_gpt4o.cost_usd == pytest.approx(20.0)
    assert res_gpt4o.source == "builtin_snapshot"
    assert res_gpt4o.snapshot_version == DEFAULT_PRICING_SNAPSHOT.version
    assert res_gpt4o.effective_date == DEFAULT_PRICING_SNAPSHOT.effective_date

    # gpt-4o-mini: input 0.15, output 0.60 per million
    res_mini = resolve_cost("gpt-4o-mini", 1_000_000, 1_000_000)
    assert res_mini.cost_usd == pytest.approx(0.75)
    assert res_mini.source == "builtin_snapshot"

    # Alias matching
    res_alias = resolve_cost("claude-3-5-sonnet-20240620", 1_000_000, 1_000_000)
    assert res_alias.cost_usd == pytest.approx(18.0)  # 3.0 + 15.0
    assert res_alias.source == "builtin_snapshot"


def test_no_substring_collision_on_unknown_variants():
    """Verify that a model like 'gpt-4o-custom-variant' does NOT match 'gpt-4o' via substring."""
    with pytest.raises(UnknownModelError):
        resolve_cost("gpt-4o-custom-variant", 1_000, 1_000, unknown_model_policy="fail_closed")

    # When zero-cost opt-in policy is used:
    res_zero = resolve_cost("gpt-4o-custom-variant", 1_000, 1_000, unknown_model_policy="zero")
    assert res_zero.cost_usd == 0.0
    assert res_zero.source == "zero_cost"


def test_priority_1_actual_cost_override():
    """Actual cost overrides both custom providers and built-in snapshots."""
    custom_provider = {"gpt-4o": {"input": 10.0, "output": 20.0}}
    res = resolve_cost(
        "gpt-4o",
        1_000_000,
        1_000_000,
        actual_cost_usd=0.042,
        price_provider=custom_provider,
    )
    assert res.cost_usd == pytest.approx(0.042)
    assert res.source == "actual_cost"


def test_priority_2_custom_provider_dict():
    """Custom dictionary provider takes precedence over built-in snapshot."""
    custom_provider = {
        "custom-model": {"input": 2.0, "output": 4.0},
        "gpt-4o": {"input": 1.0, "output": 1.0},
    }
    res_custom = resolve_cost("custom-model", 1_000_000, 1_000_000, price_provider=custom_provider)
    assert res_custom.cost_usd == pytest.approx(6.0)
    assert res_custom.source == "custom_provider"

    # gpt-4o overridden by custom provider
    res_gpt4o = resolve_cost("gpt-4o", 1_000_000, 1_000_000, price_provider=custom_provider)
    assert res_gpt4o.cost_usd == pytest.approx(2.0)
    assert res_gpt4o.source == "custom_provider"


def test_priority_2_custom_provider_callable():
    """Custom callable provider returning step cost or rate dict."""

    def provider_fn(model: str, in_tok: int, out_tok: int):
        if model == "my-fine-tune":
            return 0.123
        return None

    res = resolve_cost("my-fine-tune", 500, 500, price_provider=provider_fn)
    assert res.cost_usd == pytest.approx(0.123)
    assert res.source == "custom_provider"

    # Fallback to built-in when callable returns None
    res_builtin = resolve_cost("gpt-4o-mini", 1_000_000, 1_000_000, price_provider=provider_fn)
    assert res_builtin.cost_usd == pytest.approx(0.75)
    assert res_builtin.source == "builtin_snapshot"


def test_custom_pricing_snapshot():
    """User-supplied custom PricingSnapshot with custom version and metadata."""
    custom_snapshot = PricingSnapshot(
        version="2026.custom",
        effective_date="2026-07-23",
        source_url="https://example.com/pricing",
        rates={"my-model": ModelRates(1.0, 2.0)},
    )
    res = resolve_cost("my-model", 1_000_000, 1_000_000, snapshot=custom_snapshot)
    assert res.cost_usd == pytest.approx(3.0)
    assert res.source == "builtin_snapshot"
    assert res.snapshot_version == "2026.custom"
    assert res.effective_date == "2026-07-23"


def test_guard_session_unknown_model_fail_closed():
    """LoopGuard with max_cost_usd fails closed when recording an unknown model."""
    guard = LoopGuard(max_cost_usd=1.0)
    session = guard.session()

    with pytest.raises(UnknownModelError):
        session.record({"model": "unknown-fine-tune-99", "input_tokens": 100, "output_tokens": 100})


def test_guard_session_unknown_model_opt_in_zero_cost():
    """LoopGuard with explicit unknown_model_policy='zero' permits unknown models as free."""
    guard = LoopGuard(max_cost_usd=1.0, unknown_model_policy="zero")
    session = guard.session()

    session.record({"model": "unknown-fine-tune-99", "input_tokens": 100, "output_tokens": 100})
    summary = session.summary()
    assert summary["budget"]["total_cost_usd"] == 0.0
    assert session.call_history[0]["cost_source"] == "zero_cost"


def test_guard_session_actual_cost_usd_record():
    """Passing actual_cost_usd in step record is preserved and updates cost budget correctly."""
    guard = LoopGuard(max_cost_usd=0.10)
    session = guard.session()

    session.record(
        {
            "model": "any-unknown-model",
            "input_tokens": 100,
            "output_tokens": 100,
            "actual_cost_usd": 0.05,
        }
    )
    assert session.call_history[0]["cost_source"] == "actual_cost"
    assert session.call_history[0]["cost_usd"] == 0.05

    # Exceeding budget with actual cost
    with pytest.raises(BudgetExceededError):
        session.record(
            {
                "model": "any-unknown-model",
                "input_tokens": 100,
                "output_tokens": 100,
                "actual_cost_usd": 0.06,
            }
        )


def test_budget_tracker_pricing_provider_integration():
    """BudgetTracker correctly uses custom price provider."""
    tracker = BudgetTracker(
        max_cost_usd=5.0,
        price_provider={"custom-llm": {"input": 1.0, "output": 1.0}},
    )
    tracker.record("custom-llm", 1_000_000, 1_000_000)
    assert tracker.total_cost_usd == pytest.approx(2.0)
