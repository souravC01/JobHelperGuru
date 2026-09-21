"""Automated rollout gating and quality benchmark tests for evidence-based matching v2."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from backend.models import Resume
from backend.services.matching import evaluate_resumes
from backend.services.matching.models import EvidenceLevel
from scripts.evaluate_matching import (
    load_benchmark_cases,
    run_benchmark_evaluation,
    run_cold_path_performance_check,
)


def test_benchmark_dataset_structure_and_splits():
    cases = load_benchmark_cases(split="all")
    assert len(cases) == 30, f"Expected exactly 30 cases, found {len(cases)}"

    dev_cases = [c for c in cases if c.get("split") == "dev"]
    holdout_cases = [c for c in cases if c.get("split") == "holdout"]
    assert len(dev_cases) == 20, f"Expected 20 dev cases, found {len(dev_cases)}"
    assert len(holdout_cases) == 10, f"Expected 10 holdout cases, found {len(holdout_cases)}"

    domains = {c.get("role_domain") for c in cases}
    expected_domains = {"backend", "frontend", "data", "infrastructure", "graduate"}
    assert domains == expected_domains, f"Missing domains: {expected_domains - domains}"

    for c in cases:
        assert c.get("job_text", "").strip(), f"Case {c['id']} has empty job text"
        assert len(c.get("resumes", [])) >= 2, f"Case {c['id']} must have at least 2 resumes"
        assert len(c.get("pairwise_order", [])) >= 1, f"Case {c['id']} must specify pairwise order"


def test_rollout_gate_zero_false_positives_on_negation_and_injection():
    cases = load_benchmark_cases(split="all")
    report = run_benchmark_evaluation(cases, mode="offline")
    assert (
        report["false_positive_credits"] == 0
    ), f"Observed {report['false_positive_credits']} false positive credits on negation/injection fixtures"


def test_rollout_gate_every_credited_quote_validates_against_source():
    cases = load_benchmark_cases(split="all")
    report = run_benchmark_evaluation(cases, mode="offline")
    assert (
        report["quote_validation_failures"] == 0
    ), f"Observed {report['quote_validation_failures']} invalid quotes out of {report['total_credited_quotes']}"
    assert report["total_credited_quotes"] > 0, "Expected at least one credited quote across benchmark"


def test_rollout_gate_holdout_pairwise_ranking_agreement_exceeds_threshold():
    cases = load_benchmark_cases(split="holdout")
    report = run_benchmark_evaluation(cases, mode="offline")
    holdout_metrics = report["split_metrics"]["holdout"]
    agreement_pct = holdout_metrics["agreement_pct"]
    assert (
        agreement_pct >= 90.0
    ), f"Holdout pairwise agreement {agreement_pct}% is below the 90.0% rollout gate"
    assert holdout_metrics["total_pairs"] >= 10, "Expected at least 10 holdout pairs evaluated"


def test_rollout_gate_cold_path_performance_under_120_seconds():
    report = run_cold_path_performance_check()
    assert report["passed_latency_gate"] is True, f"Cold path performance gate failed: {report}"
    assert report["elapsed_seconds"] < 120.0, f"Cold path took {report['elapsed_seconds']}s (limit: 120s)"
    assert report["resumes_count"] == 5
    assert report["comparison_complete"] is True


def test_rollout_gate_warm_cache_avoids_recomputation():
    job_text = "Required skills:\nPython\nAWS\n"
    resumes = [
        Resume(id="cache_res_1", name="Cache Alpha", content="Built Python APIs on AWS."),
    ]
    target_date = date(2026, 9, 17)

    # Mock storage service to record snapshot saves and hits
    saved_snapshots: dict[str, dict] = {}

    class MockStorage:
        def get_matching_snapshot(self, *, user_id, resume_id, job_hash, version_key, as_of):
            key = f"{user_id}:{resume_id}:{job_hash}:{version_key}:{as_of}"
            return saved_snapshots.get(key)

        def save_matching_snapshot(self, *, id, user_id, resume_id, job_hash, source_hash, version_key, as_of, payload_json):
            key = f"{user_id}:{resume_id}:{job_hash}:{version_key}:{as_of}"
            saved_snapshots[key] = {
                "id": id,
                "user_id": user_id,
                "resume_id": resume_id,
                "job_hash": job_hash,
                "source_hash": source_hash,
                "version_key": version_key,
                "as_of": as_of,
                "payload_json": payload_json,
            }

    storage = MockStorage()

    # 1. Cold execution
    batch_cold = evaluate_resumes(
        job_text=job_text,
        resumes=resumes,
        user_id="user_cache",
        as_of=target_date,
        mode="offline",
        storage=storage,
        fresh=False,
    )
    assert batch_cold.comparison_complete is True
    assert len(saved_snapshots) == 1

    # 2. Warm execution (hits snapshot cache)
    batch_warm = evaluate_resumes(
        job_text=job_text,
        resumes=resumes,
        user_id="user_cache",
        as_of=target_date,
        mode="offline",
        storage=storage,
        fresh=False,
    )
    assert batch_warm.comparison_complete is True
    assert batch_warm.evaluations[0].match_score == batch_cold.evaluations[0].match_score
    assert batch_warm.evaluations[0].evaluation_id == batch_cold.evaluations[0].evaluation_id
