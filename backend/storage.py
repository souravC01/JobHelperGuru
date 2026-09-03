import json
import os
import sqlite3
import uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv(override=True)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

from backend.models import (
    User,
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatus,
    Resume,
    ResumeCreate,
    Settings,
    SettingsUpdate,
)
from backend.services.encryption import encrypt_value, decrypt_value



class StorageService:
    def __init__(self, db_path: str = "data/tracker.db", database_url: Optional[str] = None, force_sqlite: bool = False):
        if force_sqlite:
            raw_url = None
        elif database_url is not None:
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
        else:
            self.database_url = None
            self.is_postgres = False
            self.db_path = db_path
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        self._init_db()

    @contextmanager
    def _get_cursor(self):
        if self.is_postgres:
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
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Column migrations for existing tables
            if self.is_postgres:
                cursor.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS file_key TEXT")
                cursor.execute("ALTER TABLE resumes ADD COLUMN IF NOT EXISTS user_id TEXT")
                cursor.execute("ALTER TABLE applications ADD COLUMN IF NOT EXISTS user_id TEXT")
            else:
                try:
                    cursor.execute("ALTER TABLE resumes ADD COLUMN file_key TEXT")
                except Exception:
                    pass
                try:
                    cursor.execute("ALTER TABLE resumes ADD COLUMN user_id TEXT")
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
        self.deduplicate_existing_applications()

    # --- Users CRUD ---
    def create_user(
        self,
        email: str,
        hashed_password: Optional[str],
        name: str,
        avatar_url: Optional[str] = None,
        provider: str = "email",
    ) -> User:
        now = datetime.now().isoformat()
        user_id = str(uuid.uuid4())
        clean_email = email.strip().lower()
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "INSERT INTO users (id, email, hashed_password, name, avatar_url, provider, created_at, updated_at) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                ),
                (user_id, clean_email, hashed_password, name, avatar_url, provider, now, now),
            )
            # Claim unassigned historical records for the first registered user
            cursor.execute(
                self._format_sql("UPDATE applications SET user_id = ? WHERE user_id IS NULL"),
                (user_id,),
            )
            cursor.execute(
                self._format_sql("UPDATE resumes SET user_id = ? WHERE user_id IS NULL"),
                (user_id,),
            )
        return User(
            id=user_id,
            email=clean_email,
            name=name,
            avatar_url=avatar_url,
            provider=provider,
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
            return User(
                id=row["id"],
                email=row["email"],
                name=row["name"],
                avatar_url=row["avatar_url"],
                provider=row["provider"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    # --- Resumes CRUD ---
    def add_resume(self, name: str, content: str, file_key: Optional[str] = None, user_id: Optional[str] = None) -> Resume:
        now = datetime.now().isoformat()
        resume_id = str(uuid.uuid4())
        with self._get_cursor() as cursor:
            cursor.execute(
                self._format_sql(
                    "INSERT INTO resumes (id, user_id, name, content, file_key, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?)"
                ),
                (resume_id, user_id, name, content, file_key, now, now),
            )
        return Resume(id=resume_id, name=name, content=content, file_key=file_key, created_at=now, updated_at=now)

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

    # --- Applications CRUD ---
    def find_existing_application(
        self, url: Optional[str], company: str, role: str, user_id: Optional[str] = None
    ) -> Optional[Application]:
        with self._get_cursor() as cursor:
            # 1. Match by exact or normalized URL (excluding blank and manual_paste)
            clean_url = (url or "").strip().rstrip("/")
            if clean_url and clean_url != "manual_paste":
                if user_id:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE TRIM(RTRIM(url, '/')) = ? AND url != '' AND url != 'manual_paste' AND user_id = ?"
                        ),
                        (clean_url, user_id),
                    )
                else:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE TRIM(RTRIM(url, '/')) = ? AND url != '' AND url != 'manual_paste'"
                        ),
                        (clean_url,),
                    )
                row = cursor.fetchone()
                if row:
                    return self._row_to_application(row)

            # 2. Match by exact normalized company & role
            clean_comp = (company or "").strip().lower()
            clean_r = (role or "").strip().lower()
            if clean_comp and clean_r:
                if user_id:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE LOWER(TRIM(company)) = ? AND LOWER(TRIM(role)) = ? AND user_id = ?"
                        ),
                        (clean_comp, clean_r, user_id),
                    )
                else:
                    cursor.execute(
                        self._format_sql(
                            "SELECT * FROM applications WHERE LOWER(TRIM(company)) = ? AND LOWER(TRIM(role)) = ?"
                        ),
                        (clean_comp, clean_r),
                    )
                row = cursor.fetchone()
                if row:
                    return self._row_to_application(row)

                # 3. Match if company is a prefix or contains the other (e.g. 'MindBridge' vs 'MindBridge Analytics Inc.')
                if len(clean_comp) >= 4:
                    if user_id:
                        cursor.execute(
                            self._format_sql(
                                """
                                SELECT * FROM applications 
                                WHERE LOWER(TRIM(role)) = ? 
                                  AND (
                                      LOWER(TRIM(company)) LIKE ? || '%' 
                                      OR ? LIKE LOWER(TRIM(company)) || '%'
                                  )
                                  AND user_id = ?
                                """
                            ),
                            (clean_r, clean_comp, clean_comp, user_id),
                        )
                    else:
                        cursor.execute(
                            self._format_sql(
                                """
                                SELECT * FROM applications 
                                WHERE LOWER(TRIM(role)) = ? 
                                  AND (
                                      LOWER(TRIM(company)) LIKE ? || '%' 
                                      OR ? LIKE LOWER(TRIM(company)) || '%'
                                  )
                                """
                            ),
                            (clean_r, clean_comp, clean_comp),
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
            updated = self.update_application(existing.id, updates)
            if updated:
                return updated
            return existing

        now = datetime.now().isoformat()
        date_added = datetime.now().strftime("%Y-%m-%d")
        app_id = str(uuid.uuid4())
        status_val = app_data.status.value if isinstance(app_data.status, ApplicationStatus) else str(app_data.status)
        req_skills_json = json.dumps(app_data.required_skills or [])
        ats_keywords_json = json.dumps(app_data.ats_keywords or [])

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
                    app_data.application_date or "",
                    app_data.follow_up_date or "",
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

    def update_application(self, app_id: str, updates: Dict[str, Any] | ApplicationUpdate) -> Optional[Application]:
        if isinstance(updates, ApplicationUpdate):
            update_dict = updates.model_dump(exclude_unset=True)
        else:
            update_dict = {k: v for k, v in updates.items() if v is not None}

        if not update_dict:
            return self.get_application(app_id)

        now = datetime.now().isoformat()
        update_dict["updated_at"] = now

        fields = []
        values = []
        for k, v in update_dict.items():
            if k in ["required_skills", "ats_keywords"]:
                v = json.dumps(v)
            elif isinstance(v, ApplicationStatus):
                v = v.value
            fields.append(f"{k} = ?")
            values.append(v)

        values.append(app_id)
        query = f"UPDATE applications SET {', '.join(fields)} WHERE id = ?"

        with self._get_cursor() as cursor:
            cursor.execute(self._format_sql(query), values)

        return self.get_application(app_id)

    def delete_application(self, app_id: str, user_id: Optional[str] = None) -> bool:
        with self._get_cursor() as cursor:
            if user_id:
                cursor.execute(self._format_sql("DELETE FROM applications WHERE id = ? AND user_id = ?"), (app_id, user_id))
            else:
                cursor.execute(self._format_sql("DELETE FROM applications WHERE id = ?"), (app_id,))
            return cursor.rowcount > 0

    def _row_to_application(self, row: Any) -> Application:
        return Application(
            id=row["id"],
            company=row["company"],
            role=row["role"],
            status=ApplicationStatus(row["status"]),
            location=row["location"] or "Unknown",
            salary=row["salary"] or "Not specified",
            url=row["url"] or "",
            required_skills=json.loads(row["required_skills"]) if row["required_skills"] else [],
            ats_keywords=json.loads(row["ats_keywords"]) if row["ats_keywords"] else [],
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
            if not rows:
                cursor.execute("SELECT key, value FROM settings")
                rows = cursor.fetchall()

            settings_map = {row["key"]: row["value"] for row in rows}

        use_offline_raw = str(settings_map.get("use_offline_mode", str(defaults.use_offline_mode)))
        use_offline_mode = use_offline_raw.lower() in ["true", "1", "yes"]

        raw_key = settings_map.get("api_key", defaults.api_key)
        api_key = decrypt_value(raw_key) or ""

        raw_saved = settings_map.get("saved_keys", defaults.saved_keys)
        saved_keys = decrypt_value(raw_saved) or "[]"

        return Settings(
            api_base_url=settings_map.get("api_base_url", defaults.api_base_url),
            api_key=api_key,
            model_name=settings_map.get("model_name", defaults.model_name),
            default_follow_up_days=int(settings_map.get("default_follow_up_days", defaults.default_follow_up_days)),
            saved_keys=saved_keys,
            use_offline_mode=use_offline_mode,
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
                    cursor.execute(
                        self._format_sql(
                            "INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?) "
                            "ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value"
                        ),
                        (user_id, key, str(val)),
                    )
            else:
                for key, val in to_store.items():
                    cursor.execute(
                        self._format_sql(
                            "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value"
                        ),
                        (key, str(val)),
                    )
        return self.get_settings(user_id=user_id)

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
