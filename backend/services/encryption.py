import base64
import hashlib
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken


class DecryptionError(ValueError):
    """Raised when an encrypted secret fails decryption."""
    pass


_cached_fernet: Optional[Fernet] = None
_cached_key_fingerprint: Optional[str] = None


def _get_raw_key() -> str:
    raw = os.environ.get("SETTINGS_ENCRYPTION_KEY") or os.environ.get("SECRET_KEY")
    if raw and raw.strip():
        return raw.strip()
    app_mode = (os.getenv("APP_MODE") or os.getenv("ENVIRONMENT") or "").lower()
    if app_mode == "test":
        return "test-enc-secret-key-for-automated-tests-32chars"
    try:
        from backend.config import load_config
        return load_config().encryption_secret
    except Exception:
        return "local-fallback-encryption-key-minimum-32-chars-long"


def _get_fernet() -> Fernet:
    global _cached_fernet, _cached_key_fingerprint
    raw = _get_raw_key()
    if _cached_fernet is None or _cached_key_fingerprint != raw:
        digest = hashlib.sha256(raw.encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        _cached_fernet = Fernet(key)
        _cached_key_fingerprint = raw
    return _cached_fernet


def encrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Encrypts a string using AES-128-CBC + HMAC-SHA256 (Fernet).
    Returns versioned ciphertext string 'v1:<token>'.
    """
    if not value or not value.strip():
        return value
    token = _get_fernet().encrypt(value.strip().encode("utf-8")).decode("utf-8")
    return f"v1:{token}"


def decrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Decrypts a Fernet ciphertext token.
    Raises DecryptionError if token is corrupted or wrong key.
    Returns plaintext as-is only if strictly legacy unencrypted text.
    """
    if not value or not value.strip():
        return value

    val = value.strip()
    is_versioned = val.startswith("v1:")
    is_legacy_token = val.startswith("gAAAAA")

    if is_versioned or is_legacy_token:
        raw_token = val[3:] if is_versioned else val
        try:
            return _get_fernet().decrypt(raw_token.encode("utf-8")).decode("utf-8")
        except (InvalidToken, Exception) as e:
            raise DecryptionError(
                "Failed to decrypt sensitive value. The encryption key may have changed or data is corrupted. "
                "Please re-enter the provider key."
            ) from e

    # Value is unencrypted legacy text (e.g. older plain API key)
    return value
