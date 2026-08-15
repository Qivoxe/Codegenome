from __future__ import annotations

import json
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_session
from backend.app.schemas import ErrorResponse
from backend.app.services.analysis_service import AnalysisService
from codegenome.github import GitHubWebhookPayload, verify_webhook_signature

router = APIRouter()


@router.post("/github/webhook", responses={400: {"model": ErrorResponse}, 403: {"model": ErrorResponse}, 401: {"model": ErrorResponse}})
async def github_webhook(request: Request, session: AsyncSession = Depends(get_session)) -> dict[str, Any]:  # noqa: B008
    payload_bytes = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")
    github_webhook_secret = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    if not github_webhook_secret:
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    if not verify_webhook_signature(payload_bytes, signature, github_webhook_secret):
        raise HTTPException(status_code=403, detail="Invalid webhook signature")

    try:
        payload = await request.json()
    except (json.JSONDecodeError, TypeError):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = request.headers.get("X-GitHub-Event", "")
    if event not in {"pull_request", "pull_request_target"}:
        return {"status": "ignored", "event": event}

    action = payload.get("action", "")
    if action not in {"opened", "synchronize", "reopened"}:
        return {"status": "ignored", "action": action}

    pr = payload.get("pull_request", {})
    repo = payload.get("repository", {})
    if not pr or not repo:
        raise HTTPException(status_code=400, detail="Missing pull request or repository data")

    pr_number = pr.get("number")
    head_sha = pr.get("head", {}).get("sha")
    repo_name = repo.get("name")
    owner = repo.get("owner", {}).get("login")
    clone_url = repo.get("clone_url")
    if not all([pr_number, head_sha, repo_name, owner, clone_url]):
        raise HTTPException(status_code=400, detail="Missing required PR fields")

    webhook_payload = GitHubWebhookPayload(
        action=action,
        number=int(pr_number),
        pull_request=pr,
        repository=repo,
    )

    service = AnalysisService(session)
    try:
        analysis = await service.run_analysis_for_pr(
            repo_name=repo_name,
            owner=owner,
            pr_number=int(pr_number),
            head_sha=head_sha,
            clone_url=clone_url,
            webhook_payload=webhook_payload,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return {"status": "analyzed", "analysis_id": analysis.id}
