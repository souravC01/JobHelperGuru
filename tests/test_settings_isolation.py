import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.storage import StorageService
from backend.models import SettingsUpdate

client = TestClient(app)


def test_new_user_settings_never_inherit_global_settings(tmp_path):
    db_path = str(tmp_path / "test_isolation.db")
    storage = StorageService(db_path=db_path)

    # 1. Global settings configured with a secret admin key
    storage.update_settings(
        SettingsUpdate(
            api_key="secret_admin_openrouter_key",
            saved_keys='[{"id":"admin-key","name":"Admin Key","api_key":"secret_admin_openrouter_key"}]',
            model_name="openrouter/anthropic/claude-3.5-sonnet",
        ),
        user_id=None,
    )

    # Unauthenticated / single-user get_settings(user_id=None) returns the global key
    global_settings = storage.get_settings(user_id=None)
    assert global_settings.api_key == "secret_admin_openrouter_key"
    assert "Admin Key" in global_settings.saved_keys

    # 2. Create a new user
    new_user = storage.create_user(
        email="newbie@example.com",
        hashed_password="hash",
        name="Newbie User",
        provider="email",
    )

    # 3. New user's settings must be completely blank and NEVER inherit admin's key
    user_settings = storage.get_settings(user_id=new_user.id)
    assert user_settings.api_key == ""
    assert user_settings.saved_keys == "[]"
    assert user_settings.use_offline_mode is False

    # 4. New user sets their own key
    storage.update_settings(
        SettingsUpdate(
            api_key="newbie_custom_gemini_key",
            model_name="gemini-2.0-flash",
            use_offline_mode=False,
        ),
        user_id=new_user.id,
    )

    # 5. Verify isolation
    updated_user = storage.get_settings(user_id=new_user.id)
    assert updated_user.api_key == "newbie_custom_gemini_key"

    # Global settings remained untouched
    assert storage.get_settings(user_id=None).api_key == "secret_admin_openrouter_key"

    # Another second new user also receives completely blank settings
    user2 = storage.create_user(
        email="user2@example.com",
        hashed_password="hash",
        name="User Two",
        provider="email",
    )
    user2_settings = storage.get_settings(user_id=user2.id)
    assert user2_settings.api_key == ""
    assert user2_settings.saved_keys == "[]"
    assert user2_settings.use_offline_mode is False


def test_auth_endpoints_is_new_user_flag():
    import uuid
    # Register new user
    reg_email = f"signup_{uuid.uuid4().hex[:8]}@example.com"
    reg_res = client.post(
        "/api/auth/register",
        json={"email": reg_email, "password": "Password123!", "name": "Brand New"},
    )
    assert reg_res.status_code == 200
    reg_data = reg_res.json()
    assert reg_data["is_new_user"] is True

    # Login with existing user
    login_res = client.post(
        "/api/auth/login",
        json={"email": reg_email, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["is_new_user"] is False
