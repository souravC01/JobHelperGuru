import time
import pytest
from backend.models import Resume
from backend.services.skill_matching import supports_extracted_skill
from backend.services.matching.profiles import FactProposal, _fact, extract_resume_profile
from backend.services.matching.chunking import TextChunk
from tests.test_match_profiles import ProfileProvider


@pytest.mark.parametrize("source,skill", [
    ("QA & Testing: Functional, Regression, API, Database, Accessibility", "functional testing"),
    ("QA & Testing: Functional, Regression, API, Database, Accessibility", "database testing"),
    ("Built unit and integration tests using JUnit.", "unit testing"),
    ("Built unit and integration tests using JUnit.", "integration testing"),
    ("Built manual and automated test cases.", "manual testing"),
    ("Automated REST API tests using Postman.", "API testing"),
])
def test_explicit_testing_shorthand_is_supported(source, skill):
    assert supports_extracted_skill(source, skill)


@pytest.mark.parametrize("source,skill", [
    ("QA & Testing: Functional, Regression", "performance testing"),
    ("Functional programming and database administration", "functional testing"),
    ("Prevent regressions during feature changes", "regression testing"),
    ("Testing: performance goals; later built a database", "database testing"),
])
def test_related_words_do_not_invent_testing_skills(source, skill):
    assert not supports_extracted_skill(source, skill)


@pytest.mark.parametrize("source,level", [
    ("Projects:\nBuilt REST APIs and\npersistence features.", "demonstrated"),
    ("Projects:\nNever used REST APIs\nin production.", "contradicted"),
    ("Coursework:\nLearning REST APIs and\npersistence features.", "learning"),
])
def test_neighbor_recovery_keeps_context_and_exact_source(source, level):
    item = FactProposal(kind="skill", canonical_key="REST APIs", level="demonstrated", source_line=3)
    found = _fact(item, TextChunk(0, len(source), source), source)
    assert found.level == level
    assert found.source_quote == source.split("\n", 1)[1]


def test_recovery_never_crosses_bullet_or_section_boundaries():
    for source in ["Projects:\nPython\n- Built Rust services.", "Skills:\nPython\nProjects:",
                   "Projects:\nBuilt Rust services.\n- Used Python."]:
        item = FactProposal(kind="skill", canonical_key="Python", level="demonstrated", source_line=3 if source.endswith(('services.', 'Projects:')) else 2)
        with pytest.raises(ValueError):
            _fact(item, TextChunk(0, len(source), source), source)


@pytest.mark.parametrize("text,key", [
    ("No unit or integration tests.", "unit testing"),
    ("Without manual and automated test cases.", "manual testing"),
])
def test_new_test_forms_preserve_negation(text, key):
    source = "Projects:\n"+text
    item = FactProposal(kind="skill", canonical_key=key, level="listed", source_line=2)
    found = _fact(item, TextChunk(0, len(source), source), source)
    assert found.level == "contradicted"


def test_unresolved_claims_keep_verified_facts_and_are_cached_without_scoring(tmp_path):
    from backend.storage import StorageService
    from backend.services.matching.profiles import get_or_build_resume_profile
    from backend.services.matching.scoring import match_cached_skills
    from tests.test_match_scoring import req
    storage = StorageService(str(tmp_path/"review.db"), force_sqlite=True)
    try:
        resume = storage.add_resume("R", "Skills:\nPython", user_id="u")
        items = [dict(kind="skill", canonical_key=key, level="listed", source_line=2)
                 for key in ["Python", "InventedTool"]]
        engine = ProfileProvider([], lambda r: dict(r, items=items))
        def build():
            return get_or_build_resume_profile(resume, user_id="u", engine=engine, storage=storage, deadline=time.monotonic()+30)
        first = build()
        assert first.status == "needs_review" and first.warnings == ["unresolved_skill_claims"]
        assert [f.canonical_key for f in first.facts] == ["python"]
        assert first.unresolved_skills == ["inventedtool"] and not first.profile_fingerprint
        assert build() == first and len(engine.calls) == 1
        with pytest.raises(ValueError, match="Complete cached profile"):
            match_cached_skills([req("Python")], first)
        edited = storage.update_resume(resume.id, content="Skills:\nPython, InventedTool", user_id="u")
        complete = get_or_build_resume_profile(edited, user_id="u", engine=engine, storage=storage, deadline=time.monotonic()+30)
        assert complete.status == "complete" and not complete.unresolved_skills and len(engine.calls) == 2
    finally:
        storage.close()


def test_shared_suffix_support_uses_canonical_skill_aliases():
    assert supports_extracted_skill("Automated and manual testing", "test automation")


@pytest.mark.parametrize("line", [3,4])
@pytest.mark.parametrize("prefix,expected", [("Never used", "contradicted"), ("Learning", "learning")])
def test_recovery_preserves_earlier_wrapped_context(prefix, expected, line):
    source=f"Projects:\n{prefix}\nREST APIs and\npersistence features."
    item=FactProposal(kind="skill",canonical_key="REST APIs",level="demonstrated",source_line=line)
    found=_fact(item,TextChunk(0,len(source),source),source)
    assert found.level==expected and prefix in found.source_quote


def test_shared_testing_suffix_keeps_whole_or_group():
    from tests.test_match_extraction import Provider, extract
    from tests.test_match_skill_sources import jd_item
    text="Manual or functional testing"
    item=jd_item("manual testing",1)
    assert extract(text,Provider([],lambda r:dict(r,items=[item]))).status=="failed"
    item['alternatives']=['manual testing','functional testing']
    result=extract(text,Provider([],lambda r:dict(r,items=[item])))
    assert result.status=="complete" and result.items[0].alternatives==['functional testing','manual testing']


def test_reviewed_quote_cannot_hide_wrapped_negation():
    from backend.services.matching.profiles import extract_resume_profile, resolve_profile_review, SkillReviewDecision
    from tests.test_match_profiles import ProfileProvider
    import time
    from backend.models import Resume
    resume=Resume(id='review',name='R',content='Projects:\nNever used\nPython')
    engine=ProfileProvider([],lambda r: dict(r,items=[dict(kind='skill',canonical_key='Python',level='listed',source_quote='Projects:')]))
    pending=extract_resume_profile(resume,engine=engine,deadline=time.monotonic()+30)
    assert pending.status=='needs_review'
    result=resolve_profile_review(pending,resume,[SkillReviewDecision(skill='python',source_quote='Python')])
    assert result.status=='complete' and result.facts[0].level=='contradicted'


@pytest.mark.parametrize("key", ["Java", "SQL"])
def test_review_does_not_turn_substrings_into_skills(key):
    from backend.services.matching.profiles import extract_resume_profile, resolve_profile_review, SkillReviewDecision
    from tests.test_match_profiles import ProfileProvider
    import time
    from backend.models import Resume
    resume=Resume(id='review',name='R',content='Skills:\nJavaScript and NoSQL')
    engine=ProfileProvider([],lambda r: dict(r,items=[dict(kind='skill',canonical_key=key,level='listed',source_quote='Skills:')]))
    pending=extract_resume_profile(resume,engine=engine,deadline=time.monotonic()+30)
    with pytest.raises(ValueError):
        resolve_profile_review(pending,resume,[SkillReviewDecision(skill=key.lower(),source_quote=key)])
