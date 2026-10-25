import pytest
from tests.benchmarks.phase10_benchmark_runner import run_phase10_benchmark


def test_phase10_synthetic_benchmark_execution():
    """
    Executes the Phase 10 synthetic benchmark and verifies baseline performance thresholds.
    """
    results = run_phase10_benchmark()
    assert results is not None
    assert results["scenarios_evaluated"] == 10

    metrics = results["metrics"]
    # Verify retrieval precision & recall exceed baseline thresholds
    assert metrics["mean_precision_at_3"] > 0.0
    assert metrics["mean_recall_at_3"] > 0.0
    assert metrics["mean_reciprocal_rank_mrr"] >= 0.5
    assert metrics["ndcg_at_3"] >= 0.5

    # Verify zero cross-patient leakage
    assert metrics["cross_patient_leakage_events"] == 0

    # Verify latency meets local real-time requirements (< 250ms p50 on CPU)
    assert metrics["latency_p50_ms"] < 250.0
