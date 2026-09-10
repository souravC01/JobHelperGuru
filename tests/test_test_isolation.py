import sqlite3
import os
import subprocess
import sys
from pathlib import Path


def test_collection_import_overrides_hostile_personal_configuration(tmp_path):
    sentinel = tmp_path / "personal-import-sentinel.db"
    sentinel.write_bytes(b"personal database sentinel\n")
    transport_marker = tmp_path / "external-transport-called"
    project_root = Path(__file__).resolve().parents[1]
    script = f"""
import os, socket, sys
from pathlib import Path
marker = Path({str(transport_marker)!r})
def forbidden(*args, **kwargs):
    marker.write_text('called')
    raise AssertionError('external transport called during import')
socket.socket.connect = forbidden
socket.socket.connect_ex = forbidden
sys.path.insert(0, {str(project_root)!r})
import tests.conftest
import backend.main
assert backend.main.storage.db_path != {str(sentinel)!r}
assert backend.main.object_storage.client is None
"""
    hostile_env = os.environ.copy()
    hostile_env.update({
        "JOB_HELPER_DB": str(sentinel),
        "DATABASE_URL": "postgresql://personal.invalid/private",
        "R2_ACCOUNT_ID": "personal-account",
        "R2_ACCESS_KEY_ID": "personal-access",
        "R2_SECRET_ACCESS_KEY": "personal-secret",
        "R2_ENDPOINT_URL": "https://personal-cloud.invalid",
    })
    completed = subprocess.run(
        [sys.executable, "-c", script], cwd=project_root, env=hostile_env,
        capture_output=True, text=True, timeout=30,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert sentinel.read_bytes() == b"personal database sentinel\n"
    assert not transport_marker.exists()


def test_api_crud_and_upload_leave_personal_sentinel_unchanged(client, tmp_path, monkeypatch):
    sentinel = tmp_path / "personal-sentinel.db"
    with sqlite3.connect(sentinel) as connection:
        connection.execute("CREATE TABLE private_records (secret TEXT NOT NULL)")
        connection.execute("INSERT INTO private_records VALUES ('must remain untouched')")
    before = sentinel.read_bytes()

    monkeypatch.setenv("JOB_HELPER_DB", str(sentinel))
    monkeypatch.setenv("DATABASE_URL", "postgresql://personal.invalid/private")
    monkeypatch.setenv("R2_ENDPOINT_URL", "https://personal-cloud.invalid")
    registered = client.post("/api/auth/register", json={
        "email": "guard@example.test", "name": "Guard", "password": "TestPassword123!",
    })
    assert registered.status_code == 200
    headers = {"Authorization": "Bearer " + registered.json()["token"]}
    assert client.post("/api/applications", headers=headers, json={
        "company": "Synthetic Co", "role": "Tester",
    }).status_code == 200
    assert client.post("/api/resumes/upload", headers=headers, files={
        "file": ("synthetic.txt", b"Synthetic resume text with enough content for parsing.", "text/plain"),
    }).status_code == 200
    assert sentinel.read_bytes() == before
