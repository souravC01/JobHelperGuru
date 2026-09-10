import pytest
from backend.services.skill_matching import contains_skill, match_skills
from backend.models import JobAnalysisResult
from backend.services.heuristic_parser import HeuristicParser


def test_punctuation_skills_match_exact_resume():
    job = JobAnalysisResult(required_skills=["C++", "C#", ".NET"])
    result = HeuristicParser().match_resume("Built with C++, C# and .NET.", job)
    assert result.match_score == 100
    assert result.missing_keywords == []
    assert set(result.matched_keywords) == {"C++", "C#", ".NET"}


def test_c_does_not_match_cpp_or_csharp():
    text = "We write software in C++ and C# daily."
    assert contains_skill(text, "C++") is True
    assert contains_skill(text, "C#") is True
    assert contains_skill(text, "C") is False


def test_c_matches_standalone_or_delimited():
    assert contains_skill("Deep knowledge of C and Python.", "C") is True
    assert contains_skill("Experience in C/C++ development.", "C") is True
    assert contains_skill("Experience in C, Assembly, and Rust.", "C") is True


def test_java_does_not_match_javascript():
    assert contains_skill("Expert in JavaScript and TypeScript.", "Java") is False
    assert contains_skill("Experienced in Java and JavaScript.", "Java") is True


def test_sql_does_not_match_nosql():
    assert contains_skill("Implemented NoSQL data stores like MongoDB.", "SQL") is False
    assert contains_skill("Wrote complex SQL queries in PostgreSQL.", "SQL") is True


def test_dotnet_and_nodejs_punctuation_matching():
    assert contains_skill("Backend developed in .NET Core.", ".NET") is True
    assert contains_skill("Microservices running on Node.js.", "Node.js") is True


def test_match_skills_returns_deterministic_stable_results():
    skills = ["Python", "C++", "Go", "Docker", "SQL", "NoSQL"]
    text = "Proficient in Python, SQL, and Docker."
    matched, missing = match_skills(text, skills)
    assert matched == ["Python", "Docker", "SQL"]
    assert missing == ["C++", "Go", "NoSQL"]
