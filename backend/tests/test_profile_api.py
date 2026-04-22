"""Profile PATCH behaviour."""

from __future__ import annotations


def _token(client, email: str = "patch@example.com") -> str:
    client.post(
        "/auth/register",
        json={"name": "P", "email": email, "password": "password12"},
    )
    r = client.post("/auth/login", json={"email": email, "password": "password12"})
    return r.json()["access_token"]


def test_patch_profile(client) -> None:
    token = _token(client)
    r = client.patch(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "profession": "Backend engineer",
            "career_goal": "Move into platform leadership",
            "location": "Berlin",
            "summary": "10 years in APIs",
        },
    )
    assert r.status_code == 200
    data = r.json()
    assert data["profession"] == "Backend engineer"
    assert data["career_goal"] == "Move into platform leadership"
    assert data["location"] == "Berlin"
    assert data["willing_to_relocate"] is None


def test_patch_profile_salary_and_relocate(client) -> None:
    token = _token(client, email="nums@example.com")
    r = client.patch(
        "/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"current_salary": 120000, "salary_target": 150000, "willing_to_relocate": True},
    )
    assert r.status_code == 200
    assert r.json()["current_salary"] == 120000
    assert r.json()["salary_target"] == 150000
    assert r.json()["willing_to_relocate"] is True
