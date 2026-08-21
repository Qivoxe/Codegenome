from __future__ import annotations

import hashlib
import hmac
import json
from typing import Any

from pydantic import BaseModel, Field


class GitHubWebhookPayload(BaseModel):
    action: str
    number: int
    pull_request: dict[str, Any] = Field(default_factory=dict)
    repository: dict[str, Any] = Field(default_factory=dict)
    sender: dict[str, Any] = Field(default_factory=dict)


class GitHubClient:
    def __init__(self, token: str, base_url: str = "https://api.github.com") -> None:
        self.token = token
        self.base_url = base_url.rstrip("/")

    def post_pr_comment(self, owner: str, repo: str, pr_number: int, body: str) -> dict[str, Any]:
        import urllib.request

        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
        }
        payload = json.dumps({"body": body}).encode("utf-8")
        request = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            if isinstance(data, dict):
                return data
            return {}

    def get_pr_files(self, owner: str, repo: str, pr_number: int) -> list[dict[str, Any]]:
        import urllib.request

        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github.v3+json",
        }
        request = urllib.request.Request(url, headers=headers, method="GET")
        with urllib.request.urlopen(request, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))
            return list(data) if isinstance(data, list) else []


def verify_webhook_signature(payload_bytes: bytes, signature: str, secret: str) -> bool:
    if not signature or not secret:
        return False
    expected = "sha256=" + hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


__all__ = ["GitHubClient", "GitHubWebhookPayload", "verify_webhook_signature"]
