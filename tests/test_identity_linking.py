import hashlib
import time
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models import User
from backend.services.auth_service import create_access_token, decode_access_token
from backend.services.email_service import EmailService, FakeEmailTransport


@pytest.fixture
def fake_email_transport(monkeypatch):
    transport = FakeEmailTransport()
    monkeypatch.setattr("backend.routers.auth.email_service", EmailService(transport=transport))
    return transport


def test_password_length_bounds(client):
    # Too short (< 8 chars)
    resp = client.post(
        "/api/auth/register",
        json={"email": "short@example.test", "name": "Short", "password": "short"},
    )
    assert resp.status_code in (400, 422)

    # Too long (> 72 UTF-8 bytes) - 73 ASCII chars
    long_pass = "a" * 73
    resp = client.post(
        "/api/auth/register",
        json={"email": "long@example.test", "name": "Long", "password": long_pass},
    )
    assert resp.status_code == 422
    assert "72" in resp.text

    # Multibyte string exceeding 72 bytes (19 4-byte characters = 76 bytes)
    multibyte_long = "🚀" * 19
    assert len(multibyte_long.encode("utf-8")) == 76
    resp = client.post(
        "/api/auth/register",
        json={"email": "multibyte@example.test", "name": "Emoji", "password": multibyte_long},
    )
    assert resp.status_code == 422

    # Valid multibyte password (15 4-byte characters = 60 bytes, len 15 >= 8)
    multibyte_valid = "🔑" * 15
    assert len(multibyte_valid) >= 8 and len(multibyte_valid.encode("utf-8")) <= 72
    resp = client.post(
        "/api/auth/register",
        json={"email": "valid_emoji@example.test", "name": "Valid Emoji", "password": multibyte_valid},
    )
    assert resp.status_code == 200


def test_third_party_google_identity_cannot_link_by_email(client, monkeypatch):
    from backend.routers.auth import get_storage
    reg = client.post('/api/auth/register', json={
        'email': 'existing@example.test', 'name': 'Owner', 'password': 'OwnerPassword123!',
    })
    storage = get_storage()
    uid = reg.json()['user']['id']
    storage.update_user_verification(uid, verified=True)
    before = storage.get_user_by_email('existing@example.test')
    monkeypatch.setattr('backend.routers.auth.verify_google_id_token', lambda _: {
        'email': 'existing@example.test', 'email_verified': True,
        'sub': 'unlinked-sub', 'aud': 'test-client-id',
    })
    response = client.post('/api/auth/google', json={'credential': 'synthetic'})
    assert response.status_code == 409
    after = storage.get_user_by_email('existing@example.test')
    for key in ('hashed_password', 'google_sub', 'email_verified', 'session_version'):
        assert after[key] == before[key]


def test_google_missing_audience_is_rejected(client, monkeypatch):
    monkeypatch.setattr('backend.routers.auth.verify_google_id_token', lambda _: {
        'email': 'test@gmail.com', 'email_verified': True, 'sub': 'no-aud',
    })
    assert client.post('/api/auth/google', json={'credential': 'synthetic'}).status_code == 401


def test_storage_cannot_overwrite_a_concurrently_linked_identity(client):
    from backend.routers.auth import get_storage
    storage = get_storage()
    user = storage.create_user(email='bound@gmail.com', hashed_password=None, name='Bound',
                               google_sub='first-sub', email_verified=True)
    with pytest.raises(ValueError):
        storage.link_google_identity(user.id, 'second-sub', clear_password=True)
    assert storage.get_user_by_id(user.id).google_sub == 'first-sub'


def test_new_third_party_google_requires_mailbox_proof(client, monkeypatch, fake_email_transport):
    monkeypatch.setattr('backend.routers.auth.verify_google_id_token', lambda _: {
        'email': 'new@example.test', 'email_verified': True, 'sub': 'new-sub', 'aud': 'test-client-id',
    })
    response = client.post('/api/auth/google', json={'credential': 'synthetic'})
    assert response.status_code == 200
    assert not response.json().get('token')
    assert response.json()['requires_verification'] is True
    token = fake_email_transport.get_last_verification_token('new@example.test')
    assert token
    # Repeated sign-in must not grant a session before the application challenge.
    assert not client.post('/api/auth/google', json={'credential': 'synthetic'}).json().get('token')
    assert client.post('/api/auth/verify-email/confirm', json={'token': token}).status_code == 200
    assert client.post('/api/auth/google', json={'credential': 'synthetic'}).json().get('token')


def test_pre_account_hijacking_via_unverified_email_prevented(client, monkeypatch):
    # Step 1: Attacker registers unverified account for victim@example.test
    reg_resp = client.post(
        "/api/auth/register",
        json={"email": "victim@example.test", "name": "Imposter", "password": "AttackerPassword123!"},
    )
    assert reg_resp.status_code == 200
    attacker_token = reg_resp.json().get("token")

    # If attacker obtained a token, test accessing /api/auth/me
    if attacker_token:
        me_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {attacker_token}"})
        assert me_resp.status_code == 200

    # Step 2: Real owner logs in with Google OAuth (email_verified=True)
    google_claims = {
        "email": "victim@example.test",
        "email_verified": True,
        "sub": "google-victim-sub-9999",
        "hd": "example.test",
        "name": "Real Victim",
        "aud": "test-client-id",
    }
    monkeypatch.setattr("backend.routers.auth.verify_google_id_token", lambda token: google_claims)

    google_resp = client.post("/api/auth/google", json={"credential": "valid-mock-token"})
    assert google_resp.status_code == 200
    victim_data = google_resp.json()
    victim_token = victim_data["token"]
    assert victim_token != attacker_token

    # Step 3: Attacker old token must now be rejected (session invalidated)
    if attacker_token:
        old_session_resp = client.get("/api/auth/me", headers={"Authorization": f"Bearer {attacker_token}"})
        assert old_session_resp.status_code == 401

    # Step 4: Attacker can no longer log in with attacker password
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "victim@example.test", "password": "AttackerPassword123!"},
    )
    assert login_resp.status_code in (400, 401)

    # Step 5: Victim session is active and user has email_verified=True and bound google_sub
    victim_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {victim_token}"})
    assert victim_me.status_code == 200
    victim_user = victim_me.json()
    assert victim_user["email_verified"] is True


def test_google_unverified_email_rejected(client, monkeypatch):
    # Google claims with email_verified = False must be rejected
    google_claims = {
        "email": "unverified@example.test",
        "email_verified": False,
        "sub": "google-unverified-sub",
        "name": "Unverified User",
        "aud": "test-client-id",
    }
    monkeypatch.setattr("backend.routers.auth.verify_google_id_token", lambda token: google_claims)

    resp = client.post("/api/auth/google", json={"credential": "mock-unverified-token"})
    assert resp.status_code in (400, 401)
    assert "verified" in resp.text.lower()


def test_google_identity_collision_rejected(client, monkeypatch):
    # User 1 registers with Google under sub-A
    claims_a = {
        "email": "collision@example.test",
        "email_verified": True,
        "sub": "google-sub-alpha",
        "name": "Alpha",
        "aud": "test-client-id",
    }
    monkeypatch.setattr("backend.routers.auth.verify_google_id_token", lambda token: claims_a)
    resp_a = client.post("/api/auth/google", json={"credential": "token-a"})
    assert resp_a.status_code == 200

    # Attacker tries to login as same email with different Google sub-B
    claims_b = {
        "email": "collision@example.test",
        "email_verified": True,
        "sub": "google-sub-beta",
        "name": "Beta Imposter",
        "aud": "test-client-id",
    }
    monkeypatch.setattr("backend.routers.auth.verify_google_id_token", lambda token: claims_b)
    resp_b = client.post("/api/auth/google", json={"credential": "token-b"})
    assert resp_b.status_code in (400, 409)


def test_email_verification_token_lifecycle(client, fake_email_transport):
    # Register user
    reg = client.post(
        "/api/auth/register",
        json={"email": "lifecycle@example.test", "name": "Lifecycle", "password": "LifecyclePass123!"},
    )
    assert reg.status_code == 200

    # Check verification email was sent
    token = fake_email_transport.get_last_verification_token("lifecycle@example.test")
    assert token is not None and len(token) >= 32

    # Confirm verification with valid token
    confirm_resp = client.post("/api/auth/verify-email/confirm", json={"token": token})
    assert confirm_resp.status_code == 200
    assert confirm_resp.json()["success"] is True

    # Replay of the same token must fail
    replay_resp = client.post("/api/auth/verify-email/confirm", json={"token": token})
    assert replay_resp.status_code in (400, 404, 422)


def test_session_version_invalidation_on_password_reset(client, fake_email_transport):
    # Register and verify
    client.post(
        "/api/auth/register",
        json={"email": "reset_user@example.test", "name": "Reset User", "password": "OldPassword123!"},
    )
    token = fake_email_transport.get_last_verification_token("reset_user@example.test")
    client.post("/api/auth/verify-email/confirm", json={"token": token})

    # Log in and get active session
    login_resp = client.post(
        "/api/auth/login",
        json={"email": "reset_user@example.test", "password": "OldPassword123!"},
    )
    assert login_resp.status_code == 200
    old_session_token = login_resp.json()["token"]

    # Verify session works
    assert client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_session_token}"}).status_code == 200

    # Request password reset
    reset_req = client.post("/api/auth/password-reset/request", json={"email": "reset_user@example.test"})
    assert reset_req.status_code == 200
    reset_token = fake_email_transport.get_last_reset_token("reset_user@example.test")
    assert reset_token is not None

    # Confirm password reset
    confirm_reset = client.post(
        "/api/auth/password-reset/confirm",
        json={"token": reset_token, "new_password": "NewSecurePassword123!"},
    )
    assert confirm_reset.status_code == 200

    # Old session MUST now be invalidated (returns 401)
    old_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {old_session_token}"})
    assert old_me.status_code == 401

    # Login with new password works
    new_login = client.post(
        "/api/auth/login",
        json={"email": "reset_user@example.test", "password": "NewSecurePassword123!"},
    )
    assert new_login.status_code == 200
