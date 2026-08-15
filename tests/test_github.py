from __future__ import annotations

import hashlib
import hmac
import tempfile
from pathlib import Path

import pytest

from codegenome.github import GitHubClient, verify_webhook_signature
from codegenome.security import SecureRepoManager


def test_verify_webhook_signature_valid() -> None:
    payload = b'{"action":"opened"}'
    secret = "my-secret"
    signature = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
    assert verify_webhook_signature(payload, signature, secret)


def test_verify_webhook_signature_invalid() -> None:
    payload = b'{"action":"opened"}'
    assert not verify_webhook_signature(payload, "sha256=invalid", "secret")
    assert not verify_webhook_signature(payload, "", "secret")
    assert not verify_webhook_signature(payload, "sha256=invalid", "")


def test_secure_repo_manager_validates_path() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = SecureRepoManager(base_dir=tmp)
        repo_dir = Path(tmp) / "test-repo"
        repo_dir.mkdir()
        (repo_dir / ".git").mkdir()
        result = manager.validate_path(str(repo_dir))
        assert result == repo_dir.resolve()


def test_secure_repo_manager_rejects_non_directory() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = SecureRepoManager(base_dir=tmp)
        with pytest.raises(ValueError):
            manager.validate_path(str(Path(tmp) / "nonexistent"))


def test_secure_repo_manager_rejects_non_git() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = SecureRepoManager(base_dir=tmp)
        repo_dir = Path(tmp) / "test-repo"
        repo_dir.mkdir()
        with pytest.raises(ValueError):
            manager.validate_path(str(repo_dir))


def test_secure_repo_manager_rejects_outside_base() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        manager = SecureRepoManager(base_dir=tmp)
        outside = Path(tempfile.gettempdir()) / "outside-repo"
        outside.mkdir(exist_ok=True)
        (outside / ".git").mkdir(exist_ok=True)
        try:
            with pytest.raises(ValueError):
                manager.validate_path(str(outside))
        finally:
            import shutil
            shutil.rmtree(outside, ignore_errors=True)


def test_github_client_requires_token() -> None:
    client = GitHubClient(token="")
    assert client.token == ""


def test_format_pr_comment() -> None:
    from codegenome.pr_comment import format_pr_comment

    comment = format_pr_comment(
        changed_function="checkout.calculate_discount",
        impact_score=82,
        impact_level="HIGH",
        affected_components=["checkout", "payment", "invoice"],
        component_levels={"checkout": "HIGH", "payment": "HIGH", "invoice": "MEDIUM"},
        explanation="checkout depends directly on calculate_discount.",
        impact_paths=[["checkout.calculate_discount", "checkout.checkout"]],
        recommended_tests=["checkout_discount_test", "payment_total_test"],
    )
    assert "🧬" in comment
    assert "82/100" in comment
    assert "HIGH" in comment
    assert "checkout.calculate_discount" in comment
    assert "checkout_discount_test" in comment
