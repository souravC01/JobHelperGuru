import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_auth_register_login_and_me():
    # 1. Register new user
    reg_payload = {
        "email": "fresh_user@example.com",
        "password": "Password123!",
        "name": "Fresh User",
    }
    res_reg = client.post("/api/auth/register", json=reg_payload)
    assert res_reg.status_code == 200
    data_reg = res_reg.json()
    assert "token" in data_reg
    assert data_reg["user"]["email"] == "fresh_user@example.com"
    token = data_reg["token"]

    # 2. Access /api/auth/me with Bearer token
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["email"] == "fresh_user@example.com"

    # 3. Access without token should return 401
    res_no_auth = client.get("/api/auth/me")
    assert res_no_auth.status_code == 401

    # 4. Login with registered user
    login_payload = {
        "email": "fresh_user@example.com",
        "password": "Password123!",
    }
    res_login = client.post("/api/auth/login", json=login_payload)
    assert res_login.status_code == 200
    assert "token" in res_login.json()

    # 5. Login with wrong password
    res_bad = client.post(
        "/api/auth/login",
        json={"email": "fresh_user@example.com", "password": "WrongPassword!"},
    )
    assert res_bad.status_code == 401
