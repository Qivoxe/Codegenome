from __future__ import annotations

import hmac
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app

REPO_ROOT = Path(__file__).resolve().parent.parent.parent / "sample_repo"


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_create_repository(client: TestClient) -> None:
    response = client.post("/repositories", json={"path": str(REPO_ROOT)})
    assert response.status_code == 200
    data = response.json()
    assert data["path"] == str(REPO_ROOT)
    assert data["name"] == "sample_repo"


def test_list_repositories(client: TestClient) -> None:
    response = client.get("/repositories")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_github_webhook_requires_secret(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GITHUB_WEBHOOK_SECRET", raising=False)
    response = client.post("/github/webhook", json={"action": "opened", "number": 1})
    assert response.status_code == 500


def test_github_webhook_invalid_signature(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "secret")
    response = client.post(
        "/github/webhook",
        json={"action": "opened", "number": 1},
        headers={"X-Hub-Signature-256": "sha256=invalid"},
    )
    assert response.status_code == 403


def test_github_webhook_ignores_non_pr_events(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "secret")
    payload = b'{"action":"opened","number":1,"pull_request":{},"repository":{}}'
    signature = "sha256=" + hmac.new(b"secret", payload, __import__("hashlib").sha256).hexdigest()
    response = client.post(
        "/github/webhook",
        content=payload,
        headers={"X-Hub-Signature-256": signature, "X-GitHub-Event": "push"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
