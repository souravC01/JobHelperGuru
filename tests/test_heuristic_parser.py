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

def test_new_grad_not_extracted_as_skill():
    parser = HeuristicParser()
    sample_jd = """
    Software Engineer - New Grad 2026
    Requirements:
    - Must be a New Grad graduating from a computer science degree.
    - Strong knowledge of Java, Spring Boot, and PostgreSQL.
    """
    analysis = parser.analyze_job_text(sample_jd)
    # New grad is NOT a skill
    assert not any("new grad" in s.lower() for s in analysis.required_skills)
    assert not any("new grad" in s.lower() for s in analysis.tech_stack)
    assert not any("new grad" in s.lower() for s in analysis.ats_keywords)
    # Role is recognized as new grad role
    assert analysis.is_new_grad_role is True
    assert "Java" in analysis.required_skills
    assert "Spring Boot" in analysis.required_skills

def test_new_grad_eligibility_window():
    from datetime import datetime
    parser = HeuristicParser()
    ref_date = datetime(2026, 9, 1)

    # 1. Graduating in 1 month (Oct 2026) -> Eligible
    res_oct_2026 = "Education: B.S. in Computer Science, Expected: Oct 2026"
    el_oct = parser.check_new_grad_eligibility(res_oct_2026, ref_date)
    assert el_oct["eligible"] is True
    assert el_oct["months_diff"] == 1

    # 2. Graduated 4 months ago (May 2026) -> Eligible
    res_may_2026 = "Education: Bachelor of Engineering, Graduation: May 2026"
    el_may = parser.check_new_grad_eligibility(res_may_2026, ref_date)
    assert el_may["eligible"] is True
    assert el_may["months_diff"] == -4

    # 3. Graduating in 12 months (Sept 2027) -> Ineligible (> 4 months)
    res_2027 = "Education: Computer Science, Expected: Sep 2027"
    el_2027 = parser.check_new_grad_eligibility(res_2027, ref_date)
    assert el_2027["eligible"] is False
    assert el_2027["months_diff"] > 4

    # 4. Graduated 24 months ago (Sept 2024) -> Ineligible (> 6 months ago)
    res_2024 = "Education: B.S. in Computer Science, Graduation: Sep 2024"
    el_2024 = parser.check_new_grad_eligibility(res_2024, ref_date)
    assert el_2024["eligible"] is False
    assert el_2024["months_diff"] < -6
