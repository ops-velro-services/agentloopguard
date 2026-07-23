import math

import pytest

from agentloopguard.detectors import (
    CostVelocityDetector,
    ExactRepeatDetector,
    LexicalSimilarityDetector,
    OscillationDetector,
    SemanticSimilarityDetector,
)


def test_exact_repeat_detector():
    det = ExactRepeatDetector(n=3)

    # Not enough
    assert det.check([{"tool_name": "a", "tool_args": {}}]) is None

    # Diff tools
    assert (
        det.check(
            [
                {"tool_name": "a", "tool_args": {}},
                {"tool_name": "a", "tool_args": {}},
                {"tool_name": "b", "tool_args": {}},
            ]
        )
        is None
    )

    # Same
    res = det.check(
        [
            {"tool_name": "a", "tool_args": {"x": 1}},
            {"tool_name": "a", "tool_args": {"x": 1}},
            {"tool_name": "a", "tool_args": {"x": 1}},
        ]
    )
    assert res is not None
    assert res.detector_name == "ExactRepeatDetector"
    assert res.confidence == 1.0


def test_lexical_similarity_detector_reports_measured_similarity():
    det = LexicalSimilarityDetector(threshold=0.9, n=3)

    # Identical outputs should always be caught
    res_identical = det.check(
        [
            {"output": "the quick brown fox jumps over the lazy dog"},
            {"output": "the quick brown fox jumps over the lazy dog"},
            {"output": "the quick brown fox jumps over the lazy dog"},
        ]
    )
    assert res_identical is not None
    assert res_identical.detector_name == "LexicalSimilarityDetector"
    assert res_identical.confidence == 1.0
    assert res_identical.pattern_details["sample_size"] == 3
    assert res_identical.pattern_details["measured_similarity"] == 1.0

    # Completely different outputs should NOT be caught
    res_diff = det.check(
        [
            {"output": "the quick brown fox jumps over the lazy dog"},
            {"output": "completely unrelated text about space rockets and mars"},
            {"output": "another sentence about cooking pasta with tomato sauce"},
        ]
    )
    assert res_diff is None


def test_lexical_similarity_uses_lowest_pair_measurement_and_ignores_blank_retries():
    det = LexicalSimilarityDetector(threshold=0.8, n=3)
    result = det.check(
        [
            {"output": "search index result details"},
            {"output": "search index result"},
            {"output": "search index result"},
        ]
    )
    assert result is not None
    assert result.confidence == pytest.approx(0.8660254038)
    assert result.pattern_details["pair_similarities"] == pytest.approx([0.8660254038, 1.0])

    assert (
        det.check(
            [
                {"output": "retry attempt one"},
                {"output": ""},
                {"output": "retry attempt three"},
            ]
        )
        is None
    )
    assert (
        det.check(
            [
                {"output": "retry attempt one"},
                {"output": "retry attempt two"},
                {"output": "retry attempt three"},
            ]
        )
        is None
    )


def test_semantic_similarity_name_remains_an_alias_for_compatibility():
    assert SemanticSimilarityDetector is LexicalSimilarityDetector


def test_cost_velocity_uses_inclusive_timestamp_window_boundaries():
    detector = CostVelocityDetector(max_usd_per_min=1.0)
    result = detector.check(
        [
            {"timestamp": 100.0, "cost_usd": 1.0},
            {"timestamp": 400.0, "cost_usd": 9.0},
        ]
    )
    assert result is not None
    assert result.pattern_details == {
        "velocity_usd_per_min": 2.0,
        "threshold": 1.0,
        "sample_size": 2,
        "window_seconds": 300.0,
    }

    assert (
        detector.check(
            [
                {"timestamp": 99.0, "cost_usd": 100.0},
                {"timestamp": 100.0, "cost_usd": 0.5},
                {"timestamp": 400.0, "cost_usd": 0.5},
            ]
        )
        is None
    )
    assert (
        detector.check(
            [
                {"timestamp": 400.0, "cost_usd": 10.0},
                {"timestamp": 400.0, "cost_usd": 10.0},
            ]
        )
        is None
    )


def test_oscillation_detector():
    det = OscillationDetector(min_cycles=2)
    history = [
        {"tool_name": "A", "tool_args": {}},
        {"tool_name": "B", "tool_args": {}},
        {"tool_name": "A", "tool_args": {}},
        {"tool_name": "B", "tool_args": {}},
    ]
    res = det.check(history)
    assert res is not None
    assert "A-B oscillation" in res.description


@pytest.mark.parametrize(
    "factory, value",
    [
        (lambda value: ExactRepeatDetector(value), 0),
        (lambda value: SemanticSimilarityDetector(threshold=value), 1.1),
        (lambda value: SemanticSimilarityDetector(threshold=value), math.nan),
        (lambda value: CostVelocityDetector(value), 0),
        (lambda value: OscillationDetector(value), False),
    ],
)
def test_detector_configuration_validation(factory, value):
    with pytest.raises(ValueError):
        factory(value)
