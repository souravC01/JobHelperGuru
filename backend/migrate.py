import argparse
import os
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from backend.storage import StorageService


def run_migration(
    source_path: str,
    dest_path: Optional[str] = None,
    dry_run: bool = True,
    map_unowned_to: Optional[str] = None,
) -> Dict[str, Any]:
    source_file = Path(source_path).resolve()
    if not source_file.exists():
        raise FileNotFoundError(f"Source database not found: {source_path}")

    dest_target = dest_path or os.getenv("DATABASE_URL") or os.getenv("JOB_HELPER_DB")
    if not dest_target:
        raise ValueError("Destination database must be specified via --dest or DATABASE_URL/JOB_HELPER_DB")

    # If destination is SQLite path, resolve and check conflict
    if not dest_target.startswith("postgres://") and not dest_target.startswith("postgresql://"):
        dest_file = Path(dest_target).resolve()
        if dest_file == source_file:
            raise ValueError("Source and destination cannot be identical")

    # Connect to source database
    src_conn = sqlite3.connect(str(source_file))
    src_conn.row_factory = sqlite3.Row
    src_cursor = src_conn.cursor()

    # Read counts and unowned records
    def get_count(table: str) -> int:
        try:
            return src_cursor.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        except Exception:
            return 0

    def get_unowned_count(table: str) -> int:
        try:
            return src_cursor.execute(f"SELECT count(*) FROM {table} WHERE user_id IS NULL").fetchone()[0]
        except Exception:
            return 0

    users_count = get_count("users")
    apps_count = get_count("applications")
    unowned_apps = get_unowned_count("applications")
    resumes_count = get_count("resumes")
    unowned_resumes = get_unowned_count("resumes")
    attachments_count = get_count("attachments")
    user_settings_count = get_count("user_settings")
    global_settings_count = get_count("settings")

    summary = {
        "success": True,
        "dry_run": dry_run,
        "source": str(source_file),
        "destination": dest_target,
        "users_count": users_count,
        "applications_count": apps_count,
        "unowned_applications": unowned_apps,
        "resumes_count": resumes_count,
        "unowned_resumes": unowned_resumes,
        "attachments_count": attachments_count,
        "user_settings_count": user_settings_count,
        "global_settings_count": global_settings_count,
    }

    if dry_run:
        src_conn.close()
        return summary

    # Apply migration to destination
    dest_storage = StorageService(db_path=dest_target)
    now = datetime.now().isoformat()

    with dest_storage._get_cursor() as dst_cursor:
        # Create migration ledger
        dst_cursor.execute("""
            CREATE TABLE IF NOT EXISTS _migration_ledger (
                source_id TEXT,
                table_name TEXT,
                target_id TEXT,
                migrated_at TEXT,
                PRIMARY KEY (table_name, source_id)
            )
        """)

        # 1. Migrate Users
        try:
            src_users = src_cursor.execute("SELECT * FROM users").fetchall()
            for u in src_users:
                # Check ledger
                dst_cursor.execute(
                    dest_storage._format_sql("SELECT 1 FROM _migration_ledger WHERE table_name = ? AND source_id = ?"),
                    ("users", u["id"]),
                )
                if dst_cursor.fetchone():
                    continue
                pwd = u["hashed_password"] if "hashed_password" in u.keys() else (u["password_hash"] if "password_hash" in u.keys() else None)
                # Insert user
                dst_cursor.execute(
                    dest_storage._format_sql(
                        "INSERT INTO users (id, email, hashed_password, name, avatar_url, provider, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                        + ("ON CONFLICT (id) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(id) DO NOTHING")
                    ),
                    (u["id"], u["email"], pwd, u["name"], u["avatar_url"], u["provider"], u["created_at"], u["updated_at"]),
                )
                dst_cursor.execute(
                    dest_storage._format_sql("INSERT INTO _migration_ledger VALUES (?, ?, ?, ?)"),
                    (u["id"], "users", u["id"], now),
                )
        except Exception as e:
            print(f"[WARN] Error migrating users: {e}")

        # 2. Migrate Attachments
        try:
            src_attachments = src_cursor.execute("SELECT * FROM attachments").fetchall()
            for a in src_attachments:
                dst_cursor.execute(
                    dest_storage._format_sql("SELECT 1 FROM _migration_ledger WHERE table_name = ? AND source_id = ?"),
                    ("attachments", a["id"]),
                )
                if dst_cursor.fetchone():
                    continue
                target_user_id = a["user_id"] or map_unowned_to
                dst_cursor.execute(
                    dest_storage._format_sql(
                        "INSERT INTO attachments (id, user_id, storage_backend, object_key, original_filename, content_type, size_bytes, deletion_state, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                        + ("ON CONFLICT (id) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(id) DO NOTHING")
                    ),
                    (a["id"], target_user_id, a["storage_backend"], a["object_key"], a["original_filename"], a["content_type"], a["size_bytes"], a["deletion_state"], a["created_at"], a["updated_at"]),
                )
                dst_cursor.execute(
                    dest_storage._format_sql("INSERT INTO _migration_ledger VALUES (?, ?, ?, ?)"),
                    (a["id"], "attachments", a["id"], now),
                )
        except Exception as e:
            print(f"[WARN] Error migrating attachments: {e}")

        # 3. Migrate Resumes
        try:
            src_resumes = src_cursor.execute("SELECT * FROM resumes").fetchall()
            for r in src_resumes:
                dst_cursor.execute(
                    dest_storage._format_sql("SELECT 1 FROM _migration_ledger WHERE table_name = ? AND source_id = ?"),
                    ("resumes", r["id"]),
                )
                if dst_cursor.fetchone():
                    continue
                target_user_id = r["user_id"] or map_unowned_to
                att_id = r["attachment_id"] if "attachment_id" in r.keys() else None
                dst_cursor.execute(
                    dest_storage._format_sql(
                        "INSERT INTO resumes (id, user_id, name, content, file_key, attachment_id, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                        + ("ON CONFLICT (id) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(id) DO NOTHING")
                    ),
                    (r["id"], target_user_id, r["name"], r["content"], r["file_key"], att_id, r["created_at"], r["updated_at"]),
                )
                dst_cursor.execute(
                    dest_storage._format_sql("INSERT INTO _migration_ledger VALUES (?, ?, ?, ?)"),
                    (r["id"], "resumes", r["id"], now),
                )
        except Exception as e:
            print(f"[WARN] Error migrating resumes: {e}")

        # 4. Migrate Applications
        try:
            src_apps = src_cursor.execute("SELECT * FROM applications").fetchall()
            for app in src_apps:
                dst_cursor.execute(
                    dest_storage._format_sql("SELECT 1 FROM _migration_ledger WHERE table_name = ? AND source_id = ?"),
                    ("applications", app["id"]),
                )
                if dst_cursor.fetchone():
                    continue
                target_user_id = app["user_id"] or map_unowned_to
                date_added = app["date_added"] if "date_added" in app.keys() else app["created_at"]
                app_date = app["application_date"] if "application_date" in app.keys() else None
                dst_cursor.execute(
                    dest_storage._format_sql(
                        "INSERT INTO applications (id, user_id, company, role, status, location, salary, url, required_skills, ats_keywords, date_added, application_date, follow_up_date, notes, best_resume_id, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                        + ("ON CONFLICT (id) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(id) DO NOTHING")
                    ),
                    (
                        app["id"],
                        target_user_id,
                        app["company"],
                        app["role"],
                        app["status"],
                        app["location"],
                        app["salary"],
                        app["url"],
                        app["required_skills"],
                        app["ats_keywords"],
                        date_added,
                        app_date,
                        app["follow_up_date"],
                        app["notes"],
                        app["best_resume_id"],
                        app["created_at"],
                        app["updated_at"],
                    ),
                )
                dst_cursor.execute(
                    dest_storage._format_sql("INSERT INTO _migration_ledger VALUES (?, ?, ?, ?)"),
                    (app["id"], "applications", app["id"], now),
                )
        except Exception as e:
            print(f"[WARN] Error migrating applications: {e}")

        # 5. Migrate User Settings
        try:
            src_user_settings = src_cursor.execute("SELECT * FROM user_settings").fetchall()
            for s in src_user_settings:
                dst_cursor.execute(
                    dest_storage._format_sql(
                        "INSERT INTO user_settings (user_id, key, value, created_at, updated_at) "
                        "VALUES (?, ?, ?, ?, ?) "
                        + ("ON CONFLICT (user_id, key) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(user_id, key) DO NOTHING")
                    ),
                    (s["user_id"], s["key"], s["value"], s["created_at"], s["updated_at"]),
                )
        except Exception:
            pass

        # 6. Migrate Global Settings
        try:
            src_settings = src_cursor.execute("SELECT * FROM settings").fetchall()
            for gs in src_settings:
                dst_cursor.execute(
                    dest_storage._format_sql(
                        "INSERT INTO settings (key, value) "
                        "VALUES (?, ?) "
                        + ("ON CONFLICT (key) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(key) DO NOTHING")
                    ),
                    (gs["key"], gs["value"]),
                )
        except Exception:
            pass

    src_conn.close()
    return summary


def main():
    parser = argparse.ArgumentParser(description="Explicit safe database migration utility")
    parser.add_argument("--source", required=True, help="Path to source SQLite database")
    parser.add_argument("--dest", default=None, help="Destination database path or URL (defaults to env)")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--dry-run", action="store_true", help="Report record counts without writing")
    group.add_argument("--apply", action="store_true", help="Execute the migration")
    parser.add_argument("--map-unowned-to", default=None, help="User ID to assign unowned legacy records to")

    args = parser.parse_args()

    try:
        res = run_migration(
            source_path=args.source,
            dest_path=args.dest,
            dry_run=args.dry_run,
            map_unowned_to=args.map_unowned_to,
        )
        print("--- Migration Summary ---")
        print(f"Mode: {'DRY RUN' if res['dry_run'] else 'APPLIED'}")
        print(f"Source: {res['source']}")
        print(f"Destination: {res['destination']}")
        print(f"Users: {res['users_count']}")
        print(f"Applications: {res['applications_count']} (unowned: {res['unowned_applications']})")
        print(f"Resumes: {res['resumes_count']} (unowned: {res['unowned_resumes']})")
        print(f"Attachments: {res['attachments_count']}")
        print(f"User Settings: {res['user_settings_count']}")
        print(f"Global Settings: {res['global_settings_count']}")
    except Exception as e:
        print(f"Migration error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
