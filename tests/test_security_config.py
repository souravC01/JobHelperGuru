import os
import pytest
from backend.config import load_config, AppConfig, InsecureSecretError
from backend.services.encryption import encrypt_value, decrypt_value, DecryptionError


def test_production_fails_without_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_MODE", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "")
    monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", "a" * 32)
    with pytest.raises(InsecureSecretError, match="JWT_SECRET_KEY"):
        load_config()


def test_production_fails_with_default_jwt_secret(monkeypatch):
    monkeypatch.setenv("APP_MODE", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "jobhelperguru-super-secret-dev-jwt-key-2026")
    monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", "a" * 32)
    with pytest.raises(InsecureSecretError, match="default secret"):
        load_config()


def test_production_fails_with_short_secret(monkeypatch):
    monkeypatch.setenv("APP_MODE", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "short-key-12345")
    monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", "a" * 32)
    with pytest.raises(InsecureSecretError, match="at least 32 characters"):
        load_config()


def test_production_fails_without_encryption_secret(monkeypatch):
    monkeypatch.setenv("APP_MODE", "production")
    monkeypatch.setenv("JWT_SECRET_KEY", "b" * 32)
    monkeypatch.delenv("SETTINGS_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    with pytest.raises(InsecureSecretError, match="SETTINGS_ENCRYPTION_KEY"):
        load_config()


def test_local_mode_creates_non_default_secrets(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "local")
    monkeypatch.delenv("JWT_SECRET_KEY", raising=False)
    monkeypatch.delenv("SETTINGS_ENCRYPTION_KEY", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)
    # Inject config dir
    monkeypatch.setenv("LOCAL_SECRETS_DIR", str(tmp_path))

    cfg = load_config()
    assert cfg.app_mode == "local"
    assert len(cfg.jwt_secret_key) >= 32
    assert len(cfg.encryption_secret) >= 32
    assert "jobhelperguru" not in cfg.jwt_secret_key
    assert "jobhelperguru" not in cfg.encryption_secret


def test_decryption_error_on_corrupted_token():
    corrupted = "v1:gAAAAABnSomeCorruptedBase64CiphertextThatCannotBeDecrypted1234567890"
    with pytest.raises(DecryptionError, match="re-enter"):
        decrypt_value(corrupted)


def test_decryption_error_on_wrong_key(monkeypatch):
    import backend.services.encryption as enc_mod
    monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", "first-secret-key-that-is-at-least-32-chars-long")
    enc_mod._cached_fernet = None
    enc_mod._cached_key_fingerprint = None
    ciphertext = encrypt_value("my-api-key-12345")

    # Now switch key
    monkeypatch.setenv("SETTINGS_ENCRYPTION_KEY", "second-secret-key-that-is-at-least-32-chars-long")
    enc_mod._cached_fernet = None
    enc_mod._cached_key_fingerprint = None

    with pytest.raises(DecryptionError, match="re-enter"):
        decrypt_value(ciphertext)


def test_allowed_ai_hosts_includes_defaults_and_custom(monkeypatch):
    from backend.config import DEFAULT_ALLOWED_AI_HOSTS
    assert "api.experientiallabs.ai" in DEFAULT_ALLOWED_AI_HOSTS

    monkeypatch.setenv("APP_MODE", "local")
    monkeypatch.setenv("ALLOWED_AI_HOSTS", "custom-model.org, internal.lab.ai")

    cfg = load_config()
    assert "api.experientiallabs.ai" in cfg.allowed_provider_hosts
    assert "api.openai.com" in cfg.allowed_provider_hosts
    assert "custom-model.org" in cfg.allowed_provider_hosts
    assert "internal.lab.ai" in cfg.allowed_provider_hosts

