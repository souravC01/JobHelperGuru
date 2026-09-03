import uuid
import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_two_user_multi_tenant_isolation():
    # 1. Register User Alpha
    alpha_email = f"alpha_{uuid.uuid4().hex[:6]}@example.com"
    res_alpha_reg = client.post(
        "/api/auth/register",
        json={"email": alpha_email, "password": "Password123!", "name": "Alpha User"},
    )
    assert res_alpha_reg.status_code == 200
    alpha_token = res_alpha_reg.json()["token"]
    alpha_headers = {"Authorization": f"Bearer {alpha_token}"}

    # 2. Register User Beta
    beta_email = f"beta_{uuid.uuid4().hex[:6]}@example.com"
    res_beta_reg = client.post(
        "/api/auth/register",
        json={"email": beta_email, "password": "Password123!", "name": "Beta User"},
    )
    assert res_beta_reg.status_code == 200
    beta_token = res_beta_reg.json()["token"]
    beta_headers = {"Authorization": f"Bearer {beta_token}"}

    # 3. User Alpha adds a Resume and an Application
    res_alpha_resume = client.post(
        "/api/resumes",
        json={"name": "Alpha Senior Python", "content": "Python, Django, FastAPI specialist"},
        headers=alpha_headers,
    )
    assert res_alpha_resume.status_code == 200
    alpha_resume_id = res_alpha_resume.json()["id"]

    res_alpha_app = client.post(
        "/api/applications",
        json={"company": "AlphaCorp", "role": "Lead Architect", "status": "Applied"},
        headers=alpha_headers,
    )
    assert res_alpha_app.status_code == 200
    alpha_app_id = res_alpha_app.json()["id"]

    # 4. User Beta adds a Resume and an Application
    res_beta_resume = client.post(
        "/api/resumes",
        json={"name": "Beta React Designer", "content": "React, Tailwind, UI/UX specialist"},
        headers=beta_headers,
    )
    assert res_beta_resume.status_code == 200
    beta_resume_id = res_beta_resume.json()["id"]

    res_beta_app = client.post(
        "/api/applications",
        json={"company": "BetaCorp", "role": "Staff Frontend", "status": "Interviewing"},
        headers=beta_headers,
    )
    assert res_beta_app.status_code == 200
    beta_app_id = res_beta_app.json()["id"]

    # 5. Verify User Alpha ONLY sees Alpha's data
    alpha_resumes = client.get("/api/resumes", headers=alpha_headers).json()
    assert any(r["id"] == alpha_resume_id for r in alpha_resumes)
    assert not any(r["id"] == beta_resume_id for r in alpha_resumes)

    alpha_apps = client.get("/api/applications", headers=alpha_headers).json()
    assert any(a["id"] == alpha_app_id for a in alpha_apps)
    assert not any(a["id"] == beta_app_id for a in alpha_apps)

    # 6. Verify User Beta ONLY sees Beta's data
    beta_resumes = client.get("/api/resumes", headers=beta_headers).json()
    assert any(r["id"] == beta_resume_id for r in beta_resumes)
    assert not any(r["id"] == alpha_resume_id for r in beta_resumes)

    beta_apps = client.get("/api/applications", headers=beta_headers).json()
    assert any(a["id"] == beta_app_id for a in beta_apps)
    assert not any(a["id"] == alpha_app_id for a in beta_apps)

    # 7. User Alpha cannot delete User Beta's application or resume
    res_del_hack_app = client.delete(f"/api/applications/{beta_app_id}", headers=alpha_headers)
    assert res_del_hack_app.status_code == 404

    res_del_hack_resume = client.delete(f"/api/resumes/{beta_resume_id}", headers=alpha_headers)
    assert res_del_hack_resume.status_code == 404

    # 8. User Beta settings isolation
    client.post(
        "/api/settings",
        json={"model_name": "beta-custom-model", "api_key": "beta-secret-key"},
        headers=beta_headers,
    )
    beta_settings = client.get("/api/settings", headers=beta_headers).json()
    assert beta_settings["model_name"] == "beta-custom-model"

    alpha_settings = client.get("/api/settings", headers=alpha_headers).json()
    assert alpha_settings["model_name"] != "beta-custom-model"

    # Clean up
    client.delete(f"/api/applications/{alpha_app_id}", headers=alpha_headers)
    client.delete(f"/api/resumes/{alpha_resume_id}", headers=alpha_headers)
    client.delete(f"/api/applications/{beta_app_id}", headers=beta_headers)
    client.delete(f"/api/resumes/{beta_resume_id}", headers=beta_headers)
