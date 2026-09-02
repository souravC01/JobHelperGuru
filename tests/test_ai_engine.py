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
