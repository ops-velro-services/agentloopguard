# Detector benchmark report

Run locally or in CI:

```bash
python3 benchmarks/run_detector_benchmark.py --json
```

Record the generated metrics below. Fixture classifications are deterministic;
latency figures are observational and should be compared only on similar hardware.

| Detector | Precision | Recall | False-positive rate | p50 latency (ns) | p95 latency (ns) |
| --- | ---: | ---: | ---: | ---: | ---: |
| exact_repeat | | | | | |
| lexical_similarity | | | | | |
| cost_velocity | | | | | |
| oscillation | | | | | |

## Regression policy

The test suite requires perfect precision and recall and zero false-positive rate
on these synthetic fixtures. Any fixture change must be reviewed alongside its
label rationale; add a regression trace before changing detector behavior.
