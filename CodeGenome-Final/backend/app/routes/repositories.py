from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_session
from backend.app.schemas import (
    ErrorResponse,
    GitHubRepositoryCreate,
    GitHubRepositoryResponse,
    RepositoryCreate,
    RepositoryResponse,
)
from backend.app.services.github_repository_service import GitHubRepositoryService
from backend.app.services.repository_service import RepositoryService

router = APIRouter()


@router.get("/repositories", response_model=list[RepositoryResponse])
async def list_repositories(session: AsyncSession = Depends(get_session)) -> list[RepositoryResponse]:  # noqa: B008
    service = RepositoryService(session)
    repos = await service.list_repositories()
    return [RepositoryResponse.model_validate(r) for r in repos]


@router.post("/repositories", response_model=RepositoryResponse, responses={400: {"model": ErrorResponse}})
async def create_repository(payload: RepositoryCreate, session: AsyncSession = Depends(get_session)) -> RepositoryResponse:  # noqa: B008
    service = RepositoryService(session)
    try:
        repo = await service.create_repository(payload.path)
        return RepositoryResponse.model_validate(repo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/repositories/github", response_model=GitHubRepositoryResponse, responses={400: {"model": ErrorResponse}})
async def register_github_repo(payload: GitHubRepositoryCreate, session: AsyncSession = Depends(get_session)) -> GitHubRepositoryResponse:  # noqa: B008
    service = GitHubRepositoryService(session)
    try:
        repo = await service.register_github_repo(payload.url)
        return GitHubRepositoryResponse.model_validate(repo)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
