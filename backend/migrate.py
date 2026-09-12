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
    provider_profiles_count = get_count("provider_profiles")

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
        "provider_profiles_count": provider_profiles_count,
        "migrated_users": 0,
        "migrated_applications": 0,
        "migrated_resumes": 0,
        "migrated_attachments": 0,
        "migrated_user_settings": 0,
        "migrated_global_settings": 0,
        "migrated_provider_profiles": 0,
        "errors": [],
    }

    if dry_run:
        src_conn.close()
        return summary

    # Apply migration to destination
    is_postgres = dest_target.startswith("postgres://") or dest_target.startswith("postgresql://")
    if is_postgres:
        dest_storage = StorageService(database_url=dest_target)
    else:
        dest_storage = StorageService(db_path=dest_target, force_sqlite=True)

    now = datetime.now().isoformat()

    try:
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
                    ev = bool(u["email_verified"]) if "email_verified" in u.keys() else False
                    sv = int(u["session_version"]) if "session_version" in u.keys() else 1
                    gsub = u["google_sub"] if "google_sub" in u.keys() else None
                    # Insert user
                    dst_cursor.execute(
                        dest_storage._format_sql(
                            "INSERT INTO users (id, email, hashed_password, name, avatar_url, provider, email_verified, session_version, google_sub, created_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                            + ("ON CONFLICT (id) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(id) DO NOTHING")
                        ),
                        (u["id"], u["email"], pwd, u["name"], u["avatar_url"], u["provider"], ev, sv, gsub, u["created_at"], u["updated_at"]),
                    )
                    dst_cursor.execute(
                        dest_storage._format_sql("INSERT INTO _migration_ledger VALUES (?, ?, ?, ?)"),
                        (u["id"], "users", u["id"], now),
                    )
                    summary["migrated_users"] += 1
            except Exception as e:
                summary["errors"].append(f"users: {e}")
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
                    summary["migrated_attachments"] += 1
            except Exception as e:
                summary["errors"].append(f"attachments: {e}")
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
                    summary["migrated_resumes"] += 1
            except Exception as e:
                summary["errors"].append(f"resumes: {e}")
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
                    summary["migrated_applications"] += 1
            except Exception as e:
                summary["errors"].append(f"applications: {e}")
                print(f"[WARN] Error migrating applications: {e}")

            # 5. Migrate User Settings
            try:
                src_user_settings = src_cursor.execute("SELECT * FROM user_settings").fetchall()
                for s in src_user_settings:
                    dst_cursor.execute(
                        dest_storage._format_sql(
                            "INSERT INTO user_settings (user_id, key, value) "
                            "VALUES (?, ?, ?) "
                            + ("ON CONFLICT (user_id, key) DO UPDATE SET value = excluded.value" if dest_storage.is_postgres else "ON CONFLICT(user_id, key) DO UPDATE SET value = excluded.value")
                        ),
                        (s["user_id"], s["key"], s["value"]),
                    )
                    summary["migrated_user_settings"] += 1
            except Exception as e:
                summary["errors"].append(f"user_settings: {e}")
                print(f"[WARN] Error migrating user_settings: {e}")

            # 6. Migrate Global Settings
            try:
                src_settings = src_cursor.execute("SELECT * FROM settings").fetchall()
                for gs in src_settings:
                    dst_cursor.execute(
                        dest_storage._format_sql(
                            "INSERT INTO settings (key, value) "
                            "VALUES (?, ?) "
                            + ("ON CONFLICT (key) DO UPDATE SET value = excluded.value" if dest_storage.is_postgres else "ON CONFLICT(key) DO UPDATE SET value = excluded.value")
                        ),
                        (gs["key"], gs["value"]),
                    )
                    summary["migrated_global_settings"] += 1
            except Exception as e:
                summary["errors"].append(f"settings: {e}")
                print(f"[WARN] Error migrating settings: {e}")

            # 7. Migrate Provider Profiles
            try:
                src_profiles = src_cursor.execute("SELECT * FROM provider_profiles").fetchall()
                for p in src_profiles:
                    dst_cursor.execute(
                        dest_storage._format_sql("SELECT 1 FROM _migration_ledger WHERE table_name = ? AND source_id = ?"),
                        ("provider_profiles", p["id"]),
                    )
                    if dst_cursor.fetchone():
                        continue
                    target_user_id = p["user_id"] or map_unowned_to
                    dst_cursor.execute(
                        dest_storage._format_sql(
                            "INSERT INTO provider_profiles (id, user_id, name, api_base_url, model_name, api_key_encrypted, key_suffix, is_active, created_at, updated_at) "
                            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?) "
                            + ("ON CONFLICT (id) DO NOTHING" if dest_storage.is_postgres else "ON CONFLICT(id) DO NOTHING")
                        ),
                        (
                            p["id"],
                            target_user_id,
                            p["name"],
                            p["api_base_url"],
                            p["model_name"],
                            p["api_key_encrypted"],
                            p["key_suffix"],
                            p["is_active"],
                            p["created_at"],
                            p["updated_at"],
                        ),
                    )
                    dst_cursor.execute(
                        dest_storage._format_sql("INSERT INTO _migration_ledger VALUES (?, ?, ?, ?)"),
                        (p["id"], "provider_profiles", p["id"], now),
                    )
                    summary["migrated_provider_profiles"] += 1
            except Exception as e:
                summary["errors"].append(f"provider_profiles: {e}")
                print(f"[WARN] Error migrating provider_profiles: {e}")

    finally:
        dest_storage.close()
        src_conn.close()

    if summary["errors"]:
        summary["success"] = False

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
        print(f"Users: {res['users_count']} (migrated: {res.get('migrated_users', 0)})")
        print(f"Applications: {res['applications_count']} (migrated: {res.get('migrated_applications', 0)}, unowned: {res['unowned_applications']})")
        print(f"Resumes: {res['resumes_count']} (migrated: {res.get('migrated_resumes', 0)}, unowned: {res['unowned_resumes']})")
        print(f"Attachments: {res['attachments_count']} (migrated: {res.get('migrated_attachments', 0)})")
        print(f"User Settings: {res['user_settings_count']} (migrated: {res.get('migrated_user_settings', 0)})")
        print(f"Global Settings: {res['global_settings_count']} (migrated: {res.get('migrated_global_settings', 0)})")
        print(f"Provider Profiles: {res['provider_profiles_count']} (migrated: {res.get('migrated_provider_profiles', 0)})")
        if res.get("errors"):
            print("Errors encountered:")
            for err in res["errors"]:
                print(f"  - {err}")
    except Exception as e:
        print(f"Migration error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

