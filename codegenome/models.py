from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class NodeType(str, Enum):
    REPOSITORY = "repository"
    MODULE = "module"
    CLASS = "class"
    FUNCTION = "function"
    METHOD = "method"
    IMPORT = "import"


class EdgeType(str, Enum):
    CONTAINS = "contains"
    CALLS = "calls"
    IMPORTS = "imports"
    DEPENDS_ON = "depends_on"


class ImpactLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class FunctionArgument(BaseModel):
    name: str
    kind: str
    default: str | None = None


class GraphNode(BaseModel):
    id: str
    type: NodeType
    name: str
    qualified_name: str
    file_path: str
    lineno: int
    end_lineno: int | None = None
    arguments: list[FunctionArgument] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphEdge(BaseModel):
    source: str
    target: str
    type: EdgeType
    metadata: dict[str, Any] = Field(default_factory=dict)


class GitFileChange(BaseModel):
    file_path: str
    change_type: str
    added_lines: int = 0
    deleted_lines: int = 0
    modified_lines: int = 0


class GitChange(BaseModel):
    commit_hash: str
    message: str
    author: str
    timestamp: str
    files: list[GitFileChange] = Field(default_factory=list)


class ChangedFunction(BaseModel):
    qualified_name: str
    file_path: str
    lineno: int
    end_lineno: int | None
    change_type: str


class ImpactReport(BaseModel):
    changed_function: str
    file_path: str
    direct_impact: list[str] = Field(default_factory=list)
    transitive_impact: list[str] = Field(default_factory=list)
    impact_score: int = Field(default=0, ge=0, le=100)
    impact_level: ImpactLevel = ImpactLevel.LOW
    explanation: str = ""
    affected_components: list[str] = Field(default_factory=list)
    impact_paths: list[list[str]] = Field(default_factory=list)
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
    ml_risk: float = Field(default=0.0, ge=0.0, le=1.0)
    ml_risk_level: str = "EXPERIMENTAL"
    llm_explanation: dict[str, Any] = Field(default_factory=dict)


__all__ = [
    "ChangedFunction",
    "EdgeType",
    "FunctionArgument",
    "GitChange",
    "GitFileChange",
    "GraphEdge",
    "GraphNode",
    "ImpactLevel",
    "ImpactReport",
    "NodeType",
]
