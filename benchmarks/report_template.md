# Detector benchmark report

Run locally or in CI:

```bash
python3 benchmarks/run_detector_benchmark.py --json
```

Record the generated metrics below. Fixture classifications are deterministic;
latency figures are observational and should be compared only on similar hardware.

## Measured Detector Classification & Latency

*Environment: macOS (Apple Silicon), Python 3.12 / `.venv`*

| Detector | Precision | Recall | False-positive rate | p50 latency (ns) | p95 latency (ns) |
| --- | ---: | ---: | ---: | ---: | ---: |
| exact_repeat | 1.000 | 1.000 | 0.000 | 17,542 | 79,167 |
| lexical_similarity | 1.000 | 1.000 | 0.000 | 29,166 | 52,750 |
| cost_velocity | 1.000 | 1.000 | 0.000 | 2,125 | 5,875 |
| oscillation | 1.000 | 1.000 | 0.000 | 458 | 60,458 |

## Memory Metrics

- **Default Session Allocation:** ~88.5 KB peak memory overhead for 100 recorded steps (`max_history` default).
- **Bounded History Mode:** Default sliding history window caps memory consumption linearly, preventing unbounded memory growth during long-running agent loops.

## Regression policy

The test suite requires perfect precision and recall and zero false-positive rate
on these synthetic fixtures. Any fixture change must be reviewed alongside its
label rationale; add a regression trace before changing detector behavior.
