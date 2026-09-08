import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    from psycopg2.pool import ThreadedConnectionPool
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    ThreadedConnectionPool = None

from backend.models import (
    User,
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatus,
    Resume,
    ResumeCreate,
    ResumeAttachment,
    Settings,
    SettingsUpdate,
    ProviderProfileMetadata,
    ProviderProfileCreate,
    ProviderProfileUpdate,
)
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from backend.services.encryption import encrypt_value, decrypt_value, DecryptionError

TRACKING_QUERY_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "src", "ref", "fbclid", "gclid", "trk", "trackingid", "source"
}


def canonical_posting_url(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    clean = url.strip()
    if not clean or clean.lower() == "manual_paste":
        return None
    try:
        parts = urlsplit(clean)
        if not parts.scheme or not parts.netloc:
            return clean.rstrip("/")
        scheme = parts.scheme.lower()
        netloc = parts.netloc.lower()
        path = parts.path.rstrip("/")
        query_pairs = parse_qsl(parts.query, keep_blank_values=False)
        filtered_pairs = [(k, v) for k, v in query_pairs if k.lower() not in TRACKING_QUERY_PARAMS]
        filtered_pairs.sort()
        query = urlencode(filtered_pairs)
        return urlunsplit((scheme, netloc, path, query, ""))
    except Exception:
        return clean.rstrip("/")


class StorageService:
    def __init__(self, db_path: str = "data/tracker.db", force_sqlite: bool = False, database_url: Optional[str] = None):
        if force_sqlite:
            raw_url = None
        elif database_url:
            raw_url = database_url
        elif db_path != "data/tracker.db" and os.environ.get("JOB_HELPER_DB") != db_path:
            # Caller explicitly passed a custom db_path (e.g., in unit tests)
            raw_url = None
        else:
            raw_url = os.getenv("DATABASE_URL")
        if raw_url and (raw_url.startswith("postgres://") or raw_url.startswith("postgresql://")):
            if not PSYCOPG2_AVAILABLE:
                raise RuntimeError("psycopg2 is required to connect to PostgreSQL / Neon.")
            # Normalize postgres:// to postgresql://
            if raw_url.startswith("postgres://"):
                raw_url = raw_url.replace("postgres://", "postgresql://", 1)
            self.database_url = raw_url
            self.is_postgres = True
            self.db_path = None
            try:
                self.pool = ThreadedConnectionPool(minconn=1, maxconn=10, dsn=self.database_url)
            except Exception as e:
                print(f"[WARN] Failed to initialize ThreadedConnectionPool: {e}, falling back to direct connections.")
                self.pool = None
        else:
            self.database_url = None
            self.is_postgres = False
            self.pool = None
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _get_cursor(self):
        if self.is_postgres:
            if self.pool:
                conn = self.pool.getconn()
                is_stale = False
                try:
                    if conn.closed:
                        is_stale = True
                    else:
                        with conn.cursor() as test_cur:
                            test_cur.execute("SELECT 1")
                except Exception:
                    is_stale = True

                if is_stale:
                    try:
                        self.pool.putconn(conn, close=True)
                    except Exception:
                        pass
                    conn = psycopg2.connect(self.database_url)
                    try:
                        with conn:
                            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                                yield cursor
                    finally:
                        conn.close()
                    return

                try:
                    with conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            yield cursor
                except (psycopg2.OperationalError, psycopg2.InterfaceError):
                    try:
                        self.pool.putconn(conn, close=True)
                    except Exception:
                        pass
                    raise
                finally:
                    if not conn.closed:
                        try:
                            self.pool.putconn(conn)
                        except Exception:
                            pass
            else:
                conn = psycopg2.connect(self.database_url)
                try:
                    with conn:
                        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                            yield cursor
                finally:
                    conn.close()
        else:
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            try:
                with conn:
                    cursor = conn.cursor()
                    yield cursor
            finally:
                conn.close()

    def close(self):
        """Closes all connections in the pool if active."""
        if self.is_postgres and self.pool:
            try:
                self.pool.closeall()
            except Exception:
                pass

    def _format_sql(self, sql: str) -> str:
        if self.is_postgres:
            # Escape literal '%' to '%%' for psycopg2, and replace '?' with '%s'
            return sql.replace("%", "%%").replace("?", "%s")
        return sql

    def _init_db(self):
        with self._get_cursor() as cursor:
            # Users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT,
                    name TEXT NOT NULL,
                    avatar_url TEXT,
                    provider TEXT NOT NULL DEFAULT 'email',
                    email_verified BOOLEAN DEFAULT FALSE,
                    session_version INTEGER DEFAULT 1,
                    google_sub TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
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
                    updated_at TEXT NOT NULL
                )
            """)
            # Resumes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
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
            # Attachments table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attachments (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    storage_backend TEXT NOT NULL,
                    object_key TEXT NOT NULL,
                    original_filename TEXT,
                    content_type TEXT,
                    size_bytes INTEGER DEFAULT 0,
                    deletion_state TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Auth tokens table (verification and password recovery)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS auth_tokens (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    token_hash TEXT NOT NULL,
                    token_type TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    used_at TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            # Column migrations for existing tables
            if self.is_postgres:
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS email_verified BOOLEAN DEFAULT FALSE")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS session_version INTEGER DEFAULT 1")
                cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS google_sub TEXT")
                cursor.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_key TEXT")
                cursor.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS user_id TEXT")
                cursor.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS attachment_id TEXT")
                cursor.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id TEXT")
            else:
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN email_verified BOOLEAN DEFAULT 0")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN session_version INTEGER DEFAULT 1")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE users ADD COLUMN google_sub TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE resumes ADD COLUMN file_key TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE resumes ADD COLUMN user_id TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE resumes ADD COLUMN attachment_id TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE applications ADD COLUMN user_id TEXT")
                except Exception:
                    pass

            # Settings table (global fallback)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            # User Settings table (per-user settings)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_settings (
                    user_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value TEXT NOT NULL,
                    PRIMARY KEY (user_id, key)
                )
            """)
            # Provider Profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS provider_profiles (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    api_base_url TEXT NOT NULL,
                    model_name TEXT NOT NULL,
                    api_key_encrypted TEXT,
                    key_suffix TEXT,
                    is_active BOOLEAN DEFAULT FALSE,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Rate limits table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS rate_limits (
                    bucket TEXT NOT NULL,
                    subject TEXT NOT NULL,
                    count INTEGER NOT NULL,
                    reset_at REAL NOT NULL,
                    PRIMARY KEY (bucket, subject)
                )
            """)

    # --- Users CRUD ---
    def create_user(
        self,
        email: str,
        hashed_password: Optional[str],
        name: str,
        avatar_url: Optional[str] = None,
        provider: str = "email",
        email_verified: bool = False,
        session_version: int = 1,
        google_sub: Optional[str] = None,
    ) -> User:
        now = datetime.now().isoformat()
        user_id = str(uuid.uuid4())
        clean_email = email.strip().lower()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "INSERT INTO users (id, email, hashed_password, name, avatar_url, provider, email_verified, session_version, google_sub, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (user_id, clean_email, hashed_password, name, avatar_url, provider, email_verified, session_version, google_sub, now, now),
            )
        return User(
            id=user_id,
            email=clean_email,
            name=name,
            avatar_url=avatar_url,
            provider=provider,
            email_verified=email_verified,
            session_version=session_version,
            google_sub=google_sub,
            created_at=now,
            updated_at=now,
        )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        clean_email = email.strip().lower()
        with self._get_cursor() as cursor:
            cursor.execute(self._format_sql("SELECT * FROM users WHERE email = ?"), (clean_email,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        with self._get_cursor() as cursor:
            cursor.execute(self._format_sql("SELECT * FROM users WHERE id = ?"), (user_id,))
            row = cursor.fetchone()
            if not row:
                return None
            d = dict(row)
            return User(
                id=d["id"],
                email=d["email"],
                name=d["name"],
                avatar_url=d.get("avatar_url"),
                provider=d.get("provider", "email"),
                email_verified=bool(d.get("email_verified", False)),
                session_version=int(d.get("session_version", 1)),
                google_sub=d.get("google_sub"),
                created_at=d["created_at"],
                updated_at=d["updated_at"],
            )

    def get_user_by_google_sub(self, google_sub: str) -> Optional[Dict[str, Any]]:
        clean_sub = google_sub.strip()
        with self._get_cursor() as cursor:
            cursor.execute(self._format_sql("SELECT * FROM users WHERE google_sub = ?"), (clean_sub,))
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def update_user_verification(self, user_id: str, verified: bool = True) -> None:
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql("UPDATE users SET email_verified = ?, updated_at = ? WHERE id = ?"),
                (verified, now, user_id),
            )

    def update_user_password(self, user_id: str, hashed_password: Optional[str], increment_session: bool = True) -> None:
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            if increment_session:
                cursor.execute(
                    self._format_sql(
                        "UPDATE users SET hashed_password = ?, session_version = session_version + 1, updated_at = ? WHERE id = ?"
                    ),
                    (hashed_password, now, user_id),
                )
            else:
                cursor.execute(
                    self._format_sql("UPDATE users SET hashed_password = ?, updated_at = ? WHERE id = ?"),
                    (hashed_password, now, user_id),
                )

    def link_google_identity(
        self,
        user_id: str,
        google_sub: str,
        clear_password: bool = False,
        verify_email: bool = True,
    ) -> None:
        now = datetime.now().isoformat()
        clean_sub = google_sub.strip()
        with self._get_cursor() as cursor:
            if clear_password:
                cursor.execute(
                    self._format_sql(
                        "UPDATE users SET google_sub = ?, hashed_password = NULL, email_verified = ?, session_version = session_version + 1, updated_at = ? WHERE id = ?"
                    ),
                    (clean_sub, verify_email, now, user_id),
                )
            else:
                cursor.execute(
                    self._format_sql(
                        "UPDATE users SET google_sub = ?, email_verified = ?, updated_at = ? WHERE id = ?"
                    ),
                    (clean_sub, verify_email, now, user_id),
                )

    def increment_user_session_version(self, user_id: str) -> int:
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql("UPDATE users SET session_version = session_version + 1, updated_at = ? WHERE id = ?"),
                (now, user_id),
            )
            cursor.execute(self._format_sql("SELECT session_version FROM users WHERE id = ?"), (user_id,))
            row = cursor.fetchone()
            return int(row["session_version"]) if row else 1

    # --- Auth Tokens (Verification & Password Recovery) ---
    def create_auth_token(self, user_id: str, token_hash: str, token_type: str, expires_at: str) -> str:
        token_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "INSERT INTO auth_tokens (id, user_id, token_hash, token_type, expires_at, created_at) "
                    "VALUES (?, ?, ?, ?, ?, ?)"
                ),
                (token_id, user_id, token_hash, token_type, expires_at, now),
            )
        return token_id

    def get_auth_token(self, token_hash: str, token_type: str) -> Optional[Dict[str, Any]]:
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "SELECT * FROM auth_tokens WHERE token_hash = ? AND token_type = ? AND used_at IS NULL"
                ),
                (token_hash, token_type),
            )
            row = cursor.fetchone()
            if not row:
                return None
            return dict(row)

    def consume_auth_token(self, token_id: str) -> None:
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql("UPDATE auth_tokens SET used_at = ? WHERE id = ?"),
                (now, token_id),
            )

    def invalidate_prior_auth_tokens(self, user_id: str, token_type: str) -> None:
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql("UPDATE auth_tokens SET used_at = ? WHERE user_id = ? AND token_type = ? AND used_at IS NULL"),
                (now, user_id, token_type),
            )

    # --- Resumes CRUD ---
    def add_resume(
        self,
        name: str,
        content: str,
        file_key: Optional[str] = None,
        user_id: Optional[str] = None,
        attachment_id: Optional[str] = None,
    ) -> Resume:
        now = datetime.now().isoformat()
        resume_id = str(uuid.uuid4())
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "INSERT INTO resumes (id, user_id, name, content, file_key, attachment_id, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (resume_id, user_id, name, content, file_key, attachment_id, now, now),
            )
        return Resume(
            id=resume_id,
            name=name,
            content=content,
            file_key=file_key,
            attachment_id=attachment_id,
            created_at=now,
            updated_at=now,
        )

    def get_resumes(self, user_id: Optional[str] = None) -> List[Resume]:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(self._format_sql("SELECT * FROM resumes WHERE user_id = ? ORDER BY created_at DESC"), (user_id,))
            else:
                cursor.execute("SELECT * FROM resumes ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                Resume(
                    id=row["id"],
                    name=row["name"],
                    content=row["content"],
                    file_key=row.get("file_key") if isinstance(row, dict) else (row["file_key"] if "file_key" in row.keys() else None),
                    attachment_id=row.get("attachment_id") if isinstance(row, dict) else (row["attachment_id"] if "attachment_id" in row.keys() else None),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def get_resume(self, resume_id: str, user_id: Optional[str] = None) -> Optional[Resume]:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(self._format_sql("SELECT * FROM resumes WHERE id = ? AND user_id = ?"), (resume_id, user_id))
            else:
                cursor.execute(self._format_sql("SELECT * FROM resumes WHERE id = ?"), (resume_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Resume(
                id=row["id"],
                name=row["name"],
                content=row["content"],
                file_key=row.get("file_key") if isinstance(row, dict) else (row["file_key"] if "file_key" in row.keys() else None),
                attachment_id=row.get("attachment_id") if isinstance(row, dict) else (row["attachment_id"] if "attachment_id" in row.keys() else None),
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def delete_resume(self, resume_id: str, user_id: Optional[str] = None) -> bool:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(self._format_sql("DELETE FROM resumes WHERE id = ? AND user_id = ?"), (resume_id, user_id))
            else:
                cursor.execute(self._format_sql("DELETE FROM resumes WHERE id = ?"), (resume_id,))
            return cursor.rowcount > 0

    def count_user_resumes(self, user_id: str) -> int:
        with self._get_cursor() as cursor:
            cursor.execute(self._format_sql("SELECT COUNT(*) as cnt FROM resumes WHERE user_id = ?"), (user_id,))
            row = cursor.fetchone()
            if not row:
                return 0
            if isinstance(row, dict):
                return int(row.get("cnt", 0))
            return int(row[0])

    def get_user_upload_bytes(self, user_id: str) -> int:
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "SELECT COALESCE(SUM(size_bytes), 0) as total_bytes FROM attachments WHERE user_id = ? AND deletion_state = 'active'"
                ),
                (user_id,),
            )
            row = cursor.fetchone()
            if not row:
                return 0
            if isinstance(row, dict):
                return int(row.get("total_bytes", 0))
            return int(row[0])

    # --- Attachments CRUD ---
    def create_attachment(
        self,
        user_id: str,
        storage_backend: str,
        object_key: str,
        original_filename: Optional[str] = None,
        content_type: Optional[str] = None,
        size_bytes: int = 0,
    ) -> ResumeAttachment:
        now = datetime.now().isoformat()
        att_id = str(uuid.uuid4())
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "INSERT INTO attachments (id, user_id, storage_backend, object_key, original_filename, content_type, size_bytes, deletion_state, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (att_id, user_id, storage_backend, object_key, original_filename, content_type, size_bytes, "active", now, now),
            )
        return ResumeAttachment(
            id=att_id,
            user_id=user_id,
            storage_backend=storage_backend,
            object_key=object_key,
            original_filename=original_filename,
            content_type=content_type,
            size_bytes=size_bytes,
            deletion_state="active",
            created_at=now,
            updated_at=now,
        )

    def get_attachment(self, attachment_id: str, user_id: Optional[str] = None) -> Optional[ResumeAttachment]:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql("SELECT * FROM attachments WHERE id = ? AND user_id = ?"),
                    (attachment_id, user_id),
                )
            else:
                cursor.execute(self._format_sql("SELECT * FROM attachments WHERE id = ?"), (attachment_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return ResumeAttachment(
                id=row["id"],
                user_id=row["user_id"],
                storage_backend=row["storage_backend"],
                object_key=row["object_key"],
                original_filename=row["original_filename"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                deletion_state=row["deletion_state"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def get_attachment_by_key(self, object_key: str, user_id: Optional[str] = None) -> Optional[ResumeAttachment]:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql("SELECT * FROM attachments WHERE object_key = ? AND user_id = ?"),
                    (object_key, user_id),
                )
            else:
                cursor.execute(self._format_sql("SELECT * FROM attachments WHERE object_key = ?"), (object_key,))
            row = cursor.fetchone()
            if not row:
                return None
            return ResumeAttachment(
                id=row["id"],
                user_id=row["user_id"],
                storage_backend=row["storage_backend"],
                object_key=row["object_key"],
                original_filename=row["original_filename"],
                content_type=row["content_type"],
                size_bytes=row["size_bytes"],
                deletion_state=row["deletion_state"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def update_attachment_deletion_state(self, attachment_id: str, deletion_state: str, user_id: Optional[str] = None) -> bool:
        now = datetime.now().isoformat()
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql("UPDATE attachments SET deletion_state = ?, updated_at = ? WHERE id = ? AND user_id = ?"),
                    (deletion_state, now, attachment_id, user_id),
                )
            else:
                cursor.execute(
                    self._format_sql("UPDATE attachments SET deletion_state = ?, updated_at = ? WHERE id = ?"),
                    (deletion_state, now, attachment_id),
                )
            return cursor.rowcount > 0

    def delete_attachment(self, attachment_id: str, user_id: Optional[str] = None) -> bool:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql("DELETE FROM attachments WHERE id = ? AND user_id = ?"),
                    (attachment_id, user_id),
                )
            else:
                cursor.execute(self._format_sql("DELETE FROM attachments WHERE id = ?"), (attachment_id,))
            return cursor.rowcount > 0

    def update_resume(
        self,
        resume_id: str,
        name: Optional[str] = None,
        content: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Optional[Resume]:
        existing = self.get_resume(resume_id, user_id=user_id)
        if not existing:
            return None

        new_name = name.strip() if (name and name.strip()) else existing.name
        new_content = content if content is not None else existing.content
        now = datetime.now().isoformat()

        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql(
                        "UPDATE resumes SET name = ?, content = ?, updated_at = ? WHERE id = ? AND user_id = ?"
                    ),
                    (new_name, new_content, now, resume_id, user_id),
                )
            else:
                cursor.execute(
                    self._format_sql(
                        "UPDATE resumes SET name = ?, content = ?, updated_at = ? WHERE id = ?"
                    ),
                    (new_name, new_content, now, resume_id),
                )

        return self.get_resume(resume_id, user_id=user_id)

    # --- Applications CRUD ---
    def find_existing_application(
        self, url: Optional[str], company: str, role: str, user_id: Optional[str] = None
    ) -> Optional[Application]:
        canon_url = canonical_posting_url(url)
        with self._get_cursor() as cursor:
            # 1. Match by canonical posting URL if URL is present
            if canon_url:
                if user_id:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE url != '' AND url != 'manual_paste' AND user_id = ?"
                        ),
                        (user_id,),
                    )
                else:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE url != '' AND url != 'manual_paste'"
                        )
                    )
                rows = cursor.fetchall()
                for row in rows:
                    if canonical_posting_url(row["url"]) == canon_url:
                        return self._row_to_application(row)
                # If a canonical URL is present and didn't match, it is a distinct posting (Fixes B1)
                return None

            # 2. Match by exact normalized company & role ONLY for postings without a URL
            clean_comp = (company or "").strip().lower()
            clean_r = (role or "").strip().lower()
            if clean_comp and clean_r:
                if user_id:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE LOWER(TRIM(company)) = ? AND LOWER(TRIM(role)) = ? AND (url IS NULL OR url = '' OR url = 'manual_paste') AND user_id = ?"
                        ),
                        (clean_comp, clean_r, user_id),
                    )
                else:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE LOWER(TRIM(company)) = ? AND LOWER(TRIM(role)) = ? AND (url IS NULL OR url = '' OR url = 'manual_paste')"
                        ),
                        (clean_comp, clean_r),
                    )
                row = cursor.fetchone()
                if row:
                    return self._row_to_application(row)

            return None

    def deduplicate_existing_applications(self, user_id: Optional[str] = None):
        """Removes existing duplicate applications scoped per user, preserving the most recently updated record."""
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql("SELECT id, company, role, url, updated_at, user_id FROM applications WHERE user_id = ? ORDER BY updated_at DESC"),
                    (user_id,),
                )
            else:
                cursor.execute("SELECT id, company, role, url, updated_at, user_id FROM applications ORDER BY updated_at DESC")
            rows = cursor.fetchall()
            seen_urls = set()
            seen_roles = set()
            ids_to_delete = []

            for row in rows:
                u_id = str(row["user_id"] or "global")
                clean_url = (row["url"] or "").strip().rstrip("/")
                comp_role_key = f"{u_id}:::{row['company'].strip().lower()}:::{row['role'].strip().lower()}"
                url_key = f"{u_id}:::{clean_url}" if clean_url and clean_url != "manual_paste" else None

                is_dup = False
                if url_key and url_key in seen_urls:
                    is_dup = True
                if comp_role_key in seen_roles:
                    is_dup = True

                if is_dup:
                    ids_to_delete.append(row["id"])
                else:
                    if url_key:
                        seen_urls.add(url_key)
                    seen_roles.add(comp_role_key)

            if ids_to_delete:
                placeholders = ",".join("?" for _ in ids_to_delete)
                cursor.execute(
                    self._format_sql(f"DELETE FROM applications WHERE id IN ({placeholders})"),
                    ids_to_delete,
                )

    def add_application(self, app_data: ApplicationCreate, user_id: Optional[str] = None) -> Application:
        # Check if this application already exists in the pipeline for this user
        existing = self.find_existing_application(app_data.url, app_data.company, app_data.role, user_id=user_id)
        if existing:
            status_val = app_data.status.value if isinstance(app_data.status, ApplicationStatus) else str(app_data.status)
            final_status = existing.status
            if status_val != ApplicationStatus.WISHLIST.value or existing.status == ApplicationStatus.WISHLIST:
                final_status = ApplicationStatus(status_val)

            merged_skills = list(dict.fromkeys((existing.required_skills or []) + (app_data.required_skills or [])))
            merged_keywords = list(dict.fromkeys((existing.ats_keywords or []) + (app_data.ats_keywords or [])))

            updates = {
                "location": app_data.location if app_data.location and app_data.location != "Unknown" else existing.location,
                "salary": app_data.salary if app_data.salary and app_data.salary != "Not specified" else existing.salary,
                "url": app_data.url if app_data.url and app_data.url != "manual_paste" else existing.url,
                "required_skills": merged_skills,
                "ats_keywords": merged_keywords,
                "status": final_status,
                "notes": app_data.notes if app_data.notes else existing.notes,
                "best_resume_id": app_data.best_resume_id or existing.best_resume_id,
            }
            updated = self.update_application(existing.id, updates, user_id=user_id)
            if updated:
                return updated
            return existing

        now = datetime.now().isoformat()
        date_added = datetime.now().strftime("%Y-%m-%d")
        app_id = str(uuid.uuid4())
        status_val = app_data.status.value if isinstance(app_data.status, ApplicationStatus) else str(app_data.status)
        req_skills_json = json.dumps(app_data.required_skills or [])
        ats_keywords_json = json.dumps(app_data.ats_keywords or [])

        app_date = app_data.application_date or ""
        follow_up_date = app_data.follow_up_date or ""
        if status_val == ApplicationStatus.APPLIED.value:
            if not app_date:
                app_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            if not follow_up_date:
                user_settings = self.get_settings(user_id=user_id)
                default_days = user_settings.default_follow_up_days if user_settings else 7
                try:
                    dt = datetime.strptime(app_date, "%Y-%m-%d")
                    follow_up_date = (dt + timedelta(days=default_days)).strftime("%Y-%m-%d")
                except ValueError:
                    pass

        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    """
                    INSERT INTO applications (
                        id, user_id, company, role, status, location, salary, url,
                        required_skills, ats_keywords, date_added, application_date,
                        follow_up_date, notes, best_resume_id, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """
                ),
                (
                    app_id,
                    user_id,
                    app_data.company,
                    app_data.role,
                    status_val,
                    app_data.location or "Unknown",
                    app_data.salary or "Not specified",
                    app_data.url or "",
                    req_skills_json,
                    ats_keywords_json,
                    date_added,
                    app_date,
                    follow_up_date,
                    app_data.notes or "",
                    app_data.best_resume_id,
                    now,
                    now,
                ),
            )

        return Application(
            id=app_id,
            company=app_data.company,
            role=app_data.role,
            status=ApplicationStatus(status_val),
            location=app_data.location or "Unknown",
            salary=app_data.salary or "Not specified",
            url=app_data.url or "",
            required_skills=app_data.required_skills or [],
            ats_keywords=app_data.ats_keywords or [],
            date_added=date_added,
            application_date=app_data.application_date or "",
            follow_up_date=app_data.follow_up_date or "",
            notes=app_data.notes or "",
            best_resume_id=app_data.best_resume_id,
            created_at=now,
            updated_at=now,
        )

    def get_applications(self, user_id: Optional[str] = None) -> List[Application]:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(
                    self._format_sql("SELECT * FROM applications WHERE user_id = ? ORDER BY date_added DESC, created_at DESC"),
                    (user_id,),
                )
            else:
                cursor.execute("SELECT * FROM applications ORDER BY date_added DESC, created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_application(row) for row in rows]

    def get_application(self, app_id: str, user_id: Optional[str] = None) -> Optional[Application]:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(self._format_sql("SELECT * FROM applications WHERE id = ? AND user_id = ?"), (app_id, user_id))
            else:
                cursor.execute(self._format_sql("SELECT * FROM applications WHERE id = ?"), (app_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_application(row)

    def update_application(
        self, app_id: str, updates: Dict[str, Any] | ApplicationUpdate, *, user_id: Optional[str] = None
    ) -> Optional[Application]:
        existing = self.get_application(app_id, user_id=user_id)
        if not existing:
            return None

        if isinstance(updates, ApplicationUpdate):
            update_dict = updates.model_dump(exclude_unset=True)
        else:
            update_dict = {k: v for k, v in updates.items() if v is not None}

        # On transition to Applied, initialize application_date and follow_up_date if not set
        new_status = update_dict.get("status")
        if new_status in [ApplicationStatus.APPLIED, ApplicationStatus.APPLIED.value]:
            effective_app_date = existing.application_date
            if not effective_app_date:
                client_date = update_dict.get("application_date")
                valid_date = None
                if client_date and isinstance(client_date, str):
                    try:
                        datetime.strptime(client_date.strip(), "%Y-%m-%d")
                        valid_date = client_date.strip()
                    except ValueError:
                        valid_date = None
                if not valid_date:
                    valid_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
                update_dict["application_date"] = valid_date
                effective_app_date = valid_date

            if not existing.follow_up_date and "follow_up_date" not in update_dict and effective_app_date:
                user_settings = self.get_settings(user_id=user_id)
                default_days = user_settings.default_follow_up_days if user_settings else 7
                try:
                    dt = datetime.strptime(effective_app_date, "%Y-%m-%d")
                    follow_up = (dt + timedelta(days=default_days)).strftime("%Y-%m-%d")
                    update_dict["follow_up_date"] = follow_up
                except ValueError:
                    pass

        now = datetime.now().isoformat()
        update_dict["updated_at"] = now

        fields = []
        values = []
        for k, v in update_dict.items():
            if k in ["required_skills", "ats_keywords"]:
                v = json.dumps(v if v is not None else [])
            elif isinstance(v, ApplicationStatus):
                v = v.value
            fields.append(f"{k} = ?")
            values.append(v)

        values.append(app_id)
        if user_id:
            values.append(user_id)
            query = f"UPDATE applications SET {', '.join(fields)} WHERE id = ? AND user_id = ?"
        else:
            query = f"UPDATE applications SET {', '.join(fields)} WHERE id = ?"

        with self._get_cursor() as cursor:
            cursor.execute(self._format_sql(query), values)

        return self.get_application(app_id, user_id=user_id)

    def delete_application(self, app_id: str, user_id: Optional[str] = None) -> bool:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(self._format_sql("DELETE FROM applications WHERE id = ? AND user_id = ?"), (app_id, user_id))
            else:
                cursor.execute(self._format_sql("DELETE FROM applications WHERE id = ?"), (app_id,))
            return cursor.rowcount > 0

    def _row_to_application(self, row: Any) -> Application:
        raw_skills = row["required_skills"]
        skills = []
        if raw_skills:
            try:
                parsed = json.loads(raw_skills)
                if isinstance(parsed, list):
                    skills = parsed
            except Exception:
                skills = []

        raw_keywords = row["ats_keywords"]
        keywords = []
        if raw_keywords:
            try:
                parsed = json.loads(raw_keywords)
                if isinstance(parsed, list):
                    keywords = parsed
            except Exception:
                keywords = []

        return Application(
            id=row["id"],
            company=row["company"],
            role=row["role"],
            status=ApplicationStatus(row["status"]),
            location=row["location"] or "Unknown",
            salary=row["salary"] or "Not specified",
            url=row["url"] or "",
            required_skills=skills,
            ats_keywords=keywords,
            date_added=row["date_added"],
            application_date=row["application_date"] or "",
            follow_up_date=row["follow_up_date"] or "",
            notes=row["notes"] or "",
            best_resume_id=row["best_resume_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )

    # --- Settings ---
    def get_settings(self, user_id: Optional[str] = None) -> Settings:
        defaults = Settings()
        with self._get_cursor() as cursor:
            rows = []
            if user_id:
                cursor.execute(self._format_sql("SELECT key, value FROM user_settings WHERE user_id = ?"), (user_id,))
                rows = cursor.fetchall()
            else:
                cursor.execute("SELECT key, value FROM settings")
                rows = cursor.fetchall()

            settings_map = {row["key"]: row["value"] for row in rows}

        use_offline_raw = str(settings_map.get("use_offline_mode", str(defaults.use_offline_mode)))
        use_offline_mode = use_offline_raw.lower() in ["true", "1", "yes"]

        raw_key = settings_map.get("api_key", defaults.api_key)
        try:
            api_key = decrypt_value(raw_key) or ""
        except DecryptionError:
            api_key = ""

        raw_saved = settings_map.get("saved_keys", defaults.saved_keys)
        try:
            saved_keys = decrypt_value(raw_saved) or "[]"
        except DecryptionError:
            saved_keys = "[]"

        raw_profile_id = settings_map.get("active_profile_id")
        active_profile_id = (
            raw_profile_id.strip()
            if raw_profile_id and raw_profile_id.strip() not in ("", "None", "null")
            else None
        )

        has_api_key = bool(api_key)
        key_suffix = api_key[-4:] if (api_key and len(api_key) >= 4) else (api_key if api_key else None)

        return Settings(
            api_base_url=settings_map.get("api_base_url", defaults.api_base_url),
            api_key=api_key,
            model_name=settings_map.get("model_name", defaults.model_name),
            default_follow_up_days=int(settings_map.get("default_follow_up_days", defaults.default_follow_up_days)),
            saved_keys=saved_keys,
            use_offline_mode=use_offline_mode,
            active_profile_id=active_profile_id,
            has_api_key=has_api_key,
            key_suffix=key_suffix,
        )

    def update_settings(self, updates: SettingsUpdate, user_id: Optional[str] = None) -> Settings:
        current = self.get_settings(user_id=user_id)
        update_data = updates.model_dump(exclude_unset=True)
        merged = current.model_dump()
        merged.update(update_data)

        to_store = dict(merged)
        if to_store.get("api_key"):
            to_store["api_key"] = encrypt_value(to_store["api_key"])
        if to_store.get("saved_keys"):
            to_store["saved_keys"] = encrypt_value(to_store["saved_keys"])

        with self._get_cursor() as cursor:
            if user_id:
                for key, val in to_store.items():
                    stored_val = "" if val is None else str(val)
                    cursor.execute(
                        self._format_sql(
                            "INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?) "
                            "ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value"
                        ),
                        (user_id, key, stored_val),
                    )
            else:
                for key, val in to_store.items():
                    stored_val = "" if val is None else str(val)
                    cursor.execute(
                        self._format_sql(
                            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                        ),
                        (key, stored_val),
                    )
        return self.get_settings(user_id=user_id)

    # --- Provider Profiles CRUD ---
    def create_provider_profile(self, user_id: str, profile_in: ProviderProfileCreate) -> ProviderProfileMetadata:
        profile_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        api_key = (profile_in.api_key or "").strip()
        api_key_encrypted = encrypt_value(api_key) if api_key else None
        key_suffix = api_key[-4:] if len(api_key) >= 4 else (api_key if api_key else None)
        has_api_key = bool(api_key)
        is_active = bool(profile_in.is_active)

        with self._get_cursor() as cursor:
            if is_active:
                if self.is_postgres:
                    cursor.execute(
                        self._format_sql("UPDATE provider_profiles SET is_active = FALSE WHERE user_id = ?"),
                        (user_id,),
                    )
                else:
                    cursor.execute(
                        "UPDATE provider_profiles SET is_active = 0 WHERE user_id = ?",
                        (user_id,),
                    )

            cursor.execute(
                self._format_sql(
                    "INSERT INTO provider_profiles (id, user_id, name, api_base_url, model_name, api_key_encrypted, key_suffix, is_active, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (
                    profile_id,
                    user_id,
                    profile_in.name,
                    profile_in.api_base_url,
                    profile_in.model_name,
                    api_key_encrypted,
                    key_suffix,
                    is_active if self.is_postgres else (1 if is_active else 0),
                    now,
                    now,
                ),
            )

        if is_active:
            self.update_settings(
                SettingsUpdate(
                    active_profile_id=profile_id,
                    api_base_url=profile_in.api_base_url,
                    model_name=profile_in.model_name,
                    use_offline_mode=False,
                    api_key=api_key if api_key else None,
                ),
                user_id=user_id,
            )

        return ProviderProfileMetadata(
            id=profile_id,
            name=profile_in.name,
            api_base_url=profile_in.api_base_url,
            model_name=profile_in.model_name,
            is_active=is_active,
            has_api_key=has_api_key,
            key_suffix=key_suffix,
            created_at=now,
            updated_at=now,
        )

    def get_provider_profiles(self, user_id: str) -> List[ProviderProfileMetadata]:
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "SELECT id, user_id, name, api_base_url, model_name, api_key_encrypted, key_suffix, is_active, created_at, updated_at "
                    "FROM provider_profiles WHERE user_id = ? ORDER BY created_at DESC"
                ),
                (user_id,),
            )
            rows = cursor.fetchall()
            results = []
            for r in rows:
                row = dict(r)
                is_active = bool(row["is_active"])
                has_api_key = bool(row.get("api_key_encrypted"))
                results.append(
                    ProviderProfileMetadata(
                        id=row["id"],
                        name=row["name"],
                        api_base_url=row["api_base_url"],
                        model_name=row["model_name"],
                        is_active=is_active,
                        has_api_key=has_api_key,
                        key_suffix=row.get("key_suffix"),
                        created_at=row.get("created_at"),
                        updated_at=row.get("updated_at"),
                    )
                )
            return results

    def get_provider_profile(self, profile_id: str, user_id: str) -> Optional[ProviderProfileMetadata]:
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "SELECT id, user_id, name, api_base_url, model_name, api_key_encrypted, key_suffix, is_active, created_at, updated_at "
                    "FROM provider_profiles WHERE id = ? AND user_id = ?"
                ),
                (profile_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            r = dict(row)
            is_active = bool(r["is_active"])
            has_api_key = bool(r.get("api_key_encrypted"))
            return ProviderProfileMetadata(
                id=r["id"],
                name=r["name"],
                api_base_url=r["api_base_url"],
                model_name=r["model_name"],
                is_active=is_active,
                has_api_key=has_api_key,
                key_suffix=r.get("key_suffix"),
                created_at=r.get("created_at"),
                updated_at=r.get("updated_at"),
            )

    def get_provider_profile_secret(self, profile_id: str, user_id: str) -> Optional[str]:
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "SELECT api_key_encrypted FROM provider_profiles WHERE id = ? AND user_id = ?"
                ),
                (profile_id, user_id),
            )
            row = cursor.fetchone()
            if not row:
                return None
            r = dict(row)
            encrypted = r.get("api_key_encrypted")
            if not encrypted:
                return None
            try:
                return decrypt_value(encrypted)
            except DecryptionError:
                return None

    def update_provider_profile(
        self, profile_id: str, user_id: str, updates: ProviderProfileUpdate
    ) -> Optional[ProviderProfileMetadata]:
        existing = self.get_provider_profile(profile_id, user_id)
        if not existing:
            return None

        update_dict = updates.model_dump(exclude_unset=True)
        now = datetime.now(timezone.utc).isoformat()
        name = update_dict.get("name", existing.name)
        api_base_url = update_dict.get("api_base_url", existing.api_base_url)
        model_name = update_dict.get("model_name", existing.model_name)
        is_active = update_dict.get("is_active", existing.is_active)

        api_key_encrypted = None
        key_suffix = existing.key_suffix
        update_key_sql = ""
        key_params = []

        if "api_key" in update_dict and update_dict["api_key"] is not None:
            raw_key = update_dict["api_key"].strip()
            if raw_key:
                api_key_encrypted = encrypt_value(raw_key)
                key_suffix = raw_key[-4:] if len(raw_key) >= 4 else raw_key
            else:
                api_key_encrypted = None
                key_suffix = None
            update_key_sql = ", api_key_encrypted = ?, key_suffix = ?"
            key_params = [api_key_encrypted, key_suffix]

        with self._get_cursor() as cursor:
            if is_active and not existing.is_active:
                if self.is_postgres:
                    cursor.execute(
                        self._format_sql("UPDATE provider_profiles SET is_active = FALSE WHERE user_id = ?"),
                        (user_id,),
                    )
                else:
                    cursor.execute(
                        "UPDATE provider_profiles SET is_active = 0 WHERE user_id = ?",
                        (user_id,),
                    )

            sql = (
                f"UPDATE provider_profiles SET name = ?, api_base_url = ?, model_name = ?, is_active = ?, updated_at = ?"
                f"{update_key_sql} WHERE id = ? AND user_id = ?"
            )
            params = [
                name,
                api_base_url,
                model_name,
                is_active if self.is_postgres else (1 if is_active else 0),
                now,
            ] + key_params + [profile_id, user_id]
            cursor.execute(self._format_sql(sql), tuple(params))

        if is_active:
            secret = self.get_provider_profile_secret(profile_id, user_id)
            self.update_settings(
                SettingsUpdate(
                    active_profile_id=profile_id,
                    api_base_url=api_base_url,
                    model_name=model_name,
                    use_offline_mode=False,
                    api_key=secret if secret else None,
                ),
                user_id=user_id,
            )

        return self.get_provider_profile(profile_id, user_id)

    def activate_provider_profile(self, profile_id: str, user_id: str) -> Optional[ProviderProfileMetadata]:
        existing = self.get_provider_profile(profile_id, user_id)
        if not existing:
            return None

        with self._get_cursor() as cursor:
            if self.is_postgres:
                cursor.execute(
                    self._format_sql("UPDATE provider_profiles SET is_active = FALSE WHERE user_id = ?"),
                    (user_id,),
                )
                cursor.execute(
                    self._format_sql("UPDATE provider_profiles SET is_active = TRUE WHERE id = ? AND user_id = ?"),
                    (profile_id, user_id),
                )
            else:
                cursor.execute(
                    "UPDATE provider_profiles SET is_active = 0 WHERE user_id = ?",
                    (user_id,),
                )
                cursor.execute(
                    "UPDATE provider_profiles SET is_active = 1 WHERE id = ? AND user_id = ?",
                    (profile_id, user_id),
                )

        secret = self.get_provider_profile_secret(profile_id, user_id)
        self.update_settings(
            SettingsUpdate(
                active_profile_id=profile_id,
                api_base_url=existing.api_base_url,
                model_name=existing.model_name,
                use_offline_mode=False,
                api_key=secret if secret else None,
            ),
            user_id=user_id,
        )
        return self.get_provider_profile(profile_id, user_id)

    def delete_provider_profile(self, profile_id: str, user_id: str) -> bool:
        existing = self.get_provider_profile(profile_id, user_id)
        if not existing:
            return False

        settings = self.get_settings(user_id=user_id)
        was_active = existing.is_active or (settings.active_profile_id == profile_id)

        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql("DELETE FROM provider_profiles WHERE id = ? AND user_id = ?"),
                (profile_id, user_id),
            )

        if was_active:
            self.update_settings(
                SettingsUpdate(
                    active_profile_id=None,
                    use_offline_mode=True,
                    api_key="",
                ),
                user_id=user_id,
            )

        return True

    def migrate_from_sqlite(self, sqlite_path: str = "data/tracker.db"):
        """Migrates records from a local SQLite database into the current PostgreSQL database."""
        if not self.is_postgres or not Path(sqlite_path).exists():
            return
        local_sqlite = StorageService(db_path=sqlite_path, force_sqlite=True)
        # 1. Migrate resumes
        for r in local_sqlite.get_resumes():
            if not self.get_resume(r.id):
                with self._get_cursor() as cursor:
                    cursor.execute(
                        self._format_sql(
                            "INSERT INTO resumes (id, name, content, created_at, updated_at) VALUES (?, ?, ?, ?, ?)"
                        ),
                        (r.id, r.name, r.content, r.created_at, r.updated_at),
                    )

        # 2. Migrate applications
        for app in local_sqlite.get_applications():
            if not self.get_application(app.id):
                app_create = ApplicationCreate(
                    company=app.company,
                    role=app.role,
                    status=app.status,
                    location=app.location,
                    salary=app.salary,
                    url=app.url,
                    required_skills=app.required_skills,
                    ats_keywords=app.ats_keywords,
                    application_date=app.application_date,
                    follow_up_date=app.follow_up_date,
                    notes=app.notes,
                    best_resume_id=app.best_resume_id,
                )
                self.add_application(app_create)

        # 3. Migrate settings
        local_settings = local_sqlite.get_settings()
        self.update_settings(SettingsUpdate(
            api_base_url=local_settings.api_base_url,
            api_key=local_settings.api_key,
            model_name=local_settings.model_name,
            default_follow_up_days=local_settings.default_follow_up_days,
            saved_keys=local_settings.saved_keys,
            use_offline_mode=local_settings.use_offline_mode,
        ))
