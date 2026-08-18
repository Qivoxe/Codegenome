from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str = "ok"
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RepositoryCreate(BaseModel):
    path: str


class RepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    path: str
    name: str
    created_at: datetime
    updated_at: datetime


class AnalysisCreate(BaseModel):
    repository_id: str


class AnalysisResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    repository_id: str
    commit_hash: str
    commit_message: str
    created_at: datetime


class ImpactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    analysis_id: str
    changed_function: str
    file_path: str
    direct_impact: list[str]
    transitive_impact: list[str]
    impact_score: int
    impact_level: str
    explanation: str
    affected_components: list[str]
    impact_paths: list[list[str]]
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]
    ml_risk: int
    ml_risk_level: str
    llm_explanation: dict[str, Any]


class GraphResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    analysis_id: str
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class ErrorResponse(BaseModel):
    detail: str


class GitHubRepositoryCreate(BaseModel):
    url: str


class GitHubRepositoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    owner: str
    name: str
    url: str
    status: str
    created_at: datetime


class AnalysisStatusResponse(BaseModel):
    analysis_id: str
    status: str
    stage: str
    progress: int
    message: str


class FunctionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    qualified_name: str
    file_path: str
    lineno: int
    end_lineno: int | None
    change_type: str


class ImpactAnalysisRequest(BaseModel):
    function_id: str


class ImpactAnalysisResponse(BaseModel):
    function: str
    impact_score: int
    impact_level: str
    affected_components: list[str]
    paths: list[list[str]]
    reasons: list[str]
