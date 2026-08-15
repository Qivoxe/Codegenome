from __future__ import annotations

import tempfile
from pathlib import Path

from codegenome.git_engine import GitEngine


class SecureRepoManager:
    def __init__(self, base_dir: str | None = None) -> None:
        if base_dir is None:
            base_dir = tempfile.gettempdir()
        self.base_dir = Path(base_dir).resolve()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def clone_repo(self, repo_id: str, clone_url: str, ref: str) -> Path:
        safe_name = self._safe_repo_name(repo_id)
        target = self.base_dir / f"codegenome-{safe_name}"
        target.mkdir(parents=True, exist_ok=True)

        git_dir = target / ".git"
        if git_dir.exists():
            try:
                git = GitEngine(str(target))
                git.repo.git.fetch("origin", ref, depth=1)
                git.repo.git.reset("--hard", f"origin/{ref}", quiet=True)
                return target
            except (ValueError, RuntimeError):
                pass

        import subprocess
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", "--branch", ref, clone_url, str(target)],
                check=True,
                capture_output=True,
            )
        except subprocess.CalledProcessError as exc:
            raise ValueError(f"Failed to clone repository: {exc.stderr.decode('utf-8', errors='replace')}") from exc

        return target

    def cleanup(self, repo_id: str) -> None:
        safe_name = self._safe_repo_name(repo_id)
        target = self.base_dir / f"codegenome-{safe_name}"
        if target.exists():
            import shutil
            shutil.rmtree(target, ignore_errors=True)

    def _safe_repo_name(self, repo_id: str) -> str:
        import hashlib
        return hashlib.sha256(repo_id.encode("utf-8")).hexdigest()[:16]

    def validate_path(self, path: str) -> Path:
        p = Path(path).resolve()
        if not p.is_dir():
            raise ValueError("Repository path must be a directory")
        if not (p / ".git").exists():
            raise ValueError("Not a git repository")
        return p


__all__ = ["SecureRepoManager"]
