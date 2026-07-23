from benchmarks.run_detector_benchmark import load_traces, run_benchmark


def test_detector_benchmark_has_deterministic_perfect_fixture_metrics():
    report = run_benchmark(load_traces())

    assert report["fixture_count"] == 7
    assert set(report["detectors"]) == {
        "exact_repeat",
        "lexical_similarity",
        "cost_velocity",
        "oscillation",
    }
    for metrics in report["detectors"].values():
        assert metrics["precision"] == 1.0
        assert metrics["recall"] == 1.0
        assert metrics["false_positive_rate"] == 0.0
        assert metrics["latency_ns"]["samples"] == 7
        assert metrics["latency_ns"]["p50"] >= 0.0
        assert metrics["latency_ns"]["p95"] >= metrics["latency_ns"]["p50"]
