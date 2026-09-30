import sqlite3
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import Mock
from backend import main
from backend.storage import StorageService


def test_partial_pdf_persists_warning(client, monkeypatch):
    import pypdf
    monkeypatch.setattr(pypdf, "PdfReader", lambda _: SimpleNamespace(pages=[SimpleNamespace(extract_text=lambda: "Python developer"), SimpleNamespace(extract_text=lambda: "")]))
    user = main.storage.create_user("warnings@example.test", None, "Reader", email_verified=True)
    main.app.dependency_overrides[main.get_current_user] = lambda: user
    try:
        preview = client.post("/api/resumes/parse-file", files={"file": ("resume.pdf", b"pdf", "application/pdf")})
        assert preview.status_code == 200
        assert "page 2" in preview.json()["warnings"][0]
        # The vault resubmits preview text as an override. That must not erase warnings.
        saved = client.post("/api/resumes/upload", data={"content_override": preview.json()["text"]}, files={"file": ("resume.pdf", b"pdf", "application/pdf")})
        assert saved.status_code == 200, saved.text
        record = saved.json()
        assert record["extraction_warnings"] == preview.json()["warnings"]
        assert main.storage.get_resume(record["id"], user_id=user.id).extraction_warnings
        assert client.get("/api/resumes").json()[0]["extraction_warnings"]
    finally:
        main.app.dependency_overrides.pop(main.get_current_user, None)


def test_sqlite_old_resume_schema_adds_warnings(tmp_path):
    path = tmp_path / "old.db"
    with sqlite3.connect(path) as db:
        db.execute("CREATE TABLE resumes (id TEXT PRIMARY KEY, user_id TEXT, name TEXT NOT NULL, content TEXT NOT NULL, file_key TEXT, attachment_id TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        db.execute("INSERT INTO resumes VALUES ('old', 'u', 'Old', 'Python', NULL, NULL, 'now', 'now')")
    storage = StorageService(db_path=str(path), force_sqlite=True)
    try:
        assert storage.get_resume("old", user_id="u").extraction_warnings == []
        resume = storage.add_resume("New", "Python", user_id="u", extraction_warnings=["unreadable page"])
        assert storage.get_resume(resume.id, user_id="u").extraction_warnings == ["unreadable page"]
        reloaded = {item.id: item for item in storage.get_resumes(user_id="u")}
        assert reloaded[resume.id].extraction_warnings == ["unreadable page"]
    finally:
        storage.close()


def test_postgres_warning_migration_uses_if_not_exists():
    storage = object.__new__(StorageService)
    storage.is_postgres = True
    cursor = Mock()
    @contextmanager
    def get_cursor():
        yield cursor
    storage._get_cursor = get_cursor
    storage._init_db()
    statements = [call.args[0] for call in cursor.execute.call_args_list]
    assert any("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS extraction_warnings" in sql for sql in statements)


def test_parser_warns_on_undecodable_text():
    from backend.services.document_parser import extract_text_with_warnings
    result = extract_text_with_warnings(b"Python \xff", "resume.txt")
    assert "Python" in result.text and result.warnings


def test_postgres_warning_roundtrip_uses_json_and_user_filter():
    from threading import RLock
    storage = object.__new__(StorageService)
    storage.is_postgres = True
    storage._resume_quota_lock = RLock()
    cursor = Mock()
    @contextmanager
    def get_cursor():
        yield cursor
    storage._get_cursor = get_cursor
    storage._get_immediate_cursor = get_cursor
    saved = storage.add_resume("Resume", "Python", user_id="u", extraction_warnings=["page 2 unreadable"])
    sql, params = cursor.execute.call_args.args
    assert "extraction_warnings" in sql and "%s" in sql
    assert params[6] == '["page 2 unreadable"]'
    row = {**saved.model_dump(), "extraction_warnings": params[6]}
    cursor.fetchone.return_value = row
    cursor.fetchall.return_value = [row]
    assert storage.get_resume(saved.id, user_id="u").extraction_warnings == saved.extraction_warnings
    assert cursor.execute.call_args.args[1] == (saved.id, "u")
    assert storage.get_resumes(user_id="u")[0].extraction_warnings == saved.extraction_warnings
