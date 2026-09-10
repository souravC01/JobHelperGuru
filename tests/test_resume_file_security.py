import io
from pathlib import Path
import pytest
from backend.services.object_storage import ObjectStorageService


def test_client_cannot_supply_file_key_on_create(two_users):
    client, alpha, _ = two_users
    payload = {
        "name": "Attacker Resume",
        "content": "Resume text",
        "file_key": "resumes/victim_id/secret.pdf",
    }
    response = client.post("/api/resumes", headers=alpha, json=payload)
    # Public resume create must forbid client-supplied file_key
    assert response.status_code == 422


def test_path_traversal_delete_is_blocked(tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    sentinel = tmp_path / "sentinel_file.txt"
    sentinel.write_text("critical data", encoding="utf-8")

    storage = ObjectStorageService(endpoint_url=None)
    # Inject test upload directory
    storage.upload_dir = upload_dir

    # Attempt traversal deletions
    traversal_keys = [
        "../sentinel_file.txt",
        "..\\sentinel_file.txt",
        str(sentinel.resolve()),
        "/etc/passwd",
        "C:\\Windows\\System32\\calc.exe",
    ]
    for key in traversal_keys:
        storage.delete_file(key, user_id="user-123")
        assert sentinel.exists(), f"Sentinel was deleted by traversal key: {key}"


def test_path_traversal_get_file_is_blocked(tmp_path):
    upload_dir = tmp_path / "uploads"
    upload_dir.mkdir()
    sentinel = tmp_path / "sentinel_file.txt"
    sentinel.write_text("critical data", encoding="utf-8")

    storage = ObjectStorageService(endpoint_url=None)
    storage.upload_dir = upload_dir

    traversal_keys = [
        "../sentinel_file.txt",
        "..\\sentinel_file.txt",
        str(sentinel.resolve()),
    ]
    for key in traversal_keys:
        content = storage.get_file(key, user_id="user-123")
        assert content is None, f"Traversal get_file read data for key: {key}"


def test_authenticated_resume_download_and_owner_isolation(two_users):
    client, alpha, beta = two_users

    # Alpha uploads a resume
    file_bytes = b"John Doe\nSenior Software Engineer\nPython, FastAPI, React"
    upload_resp = client.post(
        "/api/resumes/upload",
        headers=alpha,
        files={"file": ("alpha_resume.txt", io.BytesIO(file_bytes), "text/plain")},
    )
    assert upload_resp.status_code == 200
    alpha_resume = upload_resp.json()
    alpha_resume_id = alpha_resume["id"]

    # 1. Unauthenticated download fails with 401
    anon_resp = client.get(f"/api/resumes/{alpha_resume_id}/download")
    assert anon_resp.status_code == 401

    # 2. Foreign user Beta cannot download Alpha's resume (404)
    beta_resp = client.get(f"/api/resumes/{alpha_resume_id}/download", headers=beta)
    assert beta_resp.status_code == 404

    # 3. Owner Alpha downloads successfully with 200
    alpha_download = client.get(f"/api/resumes/{alpha_resume_id}/download", headers=alpha)
    assert alpha_download.status_code == 200
    assert alpha_download.content == file_bytes


def test_r2_upload_failure_returns_503_and_creates_no_resume(two_users, monkeypatch):
    client, alpha, _ = two_users

    import backend.main as main_mod
    # Force object storage to look configured but have client.put_object fail
    monkeypatch.setattr(main_mod.object_storage, "is_configured", True)

    class FailingClient:
        def put_object(self, **kwargs):
            raise RuntimeError("Simulated R2 connection error")

    monkeypatch.setattr(main_mod.object_storage, "client", FailingClient())

    file_bytes = b"John Doe\nSoftware Engineer\nPython React"
    upload_resp = client.post(
        "/api/resumes/upload",
        headers=alpha,
        files={"file": ("test.txt", io.BytesIO(file_bytes), "text/plain")},
    )
    assert upload_resp.status_code == 503
    assert "unavailable" in upload_resp.json()["detail"].lower()

    # Verify no resume row was created
    resumes_resp = client.get("/api/resumes", headers=alpha)
    assert len(resumes_resp.json()) == 0


def test_foreign_user_cannot_delete_another_users_resume_or_file(two_users):
    client, alpha, beta = two_users

    # Alpha uploads a resume
    file_bytes = b"Alpha Secret Resume\nProprietary experience"
    upload_resp = client.post(
        "/api/resumes/upload",
        headers=alpha,
        files={"file": ("alpha_secret.txt", io.BytesIO(file_bytes), "text/plain")},
    )
    assert upload_resp.status_code == 200
    alpha_resume_id = upload_resp.json()["id"]

    # Beta attempts to delete Alpha's resume
    delete_resp = client.delete(f"/api/resumes/{alpha_resume_id}", headers=beta)
    assert delete_resp.status_code == 404

    # Verify Alpha's resume and file still exist and can be downloaded by Alpha
    check_resp = client.get(f"/api/resumes/{alpha_resume_id}/download", headers=alpha)
    assert check_resp.status_code == 200
    assert check_resp.content == file_bytes
