from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

def test_analyze_job_text_endpoint():
    res = client.post("/api/jobs/analyze", json={"text": "Software Engineer at Apple in Cupertino. Python, Swift, AWS required."})
    assert res.status_code == 200
    data = res.json()
    assert "Python" in data["required_skills"] or "Python" in data["tech_stack"]

def test_resumes_crud_and_match():
    # 1. Add Resume
    res = client.post("/api/resumes", json={"name": "Test Python Dev", "content": "Python, Docker, SQL expert with 4 years experience."})
    assert res.status_code == 200
    r_id = res.json()["id"]

    # 2. Get Resumes
    res = client.get("/api/resumes")
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 3. Match against job
    job_payload = {
        "company": "Apple",
        "title": "Backend Dev",
        "required_skills": ["Python", "Docker"],
        "tech_stack": ["Python", "SQL"],
        "ats_keywords": ["Microservices"]
    }
    match_res = client.post("/api/resumes/match", json={"job": job_payload})
    assert match_res.status_code == 200
    ranks = match_res.json()
    assert len(ranks) >= 1
    assert ranks[0]["is_best_fit"] is True

    # 4. Delete Resume
    del_res = client.delete(f"/api/resumes/{r_id}")
    assert del_res.status_code == 200

def test_applications_crud_and_excel_export():
    # 1. Create Application
    create_res = client.post("/api/applications", json={
        "company": "Meta",
        "role": "Software Engineer",
        "status": "Applied",
        "required_skills": ["Python", "React"]
    })
    assert create_res.status_code == 200
    app_id = create_res.json()["id"]

    # 2. Get Applications
    get_res = client.get("/api/applications")
    assert get_res.status_code == 200
    assert any(a["id"] == app_id for a in get_res.json())

    # 3. Export Excel
    excel_res = client.get("/api/export/excel")
    assert excel_res.status_code == 200
    assert excel_res.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert len(excel_res.content) > 1000

    # 4. Delete Application
    del_res = client.delete(f"/api/applications/{app_id}")
    assert del_res.status_code == 200
