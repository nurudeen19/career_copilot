"""Registration, login, and JWT-protected routes."""

from __future__ import annotations


def test_register_password_over_max_length_rejected(client) -> None:
    body = {"name": "Long", "email": "longpw@example.com", "password": "a" * 513}
    r = client.post("/auth/register", json=body)
    assert r.status_code == 422


def test_register_duplicate_email(client) -> None:
    body = {"name": "One", "email": "dup@example.com", "password": "password12"}
    assert client.post("/auth/register", json=body).status_code == 200
    r2 = client.post("/auth/register", json=body)
    assert r2.status_code == 400
    assert "already" in r2.json()["detail"].lower()


def test_login_invalid_credentials(client) -> None:
    r = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "wrong-pass-1"},
    )
    assert r.status_code == 401


def test_register_login_and_profile(client) -> None:
    email = "user@example.com"
    r = client.post(
        "/auth/register",
        json={"name": "Casey", "email": email, "password": "securepass1"},
    )
    assert r.status_code == 200
    reg = r.json()
    assert reg["email"] == email
    assert reg["name"] == "Casey"
    assert "id" in reg

    r2 = client.post("/auth/login", json={"email": email, "password": "securepass1"})
    assert r2.status_code == 200
    body = r2.json()
    token = body["access_token"]
    assert body["token_type"] == "bearer"
    assert body["user"]["email"] == email
    assert body["user"]["email_verified"] is True

    r_me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r_me.status_code == 200
    assert r_me.json()["email_verified"] is True

    r3 = client.get("/profile", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code == 200
    prof = r3.json()
    assert prof["user_id"] == reg["id"]
    assert prof["profession"] is None


def test_profile_requires_auth(client) -> None:
    r = client.get("/profile")
    assert r.status_code == 401
