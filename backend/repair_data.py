import argparse
import os
import sys
from typing import Optional, Dict, Any

from backend.storage import StorageService
from backend.services.object_storage import ObjectStorageService


def repair_database(
    storage: StorageService,
    object_storage: Optional[ObjectStorageService] = None,
    dry_run: bool = True,
) -> Dict[str, Any]:
    """
    Scans and repairs data anomalies:
    1. Applications with NULL or empty status -> 'Wishlist'
    2. Applications with NULL required_skills or ats_keywords -> '[]'
    3. User settings with invalid default_follow_up_days -> 7
    4. Orphaned active attachments not referenced by any resume -> cleaned up
    """
    report = {
        "corrupt_applications": 0,
        "corrupt_settings": 0,
        "orphaned_attachments": 0,
        "applied": not dry_run,
    }

    # 1. Inspect applications
    with storage._get_cursor() as cursor:
        cursor.execute(
            storage._format_sql(
                """
                SELECT id, status, required_skills, ats_keywords
                FROM applications
                WHERE status IS NULL OR status = '' OR required_skills IS NULL OR ats_keywords IS NULL
                """
            )
        )
        corrupt_apps = cursor.fetchall()
        report["corrupt_applications"] = len(corrupt_apps)

        if not dry_run and corrupt_apps:
            for app_row in corrupt_apps:
                app_id = app_row["id"] if isinstance(app_row, dict) else app_row[0]
                cursor.execute(
                    storage._format_sql(
                        """
                        UPDATE applications
                        SET status = COALESCE(NULLIF(status, ''), 'Wishlist'),
                            required_skills = COALESCE(required_skills, '[]'),
                            ats_keywords = COALESCE(ats_keywords, '[]')
                        WHERE id = ?
                        """
                    ),
                    (app_id,),
                )

    # 2. Inspect user settings
    with storage._get_cursor() as cursor:
        cursor.execute(
            storage._format_sql(
                """
                SELECT user_id, key, value
                FROM user_settings
                WHERE key = 'default_follow_up_days'
                """
            )
        )
        settings_rows = cursor.fetchall()
        corrupt_user_settings = []
        for s_row in settings_rows:
            uid = s_row["user_id"] if isinstance(s_row, dict) else s_row[0]
            val = s_row["value"] if isinstance(s_row, dict) else s_row[2]
            try:
                days = int(val)
                if days < 1 or days > 90:
                    corrupt_user_settings.append(uid)
            except (ValueError, TypeError):
                corrupt_user_settings.append(uid)

        # Global settings table
        cursor.execute("SELECT key, value FROM settings WHERE key = 'default_follow_up_days'")
        global_row = cursor.fetchone()
        global_corrupt = False
        if global_row:
            gval = global_row["value"] if isinstance(global_row, dict) else global_row[1]
            try:
                gdays = int(gval)
                if gdays < 1 or gdays > 90:
                    global_corrupt = True
            except (ValueError, TypeError):
                global_corrupt = True

        report["corrupt_settings"] = len(corrupt_user_settings) + (1 if global_corrupt else 0)

        if not dry_run:
            for uid in corrupt_user_settings:
                cursor.execute(
                    storage._format_sql(
                        "UPDATE user_settings SET value = '7' WHERE user_id = ? AND key = 'default_follow_up_days'"
                    ),
                    (uid,),
                )
            if global_corrupt:
                cursor.execute("UPDATE settings SET value = '7' WHERE key = 'default_follow_up_days'")

    # 3. Inspect orphaned attachments
    with storage._get_cursor() as cursor:
        cursor.execute(
            storage._format_sql(
                """
                SELECT id, user_id, object_key
                FROM attachments
                WHERE deletion_state = 'active'
                  AND id NOT IN (SELECT attachment_id FROM resumes WHERE attachment_id IS NOT NULL)
                """
            )
        )
        orphans = cursor.fetchall()
        report["orphaned_attachments"] = len(orphans)

        if not dry_run and orphans:
            for att_row in orphans:
                att_id = att_row["id"] if isinstance(att_row, dict) else att_row[0]
                user_id = att_row["user_id"] if isinstance(att_row, dict) else att_row[1]
                object_key = att_row["object_key"] if isinstance(att_row, dict) else att_row[2]

                if object_storage and object_key:
                    try:
                        object_storage.delete_file(object_key, user_id=user_id)
                    except Exception:
                        pass

                cursor.execute(
                    storage._format_sql(
                        "UPDATE attachments SET deletion_state = 'orphaned_cleaned' WHERE id = ?"
                    ),
                    (att_id,),
                )

    return report


def main_cli():
    parser = argparse.ArgumentParser(description="Repair database inconsistencies and clean orphaned attachments.")
    parser.add_argument("--apply", action="store_true", help="Apply fixes directly to the database (default is dry-run).")
    parser.add_argument("--db-path", default=None, help="Optional path to local SQLite database.")
    args = parser.parse_args()

    db_path = args.db_path or os.getenv("JOB_HELPER_DB", "data/tracker.db")
    storage = StorageService(db_path=db_path)
    object_storage = ObjectStorageService()

    dry_run = not args.apply
    print(f"[{'DRY RUN' if dry_run else 'APPLYING REPAIRS'}] Starting database audit...")
    result = repair_database(storage, object_storage, dry_run=dry_run)
    print("Audit results:", result)
    if dry_run:
        print("Run with --apply to commit changes to the database.")


if __name__ == "__main__":
    main_cli()
