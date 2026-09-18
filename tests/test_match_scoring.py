"""Tests for deterministic match scoring and tenure calculation."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from backend.services.matching.models import (
    Evidence,
    EvidenceLevel,
    RelevantInterval,
    Requirement,
    RequirementCategory,
)
from backend.services.matching.scoring import (
    calculate_score,
    calculate_verified_months,
)


def req(id: str, category: RequirementCategory, kind: str = "skill", key: str = "python", months: int | None = None, alternatives: list[str] | None = None) -> Requirement:
    return Requirement(
        id=id,
        category=category,
        kind=kind,
        canonical_key=key,
        alternatives=alternatives or [key],
        source_quote=key.title(),
        source_start=0,
        source_end=len(key),
        required_months=months,
    )


def ev(req_id: str, level: EvidenceLevel, quote: str | None = "Used skill", start: int | None = 0, end: int | None = 10, intervals: list[RelevantInterval] | None = None) -> Evidence:
    if level == EvidenceLevel.NOT_EVIDENCED:
        return Evidence(requirement_id=req_id, level=level)
    return Evidence(
        requirement_id=req_id,
        level=level,
        source_quote=quote,
        source_start=start,
        source_end=end if end is not None else (start + len(quote) if quote else None),
        relevant_intervals=intervals or [],
    )


def test_weighted_score_uses_evidence_fixture():
    fixture_path = Path(__file__).parent / "fixtures" / "matching" / "weighted_73.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    requirements = [Requirement(**r) for r in data["requirements"]]
    evidence = [Evidence(**e) for e in data["evidence"]]

    score = calculate_score(requirements, evidence, as_of=date(2026, 9, 17))

    assert score.match_score == 73
    assert score.raw_score == Decimal("72.50")
    assert score.category_scores[RequirementCategory.REQUIRED_SKILLS] == Decimal("80.00")
    assert score.category_scores[RequirementCategory.RESPONSIBILITIES] == Decimal("60.00")
    assert score.category_scores[RequirementCategory.RELEVANT_EXPERIENCE] == Decimal("50.00")
    assert score.category_scores[RequirementCategory.PREFERRED_QUALIFICATIONS] == Decimal("100.00")


def test_empty_requirements_raises_error():
    with pytest.raises(ValueError, match="requirements"):
        calculate_score([], [], as_of=date(2026, 9, 17))


def test_empty_evidence_yields_zero_score():
    requirements = [
        req("r1", RequirementCategory.REQUIRED_SKILLS),
        req("r2", RequirementCategory.RESPONSIBILITIES),
    ]
    score = calculate_score(requirements, [], as_of=date(2026, 9, 17))

    assert score.match_score == 0
    assert score.raw_score == Decimal("0.00")
    assert score.category_scores[RequirementCategory.REQUIRED_SKILLS] == Decimal("0.00")
    assert score.category_scores[RequirementCategory.RESPONSIBILITIES] == Decimal("0.00")


def test_absent_category_omitted_from_denominator():
    # Only required_skills present -> denominator should be 60, normalized to 100%
    requirements = [
        req("r1", RequirementCategory.REQUIRED_SKILLS, key="python"),
        req("r2", RequirementCategory.REQUIRED_SKILLS, key="sql"),
    ]
    evidence = [
        ev("r1", EvidenceLevel.DEMONSTRATED),
        ev("r2", EvidenceLevel.DEMONSTRATED),
    ]
    score = calculate_score(requirements, evidence, as_of=date(2026, 9, 17))

    assert score.match_score == 100
    assert score.raw_score == Decimal("100.00")
    assert RequirementCategory.RESPONSIBILITIES not in score.category_scores


def test_contradicted_and_conflicting_evidence():
    r1 = req("r1", RequirementCategory.REQUIRED_SKILLS, key="python")
    r2 = req("r2", RequirementCategory.REQUIRED_SKILLS, key="aws")

    # r1 is explicitly contradicted -> 0 credit
    # r2 has conflicting claims (both demonstrated and contradicted) -> 0 credit
    evidence = [
        ev("r1", EvidenceLevel.CONTRADICTED, quote="No python experience", start=0, end=20),
        ev("r2", EvidenceLevel.DEMONSTRATED, quote="Built AWS infrastructure", start=25, end=49),
        ev("r2", EvidenceLevel.CONTRADICTED, quote="No AWS experience", start=55, end=72),
    ]
    score = calculate_score([r1, r2], evidence, as_of=date(2026, 9, 17))

    assert score.match_score == 0
    assert score.raw_score == Decimal("0.00")


def test_evidence_levels_award_expected_credits():
    # Demonstrated: 1.0, Listed: 0.5, Learning: 0.25, Not evidenced: 0.0
    # 4 requirements in required_skills -> mean credit = (1.0 + 0.5 + 0.25 + 0.0) / 4 = 1.75 / 4 = 0.4375 -> 43.75%
    requirements = [
        req("r1", RequirementCategory.REQUIRED_SKILLS, key="python"),
        req("r2", RequirementCategory.REQUIRED_SKILLS, key="sql"),
        req("r3", RequirementCategory.REQUIRED_SKILLS, key="docker"),
        req("r4", RequirementCategory.REQUIRED_SKILLS, key="aws"),
    ]
    evidence = [
        ev("r1", EvidenceLevel.DEMONSTRATED),
        ev("r2", EvidenceLevel.LISTED),
        ev("r3", EvidenceLevel.LEARNING),
        ev("r4", EvidenceLevel.NOT_EVIDENCED),
    ]
    score = calculate_score(requirements, evidence, as_of=date(2026, 9, 17))

    assert score.category_scores[RequirementCategory.REQUIRED_SKILLS] == Decimal("43.75")
    assert score.raw_score == Decimal("43.75")
    assert score.match_score == 44  # half-up 43.75 -> 44


def test_overlapping_jobs_do_not_double_count_tenure():
    # Requirement: 24 months
    # Job A: Jan 1, 2024 to Jan 1, 2025 (12 months)
    # Job B: Jul 1, 2024 to Jul 1, 2025 (12 months)
    # Merged union: Jan 1, 2024 to Jul 1, 2025 = 18 months
    # Credit should be 18 / 24 = 0.75 -> 75%
    requirement = req("r1", RequirementCategory.RELEVANT_EXPERIENCE, kind="tenure", months=24)
    intervals = [
        RelevantInterval(start=date(2024, 1, 1), end=date(2025, 1, 1)),
        RelevantInterval(start=date(2024, 7, 1), end=date(2025, 7, 1)),
    ]
    evidence = [
        ev("r1", EvidenceLevel.DEMONSTRATED, quote="Software Engineer", start=0, end=17, intervals=intervals)
    ]
    score = calculate_score([requirement], evidence, as_of=date(2026, 9, 17))

    assert score.category_scores[RequirementCategory.RELEVANT_EXPERIENCE] == Decimal("75.00")
    assert score.match_score == 75


def test_tenure_ongoing_capped_at_as_of():
    # Ongoing job from Jan 1, 2025 with end=None, as_of=Jan 1, 2026 -> 12 months
    intervals = [RelevantInterval(start=date(2025, 1, 1), end=None)]
    months = calculate_verified_months(intervals, as_of=date(2026, 1, 1))
    assert months == Decimal(12)


def test_unknown_requirement_id_in_evidence_raises_error():
    requirements = [req("r1", RequirementCategory.REQUIRED_SKILLS)]
    evidence = [ev("unknown-req", EvidenceLevel.DEMONSTRATED)]

    with pytest.raises(ValueError, match="unknown requirement ID"):
        calculate_score(requirements, evidence, as_of=date(2026, 9, 17))


def test_duplicate_requirement_ids_raises_error():
    requirements = [
        req("r1", RequirementCategory.REQUIRED_SKILLS),
        req("r1", RequirementCategory.REQUIRED_SKILLS),
    ]
    with pytest.raises(ValueError, match="duplicate requirement IDs"):
        calculate_score(requirements, [], as_of=date(2026, 9, 17))


def test_determinism_across_input_permutations():
    fixture_path = Path(__file__).parent / "fixtures" / "matching" / "weighted_73.json"
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    requirements = [Requirement(**r) for r in data["requirements"]]
    evidence = [Evidence(**e) for e in data["evidence"]]

    score_original = calculate_score(requirements, evidence, as_of=date(2026, 9, 17))

    # Reversed
    score_reversed = calculate_score(list(reversed(requirements)), list(reversed(evidence)), as_of=date(2026, 9, 17))

    assert score_original.match_score == score_reversed.match_score
    assert score_original.raw_score == score_reversed.raw_score
    assert score_original.category_scores == score_reversed.category_scores
