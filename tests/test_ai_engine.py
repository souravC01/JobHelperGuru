import pytest
from backend.services.ai_engine import AIEngine, extract_json_from_llm_response
from backend.models import (
    BulletOptimizationRequest,
    ClaimStatus,
    Resume,
    JobAnalysisResult,
)

def test_extract_json_from_llm_response_with_think_tags():
    raw_llm = "<think>Analyzing candidates skills...</think>\n```json\n{\"company\": \"Google\", \"title\": \"SWE\"}\n```"
    parsed = extract_json_from_llm_response(raw_llm)
    assert parsed["company"] == "Google"
    assert parsed["title"] == "SWE"

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


def test_ai_engine_extracts_experience_required_offline():
    engine = AIEngine(api_key=None)
    text = "Senior Python Engineer at Datadog. Requires 3-5 years of backend experience."
    res = engine.analyze_job(text)
    assert res.experience_required == "3-5 years"


def test_ai_engine_extracts_experience_required_new_grad_offline():
    engine = AIEngine(api_key=None)
    text = "Software Engineer - New Grad 2026. Looking for university graduates."
    res = engine.analyze_job(text)
    assert res.experience_required == "New Grad"


def test_extract_raw_content_from_response_with_reasoning_and_null_content():
    from backend.services.ai_engine import extract_raw_content_from_response
    from unittest.mock import MagicMock

    # 1. Standard message with content
    mock_msg1 = MagicMock(content="pong", reasoning_content=None, model_extra={})
    mock_resp1 = MagicMock(choices=[MagicMock(message=mock_msg1)])
    assert extract_raw_content_from_response(mock_resp1) == "pong"

    # 2. Reasoning model (GLM-5.3, DeepSeek-R1) with content=None and reasoning_content set
    mock_msg2 = MagicMock(content=None, reasoning_content="Thinking about ping...", model_extra={})
    mock_resp2 = MagicMock(choices=[MagicMock(message=mock_msg2)])
    assert extract_raw_content_from_response(mock_resp2) == "Thinking about ping..."

    # 3. Model extra dict reasoning_content
    mock_msg3 = MagicMock(content=None, reasoning_content=None, model_extra={"reasoning_content": "Extra thought"})
    mock_resp3 = MagicMock(choices=[MagicMock(message=mock_msg3)])
    assert extract_raw_content_from_response(mock_resp3) == "Extra thought"

    # 4. Completely null / empty choices
    mock_msg4 = MagicMock(content=None, reasoning_content=None, model_extra={})
    mock_resp4 = MagicMock(choices=[MagicMock(message=mock_msg4)])
    assert extract_raw_content_from_response(mock_resp4) == ""

    assert extract_raw_content_from_response(None) == ""
    assert extract_raw_content_from_response(MagicMock(choices=[])) == ""


def test_settings_test_ai_endpoint_with_reasoning_model(monkeypatch):
    from unittest.mock import MagicMock
    from fastapi.testclient import TestClient
    from backend.main import app

    client = TestClient(app)

    mock_msg = MagicMock(content=None, reasoning_content="Thinking about pong...", model_extra={})
    mock_resp = MagicMock(choices=[MagicMock(message=mock_msg)])

    class MockCompletions:
        def create(self, **kwargs):
            return mock_resp

    class MockClient:
        chat = type("Chat", (), {"completions": MockCompletions()})()

    monkeypatch.setattr("backend.services.ai_engine.AIEngine._get_client", lambda self: MockClient())

    from backend.routers.auth import get_current_user
    from backend.models import User

    app.dependency_overrides[get_current_user] = lambda: User(
        id="user-1", email="test@example.com", name="Tester", created_at="2026-09-07T00:00:00"
    )

    try:
        res = client.post(
            "/api/settings/test-ai",
            json={
                "api_base_url": "https://api.tokenrouter.com/v1",
                "api_key": "tr-test-key",
                "model_name": "z-ai/glm-5.3",
            },
        )
        assert res.status_code == 200
        data = res.json()
        assert data["success"] is True
        assert "Successfully connected to z-ai/glm-5.3!" in data["message"]
        assert "Thinking about pong..." in data["message"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


def test_ensure_three_paragraph_cover_letter_single_paragraph_split():
    from backend.services.ai_engine import ensure_three_paragraph_cover_letter, sanitize_dashes
    job = JobAnalysisResult(company="Acme Corp", title="Staff Engineer", required_skills=["Python", "FastAPI"])
    resume = Resume(id="res-1", name="My_Resume_File.pdf", content="Experienced developer.")
    single_para = "I am excited to apply. I have extensive experience building distributed systems. I look forward to meeting the team."
    result = ensure_three_paragraph_cover_letter(single_para, job, resume, candidate_name="John Doe")

    blocks = [b.strip() for b in result.split("\n\n") if b.strip()]
    assert len(blocks) >= 5
    assert blocks[0].startswith("Dear ")
    assert "Acme Corp" in blocks[0]
    assert blocks[-1].startswith("Sincerely")
    assert "John Doe" in blocks[-1]
    assert "My_Resume_File.pdf" not in blocks[-1]
    assert "\u2014" not in result
    assert "\u2013" not in result


def test_sanitize_dashes_replaces_unicode_dashes():
    from backend.services.ai_engine import sanitize_dashes
    text = "Full\u2014Stack Developer \u2013 Python/React"
    clean = sanitize_dashes(text)
    assert clean == "Full-Stack Developer - Python/React"
    assert "\u2014" not in clean
    assert "\u2013" not in clean


def test_generate_outreach_three_paragraphs_and_zero_em_dashes():
    engine = AIEngine(api_key=None)
    job = JobAnalysisResult(company="Stripe", title="Backend Engineer", required_skills=["Python", "PostgreSQL", "Kafka"])
    resume = Resume(id="res-2", name="Senior_SWE_Resume.pdf", content="Built payment pipelines in Python and PostgreSQL.")

    outreach = engine.generate_outreach(job, resume, candidate_name="Jane Smith")
    assert outreach.subject_line != ""
    assert "Jane Smith" in outreach.subject_line
    assert "Senior_SWE_Resume.pdf" not in outreach.subject_line
    assert outreach.connection_note != ""
    assert len(outreach.connection_note) < 300

    blocks = [b.strip() for b in outreach.cover_letter_pitch.split("\n\n") if b.strip()]
    assert len(blocks) >= 5
    assert "Jane Smith" in blocks[-1]
    assert "Senior_SWE_Resume.pdf" not in blocks[-1]
    assert "\u2014" not in outreach.cover_letter_pitch
    assert "\u2013" not in outreach.cover_letter_pitch
    assert "\u2014" not in outreach.subject_line
    assert "\u2013" not in outreach.subject_line
    assert "\u2014" not in outreach.connection_note
    assert "\u2013" not in outreach.connection_note


def test_generate_outreach_prefers_account_name_over_resume_filename():
    engine = AIEngine(api_key=None)
    job = JobAnalysisResult(company="Netflix", title="Staff Engineer", required_skills=["Java", "Spring"])
    resume = Resume(id="res-3", name="My_Software_Resume_2026.pdf", content="Java expert.")

    # Account candidate name provided
    outreach = engine.generate_outreach(job, resume, candidate_name="Devon Miles")
    assert "Devon Miles" in outreach.subject_line
    assert "My_Software_Resume_2026.pdf" not in outreach.subject_line
    assert "Devon Miles" in outreach.cover_letter_pitch
    assert "My_Software_Resume_2026.pdf" not in outreach.cover_letter_pitch

    # When no candidate name provided, defaults to Candidate and never uses resume file name
    outreach_def = engine.generate_outreach(job, resume, candidate_name=None)
    assert "Candidate" in outreach_def.subject_line
    assert "My_Software_Resume_2026.pdf" not in outreach_def.subject_line
    assert "Candidate" in outreach_def.cover_letter_pitch
    assert "My_Software_Resume_2026.pdf" not in outreach_def.cover_letter_pitch

