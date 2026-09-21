"""Tests for the v2 Evidence-Based Resume Evaluation API endpoint (POST /api/resumes/evaluate)."""

from __future__ import annotations


def test_evaluate_requires_authentication(client):
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills: Python", "resume_ids": ["r-1"]},
    )
    assert res.status_code == 401


def test_evaluate_validates_empty_and_oversized_job_text(two_users):
    client, alpha, _ = two_users

    # Empty string
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "", "resume_ids": ["r-1"]},
        headers=alpha,
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

    # Whitespace only
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "   \n\t   ", "resume_ids": ["r-1"]},
        headers=alpha,
    )
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()

    # Oversized text (> 100,000 chars)
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "x" * 100_001, "resume_ids": ["r-1"]},
        headers=alpha,
    )
    assert res.status_code == 400
    assert "exceed" in res.json()["detail"].lower()


def test_evaluate_validates_resume_ids(two_users):
    client, alpha, _ = two_users

    # Empty list
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills: Python", "resume_ids": []},
        headers=alpha,
    )
    assert res.status_code == 400
    assert "at least one" in res.json()["detail"].lower()

    # Duplicate IDs
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills: Python", "resume_ids": ["r-1", "r-1"]},
        headers=alpha,
    )
    assert res.status_code == 400
    assert "duplicate" in res.json()["detail"].lower()


def test_evaluate_rejects_nonexistent_and_foreign_resumes(two_users):
    client, alpha, beta = two_users

    # Add resume for user 2 (beta)
    r2 = client.post(
        "/api/resumes",
        json={"name": "User 2 Resume", "content": "C++ developer"},
        headers=beta,
    ).json()

    # User 1 tries nonexistent resume
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills: Python", "resume_ids": ["does-not-exist"]},
        headers=alpha,
    )
    assert res.status_code == 404

    # User 1 tries to access User 2's resume
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills: Python", "resume_ids": [r2["id"]]},
        headers=alpha,
    )
    assert res.status_code == 404


def test_evaluate_success_ranking_and_evidence(two_users):
    client, alpha, _ = two_users

    # User 1 adds two resumes
    r1 = client.post(
        "/api/resumes",
        json={"name": "Python Resume", "content": "Built Python web services and deployed on AWS."},
        headers=alpha,
    ).json()
    r2 = client.post(
        "/api/resumes",
        json={"name": "Java Resume", "content": "Enterprise Java engineer with Spring Boot."},
        headers=alpha,
    ).json()

    job_text = "Required skills:\nPython\nAWS\n"
    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": job_text, "resume_ids": [r1["id"], r2["id"]]},
        headers=alpha,
    )
    assert res.status_code == 200
    batch = res.json()

    assert batch["comparison_complete"] is True
    assert len(batch["evaluations"]) == 2

    eval_r1 = next(e for e in batch["evaluations"] if e["resume_id"] == r1["id"])
    eval_r2 = next(e for e in batch["evaluations"] if e["resume_id"] == r2["id"])

    assert eval_r1["match_score"] == 100
    assert eval_r1["rank"] == 1
    assert eval_r1["is_top_match"] is True

    assert eval_r2["match_score"] == 0
    assert eval_r2["rank"] == 2
    assert eval_r2["is_top_match"] is False

    # Check evidence structure
    assert len(eval_r1["requirement_results"]) == 2
    for rr in eval_r1["requirement_results"]:
        assert len(rr["evidence"]) >= 1
        assert rr["evidence"][0]["source_quote"] != ""


def test_evaluate_ties_and_zero_matches(two_users):
    client, alpha, _ = two_users

    # Two resumes with Python -> Tie at rank 1
    r1 = client.post(
        "/api/resumes",
        json={"name": "Dev A", "content": "Built Python microservices"},
        headers=alpha,
    ).json()
    r2 = client.post(
        "/api/resumes",
        json={"name": "Dev B", "content": "Developed Python data processing"},
        headers=alpha,
    ).json()

    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills:\nPython\n", "resume_ids": [r1["id"], r2["id"]]},
        headers=alpha,
    )
    assert res.status_code == 200
    batch = res.json()
    e1 = next(e for e in batch["evaluations"] if e["resume_id"] == r1["id"])
    e2 = next(e for e in batch["evaluations"] if e["resume_id"] == r2["id"])

    assert e1["rank"] == 1
    assert e2["rank"] == 1
    assert e1["is_top_match"] is True
    assert e2["is_top_match"] is True

    # Two resumes with 0 matches -> Tie at rank 1, but NEITHER is marked is_top_match
    r_zero_1 = client.post(
        "/api/resumes",
        json={"name": "Ruby Dev", "content": "Ruby on Rails"},
        headers=alpha,
    ).json()
    r_zero_2 = client.post(
        "/api/resumes",
        json={"name": "PHP Dev", "content": "PHP Laravel"},
        headers=alpha,
    ).json()

    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "Required skills:\nPython\n", "resume_ids": [r_zero_1["id"], r_zero_2["id"]]},
        headers=alpha,
    )
    assert res.status_code == 200
    zero_batch = res.json()
    for e in zero_batch["evaluations"]:
        assert e["match_score"] == 0
        assert e["rank"] == 1
        assert e["is_top_match"] is False


def test_evaluate_unscorable_job_returns_unranked_batch(two_users):
    client, alpha, _ = two_users

    r1 = client.post(
        "/api/resumes",
        json={"name": "Dev", "content": "Python engineer"},
        headers=alpha,
    ).json()

    res = client.post(
        "/api/resumes/evaluate",
        json={"job_text": "About us: Stealth startup with great snacks.", "resume_ids": [r1["id"]]},
        headers=alpha,
    )
    assert res.status_code == 200
    batch = res.json()
    assert batch["comparison_complete"] is False
    assert len(batch["evaluations"]) == 1
    e = batch["evaluations"][0]
    assert e["status"] in {"needs_review", "failed"}
    assert e["rank"] is None
    assert e["match_score"] is None
    assert e["is_top_match"] is False


def test_evaluate_caching_and_fresh_flag(two_users):
    client, alpha, _ = two_users

    r = client.post(
        "/api/resumes",
        json={"name": "Cacher Resume", "content": "Built Python backend services."},
        headers=alpha,
    ).json()

    job_text = "Required skills:\nPython\n"
    # 1. First evaluation creates snapshot
    res1 = client.post(
        "/api/resumes/evaluate",
        json={"job_text": job_text, "resume_ids": [r["id"]], "fresh": False},
        headers=alpha,
    )
    assert res1.status_code == 200
    batch1 = res1.json()
    assert batch1["evaluations"][0]["match_score"] == 100

    # 2. Second evaluation should hit cache
    res2 = client.post(
        "/api/resumes/evaluate",
        json={"job_text": job_text, "resume_ids": [r["id"]], "fresh": False},
        headers=alpha,
    )
    assert res2.status_code == 200
    batch2 = res2.json()
    assert batch2["evaluations"][0]["match_score"] == 100

    # 3. Third evaluation with fresh=True bypasses cache
    res3 = client.post(
        "/api/resumes/evaluate",
        json={"job_text": job_text, "resume_ids": [r["id"]], "fresh": True},
        headers=alpha,
    )
    assert res3.status_code == 200
    batch3 = res3.json()
    assert batch3["evaluations"][0]["match_score"] == 100


def test_legacy_match_remains_backward_compatible(two_users):
    client, alpha, _ = two_users

    client.post(
        "/api/resumes",
        json={"name": "Legacy Resume", "content": "Python, Docker, SQL engineer."},
        headers=alpha,
    )
    job_payload = {
        "company": "Legacy Corp",
        "title": "Backend Dev",
        "required_skills": ["Python", "Docker"],
        "tech_stack": ["Python"],
        "ats_keywords": ["Docker"],
    }
    res = client.post(
        "/api/resumes/match",
        json={"job": job_payload},
        headers=alpha,
    )
    assert res.status_code == 200
    ranks = res.json()
    assert isinstance(ranks, list)
    assert len(ranks) >= 1
    assert "match_score" in ranks[0]
    assert "is_best_fit" in ranks[0]
