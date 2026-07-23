"""Run deterministic classification metrics for AgentLoopGuard's built-in detectors."""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from contextlib import suppress
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
with suppress(ValueError):
    sys.path.remove(str(SOURCE_ROOT))
sys.path.insert(0, str(SOURCE_ROOT))

from agentloopguard.detectors import (  # noqa: E402
    BaseDetector,
    CostVelocityDetector,
    ExactRepeatDetector,
    LexicalSimilarityDetector,
    OscillationDetector,
)

FIXTURE_PATH = Path(__file__).with_name("fixtures") / "detector_traces.json"


def builtin_detectors() -> tuple[BaseDetector, ...]:
    """Return the default detector configuration used by the benchmark."""
    return (
        ExactRepeatDetector(),
        LexicalSimilarityDetector(),
        CostVelocityDetector(),
        OscillationDetector(),
    )


def load_traces(path: Path = FIXTURE_PATH) -> list[dict[str, Any]]:
    """Load and minimally validate checked-in synthetic benchmark fixtures."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("traces"), list):
        raise ValueError("benchmark fixture must contain schema_version 1 and a traces list")
    return data["traces"]


def _percentile(values: list[int], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, round((len(ordered) - 1) * percentile))
    return float(ordered[index])


def run_benchmark(
    traces: list[dict[str, Any]], detectors: tuple[BaseDetector, ...] | None = None
) -> dict[str, Any]:
    """Measure detector classification metrics and per-trace check latency."""
    active_detectors = detectors or builtin_detectors()
    metrics: dict[str, dict[str, Any]] = {
        detector.detector_id: {
            "true_positive": 0,
            "false_positive": 0,
            "false_negative": 0,
            "true_negative": 0,
            "latencies_ns": [],
        }
        for detector in active_detectors
    }

    for trace in traces:
        if not isinstance(trace.get("steps"), list) or not isinstance(trace.get("labels"), list):
            raise ValueError(
                f"trace {trace.get('id', '<unknown>')} must contain steps and labels lists"
            )
        labels = set(trace["labels"])
        for detector in active_detectors:
            started_ns = time.perf_counter_ns()
            detected = detector.check(trace["steps"]) is not None
            metrics[detector.detector_id]["latencies_ns"].append(
                time.perf_counter_ns() - started_ns
            )
            expected = detector.detector_id in labels
            if detected and expected:
                metrics[detector.detector_id]["true_positive"] += 1
            elif detected:
                metrics[detector.detector_id]["false_positive"] += 1
            elif expected:
                metrics[detector.detector_id]["false_negative"] += 1
            else:
                metrics[detector.detector_id]["true_negative"] += 1

    report: dict[str, Any] = {"fixture_count": len(traces), "detectors": {}}
    for detector_id, values in metrics.items():
        tp, fp, fn = values["true_positive"], values["false_positive"], values["false_negative"]
        precision = tp / (tp + fp) if tp + fp else 1.0
        recall = tp / (tp + fn) if tp + fn else 1.0
        negatives = fp + values["true_negative"]
        report["detectors"][detector_id] = {
            "true_positive": tp,
            "false_positive": fp,
            "false_negative": fn,
            "true_negative": values["true_negative"],
            "precision": precision,
            "recall": recall,
            "false_positive_rate": fp / negatives if negatives else 0.0,
            "latency_ns": {
                "samples": len(values["latencies_ns"]),
                "p50": _percentile(values["latencies_ns"], 0.5),
                "p95": _percentile(values["latencies_ns"], 0.95),
                "mean": statistics.fmean(values["latencies_ns"]),
            },
        }
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixtures", type=Path, default=FIXTURE_PATH)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    args = parser.parse_args()
    report = run_benchmark(load_traces(args.fixtures))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return
    print(f"Detector benchmark: {report['fixture_count']} synthetic traces")
    for detector_id, values in report["detectors"].items():
        print(
            f"{detector_id}: precision={values['precision']:.3f} "
            f"recall={values['recall']:.3f} fpr={values['false_positive_rate']:.3f} "
            f"latency_ns p50={values['latency_ns']['p50']:.0f} "
            f"p95={values['latency_ns']['p95']:.0f}"
        )


if __name__ == "__main__":
    main()
