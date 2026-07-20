import pytest
from agentloopguard.detectors import (
    ExactRepeatDetector, SemanticSimilarityDetector,
    CostVelocityDetector, OscillationDetector
)

def test_exact_repeat_detector():
    det = ExactRepeatDetector(n=3)
    
    # Not enough
    assert det.check([{"tool_name": "a", "tool_args": {}}]) is None
    
    # Diff tools
    assert det.check([
        {"tool_name": "a", "tool_args": {}},
        {"tool_name": "a", "tool_args": {}},
        {"tool_name": "b", "tool_args": {}}
    ]) is None
    
    # Same
    res = det.check([
        {"tool_name": "a", "tool_args": {"x": 1}},
        {"tool_name": "a", "tool_args": {"x": 1}},
        {"tool_name": "a", "tool_args": {"x": 1}}
    ])
    assert res is not None
    assert res.detector_name == "ExactRepeatDetector"
    assert res.confidence == 1.0

def test_semantic_similarity_detector():
    det = SemanticSimilarityDetector(threshold=0.9, n=3)
    
    # Identical outputs should always be caught
    res_identical = det.check([
        {"output": "the quick brown fox jumps over the lazy dog"},
        {"output": "the quick brown fox jumps over the lazy dog"},
        {"output": "the quick brown fox jumps over the lazy dog"}
    ])
    assert res_identical is not None
    assert res_identical.detector_name == "SemanticSimilarityDetector"
    
    # Completely different outputs should NOT be caught
    res_diff = det.check([
        {"output": "the quick brown fox jumps over the lazy dog"},
        {"output": "completely unrelated text about space rockets and mars"},
        {"output": "another sentence about cooking pasta with tomato sauce"}
    ])
    assert res_diff is None

def test_oscillation_detector():
    det = OscillationDetector(min_cycles=2)
    history = [
        {"tool_name": "A", "tool_args": {}},
        {"tool_name": "B", "tool_args": {}},
        {"tool_name": "A", "tool_args": {}},
        {"tool_name": "B", "tool_args": {}}
    ]
    res = det.check(history)
    assert res is not None
    assert "A-B oscillation" in res.description
