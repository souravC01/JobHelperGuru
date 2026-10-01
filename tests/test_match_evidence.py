"""The local matcher consumes complete cached facts without an AI provider."""
from datetime import date
import time
import pytest
from backend.models import Resume
from tests.test_match_profiles import ProfileProvider, fact
from tests.test_match_scoring import req


def profile(text, facts):
    from backend.services.matching.profiles import extract_resume_profile
    result=extract_resume_profile(Resume(id="r",name="R",content=text),engine=ProfileProvider(facts),deadline=time.monotonic()+30)
    assert result.status=="complete"
    return result


def match(requirements, p):
    from backend.services.matching.scoring import match_cached_skills
    return match_cached_skills(requirements,p)


def test_matches_aliases_unknown_skills_and_preserves_cached_source():
    p=profile("Skills:\nJS, NebulaDB, JavaScript, NoSQL",[fact("JS, NebulaDB, JavaScript, NoSQL",k) for k in ["JS","NebulaDB","NoSQL"]])
    results=match([req(k) for k in ["javascript","nebuladb","java","sql"]],p)
    assert [i.level.value for i in results]==["listed","listed","not_evidenced","not_evidenced"]
    assert results[0].source_quote==p.facts[0].source_quote and results[0].source_start==p.facts[0].source_start


@pytest.mark.parametrize("level",["learning","contradicted"])
def test_non_positive_cached_skills_do_not_match(level):
    text="Projects:\nLearning Rust." if level=="learning" else "Projects:\nNever used Rust."
    p=profile(text,[fact(text.split("\n",1)[1],"Rust",level=level)])
    assert match([req("rust")],p)[0].level=="not_evidenced"


def test_same_skill_conflict_needs_review_but_other_or_alternative_can_match():
    p=profile("Skills:\nJava, Python\nProjects:\nNever used Python.",[fact("Java, Python","Java"),fact("Java, Python","Python"),fact("Never used Python.","Python",level="contradicted")])
    with pytest.raises(ValueError,match="[Cc]onflict"):match([req("python")],p)
    result=match([req("choice",alternatives=["python","java"])],p)
    assert len(result)==1 and result[0].level=="listed" and result[0].source_quote=="Java, Python"


def test_duplicate_skills_and_reordering_do_not_change_scores():
    from backend.services.matching.scoring import calculate_score
    p=profile("Skills:\nPython\nProjects:\nBuilt Python services.",[fact("Skills:\nPython","Python"),fact("Built Python services.","Python")])
    requirements=[req("python"),req("rust")]
    values=[]
    for facts in [p.facts,list(reversed(p.facts)),p.facts*2]:
        evidence=match(requirements,p.model_copy(update={"facts":facts}))
        values.append(calculate_score(requirements,evidence,as_of=date(2026,10,1)).raw_score)
    assert values==[50,50,50]


def test_incomplete_profile_cannot_prove_absence_and_activities_cannot_supply_skills():
    p=profile("Projects:\nBuilt Python services.",[fact("Built Python services.","Python services","activity")])
    assert match([req("python")],p)[0].level=="not_evidenced"
    with pytest.raises(ValueError):match([req("python")],p.model_copy(update={"status":"needs_review"}))


@pytest.mark.parametrize("level",["listed","demonstrated"])
def test_coursework_only_positive_fact_cannot_match(level):
    p=profile("Coursework:\nPython",[fact("Python","Python",level=level)])
    assert p.facts[0].level=="learning"
    assert match([req("python")],p)[0].level=="not_evidenced"


def test_oop_and_oops_use_one_explicit_skill_identity():
    p=profile("Skills:\nOOPS",[fact("OOPS","OOP",level="listed")])
    assert p.facts[0].canonical_key=="oop"
    assert match([req("object-oriented programming")],p)[0].level=="listed"
