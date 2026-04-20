"""Email verification and password reset when Mailtrap is configured (send mocked)."""

from __future__ import annotations

import re
import uuid
import pytest
from starlette.testclient import TestClient

from app.config.settings import get_settings


@pytest.fixture
def client_no_auto_verify(sqlite_database: str, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("AUTH_DEV_AUTO_VERIFY_EMAIL", "false")
    monkeypatch.setenv("MAILTRAP_API_TOKEN", "pytest-mailtrap-token")
    get_settings.cache_clear()
    from tests.app_factory import create_test_app

    with TestClient(create_test_app()) as client:
        yield client


def test_register_verify_then_login(
    client_no_auto_verify: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict] = []

    def fake_send(settings, *, to_email: str, subject: str, text: str, html: str | None = None) -> None:
        captured.append(
            {"to_email": to_email, "subject": subject, "text": text, "html": html},
        )

    monkeypatch.setattr("app.services.auth.send_transactional_email", fake_send)

    email = "verify_me@example.com"
    r = client_no_auto_verify.post(
        "/auth/register",
        json={"name": "Vera", "email": email, "password": "longpass-1"},
    )
    assert r.status_code == 200
    assert r.json()["email_verified"] is False
    assert len(captured) == 1

    body = captured[0]["html"] or captured[0]["text"]
    m_tok = re.search(r"token=([^&\s\"']+)", body)
    m_uid = re.search(r"user_id=([^&\s\"']+)", body)
    assert m_tok and m_uid
    token = m_tok.group(1)
    user_id = m_uid.group(1)
    uuid.UUID(user_id)

    assert client_no_auto_verify.post("/auth/login", json={"email": email, "password": "longpass-1"}).status_code == 403

    rv = client_no_auto_verify.get(f"/auth/verify-email?token={token}&user_id={user_id}")
    assert rv.status_code == 200

    r2 = client_no_auto_verify.post("/auth/login", json={"email": email, "password": "longpass-1"})
    assert r2.status_code == 200


def test_forgot_reset_password(
    client_no_auto_verify: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[dict] = []

    def fake_send(settings, *, to_email: str, subject: str, text: str, html: str | None = None) -> None:
        captured.append({"to_email": to_email, "subject": subject, "text": text, "html": html})

    monkeypatch.setattr("app.services.auth.send_transactional_email", fake_send)

    email = "reset_me@example.com"
    assert (
        client_no_auto_verify.post(
            "/auth/register",
            json={"name": "Rex", "email": email, "password": "original-1"},
        ).status_code
        == 200
    )
    html = captured[-1]["html"] or captured[-1]["text"]
    m_tok = re.search(r"token=([^&\s\"']+)", html)
    m_uid = re.search(r"user_id=([^&\s\"']+)", html)
    token, user_id = m_tok.group(1), m_uid.group(1)

    client_no_auto_verify.get(f"/auth/verify-email?token={token}&user_id={user_id}")
    captured.clear()

    assert client_no_auto_verify.post("/auth/forgot-password", json={"email": email}).status_code == 200
    assert len(captured) == 1
    body = captured[0]["html"] or captured[0]["text"]
    m_tok = re.search(r"token=([^&\s\"']+)", body)
    m_uid = re.search(r"user_id=([^&\s\"']+)", body)
    reset_tok, reset_uid = m_tok.group(1), m_uid.group(1)

    rp = client_no_auto_verify.post(
        "/auth/reset-password",
        json={"user_id": reset_uid, "token": reset_tok, "password": "replaced-22"},
    )
    assert rp.status_code == 200

    assert client_no_auto_verify.post("/auth/login", json={"email": email, "password": "original-1"}).status_code == 401
    assert client_no_auto_verify.post("/auth/login", json={"email": email, "password": "replaced-22"}).status_code == 200
