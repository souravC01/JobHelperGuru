import json
import sqlite3
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from backend.models import (
    Application,
    ApplicationCreate,
    ApplicationUpdate,
    ApplicationStatus,
    Resume,
    ResumeCreate,
    Settings,
    SettingsUpdate,
)


class StorageService:
    def __init__(self, db_path: str = "data/tracker.db"):
        self.db_path = db_path
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Applications table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS applications (
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
                    updated_at TEXT NOT NULL
                )
            """)
            # Resumes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS resumes (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                )
            """)
            conn.commit()

    # --- Resumes CRUD ---
    def add_resume(self, name: str, content: str) -> Resume:
        now = datetime.now().isoformat()
        resume_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO resumes (id, name, content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (resume_id, name, content, now, now),
            )
            conn.commit()
        return Resume(id=resume_id, name=name, content=content, created_at=now, updated_at=now)

    def get_resumes(self) -> List[Resume]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resumes ORDER BY created_at DESC")
            rows = cursor.fetchall()
            return [
                Resume(
                    id=row["id"],
                    name=row["name"],
                    content=row["content"],
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
                for row in rows
            ]

    def get_resume(self, resume_id: str) -> Optional[Resume]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return Resume(
                id=row["id"],
                name=row["name"],
                content=row["content"],
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )

    def delete_resume(self, resume_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
            conn.commit()
            return cursor.rowcount > 0

    # --- Applications CRUD ---
    def add_application(self, app_data: ApplicationCreate) -> Application:
        now = datetime.now().isoformat()
        date_added = datetime.now().strftime("%Y-%m-%d")
        app_id = str(uuid.uuid4())
        status_val = app_data.status.value if isinstance(app_data.status, ApplicationStatus) else str(app_data.status)
        req_skills_json = json.dumps(app_data.required_skills or [])
        ats_keywords_json = json.dumps(app_data.ats_keywords or [])

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO applications (
                    id, company, role, status, location, salary, url,
                    required_skills, ats_keywords, date_added, application_date,
                    follow_up_date, notes, best_resume_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    app_id,
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
            conn.commit()

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

    def get_applications(self) -> List[Application]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications ORDER BY date_added DESC, created_at DESC")
            rows = cursor.fetchall()
            return [self._row_to_application(row) for row in rows]

    def get_application(self, app_id: str) -> Optional[Application]:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
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

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, tuple(values))
            conn.commit()
            if cursor.rowcount == 0:
                return None

        return self.get_application(app_id)

    def delete_application(self, app_id: str) -> bool:
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM applications WHERE id = ?", (app_id,))
            conn.commit()
            return cursor.rowcount > 0

    def _row_to_application(self, row: sqlite3.Row) -> Application:
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
    def get_settings(self) -> Settings:
        defaults = Settings()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM settings")
            rows = cursor.fetchall()
            settings_map = {row["key"]: row["value"] for row in rows}

        return Settings(
            api_base_url=settings_map.get("api_base_url", defaults.api_base_url),
            api_key=settings_map.get("api_key", defaults.api_key),
            model_name=settings_map.get("model_name", defaults.model_name),
            default_follow_up_days=int(settings_map.get("default_follow_up_days", defaults.default_follow_up_days)),
        )

    def update_settings(self, updates: SettingsUpdate) -> Settings:
        current = self.get_settings()
        update_data = updates.model_dump(exclude_unset=True)
        merged = current.model_dump()
        merged.update(update_data)

        with self._get_connection() as conn:
            cursor = conn.cursor()
            for key, val in merged.items():
                cursor.execute(
                    "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                    (key, str(val)),
                )
            conn.commit()

        return self.get_settings()
