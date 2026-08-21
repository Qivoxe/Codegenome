from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Repository
from codegenome.security import SecureRepoManager

CLONE_TIMEOUT_SECONDS = 60

def _rmtree_safe(path: Path) -> None:
    if not path.exists():
        return
    if subprocess.os.name == "nt":
        subprocess.run(["cmd", "/c", "rmdir", "/s", "/q", str(path)], check=False, capture_output=True)
    else:
        shutil.rmtree(path, ignore_errors=True)


class GitHubRepositoryService:
    GITHUB_URL_PATTERN = re.compile(r"https?://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.repo_manager = SecureRepoManager()

    def parse_github_url(self, url: str) -> tuple[str, str]:
        url = url.strip()
        if not url:
            raise ValueError("Repository URL is required")
        match = self.GITHUB_URL_PATTERN.match(url)
        if not match:
            raise ValueError("Invalid GitHub repository URL. Expected format: https://github.com/owner/repository")
        owner = match.group(1)
        repo = match.group(2).removesuffix(".git")
        if not owner or not repo:
            raise ValueError("Invalid GitHub repository URL")
        return owner, repo

    async def register_github_repo(self, url: str) -> Repository:
        owner, name = self.parse_github_url(url)
        clone_url = f"https://github.com/{owner}/{name}.git"
        repo_id = f"github:{owner}/{name}"
        safe_name = f"{owner}-{name}"
        workspace = Path(tempfile.gettempdir()) / "codegenome-workspace" / safe_name

        existing = await self.session.get(Repository, repo_id)
        if existing:
            if not workspace.exists():
                _rmtree_safe(workspace)
                try:
                    subprocess.run(
                        ["git", "clone", clone_url, str(workspace)],
                        check=True,
                        capture_output=True,
                        timeout=CLONE_TIMEOUT_SECONDS,
                    )
                except subprocess.CalledProcessError as exc:
                    _rmtree_safe(workspace)
                    raise ValueError(f"Failed to clone repository: {exc.stderr.decode('utf-8', errors='replace')}") from exc
            return existing

        _rmtree_safe(workspace)
        try:
            subprocess.run(
                ["git", "clone", clone_url, str(workspace)],
                check=True,
                capture_output=True,
                timeout=CLONE_TIMEOUT_SECONDS,
            )
        except subprocess.CalledProcessError as exc:
            _rmtree_safe(workspace)
            raise ValueError(f"Failed to clone repository: {exc.stderr.decode('utf-8', errors='replace')}") from exc
        repo = Repository(
            id=repo_id,
            path=str(workspace),
            name=name,
            owner=owner,
            url=url,
            status="ready",
        )
        self.session.add(repo)
        await self.session.commit()
        await self.session.refresh(repo)
        return repo

    async def get_repository(self, repository_id: str) -> Repository | None:
        return await self.session.get(Repository, repository_id)
