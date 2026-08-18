from __future__ import annotations

import asyncio
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_session
from backend.app.models import AnalysisRun, ChangedFunction, ImpactResult
from backend.app.schemas import (
    AnalysisCreate,
    AnalysisResponse,
    AnalysisStatusResponse,
    ErrorResponse,
    FunctionResponse,
    GraphResponse,
    ImpactAnalysisRequest,
    ImpactAnalysisResponse,
    ImpactResponse,
)
from backend.app.services.analysis_service import AnalysisService

router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse, responses={400: {"model": ErrorResponse}})
async def analyze_repository(payload: AnalysisCreate, session: AsyncSession = Depends(get_session)) -> AnalysisResponse:  # noqa: B008
    service = AnalysisService(session)
    try:
        analysis = await service.run_analysis(payload.repository_id)
        return AnalysisResponse.model_validate(analysis)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse, responses={404: {"model": ErrorResponse}})
async def get_analysis(analysis_id: str, session: AsyncSession = Depends(get_session)) -> AnalysisResponse:  # noqa: B008
    result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis)


@router.get("/analysis/{analysis_id}/status", response_model=AnalysisStatusResponse, responses={404: {"model": ErrorResponse}})
async def get_analysis_status(analysis_id: str, session: AsyncSession = Depends(get_session)) -> AnalysisStatusResponse:  # noqa: B008
    result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisStatusResponse(
        analysis_id=analysis.id,
        status=analysis.status,
        stage=analysis.stage,
        progress=analysis.progress,
        message=analysis.message,
    )


@router.get("/analysis/{analysis_id}/functions", response_model=list[FunctionResponse], responses={404: {"model": ErrorResponse}})
async def get_analysis_functions(analysis_id: str, session: AsyncSession = Depends(get_session)) -> list[FunctionResponse]:  # noqa: B008
    result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    funcs_result = await session.execute(
        select(ChangedFunction).where(ChangedFunction.analysis_run_id == analysis_id)
    )
    funcs = funcs_result.scalars().all()
    return [FunctionResponse.model_validate(f) for f in funcs]


@router.post("/analysis/{analysis_id}/impact", response_model=ImpactAnalysisResponse, responses={404: {"model": ErrorResponse}, 400: {"model": ErrorResponse}})
async def analyze_function_impact(analysis_id: str, payload: ImpactAnalysisRequest, session: AsyncSession = Depends(get_session)) -> ImpactAnalysisResponse:  # noqa: B008
    result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    service = AnalysisService(session)
    try:
        report = await service.compute_impact_for_function(analysis_id, payload.function_id)
        return ImpactAnalysisResponse(
            function=report.changed_function,
            impact_score=report.impact_score,
            impact_level=report.impact_level.value,
            affected_components=report.affected_components,
            paths=report.impact_paths,
            reasons=[report.explanation],
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/analysis/{analysis_id}/impact", response_model=list[ImpactResponse], responses={404: {"model": ErrorResponse}})
async def get_analysis_impact(analysis_id: str, session: AsyncSession = Depends(get_session)) -> list[ImpactResponse]:  # noqa: B008
    result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    service = AnalysisService(session)
    impacts = await service.get_impact_results(analysis_id)
    if not impacts:
        raise HTTPException(status_code=404, detail="Impact results not found")
    return [ImpactResponse.model_validate(i) for i in impacts]


@router.get("/analysis/{analysis_id}/graph", response_model=GraphResponse, responses={404: {"model": ErrorResponse}})
async def get_analysis_graph(analysis_id: str, session: AsyncSession = Depends(get_session)) -> GraphResponse:  # noqa: B008
    result = await session.execute(select(AnalysisRun).where(AnalysisRun.id == analysis_id))
    analysis = result.scalar_one_or_none()
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    service = AnalysisService(session)
    graph_data = await service.get_graph_data(analysis_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail="Graph data not found")
    nodes, edges = graph_data
    return GraphResponse(analysis_id=analysis_id, nodes=nodes, edges=edges)
