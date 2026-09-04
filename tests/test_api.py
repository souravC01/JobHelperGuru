from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def get_auth_headers():
    res = client.post(
        "/api/auth/register",
        json={
            "email": "api_tester@example.com",
            "password": "Password123!",
            "name": "API Tester",
        },
    )
    if res.status_code == 200:
        token = res.json()["token"]
    else:
        res_login = client.post(
            "/api/auth/login",
            json={"email": "api_tester@example.com", "password": "Password123!"},
        )
        token = res_login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_api_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    res_head = client.head("/api/health")
    assert res_head.status_code == 200

    res_alt_get = client.get("/health")
    assert res_alt_get.status_code == 200
    assert res_alt_get.json()["status"] == "ok"

    res_alt_head = client.head("/health")
    assert res_alt_head.status_code == 200


def test_analyze_job_text_endpoint():
    res = client.post(
        "/api/jobs/analyze",
        json={"text": "Software Engineer at Apple in Cupertino. Python, Swift, AWS required."},
    )
    assert res.status_code == 200
    data = res.json()
    assert "Python" in data["required_skills"] or "Python" in data["tech_stack"]


def test_resumes_crud_and_match():
    headers = get_auth_headers()
    # 1. Add Resume
    res = client.post(
        "/api/resumes",
        json={"name": "Test Python Dev", "content": "Python, Docker, SQL expert with 4 years experience."},
        headers=headers,
    )
    assert res.status_code == 200
    r_id = res.json()["id"]

    # 2. Get Resumes
    res = client.get("/api/resumes", headers=headers)
    assert res.status_code == 200
    assert len(res.json()) >= 1

    # 3. Match against job
    job_payload = {
        "company": "Apple",
        "title": "Backend Dev",
        "required_skills": ["Python", "Docker"],
        "tech_stack": ["Python", "SQL"],
        "ats_keywords": ["Microservices"],
    }
    match_res = client.post("/api/resumes/match", json={"job": job_payload}, headers=headers)
    assert match_res.status_code == 200
    ranks = match_res.json()
    assert len(ranks) >= 1
    assert ranks[0]["is_best_fit"] is True

    # 4. Delete Resume
    del_res = client.delete(f"/api/resumes/{r_id}", headers=headers)
    assert del_res.status_code == 200


def test_upload_resume_file_endpoint():
    import docx
    import io

    headers = get_auth_headers()
    doc = docx.Document()
    doc.add_paragraph("Staff Engineer with extensive Kubernetes and Go experience.")
    bio = io.BytesIO()
    doc.save(bio)
    docx_bytes = bio.getvalue()

    files = {
        "file": (
            "staff_resume.docx",
            docx_bytes,
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    }
    data = {"name": "Staff Resume"}

    upload_res = client.post("/api/resumes/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 200
    res_data = upload_res.json()
    assert res_data["name"] == "Staff Resume"
    assert "Kubernetes" in res_data["content"]
    assert "Go" in res_data["content"]

    # Cleanup
    client.delete(f"/api/resumes/{res_data['id']}", headers=headers)


def test_upload_rejects_disallowed_extension():
    headers = get_auth_headers()
    files = {"file": ("malicious.exe", b"\x4d\x5a\x90\x00", "application/x-msdownload")}
    res = client.post("/api/resumes/upload", files=files, headers=headers)
    assert res.status_code == 400
    assert "unsupported file type" in res.json()["detail"].lower()


def test_upload_rejects_oversized_file():
    headers = get_auth_headers()
    # 10MB + 1KB dummy content
    large_bytes = b"0" * (10 * 1024 * 1024 + 1024)
    files = {"file": ("huge_resume.pdf", large_bytes, "application/pdf")}
    res = client.post("/api/resumes/upload", files=files, headers=headers)
    assert res.status_code == 413
    assert "maximum allowed size" in res.json()["detail"].lower()



def test_applications_crud_and_excel_export():
    headers = get_auth_headers()
    # 1. Create Application
    create_res = client.post(
        "/api/applications",
        json={
            "company": "Meta",
            "role": "Software Engineer",
            "status": "Applied",
            "required_skills": ["Python", "React"],
        },
        headers=headers,
    )
    assert create_res.status_code == 200
    app_id = create_res.json()["id"]

    # 2. Get Applications
    get_res = client.get("/api/applications", headers=headers)
    assert get_res.status_code == 200
    assert any(a["id"] == app_id for a in get_res.json())

    # 3. Export Excel
    excel_res = client.get("/api/export/excel", headers=headers)
    assert excel_res.status_code == 200
    assert (
        excel_res.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    assert len(excel_res.content) > 1000

    # 4. Delete Application
    del_res = client.delete(f"/api/applications/{app_id}", headers=headers)
    assert del_res.status_code == 200


def test_all_route_type_annotations_resolve():
    import typing
    for route in app.routes:
        endpoint = getattr(route, "endpoint", None)
        if endpoint and callable(endpoint):
            hints = typing.get_type_hints(endpoint)
            assert isinstance(hints, dict)
