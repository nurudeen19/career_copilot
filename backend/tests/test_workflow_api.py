"""Workflow streaming endpoint auth gate."""

from __future__ import annotations


def test_workflow_stream_requires_authentication(client) -> None:
    r = client.post("/workflow/stream", json={"message": "Hello"})
    assert r.status_code == 401
