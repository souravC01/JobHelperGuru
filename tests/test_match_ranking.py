from datetime import date
from decimal import Decimal, ROUND_HALF_UP
import pytest
from backend.services.matching.models import Evaluation, RequirementResult
from tests.test_match_scoring import req, ev


def evaluation(id, raw="80", status="complete", **fields):
    data=dict(resume_id=id,status=status,as_of=date(2026,9,30),job_fingerprint="job",resume_fingerprint=id,
              source_fingerprint=id,rubric_fingerprint="rubric")
    if status=="complete":
        value=Decimal(raw)
        data.update(raw_score=value,match_score=int(value.quantize(Decimal(1),rounding=ROUND_HALF_UP)),
                    requirement_results=[RequirementResult(requirement=req(),evidence=[ev()])])
    return Evaluation(**{**data,**fields})


def rank(items):
    from backend.services.matching.scoring import rank_evaluations
    return rank_evaluations(items)


def test_raw_scores_rank_before_display_rounding():
    ranked=rank([evaluation("a","80.01"),evaluation("z","80.49")])
    assert [r.resume_id for r in ranked]==["z","a"] and [r.rank for r in ranked]==[1,2]
    assert [r.match_score for r in ranked]==[80,80]


def test_equal_raw_scores_rank_one_one_three():
    originals=[evaluation("b","80.49"),evaluation("c","60"),evaluation("a","80.49")]
    ranked=rank(originals)
    assert [r.resume_id for r in ranked]==["a","b","c"] and [r.rank for r in ranked]==[1,1,3]
    assert [r.is_top_match for r in ranked]==[True,True,False]
    assert all(r.rank is None and not r.is_top_match for r in originals)
    assert rank(list(reversed(originals)))==ranked
    extended=rank(originals+[evaluation("d","40")])
    assert {r.resume_id:r.raw_score for r in extended if r.resume_id!="d"}=={r.resume_id:r.raw_score for r in ranked}


def test_incomplete_comparison_clears_all_cached_ranks():
    old=rank([evaluation("a"),evaluation("b","70")])
    ranked=rank(old+[evaluation("c",status="needs_review")])
    assert all(r.rank is None and not r.is_top_match for r in ranked)
    assert old[0].rank==1


def test_zero_display_with_positive_raw_can_lead_but_all_zero_has_no_top():
    assert rank([evaluation("r","0.40")])[0].is_top_match
    assert all(r.rank==1 and not r.is_top_match for r in rank([evaluation("a","0"),evaluation("b","0")]))
    assert rank([])==[]


@pytest.mark.parametrize("other",[{"job_fingerprint":"other"},{"rubric_fingerprint":"other"},{"as_of":date(2026,9,29)}, {"scorer_version":"other"}])
def test_incomparable_evaluations_rejected(other):
    with pytest.raises(ValueError): rank([evaluation("a"),evaluation("b",**other)])


def test_duplicate_resume_ids_rejected():
    with pytest.raises(ValueError): rank([evaluation("a"),evaluation("a")])


def test_same_requirement_id_with_different_definition_cannot_rank():
    a=evaluation("a")
    changed=RequirementResult(requirement=req(category="preferred_qualifications"),evidence=[ev()])
    b=evaluation("b",requirement_results=[changed])
    with pytest.raises(ValueError): rank([a,b])
