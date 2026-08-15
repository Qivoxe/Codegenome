from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import Repository


class RepositoryService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_repositories(self) -> list[Repository]:
        result = await self.session.execute(select(Repository).order_by(Repository.created_at.desc()))
        return list(result.scalars().all())

    async def get_repository(self, repository_id: str) -> Repository | None:
        return await self.session.get(Repository, repository_id)

    async def create_repository(self, path: str) -> Repository:
        path_obj = Path(path).resolve()
        if not path_obj.exists():
            raise ValueError("Path does not exist")
        if not path_obj.is_dir():
            raise ValueError("Path is not a directory")

        git_dir = path_obj / ".git"
        if not git_dir.exists():
            raise ValueError("Not a git repository")

        name = path_obj.name
        repo = Repository(path=str(path_obj), name=name)
        self.session.add(repo)
        await self.session.commit()
        await self.session.refresh(repo)
        return repo
