"""Single-pass source references and deterministic category matching."""
import time
import pytest
from backend.models import Resume
from tests.test_match_extraction import Provider, extract
from tests.test_match_profiles import ProfileProvider, fact
from tests.test_match_evidence import profile, match
from tests.test_match_scoring import req


def jd_item(key, line, **extra):
    return {**dict(category="required_skills", kind="skill", canonical_key=key,
                   alternatives=[], required_months=None, source_line=line), **extra}


def test_jd_line_reference_keeps_repeated_source_and_or_meaning():
    text = "Java or Python\nJava or Python"
    provider = Provider([], lambda r: dict(r, items=[jd_item("Java", 2, alternatives=["Java", "Python"])]))
    result = extract(text, provider)
    assert result.status == "complete" and len(provider.calls) == 1
    assert result.items[0].source_start == 15
    assert result.items[0].source_quote == "Java or Python"
    assert result.items[0].alternatives == ["java", "python"]


@pytest.mark.parametrize("item", [jd_item("Kafka", 1), jd_item("Python", 9), jd_item("Python", True),
                                    jd_item("Python", 1, source_quote="Python")])
def test_bad_reference_or_invented_skill_fails_once(item):
    provider = Provider([], lambda r: dict(r, items=[item]))
    result = extract("Required Python", provider)
    assert result.status == "failed" and not result.items and len(provider.calls) == 1


def test_line_reference_cannot_hide_or_alternative():
    result = extract("Java or Python", Provider([], lambda r: dict(r, items=[jd_item("Python", 1)])))
    assert result.status == "failed"


def test_resume_lines_keep_positive_negative_and_learning_context():
    from backend.services.matching.profiles import extract_resume_profile, validate_profile
    text = "Skills:\nPython\nProjects:\nNever used Python.\nCoursework:\nRust"
    items = [dict(kind="skill", canonical_key=k, level="listed", source_line=n)
             for k, n in [("Python", 2), ("Python", 4), ("Rust", 6)]]
    engine = ProfileProvider([], lambda r: dict(r, items=items))
    resume = Resume(id="r", name="R", content=text)
    result = extract_resume_profile(resume, engine=engine, deadline=time.monotonic()+30)
    assert result.status == "complete" and len(engine.calls) == 1
    assert [f.level.value for f in result.facts] == ["listed", "contradicted", "learning"]
    assert validate_profile(result, resume) == result
    with pytest.raises(ValueError, match="Conflicting"):
        match([req("programming languages")], result)


def test_clear_coordinated_testing_list_can_expand_without_invention():
    from backend.services.matching.profiles import extract_resume_profile
    text = "Skills:\nManual, functional and regression testing"
    engine = ProfileProvider([], lambda r: dict(r, items=[dict(kind="skill", canonical_key=k,
                              level="listed", source_line=2) for k in ["manual testing", "functional testing", "regression testing"]]))
    result = extract_resume_profile(Resume(id="r", name="R", content=text), engine=engine, deadline=time.monotonic()+30)
    assert result.status == "complete" and len(result.facts) == 3
    invented = extract(text, Provider([], lambda r: dict(r, items=[jd_item("performance testing", 2)])))
    assert invented.status == "failed"


@pytest.mark.parametrize("wanted,held,expected", [
    ("programming languages", "Python", "listed"),
    ("test automation frameworks", "Playwright", "listed"),
    ("cloud platforms", "AWS", "listed"),
    ("Java", "Python", "not_evidenced"),
    ("AWS", "cloud platforms", "not_evidenced"),
    ("Selenium", "Playwright", "not_evidenced"),
    ("test case design", "test case development", "listed"),
    ("CI/CD", "continuous integration / continuous delivery", "listed"),
])
def test_reviewed_category_members_and_synonyms_are_directional(wanted, held, expected):
    p = profile("Skills:\n"+held, [fact(held, held, level="listed")])
    assert match([req(wanted)], p)[0].level == expected


def test_synonyms_do_not_duplicate_jd_denominator():
    text = "Test case design\nTest case development"
    provider = Provider([], lambda r: dict(r, items=[jd_item("test case design", 1), jd_item("test case development", 2)]))
    result = extract(text, provider)
    assert result.status == "complete" and len(result.items) == 1


def test_or_group_accepts_parenthetical_expansion_of_same_skill():
    text = "WebdriverIO, BDD (Behavior Driven Development), or performance testing"
    item = jd_item("BDD", 1, alternatives=["WebdriverIO", "BDD", "performance testing"])
    result = extract(text, Provider([], lambda r: dict(r, items=[item])))
    assert result.status == "complete" and len(result.items) == 1
    assert result.items[0].alternatives == ["bdd", "performance testing", "webdriverio"]
    item["alternatives"] = ["WebdriverIO", "performance testing"]
    assert extract(text, Provider([], lambda r: dict(r, items=[item]))).status == "failed"


def test_split_or_proposals_are_one_source_backed_cached_requirement():
    from backend.services.matching.pipeline import _validate_rubric
    from backend.services.matching.provenance import fingerprint
    text = "Exposure to WebdriverIO, BDD (Behavior Driven Development), or performance testing is a plus."
    items = [jd_item(key, 1, category="preferred_qualifications") for key in
             ["WebdriverIO", "BDD (Behavior-Driven Development)", "Performance testing"]]
    provider = Provider([], lambda r: dict(r, items=items))
    result = extract(text, provider)
    assert result.status == "complete" and len(result.items) == 1
    assert len(provider.calls) == 1
    assert result.items[0].alternatives == ["bdd", "performance testing", "webdriverio"]
    row = dict(payload_json=result.model_dump_json(), rubric_fingerprint=fingerprint(result.model_dump(mode="json")))
    assert _validate_rubric(row, text) == result
    # Missing options, conflicting categories and invented acronym expansions stay blocked.
    for invalid in [items[:1]+items[2:],
                    [items[0], dict(items[1], category="required_skills"), items[2]],
                    [items[0], dict(items[1], canonical_key="BDD (Kafka)"), items[2]]]:
        assert extract(text, Provider([], lambda r: dict(r, items=invalid))).status == "failed"


@pytest.mark.parametrize("text", ["Java and Python", "Java or Python"])
def test_split_source_lists_preserve_and_versus_or(text):
    items = [jd_item(key, 1) for key in ["Java", "Python"]]
    result = extract(text, Provider([], lambda r: dict(r, items=items)))
    assert result.status == "complete"
    assert len(result.items) == (1 if " or " in text else 2)


@pytest.mark.parametrize("text,key", [("  Python", "Python"), ("Python  ", "Python"),
    ("No behavior driven development experience.", "BDD"),
    ("No manual, functional and regression testing experience.", "manual testing")])
def test_source_line_roundtrip_preserves_spacing_and_negation(text, key):
    from backend.services.matching.profiles import extract_resume_profile, validate_profile
    resume = Resume(id="r", name="R", content="Skills:\n"+text)
    engine = ProfileProvider([], lambda r: dict(r, items=[dict(kind="skill", canonical_key=key, level="listed", source_line=2)]))
    result = extract_resume_profile(resume, engine=engine, deadline=time.monotonic()+30)
    assert result.status == "complete"
    assert result.facts[0].source_quote == text
    assert result.facts[0].level == ("contradicted" if text.startswith("No ") else "listed")
    assert validate_profile(result, resume) == result


@pytest.mark.parametrize("text,keys", [("  Required Python  ", ["Python"]),
    ("Selenium WebDriver or Playwright", ["Selenium", "Playwright"]),
    ("CI/CD pipelines or Jenkins", ["CI/CD", "Jenkins"])])
def test_jd_line_and_long_alias_roundtrip(text, keys):
    from backend.services.matching.pipeline import _validate_rubric
    from backend.services.matching.provenance import fingerprint
    item = jd_item(keys[0], 1, alternatives=keys if len(keys)>1 else [])
    result = extract(text, Provider([], lambda r: dict(r, items=[item])))
    assert result.status == "complete"
    row = dict(payload_json=result.model_dump_json(), rubric_fingerprint=fingerprint(result.model_dump(mode="json")))
    assert _validate_rubric(row, text) == result


@pytest.mark.parametrize("compound,parts", [("Agile/Scrum", ["agile", "scrum"]), ("SDLC / STLC", ["sdlc", "stlc"])])
def test_known_compounds_supply_both_skills_without_ai(compound, parts):
    p = profile("Skills:\n"+compound, [fact(compound, compound, level="listed")])
    assert all(e.level == "listed" for e in match([req(k) for k in parts], p))
    result = extract(compound, Provider([], lambda r: dict(r, items=[jd_item(compound, 1)])))
    assert result.status == "complete" and {r.canonical_key for r in result.items} == set(parts)
    negative = profile("Skills:\nNever used "+compound, [fact("Never used "+compound, compound, level="listed")])
    assert all(e.level == "not_evidenced" for e in match([req(k) for k in parts], negative))
    assert match([req("ci")], profile("Skills:\nCI/CD", [fact("CI/CD", "CI/CD", level="listed")]))[0].level == "not_evidenced"
