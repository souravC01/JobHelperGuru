import base64
import hashlib
import os
from typing import Optional
from cryptography.fernet import Fernet, InvalidToken


def _get_fernet_key() -> bytes:
    raw = (
        os.environ.get("SETTINGS_ENCRYPTION_KEY")
        or os.environ.get("SECRET_KEY")
        or "jobhelperguru-default-secret-salt-2026"
    )
    # Generate 32-byte digest via SHA-256 and base64 urlsafe encode for Fernet
    digest = hashlib.sha256(raw.strip().encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


def encrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Encrypts a string using AES-128-CBC + HMAC-SHA256 (Fernet).
    Returns the ciphertext string.
    """
    if not value or not value.strip():
        return value
    fernet = Fernet(_get_fernet_key())
    return fernet.encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: Optional[str]) -> Optional[str]:
    """
    Decrypts a Fernet ciphertext token.
    If the value is unencrypted plaintext (legacy), returns it as-is for backward compatibility.
    """
    if not value or not value.strip():
        return value
    try:
        fernet = Fernet(_get_fernet_key())
        return fernet.decrypt(value.encode("utf-8")).decode("utf-8")
    except (InvalidToken, Exception):
        # Fallback for unencrypted legacy keys
        return value
