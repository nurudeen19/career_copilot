"""DELETE /workflow/thread/{thread_id} removes registry row and checkpoints (mocked)."""

from __future__ import annotations

import uuid
from unittest.mock import MagicMock

import pytest
from sqlalchemy import select

from app.models.workflow_thread import WorkflowThread


@pytest.fixture(autouse=True)
def _dispose_langgraph_checkpointer():
    yield
    from app.graph.checkpoint import dispose_checkpointer

    dispose_checkpointer()


def test_delete_workflow_thread_removes_registry_row(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_delete_cp = MagicMock()
    monkeypatch.setattr("app.services.workflow_thread.delete_thread_checkpoints", mock_delete_cp)

    email = "wf-del-owner@example.com"
    assert client.post("/auth/register", json={"name": "U", "email": email, "password": "password12"}).status_code == 200
    login = client.post("/auth/login", json={"email": email, "password": "password12"})
    assert login.status_code == 200
    token = login.json()["access_token"]
    me = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    user_id = uuid.UUID(me.json()["id"])

    tid = str(uuid.uuid4())
    from app.db.session import open_tool_session

    db = open_tool_session()
    try:
        db.add(WorkflowThread(user_id=user_id, thread_id=tid))
        db.commit()
    finally:
        db.close()

    r = client.delete(f"/workflow/thread/{tid}", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 204
    mock_delete_cp.assert_called_once_with(tid)

    db2 = open_tool_session()
    try:
        row = db2.scalar(select(WorkflowThread).where(WorkflowThread.thread_id == tid))
        assert row is None
    finally:
        db2.close()


def test_delete_workflow_thread_forbidden_other_user(
    client,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("app.services.workflow_thread.delete_thread_checkpoints", MagicMock())

    email_a = "wf-del-a@example.com"
    email_b = "wf-del-b@example.com"
    for em in (email_a, email_b):
        assert client.post("/auth/register", json={"name": "U", "email": em, "password": "password12"}).status_code == 200

    login_a = client.post("/auth/login", json={"email": email_a, "password": "password12"})
    token_a = login_a.json()["access_token"]
    me_a = client.get("/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    user_a = uuid.UUID(me_a.json()["id"])

    tid = str(uuid.uuid4())
    from app.db.session import open_tool_session

    db = open_tool_session()
    try:
        db.add(WorkflowThread(user_id=user_a, thread_id=tid))
        db.commit()
    finally:
        db.close()

    login_b = client.post("/auth/login", json={"email": email_b, "password": "password12"})
    token_b = login_b.json()["access_token"]
    r = client.delete(f"/workflow/thread/{tid}", headers={"Authorization": f"Bearer {token_b}"})
    assert r.status_code == 403
