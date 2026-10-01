from datetime import date
from decimal import Decimal
import pytest
from pydantic import ValidationError


def base_evaluation():
    return dict(resume_id="r", status="needs_review", as_of=date(2026, 9, 30), job_fingerprint="j", resume_fingerprint="r", source_fingerprint="s", rubric_fingerprint="rubric")


def test_incomplete_evaluation_has_no_score_or_rank():
    from backend.services.matching.models import Evaluation
    value = Evaluation(**base_evaluation())
    assert value.match_score is None and value.rank is None and not value.is_top_match
    for field, value in [("match_score", 50), ("rank", 1), ("is_top_match", True), ("raw_score", Decimal(50)), ("skill_coverage_score", Decimal(50)), ("category_scores", {"required_skills": Decimal(50)})]:
        with pytest.raises(ValidationError):
            Evaluation(**{**base_evaluation(), field: value})


@pytest.mark.parametrize("score", [-1, 101, "50", True])
def test_score_bounds_are_strict(score):
    from backend.services.matching.models import ScoreBreakdown
    with pytest.raises(ValidationError):
        ScoreBreakdown(match_score=score, raw_score=Decimal(50))


def test_contract_kinds_reasons_and_removed_role_fields():
    from backend.services.matching.models import Requirement, Evaluation
    req = dict(id="q", category="required_skills", kind="skill", canonical_key="python", source_quote="Python", source_start=0, source_end=6)
    assert Requirement(**req).kind == "skill"
    for change in [{"kind": "unknown"}, {"source_end": 7}]:
        with pytest.raises(ValidationError):
            Requirement(**{**req, **change})
    for change in [{"role_focus": "Java"}, {"reason_codes": ["unknown"]}]:
        with pytest.raises(ValidationError):
            Evaluation(**{**base_evaluation(), **change})


def test_positive_evidence_requires_provenance_and_coverage():
    from backend.services.matching.models import Evidence, EvidenceExtraction
    with pytest.raises(ValidationError):
        Evidence(requirement_id="q", level="demonstrated")
    with pytest.raises(ValidationError):
        EvidenceExtraction(status="complete", source_hash="s", extractor_version="v", assessed_requirement_ids=["q"], items=[])


def test_batch_cannot_claim_complete_or_mix_rubrics():
    from backend.services.matching.models import Evaluation, EvaluationBatch
    incomplete = Evaluation(**base_evaluation())
    with pytest.raises(ValidationError):
        EvaluationBatch(job_fingerprint="j", comparison_complete=True, evaluations=[incomplete])
    with pytest.raises(ValidationError):
        EvaluationBatch(job_fingerprint="j", comparison_complete=False, evaluations=[incomplete, incomplete])


def complete_evaluation(**changes):
    from backend.services.matching.models import Evaluation
    req = dict(id="q", category="required_skills", kind="skill", canonical_key="python", source_quote="Python", source_start=0, source_end=6)
    return Evaluation(**{**base_evaluation(), "status": "complete", "match_score": 1, "raw_score": Decimal("0.50"), "requirement_results": [{"requirement": req, "evidence": [{"requirement_id": "q", "level": "not_evidenced"}]}], **changes})


def test_complete_scores_require_rubric_and_explicit_outcomes():
    assert complete_evaluation().score_scope == "skill_fit"
    with pytest.raises(ValidationError): complete_evaluation(score_scope="overall_job_fit")
    for changes in [{"rubric_fingerprint": None}, {"raw_score": None}, {"requirement_results": []}, {"reason_codes": ["source_incomplete"]}]:
        with pytest.raises(ValidationError):
            complete_evaluation(**changes)


def test_batch_checks_frozen_rubric_job_and_incomplete_winners():
    from backend.services.matching.models import EvaluationBatch
    a = complete_evaluation()
    for b in [complete_evaluation(resume_id="other", rubric_fingerprint="other"), complete_evaluation(resume_id="other", job_fingerprint="other")]:
        with pytest.raises(ValidationError):
            EvaluationBatch(job_fingerprint="j", comparison_complete=True, evaluations=[a, b])
    with pytest.raises(ValidationError):
        EvaluationBatch(job_fingerprint="j", comparison_complete=False, evaluations=[complete_evaluation(rank=1, is_top_match=True)])


def test_positive_raw_score_can_lead_when_display_rounds_to_zero():
    value = complete_evaluation(raw_score=Decimal("0.40"), match_score=0, rank=1, is_top_match=True)
    assert value.is_top_match and value.raw_score > 0
