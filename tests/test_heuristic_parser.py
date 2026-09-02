from backend.services.heuristic_parser import HeuristicParser

def test_heuristic_skill_extraction():
    parser = HeuristicParser()
    sample_jd = """
    Senior Backend Engineer at Netflix
    Salary: $140,000 - $180,000
    Location: Los Gatos, CA (Hybrid)
    Requirements:
    - 5+ years with Python, FastAPI, and PostgreSQL.
    - Experience with Docker, Kubernetes, and AWS is required.
    - Excellent communication and Agile collaboration.
    Bonus:
    - Experience with Kafka or GraphQL.
    """
    analysis = parser.analyze_job_text(sample_jd)
    assert any("Python" in s for s in analysis.required_skills)
    assert any("PostgreSQL" in s for s in analysis.required_skills)
    assert any("Docker" in s or "Kubernetes" in s for s in analysis.tech_stack)
    assert "$140,000 - $180,000" in analysis.salary_range
    assert "Hybrid" in analysis.work_mode
    assert len(analysis.ats_keywords) >= 5

def test_heuristic_resume_matching():
    parser = HeuristicParser()
    sample_jd = "Requirements: Python, Docker, Kubernetes, PostgreSQL, AWS"
    analysis = parser.analyze_job_text(sample_jd)
    
    resume_backend = "Experience: 4 years writing Python, Docker, and PostgreSQL applications."
    match = parser.match_resume(resume_backend, analysis)
    assert "Python" in match.matched_keywords
    assert "Docker" in match.matched_keywords
    assert "Kubernetes" in match.missing_keywords or "AWS" in match.missing_keywords
    assert 30 <= match.match_score <= 80
