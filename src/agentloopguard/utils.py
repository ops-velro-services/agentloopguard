"""Utility functions for AgentLoopGuard."""

import hashlib
import json
import math
from collections.abc import Mapping
from dataclasses import fields, is_dataclass
from typing import Any, Optional


def _type_name(value: Any) -> str:
    value_type = type(value)
    return f"{value_type.__module__}.{value_type.__qualname__}"


def _safe_repr(value: Any) -> str:
    try:
        return repr(value)
    except Exception:
        return f"<{_type_name(value)} unrepresentable>"


def canonicalize_call_value(value: Any, seen: Optional[set[int]] = None) -> Any:
    """Return a JSON-safe, deterministic representation of a call argument.

    Native JSON values retain their shape. Common Python containers, dataclasses,
    and mapping-like SDK values are normalized recursively. Unsupported values use
    their qualified type name and a safe ``repr`` fallback, so they never prevent
    loop detection from recording a call.
    """
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else {"__float__": repr(value)}
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}

    active = seen if seen is not None else set()
    value_id = id(value)
    if value_id in active:
        return {"__cycle__": _type_name(value)}

    active.add(value_id)
    try:
        if isinstance(value, Mapping):
            items = [
                (canonicalize_call_value(key, active), canonicalize_call_value(item, active))
                for key, item in value.items()
            ]
            items.sort(key=lambda pair: json.dumps(pair[0], sort_keys=True, default=_safe_repr))
            return {"__mapping__": items}
        if isinstance(value, (list, tuple)):
            return {
                "__sequence__": [canonicalize_call_value(item, active) for item in value],
                "__type__": _type_name(value),
            }
        if isinstance(value, (set, frozenset)):
            items = [canonicalize_call_value(item, active) for item in value]
            items.sort(key=lambda item: json.dumps(item, sort_keys=True, default=_safe_repr))
            return {"__set__": items, "__type__": _type_name(value)}
        if is_dataclass(value) and not isinstance(value, type):
            return {
                "__dataclass__": _type_name(value),
                "value": {
                    field.name: canonicalize_call_value(getattr(value, field.name), active)
                    for field in fields(value)
                },
            }
        return {"__object__": _type_name(value), "__repr__": _safe_repr(value)}
    finally:
        active.remove(value_id)


def hash_call(tool_name: str, args: dict[str, Any]) -> str:
    """Deterministic hash of a tool call, including non-JSON arguments safely."""
    call_repr = json.dumps(
        canonicalize_call_value({"name": tool_name, "args": args}),
        sort_keys=True,
        separators=(",", ":"),
        default=_safe_repr,
    )
    return hashlib.sha256(call_repr.encode("utf-8")).hexdigest()


def simple_tokenize(text: str) -> list[str]:
    """Basic whitespace tokenizer."""
    if not text:
        return []
    return [word.lower().strip(".,!?()[]{}\"'") for word in text.split() if word.strip()]


def tfidf_vector(text: str, vocabulary: list[str]) -> list[float]:
    """Simple TF-IDF vectorization without external deps."""
    tokens = simple_tokenize(text)
    if not tokens or not vocabulary:
        return [0.0] * len(vocabulary)

    # TF
    tf: dict[str, float] = {}
    total_tokens = len(tokens)
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1 / total_tokens

    # IDF (simplified - assumes doc frequency is 1 for words present, 2 for vocabulary)
    # This is a hacky way to do it for single comparisons without a full corpus
    vec = []
    for word in vocabulary:
        val = tf.get(word, 0.0)
        # simplistic idf weight for demonstration
        vec.append(val * 1.5)
    return vec


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Simple cosine similarity."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return dot_product / (norm_a * norm_b)


PRICING_TABLE = {
    "gpt-4o": {"input": 5.0, "output": 15.0},
    "gpt-4o-mini": {"input": 0.150, "output": 0.600},
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
    "claude-3.5-sonnet": {"input": 3.0, "output": 15.0},
    "claude-3-haiku": {"input": 0.25, "output": 1.25},
    "claude-3-opus": {"input": 15.0, "output": 75.0},
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.30},
    "gemini-2.0-flash": {"input": 0.10, "output": 0.40},
}


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    """Estimate cost in USD for a given model and token usage."""
    model_lower = model.lower()
    for key, rates in PRICING_TABLE.items():
        if key in model_lower:
            cost_in = (input_tokens / 1_000_000) * rates["input"]
            cost_out = (output_tokens / 1_000_000) * rates["output"]
            return cost_in + cost_out
    return 0.0
