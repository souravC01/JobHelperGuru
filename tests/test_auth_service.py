import pytest
from backend.services.auth_service import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)


def test_password_hashing_and_verification():
    raw_pass = "SuperSecret123!"
    hashed = hash_password(raw_pass)
    assert hashed != raw_pass
    assert verify_password(raw_pass, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_token_generation_and_decoding():
    token = create_access_token(
        user_id="usr-12345",
        email="test@example.com",
        name="Test User",
    )
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "usr-12345"
    assert payload["email"] == "test@example.com"
    assert payload["name"] == "Test User"


def test_invalid_jwt_decoding():
    assert decode_access_token("invalid.token.payload") is None
