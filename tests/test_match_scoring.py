from datetime import date
from decimal import Decimal
import pytest
from backend.services.matching.models import Evidence, Requirement

AS_OF=date(2026,9,30)


def req(id="q", category="required_skills", kind="skill", months=None, alternatives=None):
    return Requirement(id=id,category=category,kind=kind,canonical_key=id,alternatives=alternatives or [],
                       source_quote=id,source_start=0,source_end=len(id),required_months=months)


def ev(id="q", level="demonstrated", start=0, intervals=None):
    if level=="not_evidenced": return Evidence(requirement_id=id,level=level)
    return Evidence(requirement_id=id,level=level,source_quote="Source evidence",source_start=start,source_end=start+15,
                    section="work",relevant_intervals=intervals or [])


def score(requirements,evidence):
    from backend.services.matching.scoring import calculate_score
    return calculate_score(requirements,evidence,as_of=AS_OF)


def test_required_and_preferred_skill_weights():
    requirements=[req("java"),req("python"),req("sql","preferred_qualifications")]
    result=score(requirements,[ev("java","listed"),ev("python","not_evidenced"),ev("sql")])
    assert result.raw_score==Decimal("53.85") and result.match_score==54
    assert result.category_scores=={"required_skills":Decimal(50),"preferred_qualifications":Decimal(100)}
    assert result.skill_coverage_score==Decimal("66.67")


@pytest.mark.parametrize("category",["required_skills","preferred_qualifications"])
def test_absent_categories_renormalize_and_listing_equals_demonstration(category):
    assert score([req(category=category)],[ev(level="listed")]).raw_score==100
    assert score([req(category=category)],[ev()]).raw_score==100


@pytest.mark.parametrize("level",["learning","contradicted","not_evidenced"])
def test_learning_and_absence_have_zero_credit(level):
    assert score([req()],[ev(level=level)]).raw_score==Decimal("0.00")


@pytest.mark.parametrize("category,kind",[("responsibilities","semantic"),("relevant_experience","experience"),("required_skills","credential"),("required_skills","semantic")])
def test_non_skill_inputs_are_rejected(category,kind):
    with pytest.raises(ValueError):score([req(category=category,kind=kind)],[ev()])


def test_repeated_evidence_never_multiplies_credit_and_or_is_one_requirement():
    r=req(alternatives=["java","python"])
    original=score([r],[ev(level="listed")])
    repeated=score([r],[ev(level="listed"),ev(level="listed"),ev(level="listed",start=20)])
    assert original.raw_score==repeated.raw_score==100
    assert score([r],[ev(level="listed"),ev(start=20)]).match_score==100


@pytest.mark.parametrize("requirements,evidence",[([],[]),([req()],[]),([req()],[ev("foreign")]),([req(),req()],[ev()]),([req(kind="tenure",months=12)],[ev()]),([req(kind="tenure")],[ev()])])
def test_incomplete_or_invalid_inputs_cannot_score(requirements,evidence):
    with pytest.raises(ValueError): score(requirements,evidence)


def test_positive_contradicted_conflicts_are_unresolved_at_validation():
    evidence=[ev(),ev(level="contradicted",start=20)]
    with pytest.raises(ValueError,match="[Cc]onflict"):
        score([req()],evidence)


def test_score_is_independent_of_input_order_and_round_trips():
    requirements=[req("a"),req("b"),req("c","preferred_qualifications")]
    evidence=[ev("a"),ev("b","listed"),ev("c","learning")]
    a=score(requirements,evidence)
    b=score(list(reversed(requirements)),list(reversed(evidence)))
    assert a.raw_score==b.raw_score and a.category_scores==b.category_scores and a.skill_coverage_score==b.skill_coverage_score
    from backend.services.matching.models import ScoreBreakdown
    assert ScoreBreakdown.model_validate_json(a.model_dump_json())==a


@pytest.mark.parametrize("category",["responsibilities","relevant_experience"])
def test_skill_kind_cannot_be_scored_in_wrong_category(category):
    with pytest.raises(ValueError):
        score([req(category=category)],[ev(level="listed")])


def test_skill_half_up_rounding_and_no_role_parameter():
    requirements=[req(str(i)) for i in range(8)]
    evidence=[ev(str(i),"demonstrated" if i<3 else "not_evidenced") for i in range(8)]
    result=score(requirements,evidence)
    assert result.raw_score==Decimal("37.50") and result.match_score==38
    from backend.services.matching.scoring import calculate_score
    with pytest.raises(TypeError): calculate_score(requirements,evidence,as_of=AS_OF,role_focus="Python")
