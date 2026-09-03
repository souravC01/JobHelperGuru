import pytest
from backend.services.ai_engine import AIEngine
from backend.models import (
    BulletOptimizationRequest,
    ClaimStatus,
    Resume,
    JobAnalysisResult,
)

def test_bulletskill_optimization_fallback():
    # When no API key is provided, AIEngine must use Bulletskill.md rules offline
    engine = AIEngine(api_key=None)
    req = BulletOptimizationRequest(
        target_job_title="Senior Java Developer",
        section_type="project",
        target_keyword="Kafka",
        existing_bullet="Built order processing backend using Spring Boot and PostgreSQL.",
        evidence_context=["Used Spring Boot", "Used PostgreSQL"]
    )
    res = engine.optimize_bullet(req)
    assert res.target_keyword == "Kafka"
    assert res.claim_status in [ClaimStatus.UNVERIFIED_SKILL, ClaimStatus.VERIFIED]
    assert len(res.alternatives) >= 1

    # Check What + How + Result format
    alt = res.alternatives[0]
    assert alt.what != ""
    assert alt.how != ""
    assert alt.result_or_reason != ""
    assert "." in alt.bullet
    # Since Kafka was not in evidence_context, it must be UNVERIFIED_SKILL
    assert res.claim_status == ClaimStatus.UNVERIFIED_SKILL
    assert res.requires_confirmation is True
    assert "Kafka" in res.warning

def test_bulletskill_multiple_keywords_incorporation():
    engine = AIEngine(api_key=None)
    req = BulletOptimizationRequest(
        target_job_title="Full Stack Engineer",
        section_type="project",
        target_keywords=["Kafka", "Redis", "Docker"],
        existing_bullet="",
        evidence_context=["Built React frontend and Node.js backend"]
    )
    res = engine.optimize_bullet(req)
    assert "Kafka" in res.target_keyword
    assert "Redis" in res.target_keyword
    assert "Docker" in res.target_keyword
    assert len(res.alternatives) == 3
    for alt in res.alternatives:
        assert "Kafka" in alt.bullet
        assert "Redis" in alt.bullet
        assert "Docker" in alt.bullet
        assert alt.what != ""
        assert alt.how != ""
        assert alt.result_or_reason != ""

    # Check project and bullet to replace detection
    assert res.target_project_name is not None
    assert res.original_bullet_to_replace is not None
    assert res.replacement_rationale is not None

def test_project_bullet_selects_project_section_not_work_history():
    engine = AIEngine(api_key=None)
    resume_context = """
    Experience:
    Senior Software Engineer at Google (2021 - Present)
    - Architected global payment gateway handling $10M transactions daily.

    Projects:
    Personal Distributed Event Bus
    - Built streaming order catalog using Node.js and SQLite.
    """

    # 1. Project request must pick from Projects section
    proj_req = BulletOptimizationRequest(
        target_job_title="Backend Engineer",
        section_type="project",
        target_keywords=["Kafka"],
        evidence_context=[resume_context]
    )
    proj_res = engine.optimize_bullet(proj_req)
    assert "Event Bus" in proj_res.target_project_name or "Project" in proj_res.target_project_name
    assert "streaming order catalog" in proj_res.original_bullet_to_replace
    assert "Google" not in proj_res.target_project_name
    assert "payment gateway" not in proj_res.original_bullet_to_replace

    # 2. Work history request must pick from Work History section
    work_req = BulletOptimizationRequest(
        target_job_title="Backend Engineer",
        section_type="work_history",
        target_keywords=["Kafka"],
        evidence_context=[resume_context]
    )
    work_res = engine.optimize_bullet(work_req)
    assert "Google" in work_res.target_project_name or "Experience" in work_res.target_project_name
    assert "payment gateway" in work_res.original_bullet_to_replace
    assert "Event Bus" not in work_res.target_project_name

def test_bulletskill_verified_claim():
    engine = AIEngine(api_key=None)
    req = BulletOptimizationRequest(
        target_job_title="Backend Developer",
        section_type="work_history",
        target_keyword="PostgreSQL",
        existing_bullet="Maintained databases and wrote queries.",
        evidence_context=["Used PostgreSQL for 2 years", "Wrote complex SQL queries"]
    )
    res = engine.optimize_bullet(req)
    assert res.target_keyword == "PostgreSQL"
    assert res.claim_status == ClaimStatus.VERIFIED
    assert res.requires_confirmation is False
    assert res.alternatives[0].what != ""

def test_rank_resumes_offline():
    engine = AIEngine(api_key=None)
    job = JobAnalysisResult(
        company="Uber",
        title="Distributed Systems Engineer",
        required_skills=["Go", "Kafka", "Kubernetes", "Docker"],
        tech_stack=["Go", "Kafka", "Docker", "AWS"],
        ats_keywords=["Kafka", "Go", "Distributed Systems"]
    )
    resumes = [
        Resume(id="1", name="Go Backend", content="Built Go microservices with Kafka, Docker, and Kubernetes on AWS."),
        Resume(id="2", name="Frontend React", content="React, CSS, Tailwind, Next.js, HTML, Figma developer.")
    ]
    ranked = engine.rank_resumes(resumes, job)
    assert len(ranked) == 2
    assert ranked[0].resume_name == "Go Backend"
    assert ranked[0].is_best_fit is True
    assert ranked[0].match_score > ranked[1].match_score
    assert "Go" in ranked[0].matched_keywords

def test_generate_outreach_offline():
    engine = AIEngine(api_key=None)
    job = JobAnalysisResult(
        company="Stripe",
        title="Software Engineer",
        required_skills=["Python", "PostgreSQL", "APIs"],
        ats_keywords=["Financial Infrastructure", "APIs"]
    )
    resume = Resume(id="1", name="Software Engineer", content="Python, PostgreSQL, REST APIs.")
    outreach = engine.generate_outreach(job, resume)
    assert "Stripe" in outreach.subject_line or "Software Engineer" in outreach.subject_line
    assert len(outreach.cover_letter_pitch) > 100
    assert len(outreach.connection_note) > 30

def test_ai_engine_raises_error_when_api_fails_instead_of_silent_fallback(monkeypatch):
    engine = AIEngine(api_base_url="https://api.openai.com/v1", api_key="sk-test-fail-key", model_name="gpt-4o-mini")

    class MockFailingCompletions:
        def create(self, *args, **kwargs):
            raise ConnectionError("Upstream AI Provider Quota Exceeded (429)")

    class MockClient:
        chat = type("Chat", (), {"completions": MockFailingCompletions()})()

    monkeypatch.setattr(engine, "_get_client", lambda: MockClient())

    # 1. analyze_job must raise RuntimeError, NOT silently return heuristic
    with pytest.raises(RuntimeError) as excinfo:
        engine.analyze_job("Software Engineer with Python experience")
    assert "AI API Provider Failed" in str(excinfo.value)
    assert "Quota Exceeded" in str(excinfo.value)

    # 2. rank_resumes must raise RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        engine.rank_resumes(
            [Resume(id="1", name="Test", content="Python")],
            JobAnalysisResult(title="SE", company="Co", required_skills=["Python"])
        )
    assert "AI API Provider Failed" in str(excinfo.value)

    # 3. optimize_bullet must raise RuntimeError
    with pytest.raises(RuntimeError) as excinfo:
        engine.optimize_bullet(
            BulletOptimizationRequest(
                target_job_title="Engineer",
                section_type="project",
                target_keyword="Python",
                existing_bullet="Built backend.",
            )
        )
    assert "AI API Provider Failed" in str(excinfo.value)

def test_ai_engine_offline_heuristic_mode_bypasses_api():
    # When model_name is "offline-heuristic", it must not initialize an online client
    engine = AIEngine(api_base_url="https://invalid.endpoint", api_key="sk-some-key", model_name="offline-heuristic")
    assert engine._get_client() is None

    # Must succeed cleanly offline
    job = engine.analyze_job("Software Engineer at Google. Requirements: Python, Go, Docker.")
    assert "Python" in job.required_skills or "Python" in job.tech_stack
