import pytest
from pathlib import Path
from backend.services.object_storage import ObjectStorageService


def test_object_storage_local_fallback(tmp_path, monkeypatch):
    # Ensure no ambient R2 environment variables during unit test
    monkeypatch.setenv("R2_ACCOUNT_ID", "")
    monkeypatch.setenv("R2_ACCESS_KEY_ID", "")
    monkeypatch.setenv("R2_SECRET_ACCESS_KEY", "")

    storage = ObjectStorageService()
    assert storage.is_configured is False

    test_content = b"%PDF-1.4 Mock resume content for testing"
    filename = "test_candidate_resume.pdf"

    # 1. Upload file
    key = storage.upload_file(test_content, filename, "application/pdf")
    assert key is not None
    assert key.startswith("resumes/")
    assert key.endswith(".pdf")

    # 2. Retrieve file
    downloaded = storage.get_file(key)
    assert downloaded == test_content

    # 3. Delete file
    deleted = storage.delete_file(key)
    assert deleted is True
    assert storage.get_file(key) is None


def test_user_scoped_upload(tmp_path, monkeypatch):
    monkeypatch.setenv("R2_ACCOUNT_ID", "")
    storage = ObjectStorageService()
    test_content = b"%PDF-1.4 User scoped resume test"
    key = storage.upload_file(test_content, "resume.pdf", user_id="usr-999")
    assert key.startswith("resumes/usr-999/")

