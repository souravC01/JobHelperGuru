"""Tests for competition ranking, tie breaking, zero-score, and incomplete evaluation handling."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from backend.services.matching.models import (
    Evaluation,
    EvaluationStatus,
    Evidence,
    EvidenceLevel,
    Requirement,
    RequirementCategory,
    RequirementResult,
)
from backend.services.matching.scoring import rank_evaluations


def make_eval(
    resume_id: str,
    status: EvaluationStatus = EvaluationStatus.COMPLETE,
    score: int | None = 80,
    raw_score: Decimal | None = None,
) -> Evaluation:
    r = Requirement(
        id="req-1",
        category=RequirementCategory.REQUIRED_SKILLS,
        kind="skill",
        canonical_key="python",
        alternatives=["python"],
        source_quote="Python",
        source_start=0,
        source_end=6,
    )
    e = Evidence(
        requirement_id="req-1",
        level=EvidenceLevel.DEMONSTRATED if (score or 0) > 0 else EvidenceLevel.NOT_EVIDENCED,
        source_quote="Python" if (score or 0) > 0 else None,
        source_start=0 if (score or 0) > 0 else None,
        source_end=6 if (score or 0) > 0 else None,
    )
    res = RequirementResult(requirement=r, evidence=[e])

    if status != EvaluationStatus.COMPLETE:
        return Evaluation(
            resume_id=resume_id,
            status=status,
            as_of=date(2026, 9, 17),
            job_fingerprint="job-fp",
            resume_fingerprint="resume-fp",
            source_fingerprint="source-fp",
        )

    computed_raw = raw_score if raw_score is not None else Decimal(str(score))
    return Evaluation(
        resume_id=resume_id,
        status=status,
        as_of=date(2026, 9, 17),
        job_fingerprint="job-fp",
        resume_fingerprint="resume-fp",
        source_fingerprint="source-fp",
        match_score=score,
        raw_score=computed_raw,
        category_scores={RequirementCategory.REQUIRED_SKILLS: computed_raw},
        requirement_results=[res],
    )


def test_ranking_sorts_by_displayed_score_descending():
    evals = [
        make_eval("res-low", score=60),
        make_eval("res-high", score=90),
        make_eval("res-mid", score=75),
    ]
    ranked = rank_evaluations(evals)

    assert [r.resume_id for r in ranked] == ["res-high", "res-mid", "res-low"]
    assert [r.rank for r in ranked] == [1, 2, 3]
    assert ranked[0].is_top_match is True
    assert ranked[1].is_top_match is False
    assert ranked[2].is_top_match is False


def test_tied_scores_receive_competition_rank():
    evals = [
        make_eval("res-a", score=85),
        make_eval("res-b", score=85),
        make_eval("res-c", score=70),
    ]
    ranked = rank_evaluations(evals)

    assert [r.resume_id for r in ranked] == ["res-a", "res-b", "res-c"]
    assert [r.rank for r in ranked] == [1, 1, 3]
    assert ranked[0].is_top_match is True
    assert ranked[1].is_top_match is True
    assert ranked[2].is_top_match is False


def test_stable_tie_breaking_by_resume_id():
    evals = [
        make_eval("res-zebra", score=80),
        make_eval("res-apple", score=80),
    ]
    ranked = rank_evaluations(evals)

    assert [r.resume_id for r in ranked] == ["res-apple", "res-zebra"]
    assert [r.rank for r in ranked] == [1, 1]


def test_all_zero_scores_do_not_advertise_top_fit():
    evals = [
        make_eval("res-1", score=0),
        make_eval("res-2", score=0),
    ]
    ranked = rank_evaluations(evals)

    assert [r.rank for r in ranked] == [1, 1]
    assert all(r.is_top_match is False for r in ranked)


def test_unranked_errors_and_incomplete_evaluations():
    evals = [
        make_eval("res-good", score=80),
        make_eval("res-review", status=EvaluationStatus.NEEDS_REVIEW, score=None),
        make_eval("res-fail", status=EvaluationStatus.FAILED, score=None),
    ]
    ranked = rank_evaluations(evals)

    # Scorable first, then incomplete unranked items
    assert ranked[0].resume_id == "res-good"
    assert ranked[0].rank == 1
    assert ranked[0].is_top_match is True

    unranked = [r for r in ranked if r.status != EvaluationStatus.COMPLETE]
    assert len(unranked) == 2
    assert all(r.rank is None for r in unranked)
    assert all(r.is_top_match is False for r in unranked)


def test_ranking_determinism_across_permutations():
    evals = [
        make_eval("res-3", score=70),
        make_eval("res-1", score=90),
        make_eval("res-2", score=90),
        make_eval("res-4", score=50),
    ]
    ranked1 = rank_evaluations(evals)
    ranked2 = rank_evaluations(list(reversed(evals)))

    assert [r.resume_id for r in ranked1] == [r.resume_id for r in ranked2]
    assert [r.rank for r in ranked1] == [r.rank for r in ranked2]
    assert [r.is_top_match for r in ranked1] == [r.is_top_match for r in ranked2]
