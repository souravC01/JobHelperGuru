"""Hermetic defaults shared by every backend test."""

import os
import secrets
import shutil
import socket
import tempfile
from pathlib import Path

import dotenv
import pytest
from fastapi.testclient import TestClient


# pytest loads conftest before importing test modules. Seal the process here so
# backend.main cannot read a developer .env or open personal services on import.
_COLLECTION_ROOT = Path(tempfile.mkdtemp(prefix="jobhelperguru-tests-"))
os.environ.update({
    "PYTHON_DOTENV_DISABLED": "1",
    "APP_MODE": "test",
    "JOB_HELPER_DB": str(_COLLECTION_ROOT / "collection.db"),
    "DATABASE_URL": "",
    "R2_ACCOUNT_ID": "",
    "R2_ACCESS_KEY_ID": "",
    "R2_SECRET_ACCESS_KEY": "",
    "R2_ENDPOINT_URL": "",
    "JWT_SECRET_KEY": "test-only-" + secrets.token_hex(32),
    "SECRET_KEY": "test-only-" + secrets.token_hex(32),
    "SETTINGS_ENCRYPTION_KEY": "test-only-" + secrets.token_hex(32),
    "GOOGLE_CLIENT_ID": "test-client-id",
    "OPENAI_API_KEY": "",
    "GEMINI_API_KEY": "",
})
dotenv.load_dotenv = lambda *args, **kwargs: False

from backend import main  # noqa: E402
from backend.routers.auth import set_storage_service  # noqa: E402
from backend.storage import StorageService  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    main.storage.close()
    shutil.rmtree(_COLLECTION_ROOT, ignore_errors=True)


class FakeObjectStorage:
    is_configured = False
    client = None

    def __init__(self, root):
        self.root = Path(root)

    def upload_file(self, content_bytes, filename, content_type=None, user_id=None):
        if self.is_configured and self.client:
            self.client.put_object(Bucket="fake", Key="fake", Body=content_bytes)
        key = f"resumes/{user_id or 'anonymous'}/{secrets.token_hex(12)}_{Path(filename).name}"
        target = self.root / key
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content_bytes)
        return key

    def generate_download_url(self, object_key, expires_in=3600):
        if self.is_configured and self.client:
            return f"https://r2.fake.test/{object_key}"
        return None

    def get_file(self, object_key, user_id=None):
        target = self.root / object_key
        return target.read_bytes() if target.is_file() else None

    def delete_file(self, object_key, user_id=None):
        target = self.root / object_key
        if not target.exists():
            return True
        if not target.is_file():
            return False
        try:
            target.unlink()
            return True
        except Exception:
            return False



@pytest.fixture(autouse=True)
def isolate_test_process(monkeypatch, tmp_path):
    db_path = tmp_path / "test.db"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("JOB_HELPER_DB", str(db_path))
    for name in ("DATABASE_URL", "R2_ACCOUNT_ID", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY", "R2_ENDPOINT_URL"):
        monkeypatch.setenv(name, "")

    storage = StorageService(db_path=str(db_path), force_sqlite=True)
    previous_storage = main.storage
    previous_object_storage = main.object_storage
    main.storage = storage
    main.object_storage = FakeObjectStorage(tmp_path / "uploads")
    set_storage_service(storage)

    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex

    def blocked(sock, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host in {"127.0.0.1", "::1", "localhost"}:
            return original_connect(sock, address, *args, **kwargs)
        raise OSError(f"External network disabled during tests: {host}")

    def blocked_ex(sock, address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else address
        if host in {"127.0.0.1", "::1", "localhost"}:
            return original_connect_ex(sock, address, *args, **kwargs)
        raise OSError(f"External network disabled during tests: {host}")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked_ex)
    if main.scraper.__class__.__module__ == "backend.services.scraper":
        monkeypatch.setattr(
            "backend.services.scraper.cffi_requests.get",
            lambda *args, **kwargs: (_ for _ in ()).throw(
                OSError("External curl transport disabled during tests")
            ),
            raising=False,
        )
    yield
    storage.close()
    main.storage = previous_storage
    main.object_storage = previous_object_storage
    set_storage_service(previous_storage)


@pytest.fixture
def client():
    with TestClient(main.app) as test_client:
        yield test_client


@pytest.fixture
def two_users(client):
    def signup(email):
        response = client.post("/api/auth/register", json={
            "email": email, "name": "Test User", "password": "TestPassword123!",
        })
        assert response.status_code == 200, response.text
        return {"Authorization": "Bearer " + response.json()["token"]}

    return client, signup("alpha@example.test"), signup("beta@example.test")
