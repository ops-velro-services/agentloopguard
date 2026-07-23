"""Detectors for AgentLoopGuard."""

import math
import time
from collections import Counter
from typing import Any, Optional

from agentloopguard.schema import DetectionResult as DetectionResult
from agentloopguard.utils import cosine_similarity, hash_call, simple_tokenize


class BaseDetector:
    detector_id = "base"

    @property
    def history_window(self) -> Optional[int]:
        """Maximum number of recent calls needed for this detector, if finite."""
        return None

    def check(self, call_history: list[dict[str, Any]]) -> Optional[DetectionResult]:
        raise NotImplementedError


class ExactRepeatDetector(BaseDetector):
    detector_id = "exact_repeat"

    def __init__(self, n: int = 3):
        _validate_positive_integer("n", n)
        self.n = n

    @property
    def history_window(self) -> int:
        return self.n

    def check(self, call_history: list[dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < self.n:
            return None

        recent_calls = call_history[-self.n :]

        # We need tool_name and tool_args
        first_call = recent_calls[0]
        if "tool_name" not in first_call or "tool_args" not in first_call:
            return None

        first_hash = hash_call(first_call["tool_name"], first_call["tool_args"])

        for call in recent_calls[1:]:
            if "tool_name" not in call or "tool_args" not in call:
                return None
            if hash_call(call["tool_name"], call["tool_args"]) != first_hash:
                return None

        return DetectionResult(
            detector_name="ExactRepeatDetector",
            confidence=1.0,
            description=f"Exact same tool call repeated {self.n} times.",
            pattern_details={"tool_name": first_call["tool_name"], "repeats": self.n},
            detector_id=self.detector_id,
            measured_values={"repeats": self.n},
        )


class LexicalSimilarityDetector(BaseDetector):
    """Detect consecutive outputs with high token-overlap cosine similarity.

    This deliberately measures lexical similarity; it does not claim to infer
    semantic meaning. A detection requires ``n`` consecutive non-empty string
    outputs. Empty, non-string, or tokenless outputs break the candidate window,
    so transient blank retry responses do not become false loop detections.
    """

    detector_id = "lexical_similarity"

    def __init__(self, threshold: float = 0.92, n: int = 3):
        if (
            isinstance(threshold, bool)
            or not isinstance(threshold, (int, float))
            or not math.isfinite(threshold)
            or not 0 <= threshold <= 1
        ):
            raise ValueError("threshold must be a finite number between zero and one")
        _validate_positive_integer("n", n)
        self.threshold = threshold
        self.n = n

    @property
    def history_window(self) -> int:
        return self.n

    def check(self, call_history: list[dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < self.n:
            return None

        recent_outputs = [
            output
            for call in call_history[-self.n :]
            if isinstance((output := call.get("output")), str)
        ]
        if len(recent_outputs) != self.n:
            return None

        tokenized_outputs = [simple_tokenize(output) for output in recent_outputs]
        if any(not tokens for tokens in tokenized_outputs):
            return None

        vocabulary = sorted({token for tokens in tokenized_outputs for token in tokens})
        vectors = [
            [float(Counter(tokens)[token]) for token in vocabulary] for tokens in tokenized_outputs
        ]
        similarities = [
            cosine_similarity(vectors[index], vectors[index + 1])
            for index in range(len(vectors) - 1)
        ]
        measured_similarity = min(similarities)
        if measured_similarity < self.threshold:
            return None

        return DetectionResult(
            detector_name="LexicalSimilarityDetector",
            confidence=measured_similarity,
            description=(
                f"Lexical similarity of {measured_similarity:.3f} across "
                f"{self.n} consecutive outputs meets the {self.threshold:.3f} threshold."
            ),
            pattern_details={
                "threshold": self.threshold,
                "measured_similarity": measured_similarity,
                "pair_similarities": similarities,
                "sample_size": self.n,
            },
            detector_id=self.detector_id,
            measured_values={"similarity": measured_similarity, "sample_size": self.n},
        )


# Kept as an import-compatible alias for existing callers. New code should use
# LexicalSimilarityDetector, whose name accurately describes the algorithm.
SemanticSimilarityDetector = LexicalSimilarityDetector


class CostVelocityDetector(BaseDetector):
    detector_id = "cost_velocity"

    def __init__(self, max_usd_per_min: float = 2.0, max_events: int = 1000):
        if (
            isinstance(max_usd_per_min, bool)
            or not isinstance(max_usd_per_min, (int, float))
            or not math.isfinite(max_usd_per_min)
            or max_usd_per_min <= 0
        ):
            raise ValueError("max_usd_per_min must be a finite number greater than zero")
        _validate_positive_integer("max_events", max_events)
        self.max_usd_per_min = max_usd_per_min
        self.max_events = max_events

    @property
    def history_window(self) -> int:
        return self.max_events

    def check(self, call_history: list[dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < 2:
            return None

        # Use an inclusive five-minute event window ending at the latest event,
        # rather than a wall-clock-dependent partial history.
        now = time.time()
        recent_calls = call_history[-self.max_events :]
        latest_timestamp = recent_calls[-1].get("timestamp", now)
        if not isinstance(latest_timestamp, (int, float)):
            return None
        window_start = latest_timestamp - 300
        recent_history = [
            call
            for call in recent_calls
            if isinstance(call.get("timestamp"), (int, float))
            and window_start <= call["timestamp"] <= latest_timestamp
        ]

        if len(recent_history) < 2:
            return None

        total_cost = sum(call.get("cost_usd", 0.0) for call in recent_history)
        duration_sec = latest_timestamp - recent_history[0]["timestamp"]
        if duration_sec <= 0:
            return None

        velocity = (total_cost / duration_sec) * 60

        if velocity > self.max_usd_per_min:
            return DetectionResult(
                detector_name="CostVelocityDetector",
                confidence=1.0,
                description=(
                    f"Cost velocity {velocity:.2f} USD/min exceeds threshold of "
                    f"{self.max_usd_per_min:.2f} USD/min."
                ),
                pattern_details={
                    "velocity_usd_per_min": velocity,
                    "threshold": self.max_usd_per_min,
                    "sample_size": len(recent_history),
                    "window_seconds": duration_sec,
                },
                detector_id=self.detector_id,
                measured_values={
                    "velocity_usd_per_min": velocity,
                    "sample_size": len(recent_history),
                    "window_seconds": duration_sec,
                },
            )
        return None


class OscillationDetector(BaseDetector):
    detector_id = "oscillation"

    def __init__(self, min_cycles: int = 3):
        _validate_positive_integer("min_cycles", min_cycles)
        self.min_cycles = min_cycles

    @property
    def history_window(self) -> int:
        return self.min_cycles * 3

    def check(self, call_history: list[dict[str, Any]]) -> Optional[DetectionResult]:
        if len(call_history) < self.min_cycles * 2:
            return None

        hashes = []
        for call in call_history:
            if "tool_name" in call and "tool_args" in call:
                hashes.append(hash_call(call["tool_name"], call["tool_args"]))
            else:
                hashes.append(str(id(call)))  # Fallback

        # Check A-B-A-B
        seq = hashes[-self.min_cycles * 2 :]
        pattern_len = 2
        is_oscillation = True

        for i in range(self.min_cycles):
            for j in range(pattern_len):
                idx1 = j
                idx2 = i * pattern_len + j
                if seq[idx1] != seq[idx2]:
                    is_oscillation = False
                    break
            if not is_oscillation:
                break

        if is_oscillation:
            return DetectionResult(
                detector_name="OscillationDetector",
                confidence=1.0,
                description=f"Detected A-B oscillation over {self.min_cycles} cycles.",
                pattern_details={"cycle_length": 2, "cycles": self.min_cycles},
                detector_id=self.detector_id,
                measured_values={"cycle_length": 2, "cycles": self.min_cycles},
            )

        # Check A-B-C-A-B-C
        if len(call_history) >= self.min_cycles * 3:
            seq = hashes[-self.min_cycles * 3 :]
            pattern_len = 3
            is_oscillation = True

            for i in range(self.min_cycles):
                for j in range(pattern_len):
                    idx1 = j
                    idx2 = i * pattern_len + j
                    if seq[idx1] != seq[idx2]:
                        is_oscillation = False
                        break
                if not is_oscillation:
                    break

            if is_oscillation:
                return DetectionResult(
                    detector_name="OscillationDetector",
                    confidence=1.0,
                    description=f"Detected A-B-C oscillation over {self.min_cycles} cycles.",
                    pattern_details={"cycle_length": 3, "cycles": self.min_cycles},
                    detector_id=self.detector_id,
                    measured_values={"cycle_length": 3, "cycles": self.min_cycles},
                )

        return None


def _validate_positive_integer(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
