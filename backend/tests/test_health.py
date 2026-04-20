"""Public health endpoint."""

from __future__ import annotations


def test_health_reports_database_ok_and_prompt_guard_not_ready(client) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["version"]
    assert data["app_name"] == "Career Copilot"
    assert data["checks"]["database"]["status"] == "ok"
    assert data["checks"]["database"]["detail"] is None
    assert data["checks"]["prompt_guard"]["status"] == "not_ready"
    assert data["status"] == "degraded"
