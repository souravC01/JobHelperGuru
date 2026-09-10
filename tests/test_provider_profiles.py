import pytest
from fastapi.testclient import TestClient

from backend.main import app


def get_user_headers(client, email, password="Password123!", name="Profile Tester"):
    res = client.post(
        "/api/auth/register",
        json={"email": email, "password": password, "name": name},
    )
    if res.status_code == 200 and res.json().get("token"):
        token = res.json()["token"]
    else:
        # Try login
        res_login = client.post(
            "/api/auth/login",
            json={"email": email, "password": password},
        )
        token = res_login.json()["token"]
    return {"Authorization": f"Bearer {token}"}


def test_settings_and_profiles_never_leak_plaintext_secret_in_get(client):
    headers = get_user_headers(client, "leak_test@example.test")
    secret_key = "sk-super-secret-production-key-9876"

    # Create profile with secret key
    create_resp = client.post(
        "/api/settings/profiles",
        headers=headers,
        json={
            "name": "OpenAI Production",
            "api_base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4o",
            "api_key": secret_key,
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200, create_resp.text
    profile = create_resp.json()
    profile_id = profile["id"]

    # Creation response must NOT return the full plaintext secret
    assert secret_key not in str(create_resp.content)
    assert profile["has_api_key"] is True
    assert profile["key_suffix"] == "9876"

    # GET /api/settings/profiles must NOT contain secret
    list_resp = client.get("/api/settings/profiles", headers=headers)
    assert list_resp.status_code == 200
    assert secret_key not in str(list_resp.content)

    # GET /api/settings/profiles/{id} must NOT contain secret
    single_resp = client.get(f"/api/settings/profiles/{profile_id}", headers=headers)
    assert single_resp.status_code == 200
    assert secret_key not in str(single_resp.content)

    # GET /api/settings must NOT contain secret
    settings_resp = client.get("/api/settings", headers=headers)
    assert settings_resp.status_code == 200
    assert secret_key not in str(settings_resp.content)


def test_profile_owner_isolation(client):
    headers_a = get_user_headers(client, "owner_a@example.test")
    headers_b = get_user_headers(client, "owner_b@example.test")

    # User A creates a profile
    create_resp = client.post(
        "/api/settings/profiles",
        headers=headers_a,
        json={
            "name": "User A Profile",
            "api_base_url": "https://api.groq.com/v1",
            "model_name": "llama-3.3-70b",
            "api_key": "gsk-user-a-secret",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    profile_id = create_resp.json()["id"]

    # User B attempts to read User A's profile -> 404
    assert client.get(f"/api/settings/profiles/{profile_id}", headers=headers_b).status_code == 404

    # User B attempts to update User A's profile -> 404
    assert client.patch(
        f"/api/settings/profiles/{profile_id}",
        headers=headers_b,
        json={"name": "Hacked Profile"},
    ).status_code == 404

    # User B attempts to activate User A's profile -> 404
    assert client.post(
        f"/api/settings/profiles/{profile_id}/activate",
        headers=headers_b,
    ).status_code == 404

    # User B attempts to delete User A's profile -> 404
    assert client.delete(
        f"/api/settings/profiles/{profile_id}",
        headers=headers_b,
    ).status_code == 404


def test_omitted_replacement_key_preserves_existing_secret(client):
    headers = get_user_headers(client, "preserve_key@example.test")

    # Create profile with key
    create_resp = client.post(
        "/api/settings/profiles",
        headers=headers,
        json={
            "name": "Initial Name",
            "api_base_url": "https://openrouter.ai/api/v1",
            "model_name": "anthropic/claude-3.5-sonnet",
            "api_key": "sk-or-initial-key-4321",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    profile_id = create_resp.json()["id"]
    assert create_resp.json()["has_api_key"] is True

    # Update only the name without providing api_key
    update_resp = client.patch(
        f"/api/settings/profiles/{profile_id}",
        headers=headers,
        json={"name": "Updated Name"},
    )
    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["name"] == "Updated Name"
    # Secret key must still be preserved
    assert data["has_api_key"] is True
    assert data["key_suffix"] == "4321"


def test_active_profile_deletion_is_transactional_and_selects_offline_mode(client):
    headers = get_user_headers(client, "active_delete@example.test")

    # Create and activate profile
    create_resp = client.post(
        "/api/settings/profiles",
        headers=headers,
        json={
            "name": "Active To Delete",
            "api_base_url": "https://api.deepseek.com/v1",
            "model_name": "deepseek-chat",
            "api_key": "sk-deepseek-key-1111",
            "is_active": True,
        },
    )
    assert create_resp.status_code == 200
    profile_id = create_resp.json()["id"]

    # Verify settings indicate active online profile
    settings_before = client.get("/api/settings", headers=headers).json()
    assert settings_before["active_profile_id"] == profile_id
    assert settings_before["use_offline_mode"] is False

    # Delete the active profile
    del_resp = client.delete(f"/api/settings/profiles/{profile_id}", headers=headers)
    assert del_resp.status_code == 200

    # Settings must atomically switch to offline mode and clear active_profile_id
    settings_after = client.get("/api/settings", headers=headers).json()
    assert settings_after["active_profile_id"] is None
    assert settings_after["use_offline_mode"] is True

    # Profile must be gone from profile list
    list_after = client.get("/api/settings/profiles", headers=headers).json()
    assert not any(p["id"] == profile_id for p in list_after)


def test_settings_validation_rejects_invalid_follow_up_days(client):
    headers = get_user_headers(client, "settings_bounds@example.test")

    # Reject follow up days < 1
    resp_low = client.post("/api/settings", headers=headers, json={"default_follow_up_days": 0})
    assert resp_low.status_code == 422

    # Reject follow up days > 90
    resp_high = client.post("/api/settings", headers=headers, json={"default_follow_up_days": 91})
    assert resp_high.status_code == 422

    # Accept follow up days in range [1, 90]
    resp_ok = client.post("/api/settings", headers=headers, json={"default_follow_up_days": 14})
    assert resp_ok.status_code == 200
    assert resp_ok.json()["default_follow_up_days"] == 14


def test_legacy_settings_keys_auto_migrated_to_profiles(client):
    from backend.main import storage
    from backend.services.encryption import encrypt_value

    email = "legacy_user@example.test"
    headers = get_user_headers(client, email)

    user = storage.get_user_by_email(email)
    assert user is not None

    # Simulate legacy database state: keys stored in user_settings table
    user_id = user["id"] if isinstance(user, dict) else user.id
    with storage._get_cursor() as cursor:
        cursor.execute(
            storage._format_sql("INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)"),
            (user_id, "api_key", encrypt_value("sk-legacy-key-9999")),
        )
        cursor.execute(
            storage._format_sql("INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)"),
            (user_id, "api_base_url", "https://api.legacy.test/v1"),
        )
        cursor.execute(
            storage._format_sql("INSERT INTO user_settings (user_id, key, value) VALUES (?, ?, ?)"),
            (user_id, "model_name", "legacy-model"),
        )

    # Calling GET /api/settings/profiles must auto-migrate the legacy key into provider_profiles
    list_resp = client.get("/api/settings/profiles", headers=headers)
    assert list_resp.status_code == 200
    profiles = list_resp.json()
    assert len(profiles) == 1
    assert profiles[0]["name"] == "legacy-model"
    assert profiles[0]["api_base_url"] == "https://api.legacy.test/v1"
    assert profiles[0]["model_name"] == "legacy-model"
    assert profiles[0]["has_api_key"] is True
    assert profiles[0]["key_suffix"] == "9999"
    assert profiles[0]["is_active"] is True

    # Confirm settings now reflects active_profile_id
    settings_resp = client.get("/api/settings", headers=headers).json()
    assert settings_resp["active_profile_id"] == profiles[0]["id"]

