"""Tests for matching evaluation pipeline orchestration, concurrency, deadlines, and caching."""

from __future__ import annotations

import time
from datetime import date

from backend.models import Resume
from backend.services.matching.models import (
    EvaluationStatus,
)
from backend.services.matching.pipeline import evaluate_resumes
from backend.storage import StorageService


def make_resume(id: str, content: str, name: str = "Test Resume", user_id: str = "user-1") -> Resume:
    now = "2026-09-17T00:00:00"
    return Resume(
        id=id,
        user_id=user_id,
        name=name,
        content=content,
        created_at=now,
        updated_at=now,
    )


def test_evaluate_resumes_offline_batch():
    job_text = "Required skills:\nPython\nSQL\n"
    resumes = [
        make_resume("res-1", "Built Python APIs with SQL."),
        make_resume("res-2", "Used Python in production."),
    ]

    batch = evaluate_resumes(
        job_text,
        resumes,
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
    )

    assert batch.comparison_complete is True
    assert len(batch.evaluations) == 2

    e1 = next(e for e in batch.evaluations if e.resume_id == "res-1")
    e2 = next(e for e in batch.evaluations if e.resume_id == "res-2")

    assert e1.match_score == 100
    assert e1.rank == 1
    assert e1.is_top_match is True

    assert e2.match_score == 50
    assert e2.rank == 2
    assert e2.is_top_match is False


def test_evaluate_resumes_caching_and_fresh_bypass(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "test_pipeline_cache.db"))
    job_text = "Required skills:\nPython\nAWS\n"
    resume = make_resume("res-cache-1", "Built Python systems on AWS.")

    # 1. Initial evaluation -> saves to storage
    batch1 = evaluate_resumes(
        job_text,
        [resume],
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
        storage=storage,
    )
    e1 = batch1.evaluations[0]
    assert e1.match_score == 100
    assert e1.evaluation_id is not None

    # 2. Subsequent evaluation with identical inputs -> cache hit (same evaluation_id)
    batch2 = evaluate_resumes(
        job_text,
        [resume],
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
        storage=storage,
    )
    e2 = batch2.evaluations[0]
    assert e2.evaluation_id == e1.evaluation_id
    assert e2.match_score == 100

    # 3. Fresh evaluation -> bypasses cache and generates new evaluation_id
    batch3 = evaluate_resumes(
        job_text,
        [resume],
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
        storage=storage,
        fresh=True,
    )
    e3 = batch3.evaluations[0]
    assert e3.evaluation_id != e1.evaluation_id
    assert e3.match_score == 100


def test_resume_text_edit_invalidates_cache(tmp_path):
    storage = StorageService(db_path=str(tmp_path / "test_pipeline_edit.db"))
    job_text = "Required skills:\nPython\nAWS\n"
    resume_v1 = make_resume("res-1", "No experience with Python or AWS.")

    batch1 = evaluate_resumes(
        job_text,
        [resume_v1],
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
        storage=storage,
    )
    assert batch1.evaluations[0].match_score == 0

    # User edits resume to add Python
    resume_v2 = make_resume("res-1", "Built Python web services.")
    batch2 = evaluate_resumes(
        job_text,
        [resume_v2],
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
        storage=storage,
    )
    assert batch2.evaluations[0].match_score == 50


def test_unscorable_job_leaves_resumes_unranked():
    job_text = "About Us:\nWe are a stealth startup in San Francisco."
    resumes = [make_resume("res-1", "Python programmer")]

    batch = evaluate_resumes(
        job_text,
        resumes,
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
    )

    assert batch.comparison_complete is False
    assert len(batch.evaluations) == 1
    eval_res = batch.evaluations[0]
    assert eval_res.status in {EvaluationStatus.NEEDS_REVIEW, EvaluationStatus.FAILED}
    assert eval_res.match_score is None
    assert eval_res.rank is None
    assert eval_res.is_top_match is False


def test_individual_resume_failure_does_not_crash_batch(monkeypatch):

    job_text = "Required skills:\nPython\n"
    res1 = make_resume("res-good", "Built Python services")
    res2 = make_resume("res-bad", "x" * 120_000)  # Exceeds chunk/document limits

    batch = evaluate_resumes(
        job_text,
        [res1, res2],
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
    )

    assert batch.comparison_complete is False
    good = next(e for e in batch.evaluations if e.resume_id == "res-good")
    bad = next(e for e in batch.evaluations if e.resume_id == "res-bad")

    assert good.status == EvaluationStatus.COMPLETE
    assert good.match_score == 100
    assert good.rank == 1
    assert good.is_top_match is True

    assert bad.status in {EvaluationStatus.FAILED, EvaluationStatus.NEEDS_REVIEW}
    assert bad.match_score is None
    assert bad.rank is None
    assert bad.is_top_match is False


def test_concurrency_limit_and_deadline(monkeypatch):
    from backend.services.matching import extraction

    active_calls = 0
    max_concurrent_observed = 0

    original_extract_evidence = extraction.extract_evidence

    def slow_extract_evidence(*args, **kwargs):
        nonlocal active_calls, max_concurrent_observed
        active_calls += 1
        max_concurrent_observed = max(max_concurrent_observed, active_calls)
        time.sleep(0.05)
        active_calls -= 1
        return original_extract_evidence(*args, **kwargs)

    monkeypatch.setattr(extraction, "extract_evidence", slow_extract_evidence)

    job_text = "Required skills:\nPython\n"
    resumes = [make_resume(f"res-{i}", "Python developer") for i in range(4)]

    batch = evaluate_resumes(
        job_text,
        resumes,
        user_id="user-1",
        as_of=date(2026, 9, 17),
        mode="offline",
        max_workers=2,
    )

    assert batch.comparison_complete is True
    assert max_concurrent_observed <= 2
