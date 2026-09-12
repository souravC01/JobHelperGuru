import pytest
from backend import main
from backend.models import ApplicationCreate
from backend.repair_data import repair_database


def test_reject_null_status_in_application_update(two_users):
    client, alpha, _ = two_users

    create_resp = client.post("/api/applications", headers=alpha, json={
        "company": "Test Co",
        "role": "Engineer",
        "status": "Wishlist",
    })
    assert create_resp.status_code == 200
    app_id = create_resp.json()["id"]

    # Explicit null status must be rejected with 422
    patch_resp = client.patch(f"/api/applications/{app_id}", headers=alpha, json={
        "status": None,
    })
    assert patch_resp.status_code == 422


def test_repair_database_fixes_null_status_and_orphans(two_users):
    client, alpha, _ = two_users
    storage = main.storage

    # Insert raw corrupted records directly into database bypassing validation
    with storage._get_cursor() as cursor:
        cursor.execute(
            storage._format_sql(
                """
                INSERT INTO applications (
                    id, user_id, company, role, status, location, salary, url,
                    required_skills, ats_keywords, date_added, application_date,
                    follow_up_date, notes, best_resume_id, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            ),
            (
                "corrupt-app-1",
                "user-1",
                "Legacy Corp",
                "Developer",
                "",  # Empty status
                "Remote",
                "$100k",
                "https://example.com",
                None,  # Null skills
                None,  # Null keywords
                "2026-01-01",
                "",
                "",
                "",
                None,
                "2026-01-01T00:00:00",
                "2026-01-01T00:00:00",
            ),
        )

        # Create an orphaned attachment
        cursor.execute(
            storage._format_sql(
                """
                INSERT INTO attachments (
                    id, user_id, storage_backend, object_key, original_filename,
                    content_type, size_bytes, deletion_state, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
            ),
            (
                "orphan-att-1",
                "user-1",
                "local",
                "resumes/user-1/orphan.pdf",
                "orphan.pdf",
                "application/pdf",
                1024,
                "active",
                "2026-01-01T00:00:00",
                "2026-01-01T00:00:00",
            ),
        )

        # Create invalid default_follow_up_days in user_settings
        cursor.execute(
            storage._format_sql(
                "INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)"
            ),
            ("user-1", "default_follow_up_days", "999"),
        )

    # 1. Dry run should report findings without mutating
    dry_report = repair_database(storage=storage, object_storage=main.object_storage, dry_run=True)
    assert dry_report["corrupt_applications"] == 1
    assert dry_report["corrupt_settings"] == 1
    assert dry_report["orphaned_attachments"] == 1
    assert dry_report["applied"] is False

    # Check database was not modified yet
    with storage._get_cursor() as cursor:
        cursor.execute(storage._format_sql("SELECT status FROM applications WHERE id = ?"), ("corrupt-app-1",))
        row = cursor.fetchone()
        val = row["status"] if isinstance(row, dict) else row[0]
        assert val == ""

        cursor.execute(storage._format_sql("SELECT value FROM user_settings WHERE user_id = ? AND key = ?"), ("user-1", "default_follow_up_days"))
        row = cursor.fetchone()
        s_val = row["value"] if isinstance(row, dict) else row[0]
        assert s_val == "999"

    # 2. Apply repair
    apply_report = repair_database(storage=storage, object_storage=main.object_storage, dry_run=False)
    assert apply_report["corrupt_applications"] == 1
    assert apply_report["corrupt_settings"] == 1
    assert apply_report["orphaned_attachments"] == 1
    assert apply_report["applied"] is True

    # Check database was fixed
    with storage._get_cursor() as cursor:
        cursor.execute(storage._format_sql("SELECT status, required_skills FROM applications WHERE id = ?"), ("corrupt-app-1",))
        row = cursor.fetchone()
        status_val = row["status"] if isinstance(row, dict) else row[0]
        skills_val = row["required_skills"] if isinstance(row, dict) else row[1]
        assert status_val == "Wishlist"
        assert skills_val == "[]"

        cursor.execute(storage._format_sql("SELECT value FROM user_settings WHERE user_id = ? AND key = ?"), ("user-1", "default_follow_up_days"))
        row = cursor.fetchone()
        s_val = row["value"] if isinstance(row, dict) else row[0]
        assert s_val == "7"

        cursor.execute(storage._format_sql("SELECT deletion_state FROM attachments WHERE id = ?"), ("orphan-att-1",))
        att_row = cursor.fetchone()
        del_state = att_row["deletion_state"] if isinstance(att_row, dict) else att_row[0]
        assert del_state in ("deleted", "orphaned_cleaned")
