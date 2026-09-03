import pytest
from backend.services.encryption import encrypt_value, decrypt_value


def test_encrypt_and_decrypt():
    secret = "nvapi-secr3t-token-xyz-123"
    cipher = encrypt_value(secret)
    assert cipher != secret
    assert cipher.startswith("gAAAAA")

    decrypted = decrypt_value(cipher)
    assert decrypted == secret


def test_decrypt_legacy_plaintext():
    plain = "sk-legacy-unencrypted-key"
    # Legacy unencrypted value should be returned as-is
    res = decrypt_value(plain)
    assert res == plain


def test_empty_value_handling():
    assert encrypt_value("") == ""
    assert encrypt_value(None) is None
    assert decrypt_value("") == ""
    assert decrypt_value(None) is None
