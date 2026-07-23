"""Pricing provider abstraction and cost resolution for AgentLoopGuard."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, Union

from agentloopguard.exceptions import UnknownModelError

PRICING_SNAPSHOT_VERSION = "2026.01"
PRICING_EFFECTIVE_DATE = "2026-01-01"
PRICING_SOURCE_URL = (
    "https://github.com/ops-velro-services/agentloopguard/blob/main/src/agentloopguard/pricing.py"
)


@dataclass(frozen=True)
class ModelRates:
    """Cost in USD per 1,000,000 tokens."""

    input_cost_per_million: float
    output_cost_per_million: float


@dataclass(frozen=True)
class PricingSnapshot:
    """Versioned price snapshot for built-in model rates."""

    version: str
    effective_date: str
    source_url: str
    rates: Mapping[str, ModelRates]
    aliases: Mapping[str, str] = field(default_factory=dict)


DEFAULT_RATES: dict[str, ModelRates] = {
    "gpt-4o": ModelRates(5.0, 15.0),
    "gpt-4o-mini": ModelRates(0.15, 0.60),
    "gpt-4-turbo": ModelRates(10.0, 30.0),
    "gpt-3.5-turbo": ModelRates(0.50, 1.50),
    "claude-3.5-sonnet": ModelRates(3.0, 15.0),
    "claude-3-haiku": ModelRates(0.25, 1.25),
    "claude-3-opus": ModelRates(15.0, 75.0),
    "gemini-1.5-pro": ModelRates(3.5, 10.5),
    "gemini-1.5-flash": ModelRates(0.075, 0.30),
    "gemini-2.0-flash": ModelRates(0.10, 0.40),
}

DEFAULT_ALIASES: dict[str, str] = {
    "gpt-4o-2024-05-13": "gpt-4o",
    "gpt-4o-2024-08-06": "gpt-4o",
    "gpt-4o-mini-2024-07-18": "gpt-4o-mini",
    "gpt-4-turbo-2024-04-09": "gpt-4-turbo",
    "claude-3-5-sonnet": "claude-3.5-sonnet",
    "claude-3-5-sonnet-20240620": "claude-3.5-sonnet",
    "claude-3-5-sonnet-20241022": "claude-3.5-sonnet",
    "claude-3-5-haiku": "claude-3-haiku",
    "claude-3-haiku-20240307": "claude-3-haiku",
    "claude-3-opus-20240229": "claude-3-opus",
}

DEFAULT_PRICING_SNAPSHOT = PricingSnapshot(
    version=PRICING_SNAPSHOT_VERSION,
    effective_date=PRICING_EFFECTIVE_DATE,
    source_url=PRICING_SOURCE_URL,
    rates=DEFAULT_RATES,
    aliases=DEFAULT_ALIASES,
)


@dataclass(frozen=True)
class PricingEstimate:
    cost_usd: float
    source: str  # "actual_cost", "custom_provider", "builtin_snapshot", "zero_cost"
    snapshot_version: Optional[str] = None
    effective_date: Optional[str] = None
    model: str = ""


PriceProviderType = Union[
    Callable[..., Any],
    Mapping[str, Any],
]


def resolve_cost(
    model: str,
    input_tokens: int,
    output_tokens: int,
    actual_cost_usd: Optional[float] = None,
    price_provider: Optional[PriceProviderType] = None,
    unknown_model_policy: str = "fail_closed",
    snapshot: Optional[PricingSnapshot] = None,
) -> PricingEstimate:
    """Resolve step cost: actual cost -> price provider -> built-in snapshot."""
    active_snapshot = snapshot or DEFAULT_PRICING_SNAPSHOT

    # 1. User-supplied actual cost
    if actual_cost_usd is not None:
        if (
            isinstance(actual_cost_usd, bool)
            or not isinstance(actual_cost_usd, (int, float))
            or actual_cost_usd < 0
        ):
            raise ValueError("actual_cost_usd must be a non-negative number")
        return PricingEstimate(
            cost_usd=float(actual_cost_usd),
            source="actual_cost",
            snapshot_version=active_snapshot.version,
            effective_date=active_snapshot.effective_date,
            model=model,
        )

    # 0 tokens cost $0.00
    if input_tokens == 0 and output_tokens == 0:
        return PricingEstimate(
            cost_usd=0.0,
            source="zero_cost",
            snapshot_version=active_snapshot.version,
            effective_date=active_snapshot.effective_date,
            model=model,
        )

    norm_model = model.strip().lower()

    # 2. Custom price provider
    if price_provider is not None:
        custom_res = _try_custom_provider(
            price_provider, model, norm_model, input_tokens, output_tokens
        )
        if custom_res is not None:
            return PricingEstimate(
                cost_usd=custom_res,
                source="custom_provider",
                snapshot_version=active_snapshot.version,
                effective_date=active_snapshot.effective_date,
                model=model,
            )

    # 3. Built-in snapshot with exact alias matching (NO substring matching)
    rates = _lookup_snapshot_rates(active_snapshot, norm_model)
    if rates is not None:
        cost = (input_tokens / 1_000_000 * rates.input_cost_per_million) + (
            output_tokens / 1_000_000 * rates.output_cost_per_million
        )
        return PricingEstimate(
            cost_usd=cost,
            source="builtin_snapshot",
            snapshot_version=active_snapshot.version,
            effective_date=active_snapshot.effective_date,
            model=model,
        )

    # 4. Unknown model handling
    if unknown_model_policy in {"fail_closed", "raise"}:
        msg = f"Unknown model '{model}' and no price provider or actual cost given."
        raise UnknownModelError(msg)
    elif unknown_model_policy in {"zero", "allow"}:
        return PricingEstimate(
            cost_usd=0.0,
            source="zero_cost",
            snapshot_version=active_snapshot.version,
            effective_date=active_snapshot.effective_date,
            model=model,
        )
    else:
        raise ValueError(f"Invalid unknown_model_policy: '{unknown_model_policy}'")


def _lookup_snapshot_rates(snapshot: PricingSnapshot, norm_model: str) -> Optional[ModelRates]:
    if norm_model in snapshot.rates:
        return snapshot.rates[norm_model]
    if norm_model in snapshot.aliases:
        target = snapshot.aliases[norm_model]
        return snapshot.rates.get(target)
    return None


def _try_custom_provider(
    provider: PriceProviderType,
    raw_model: str,
    norm_model: str,
    input_tokens: int,
    output_tokens: int,
) -> Optional[float]:
    if callable(provider):
        try:
            val = provider(raw_model, input_tokens, output_tokens)
        except TypeError:
            val = provider(raw_model)
        return _extract_cost_from_val(val, input_tokens, output_tokens)
    elif isinstance(provider, Mapping):
        entry = provider.get(raw_model)
        if entry is None:
            entry = provider.get(norm_model)
        if entry is None:
            for k, v in provider.items():
                if isinstance(k, str) and k.strip().lower() == norm_model:
                    entry = v
                    break
        if entry is not None:
            return _extract_cost_from_val(entry, input_tokens, output_tokens)
    return None


def _extract_cost_from_val(val: Any, input_tokens: int, output_tokens: int) -> Optional[float]:
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, (int, float)):
        return float(val)
    if isinstance(val, Mapping):
        in_rate = val.get("input") or val.get("input_cost_per_million") or 0.0
        out_rate = val.get("output") or val.get("output_cost_per_million") or 0.0
        return (input_tokens / 1_000_000 * float(in_rate)) + (
            output_tokens / 1_000_000 * float(out_rate)
        )
    return None
