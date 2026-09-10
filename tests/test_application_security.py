"""Tests for application update ownership, deduplication, and null validation."""

import pytest
from backend.storage import StorageService


def test_foreign_application_patch_is_not_found(two_users):
    client, alpha, beta = two_users
    owned = client.post(
        "/api/applications",
        headers=beta,
        json={"company": "Acme", "role": "Engineer"},
    ).json()

    for update in ({}, {"notes": "changed"}):
        response = client.patch(
            "/api/applications/" + owned["id"],
            headers=alpha,
            json=update,
        )
        assert response.status_code == 404


def test_registration_does_not_claim_unowned_records(client, tmp_path):
    # Insert legacy record with NULL user_id directly into storage
    storage = StorageService(db_path=str(tmp_path / "legacy.db"), force_sqlite=True)
    with storage._get_cursor() as cursor:
        cursor.execute(
            storage._format_sql(
                "INSERT INTO applications (id, user_id, company, role, status, date_added, created_at, updated_at) "
                "VALUES ('legacy-app-1', NULL, 'Legacy Corp', 'Architect', 'Wishlist', '2026-01-01', '2026-01-01', '2026-01-01')"
            )
        )
        cursor.execute(
            storage._format_sql(
                "INSERT INTO resumes (id, user_id, name, content, created_at, updated_at) "
                "VALUES ('legacy-res-1', NULL, 'Legacy Resume', 'Content', '2026-01-01', '2026-01-01')"
            )
        )

    # Register a new user
    user = storage.create_user("newuser@example.test", "hash", "New User")

    # Verify unowned records are STILL unowned (user_id IS NULL)
    with storage._get_cursor() as cursor:
        cursor.execute(storage._format_sql("SELECT user_id FROM applications WHERE id = 'legacy-app-1'"))
        row = cursor.fetchone()
        assert row["user_id"] is None

        cursor.execute(storage._format_sql("SELECT user_id FROM resumes WHERE id = 'legacy-res-1'"))
        row = cursor.fetchone()
        assert row["user_id"] is None
    storage.close()


def test_application_patch_rejects_null_collections(two_users):
    client, alpha, _ = two_users
    app = client.post(
        "/api/applications",
        headers=alpha,
        json={"company": "Tech Corp", "role": "Developer"},
    ).json()

    for field in ["required_skills", "ats_keywords", "company", "role", "status"]:
        res = client.patch(
            f"/api/applications/{app['id']}",
            headers=alpha,
            json={field: None},
        )
        assert res.status_code == 422, f"Expected 422 for null {field}, got {res.status_code}"

    # Verify listing still succeeds with 200
    list_res = client.get("/api/applications", headers=alpha)
    assert list_res.status_code == 200


def test_distinct_urls_same_company_and_role_are_not_merged(two_users):
    client, alpha, _ = two_users
    # Create two postings with same company and role but different URLs/locations
    app1 = client.post(
        "/api/applications",
        headers=alpha,
        json={
            "company": "Google",
            "role": "Software Engineer",
            "location": "Toronto, ON",
            "url": "https://careers.google.com/jobs/results/11111/?src=Online/Direct",
        },
    ).json()

    app2 = client.post(
        "/api/applications",
        headers=alpha,
        json={
            "company": "Google",
            "role": "Software Engineer",
            "location": "Mountain View, CA",
            "url": "https://careers.google.com/jobs/results/22222/?src=Online/Direct",
        },
    ).json()

    assert app1["id"] != app2["id"], "Distinct job URLs must create separate applications"

    # Both must be present in the application list
    all_apps = client.get("/api/applications", headers=alpha).json()
    app_ids = [a["id"] for a in all_apps]
    assert app1["id"] in app_ids
    assert app2["id"] in app_ids
