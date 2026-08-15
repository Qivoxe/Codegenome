from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.database import get_session
from backend.app.schemas import (
    AnalysisCreate,
    AnalysisResponse,
    ErrorResponse,
    GraphResponse,
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
    service = AnalysisService(session)
    analysis = await service.get_analysis(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return AnalysisResponse.model_validate(analysis)


@router.get("/analysis/{analysis_id}/impact", response_model=list[ImpactResponse], responses={404: {"model": ErrorResponse}})
async def get_analysis_impact(analysis_id: str, session: AsyncSession = Depends(get_session)) -> list[ImpactResponse]:  # noqa: B008
    service = AnalysisService(session)
    impacts = await service.get_impact_results(analysis_id)
    if not impacts:
        raise HTTPException(status_code=404, detail="Impact results not found")
    return [ImpactResponse.model_validate(i) for i in impacts]


@router.get("/analysis/{analysis_id}/graph", response_model=GraphResponse, responses={404: {"model": ErrorResponse}})
async def get_analysis_graph(analysis_id: str, session: AsyncSession = Depends(get_session)) -> GraphResponse:  # noqa: B008
    service = AnalysisService(session)
    graph_data = await service.get_graph_data(analysis_id)
    if graph_data is None:
        raise HTTPException(status_code=404, detail="Graph data not found")
    nodes, edges = graph_data
    return GraphResponse(analysis_id=analysis_id, nodes=nodes, edges=edges)
