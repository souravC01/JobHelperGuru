import base64
import hashlib
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken


_cached_fernet: Optional[Fernet] = None
_cached_key_fingerprint: Optional[str] = None


def _get_fernet() -> Fernet:
    global _cached_fernet, _cached_key_fingerprint
    raw = (
        os.environ.get("SETTINGS_ENCRYPTION_KEY")
        or os.environ.get("SECRET_KEY")
        or "jobhelperguru-default-secret-salt-2026"
    )
    if _cached_fernet is None or _cached_key_fingerprint != raw:
        digest = hashlib.sha256(raw.strip().encode("utf-8")).digest()
        key = base64.urlsafe_b64encode(digest)
        _cached_fernet = Fernet(key)
        _cached_key_fingerprint = raw
    return _cached_fernet


def encrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Encrypts a string using AES-128-CBC + HMAC-SHA256 (Fernet).
    Returns the ciphertext string.
    """
    if not value or not value.strip():
        return value
    return _get_fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Decrypts a Fernet ciphertext token.
    If the value is unencrypted plaintext (legacy), returns it as-is for backward compatibility.
    """
    if not value or not value.strip():
        return value
    try:
        return _get_fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Fallback for unencrypted legacy keys
        return value

