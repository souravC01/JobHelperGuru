import pytest
from datetime import datetime
from unittest.mock import MagicMock
from fastapi.testclient import TestClient

from backend.models import (
    JobAnalysisResult,
    Resume,
    ResumeMatchResult,
    BulletOptimizationRequest,
    ClaimStatus,
    User,
)
from backend.services.heuristic_parser import HeuristicParser
from backend.services.ai_engine import AIEngine


def test_heuristic_parser_does_not_use_detected_company_placeholder():
    parser = HeuristicParser()
    result = parser.analyze_job_text("Looking for a Python developer with Docker skills.")
    assert result.company in ["Unknown Company", "Unknown", ""]
    assert result.location in ["Unknown", ""]
    assert result.company != "Detected Company"
    assert result.location != "Identified Location"


def test_scraped_metadata_survives_heuristic_path(monkeypatch):
    from backend.main import app
    from backend.services.scraper import ScrapedJob

    mock_scraped = ScrapedJob(
        title="Staff Security Engineer",
        company="Acme Cyber Defense",
        location="Toronto, ON",
        raw_text="Staff Security Engineer. Requirements: Python, C++, Docker, Kubernetes. Build secure services.",
        source_url="https://jobs.example.com/staff-sec",
    )

    monkeypatch.setattr("backend.services.scraper.ScraperService.scrape_url", lambda self, url: mock_scraped)
    client = TestClient(app)

    res = client.post("/api/jobs/analyze", json={"url": "https://jobs.example.com/staff-sec"})
    assert res.status_code == 200
    data = res.json()
    assert data["company"] == "Acme Cyber Defense"
    assert data["location"] == "Toronto, ON"
    assert data["title"] == "Staff Security Engineer"
    assert data["analysis"]["company"] == "Acme Cyber Defense"
    assert data["analysis"]["location"] == "Toronto, ON"


def test_scraped_metadata_survives_ai_path_with_generic_placeholders(monkeypatch):
    from backend.main import app
    from backend.services.scraper import ScrapedJob

    mock_scraped = ScrapedJob(
        title="Senior Site Reliability Engineer",
        company="Stripe Payments",
        location="Remote, Canada",
        raw_text="Senior Site Reliability Engineer. Requirements: Go, Kubernetes, Terraform.",
        source_url="https://stripe.com/jobs/sre",
    )
    monkeypatch.setattr("backend.services.scraper.ScraperService.scrape_url", lambda self, url: mock_scraped)

    ai_generic_result = JobAnalysisResult(
        company="Company Name",
        title="Exact Role Title",
        location="City, State or Remote/Hybrid",
        required_skills=["Go", "Kubernetes"],
    )
    monkeypatch.setattr("backend.services.ai_engine.AIEngine.analyze_job", lambda self, text, source_url="": ai_generic_result)

    client = TestClient(app)
    res = client.post("/api/jobs/analyze", json={"url": "https://stripe.com/jobs/sre"})
    assert res.status_code == 200
    data = res.json()
    assert data["company"] == "Stripe Payments"
    assert data["location"] == "Remote, Canada"
    assert data["title"] == "Senior Site Reliability Engineer"


def test_candidate_c_does_not_contain_hardcoded_99_9():
    engine = AIEngine(api_key=None)
    req = BulletOptimizationRequest(
        target_job_title="DevOps Engineer",
        section_type="project",
        target_keyword="Kubernetes",
        existing_bullet="",
        evidence_context=["Worked with Docker containers"]
    )
    resp = engine.optimize_bullet(req)
    for alt in resp.alternatives:
        assert "99.9%" not in alt.bullet
        assert "99.9%" not in alt.result_or_reason


def test_optimize_bullet_handles_null_existing_bullet():
    engine = AIEngine(api_key=None)
    req = BulletOptimizationRequest(
        target_job_title="Software Engineer",
        section_type="work_history",
        target_keyword="Python",
        existing_bullet=None,
        evidence_context=["Python developer"]
    )
    resp = engine.optimize_bullet(req)
    assert resp.status in ["rewritten", "suggested"]
    assert len(resp.alternatives) == 3


def test_empty_resume_outreach_does_not_affirm_hands_on_skills():
    engine = AIEngine(api_key=None)
    job = JobAnalysisResult(
        company="Datadog",
        title="Senior Go Engineer",
        required_skills=["Go", "Kubernetes", "Kafka"],
    )
    empty_resume = Resume(id="empty-1", name="Empty Resume", content="")
    outreach = engine.generate_outreach(job, empty_resume)

    pitch_lower = outreach.cover_letter_pitch.lower()
    note_lower = outreach.connection_note.lower()

    # Must not claim hands-on experience or strong experience when resume has no content
    assert "hands-on experience in go" not in pitch_lower
    assert "strong experience in go" not in note_lower
    assert "draft" in pitch_lower or "[" in pitch_lower or "interest in" in pitch_lower


def test_new_grad_eligibility_unknown_when_no_grad_date_detected():
    parser = HeuristicParser()
    resume_no_date = "Experienced Engineer with 10 years experience in Java and SQL."
    res = parser.check_new_grad_eligibility(resume_no_date)
    assert res["eligible"] is None
    assert "not detected" in res["status"].lower()
    assert res["grad_date"] is None


def test_new_grad_eligibility_unknown_when_employer_criteria_unspecified():
    parser = HeuristicParser()
    resume_with_date = "Education: B.S. Computer Science, Expected: May 2026"
    res = parser.check_new_grad_eligibility(resume_with_date, employer_criteria=None)
    assert res["eligible"] is None
    assert "not specified" in res["status"].lower()
    assert res["grad_date"] == "May 2026"


def test_new_grad_eligibility_explicit_employer_date_window():
    parser = HeuristicParser()
    employer_criteria = "Between May 2025 and June 2026"

    # In window: Dec 2025 -> eligible
    res_in = parser.check_new_grad_eligibility(
        "B.S. in Software Engineering, Expected: Dec 2025",
        employer_criteria=employer_criteria
    )
    assert res_in["eligible"] is True

    # Out of window: Dec 2024 -> ineligible
    res_out = parser.check_new_grad_eligibility(
        "B.S. in Software Engineering, Graduated: Dec 2024",
        employer_criteria=employer_criteria
    )
    assert res_out["eligible"] is False


def test_new_grad_job_does_not_default_to_hardcoded_4_6_month_criteria():
    parser = HeuristicParser()
    text = "Software Engineer - New Grad 2026. Join our team."
    res = parser.analyze_job_text(text)
    assert res.is_new_grad_role is True
    # If no window is stated in text, new_grad_criteria should be None or not hardcoded 4/6 month
    assert res.new_grad_criteria is None or "4 months" not in res.new_grad_criteria
