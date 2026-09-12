import os
import sqlite3
import pytest
from pathlib import Path
from backend.migrate import run_migration


def create_sample_source_db(db_path: Path):
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    # Schema
    cursor.execute("""
        CREATE TABLE users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            hashed_password TEXT,
            avatar_url TEXT,
            provider TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE applications (
            id TEXT PRIMARY KEY,
            company TEXT NOT NULL,
            role TEXT NOT NULL,
            status TEXT NOT NULL,
            location TEXT,
            salary TEXT,
            url TEXT,
            required_skills TEXT,
            ats_keywords TEXT,
            date_added TEXT NOT NULL,
            application_date TEXT,
            follow_up_date TEXT,
            notes TEXT,
            best_resume_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            user_id TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE resumes (
            id TEXT PRIMARY KEY,
            user_id TEXT,
            name TEXT NOT NULL,
            content TEXT NOT NULL,
            file_key TEXT,
            attachment_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE attachments (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            storage_backend TEXT NOT NULL,
            object_key TEXT NOT NULL,
            original_filename TEXT,
            content_type TEXT,
            size_bytes INTEGER,
            deletion_state TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE user_settings (
            user_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY (user_id, key)
        )
    """)
    cursor.execute("""
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    cursor.execute("""
        CREATE TABLE provider_profiles (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            name TEXT NOT NULL,
            api_base_url TEXT,
            model_name TEXT,
            api_key_encrypted TEXT,
            key_suffix TEXT,
            is_active INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)

    # Seed data: 2 users
    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("user-1", "user1@example.com", "User One", "hash1", None, "email", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    cursor.execute(
        "INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("user-2", "user2@example.com", "User Two", "hash2", None, "email", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )

    # User 1 has two applications for Google Software Engineer at distinct URLs (B1 scenario)
    cursor.execute(
        "INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("app-1", "Google", "Software Engineer", "Applied", "Mountain View", "150k", "https://careers.google.com/jobs/results/1", "[]", "[]", "2026-01-01", "2026-01-01", None, None, None, "2026-01-01T00:00:00", "2026-01-01T00:00:00", "user-1"),
    )
    cursor.execute(
        "INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("app-2", "Google", "Software Engineer", "Interviewing", "New York", "160k", "https://careers.google.com/jobs/results/2", "[]", "[]", "2026-01-02", "2026-01-02", None, None, None, "2026-01-02T00:00:00", "2026-01-02T00:00:00", "user-1"),
    )
    # Unowned application (legacy)
    cursor.execute(
        "INSERT INTO applications VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("app-unowned", "Meta", "SWE", "Wishlist", "Remote", None, "https://meta.com/jobs/1", "[]", "[]", "2026-01-01", None, None, None, None, "2026-01-01T00:00:00", "2026-01-01T00:00:00", None),
    )

    # Resume & Attachment for User 1
    cursor.execute(
        "INSERT INTO attachments VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("att-1", "user-1", "local", "resumes/user-1/uuid_resume.pdf", "resume.pdf", "application/pdf", 1024, "active", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    cursor.execute(
        "INSERT INTO resumes VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        ("res-1", "user-1", "Primary Resume", "Experienced Developer", "resumes/user-1/uuid_resume.pdf", "att-1", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )

    # User Settings & Global Settings & Provider Profiles
    cursor.execute(
        "INSERT INTO user_settings VALUES (?, ?, ?, ?, ?)",
        ("user-1", "model_name", "gemini-2.0-flash", "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )
    cursor.execute(
        "INSERT INTO settings VALUES (?, ?)",
        ("system_version", "1.0"),
    )
    cursor.execute(
        "INSERT INTO provider_profiles VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        ("prof-1", "user-1", "My OpenAI", "https://api.openai.com/v1", "gpt-4o", "enc_key", "...1234", 1, "2026-01-01T00:00:00", "2026-01-01T00:00:00"),
    )

    conn.commit()
    conn.close()


def test_dry_run_reports_counts_and_leaves_destination_empty(tmp_path):
    source_db = tmp_path / "source.db"
    dest_db = tmp_path / "dest.db"
    create_sample_source_db(source_db)

    result = run_migration(source_path=str(source_db), dest_path=str(dest_db), dry_run=True)
    assert result["success"] is True
    assert result["dry_run"] is True
    assert result["users_count"] == 2
    assert result["applications_count"] == 3
    assert result["unowned_applications"] == 1
    assert result["resumes_count"] == 1
    assert result["attachments_count"] == 1
    assert result["user_settings_count"] == 1
    assert result["global_settings_count"] == 1
    assert result["provider_profiles_count"] == 1

    # Destination DB should not exist or be empty
    if dest_db.exists():
        conn = sqlite3.connect(str(dest_db))
        tables = conn.cursor().execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        conn.close()
        assert len(tables) == 0


def test_apply_migrates_all_records_and_relationships(tmp_path):
    source_db = tmp_path / "source.db"
    dest_db = tmp_path / "dest.db"
    create_sample_source_db(source_db)

    result = run_migration(source_path=str(source_db), dest_path=str(dest_db), dry_run=False)
    assert result["success"] is True
    assert result["dry_run"] is False
    assert result["migrated_user_settings"] == 1
    assert result["migrated_global_settings"] == 1
    assert result["migrated_provider_profiles"] == 1
    assert result["errors"] == []

    # Connect to dest and verify records
    conn = sqlite3.connect(str(dest_db))
    cursor = conn.cursor()

    users = cursor.execute("SELECT id, email FROM users ORDER BY id").fetchall()
    assert len(users) == 2
    assert users[0][0] == "user-1"
    assert users[1][0] == "user-2"

    apps = cursor.execute("SELECT id, company, role, url, user_id FROM applications ORDER BY id").fetchall()
    assert len(apps) == 3
    # Distinct URLs same-title preserved
    app_map = {row[0]: row for row in apps}
    assert app_map["app-1"][3] == "https://careers.google.com/jobs/results/1"
    assert app_map["app-2"][3] == "https://careers.google.com/jobs/results/2"
    # Unowned stays unowned
    assert app_map["app-unowned"][4] is None

    resumes = cursor.execute("SELECT id, user_id, attachment_id FROM resumes").fetchall()
    assert len(resumes) == 1
    assert resumes[0] == ("res-1", "user-1", "att-1")

    user_settings = cursor.execute("SELECT user_id, key, value FROM user_settings").fetchall()
    assert len(user_settings) == 1
    assert user_settings[0] == ("user-1", "model_name", "gemini-2.0-flash")

    global_settings = cursor.execute("SELECT key, value FROM settings").fetchall()
    assert len(global_settings) == 1
    assert global_settings[0] == ("system_version", "1.0")

    profiles = cursor.execute("SELECT id, user_id, name, model_name FROM provider_profiles").fetchall()
    assert len(profiles) == 1
    assert profiles[0] == ("prof-1", "user-1", "My OpenAI", "gpt-4o")

    # Ledger exists
    ledger = cursor.execute("SELECT count(*) FROM _migration_ledger").fetchone()[0]
    assert ledger > 0

    conn.close()


def test_apply_is_idempotent(tmp_path):
    source_db = tmp_path / "source.db"
    dest_db = tmp_path / "dest.db"
    create_sample_source_db(source_db)

    # Run once
    run_migration(source_path=str(source_db), dest_path=str(dest_db), dry_run=False)
    # Run second time
    result2 = run_migration(source_path=str(source_db), dest_path=str(dest_db), dry_run=False)
    assert result2["success"] is True

    conn = sqlite3.connect(str(dest_db))
    cursor = conn.cursor()
    assert cursor.execute("SELECT count(*) FROM users").fetchone()[0] == 2
    assert cursor.execute("SELECT count(*) FROM applications").fetchone()[0] == 3
    assert cursor.execute("SELECT count(*) FROM resumes").fetchone()[0] == 1
    assert cursor.execute("SELECT count(*) FROM user_settings").fetchone()[0] == 1
    assert cursor.execute("SELECT count(*) FROM settings").fetchone()[0] == 1
    assert cursor.execute("SELECT count(*) FROM provider_profiles").fetchone()[0] == 1
    conn.close()


def test_source_equals_destination_is_rejected(tmp_path):
    same_db = str(tmp_path / "same.db")
    Path(same_db).touch()
    with pytest.raises(ValueError, match="Source and destination cannot be identical"):
        run_migration(source_path=same_db, dest_path=same_db, dry_run=False)


def test_postgres_destination_initialization(monkeypatch, tmp_path):
    source_db = tmp_path / "source.db"
    create_sample_source_db(source_db)

    captured = {}

    class MockStorageService:
        def __init__(self, db_path=None, force_sqlite=False, database_url=None):
            captured["db_path"] = db_path
            captured["force_sqlite"] = force_sqlite
            captured["database_url"] = database_url
            self.is_postgres = True

        def _get_cursor(self):
            from contextlib import contextmanager

            @contextmanager
            def _cur():
                class DummyCursor:
                    def execute(self, *args, **kwargs):
                        pass
                    def fetchall(self):
                        return []
                    def fetchone(self):
                        return None
                yield DummyCursor()
            return _cur()

        def _format_sql(self, sql):
            return sql

        def close(self):
            captured["closed"] = True

    monkeypatch.setattr("backend.migrate.StorageService", MockStorageService)

    result = run_migration(
        source_path=str(source_db),
        dest_path="postgresql://user:pass@host:5432/testdb",
        dry_run=False,
    )
    assert result["success"] is True
    assert captured["database_url"] == "postgresql://user:pass@host:5432/testdb"
    assert captured["db_path"] is None
    assert captured["closed"] is True
