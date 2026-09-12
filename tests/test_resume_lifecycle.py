import io
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
import pytest
from backend import main


def test_concurrent_resume_creation_obeys_quota_limit(two_users):
    client, alpha, _ = two_users

    # Fill up to 9 resumes
    for i in range(9):
        resp = client.post("/api/resumes", headers=alpha, json={
            "name": f"Resume {i}",
            "content": f"Software Engineer Experience {i}",
        })
        assert resp.status_code == 200

    # User now has 9 resumes. Only 1 slot remains before hitting the 10-resume cap.
    start = Barrier(4)
    def attempt_create(idx):
        start.wait()
        return client.post("/api/resumes", headers=alpha, json={
            "name": f"Concurrent Resume {idx}",
            "content": f"Concurrent Software Engineer Experience {idx}",
        })

    with ThreadPoolExecutor(max_workers=4) as workers:
        results = list(workers.map(attempt_create, range(4)))

    successes = [r for r in results if r.status_code == 200]
    rejected = [r for r in results if r.status_code == 422]

    assert len(successes) == 1
    assert len(rejected) == 3

    # Confirm database contains exactly 10 resumes for this user
    all_resumes = client.get("/api/resumes", headers=alpha).json()
    assert len(all_resumes) == 10


def test_unicode_resume_filename_download(two_users):
    client, alpha, _ = two_users

    unicode_filename = "简历_Sourav_2026.txt"
    file_content = b"Resume content in UTF-8: Engineering lead with NLP experience."

    upload_resp = client.post(
        "/api/resumes/upload",
        headers=alpha,
        files={"file": (unicode_filename, io.BytesIO(file_content), "text/plain")},
    )
    assert upload_resp.status_code == 200
    resume_id = upload_resp.json()["id"]

    download_resp = client.get(f"/api/resumes/{resume_id}/download", headers=alpha)
    assert download_resp.status_code == 200
    assert download_resp.content == file_content


    # Content-Disposition header must be ASCII-safe and include filename*
    disposition = download_resp.headers.get("content-disposition", "")
    assert "filename*=" in disposition
    assert "UTF-8''" in disposition


def test_delete_resume_with_missing_binary_is_idempotent(two_users):
    client, alpha, _ = two_users

    file_content = b"Resume text with binary that will disappear."
    upload_resp = client.post(
        "/api/resumes/upload",
        headers=alpha,
        files={"file": ("to_delete.txt", io.BytesIO(file_content), "text/plain")},
    )
    assert upload_resp.status_code == 200
    resume_id = upload_resp.json()["id"]

    # Delete underlying storage file so it's missing
    resume = main.storage.get_resume(resume_id)
    if resume and resume.file_key:
        main.object_storage.delete_file(resume.file_key)

    # Deleting the resume when binary is already missing must succeed idempotently (200), not 500
    del_resp = client.delete(f"/api/resumes/{resume_id}", headers=alpha)
    assert del_resp.status_code == 200

    # Second delete returns 404 because resume is gone
    del_resp2 = client.delete(f"/api/resumes/{resume_id}", headers=alpha)
    assert del_resp2.status_code == 404
