import pytest
from backend.storage import StorageService
from backend.models import SettingsUpdate


def test_api_key_encrypted_at_rest(tmp_path):
    db_file = str(tmp_path / "test_enc.db")
    storage = StorageService(db_path=db_file, force_sqlite=True)

    test_user_id = "usr-enc-123"
    plain_api_key = "nvapi-very-secret-test-key-999"

    # 1. Update settings with plain API key
    storage.update_settings(
        SettingsUpdate(api_key=plain_api_key, model_name="nvidia/nemotron-4-340b-instruct"),
        user_id=test_user_id,
    )

    # 2. Inspect raw database row in user_settings table
    with storage._get_cursor() as cursor:
        cursor.execute("SELECT value FROM user_settings WHERE user_id = ? AND key = 'api_key'", (test_user_id,))
        raw_row = cursor.fetchone()
        assert raw_row is not None
        raw_db_value = raw_row["value"]

    # Must NOT be stored in plain text!
    assert raw_db_value != plain_api_key
    assert raw_db_value.startswith("gAAAAA")

    # 3. get_settings must return decrypted API key
    retrieved = storage.get_settings(user_id=test_user_id)
    assert retrieved.api_key == plain_api_key
    assert retrieved.model_name == "nvidia/nemotron-4-340b-instruct"


def test_legacy_plaintext_backward_compatibility(tmp_path):
    db_file = str(tmp_path / "test_legacy.db")
    storage = StorageService(db_path=db_file, force_sqlite=True)

    test_user_id = "usr-legacy-456"
    legacy_key = "sk-legacy-unencrypted-token-888"

    # Insert raw unencrypted value directly into DB
    with storage._get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO user_settings (user_id, key, value) VALUES (?, 'api_key', ?)",
            (test_user_id, legacy_key),
        )

    # Should gracefully return the unencrypted key
    retrieved = storage.get_settings(user_id=test_user_id)
    assert retrieved.api_key == legacy_key
