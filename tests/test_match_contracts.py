"""Public validation rules for evidence-based matching v2 contracts."""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from backend.services.matching.models import (
    EligibilityResult,
    EligibilityStatus,
    Evaluation,
    Evidence,
    EvidenceLevel,
    Requirement,
    RequirementCategory,
    RequirementResult,
)


def requirement_payload(**overrides):
    payload = {
        "id": "required-python",
        "category": "required_skills",
        "kind": "skill",
        "canonical_key": "python",
        "alternatives": ["python"],
        "source_quote": "Python",
        "source_start": 0,
        "source_end": 6,
    }
    payload.update(overrides)
    return payload


def evidence_payload(**overrides):
    payload = {
        "requirement_id": "required-python",
        "level": "demonstrated",
        "source_quote": "Built Python APIs",
        "source_start": 0,
        "source_end": 17,
        "section": "experience",
    }
    payload.update(overrides)
    return payload


def complete_evaluation(**overrides):
    requirement = Requirement(**requirement_payload())
    evidence = Evidence(**evidence_payload())
    payload = {
        "resume_id": "resume-1",
        "status": "complete",
        "match_score": 80,
        "as_of": date(2026, 9, 17),
        "job_fingerprint": "job-source-sha256",
        "resume_fingerprint": "resume-source-sha256",
        "source_fingerprint": "extraction-input-sha256",
        "requirement_results": [
            RequirementResult(requirement=requirement, evidence=[evidence])
        ],
    }
    payload.update(overrides)
    return Evaluation(**payload)


def test_contract_exposes_only_the_four_scored_categories():
    assert {category.value for category in RequirementCategory} == {
        "required_skills",
        "responsibilities",
        "relevant_experience",
        "preferred_qualifications",
    }
    with pytest.raises(ValidationError):
        Requirement(**requirement_payload(category="culture_fit"))


def test_requirement_requires_a_nonempty_id_and_valid_source_offsets():
    with pytest.raises(ValidationError):
        Requirement(**requirement_payload(id=""))
    with pytest.raises(ValidationError):
        Requirement(**requirement_payload(source_start=5, source_end=5))
    with pytest.raises(ValidationError):
        Requirement(**requirement_payload(source_start=1, source_end=6))


def test_evidence_requires_resume_provenance_when_it_affects_credit_or_contradicts():
    for level in (
        EvidenceLevel.DEMONSTRATED,
        EvidenceLevel.LISTED,
        EvidenceLevel.LEARNING,
        EvidenceLevel.CONTRADICTED,
    ):
        with pytest.raises(ValidationError):
            Evidence(**evidence_payload(level=level, source_quote=None, source_start=None, source_end=None))

    zero_credit = Evidence(
        requirement_id="required-python",
        level=EvidenceLevel.NOT_EVIDENCED,
        section=None,
    )
    assert zero_credit.source_quote is None


def test_incomplete_evaluation_cannot_claim_a_percentage_or_rank():
    with pytest.raises(ValidationError):
        Evaluation(resume_id="r1", status="needs_review", match_score=80)
    with pytest.raises(ValidationError):
        Evaluation(resume_id="r1", status="failed", rank=1)


def test_scored_evaluation_requires_complete_source_coverage_and_unique_requirements():
    requirement = Requirement(**requirement_payload())
    no_evidence = Evidence(requirement_id="required-python", level="not_evidenced")
    complete_evaluation(
        requirement_results=[RequirementResult(requirement=requirement, evidence=[no_evidence])]
    )

    with pytest.raises(ValidationError):
        complete_evaluation(requirement_results=[])
    with pytest.raises(ValidationError):
        complete_evaluation(
            requirement_results=[RequirementResult(requirement=requirement, evidence=[])]
        )
    with pytest.raises(ValidationError):
        complete_evaluation(
            requirement_results=[
                RequirementResult(requirement=requirement, evidence=[no_evidence]),
                RequirementResult(requirement=requirement, evidence=[no_evidence]),
            ]
        )
    with pytest.raises(ValidationError):
        complete_evaluation(
            requirement_results=[
                RequirementResult(
                    requirement=requirement,
                    evidence=[Evidence(**evidence_payload(requirement_id="other-requirement"))],
                )
            ]
        )


def test_category_scores_and_raw_display_scores_stay_within_their_contract():
    complete_evaluation(
        category_scores={"required_skills": Decimal(80)},
        raw_score=Decimal("72.5"),
        match_score=73,
    )
    for invalid_score in (Decimal("-0.01"), Decimal("100.01")):
        with pytest.raises(ValidationError):
            complete_evaluation(category_scores={"required_skills": invalid_score})
    with pytest.raises(ValidationError):
        complete_evaluation(raw_score=Decimal("72.5"), match_score=72)


def test_evaluation_rank_and_top_match_flags_are_consistent():
    complete_evaluation(rank=1, is_top_match=True)
    with pytest.raises(ValidationError):
        complete_evaluation(rank=1, is_top_match=False)
    with pytest.raises(ValidationError):
        complete_evaluation(rank=2, is_top_match=True)
    with pytest.raises(ValidationError):
        Evaluation(
            resume_id="r1",
            status="needs_review",
            is_top_match=True,
            as_of=date(2026, 9, 17),
            job_fingerprint="job-source-sha256",
            resume_fingerprint="resume-source-sha256",
            source_fingerprint="extraction-input-sha256",
        )


def test_eligibility_uses_explicit_statuses_and_evaluations_record_auditable_inputs():
    eligibility = EligibilityResult(
        criterion="work authorization",
        status=EligibilityStatus.UNKNOWN,
    )
    evaluation = complete_evaluation(eligibility=[eligibility])
    assert evaluation.as_of == date(2026, 9, 17)
    assert evaluation.job_fingerprint == "job-source-sha256"
    assert evaluation.resume_fingerprint == "resume-source-sha256"
    assert evaluation.source_fingerprint == "extraction-input-sha256"
    with pytest.raises(ValidationError):
        EligibilityResult(criterion="work authorization", status="probably eligible")


def test_weighted_fixture_has_hand_derived_73_percent_expectation_and_valid_quotes():
    fixture = Path(__file__).parent / "fixtures" / "matching" / "weighted_73.json"
    data = json.loads(fixture.read_text(encoding="utf-8"))

    assert data["expected"] == {
        "category_coverage": {
            "required_skills": 80,
            "responsibilities": 60,
            "relevant_experience": 50,
            "preferred_qualifications": 100,
        },
        "raw_score": 72.5,
        "display_score": 73,
    }
    for requirement in data["requirements"]:
        assert data["job_text"][requirement["source_start"]:requirement["source_end"]] == requirement["source_quote"]
    for evidence in data["evidence"]:
        if evidence["level"] != "not_evidenced":
            assert data["resume_text"][evidence["source_start"]:evidence["source_end"]] == evidence["source_quote"]


def test_immutable_fixture_set_covers_the_required_matching_regressions():
    fixture_dir = Path(__file__).parent / "fixtures" / "matching"
    fixture_names = {path.stem for path in fixture_dir.glob("*.json")}
    assert {
        "backend_resume_version",
        "frontend_resume_version",
        "aliases",
        "negation",
        "missing_data",
        "or_and_requirements",
        "dated_tenure",
        "late_document_skill",
        "weighted_73",
    } <= fixture_names

    late_document = json.loads((fixture_dir / "late_document_skill.json").read_text(encoding="utf-8"))
    offset = late_document["expected"]["late_skill_offset"]
    assert offset > 3000
    assert late_document["resume_text"][offset:offset + len("Kubernetes")] == "Kubernetes"


def test_immutable_fixture_contents_capture_each_regression_scenario():
    fixture_dir = Path(__file__).parent / "fixtures" / "matching"
    load = lambda name: json.loads((fixture_dir / name).read_text(encoding="utf-8"))

    backend = load("backend_resume_version.json")
    frontend = load("frontend_resume_version.json")
    aliases = load("aliases.json")
    negation = load("negation.json")
    missing = load("missing_data.json")
    alternatives = load("or_and_requirements.json")
    tenure = load("dated_tenure.json")
    late = load("late_document_skill.json")

    assert backend["expected"]["focus"] == "backend"
    assert backend["expected"]["supported_skills"] == ["Python", "PostgreSQL"]
    assert frontend["expected"]["focus"] == "frontend"
    assert frontend["expected"]["supported_skills"] == ["React", "TypeScript"]
    assert aliases["expected"]["alias_pairs"] == [
        ["Go", "Golang"],
        ["Amazon Web Services", "AWS"],
    ]
    assert negation["expected"]["evidence_levels"] == {
        "python": "contradicted",
        "aws": "contradicted",
    }
    assert missing["resume_text"] == ""
    assert missing["expected"] == {
        "status": "needs_review",
        "reason": "resume text is missing",
        "match_score": None,
    }
    assert alternatives["expected"]["requirement_groups"] == [
        {"operator": "or", "alternatives": ["Python", "Java"], "credit": 1},
        {"operator": "and", "requirements": ["SQL", "Docker"], "credit": 0.5},
    ]
    assert tenure["expected"] == {
        "required_months": 24,
        "verified_months": 24,
        "credit": 1,
        "intervals": [{"start": "2024-01-01", "end": "2026-01-01"}],
    }
    assert late["expected"]["late_skill_offset"] > late["expected"]["prior_legacy_limit"]
    assert late["expected"]["skill"] == "Kubernetes"
