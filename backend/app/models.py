from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.sqlite import JSON
from sqlalchemy.orm import relationship

from backend.app.database import Base


class Repository(Base):
    __tablename__ = "repositories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    path = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    analysis_runs = relationship("AnalysisRun", back_populates="repository", cascade="all, delete-orphan")


class AnalysisRun(Base):
    __tablename__ = "analysis_runs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    repository_id = Column(String, ForeignKey("repositories.id"), nullable=False)
    commit_hash = Column(String, nullable=False)
    commit_message = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    repository = relationship("Repository", back_populates="analysis_runs")
    changed_functions = relationship("ChangedFunction", back_populates="analysis_run", cascade="all, delete-orphan")
    impact_results = relationship("ImpactResult", back_populates="analysis_run", cascade="all, delete-orphan")


class ChangedFunction(Base):
    __tablename__ = "changed_functions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    qualified_name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    lineno = Column(Integer, nullable=False)
    end_lineno = Column(Integer, nullable=True)
    change_type = Column(String, nullable=False)

    analysis_run = relationship("AnalysisRun", back_populates="changed_functions")


class ImpactResult(Base):
    __tablename__ = "impact_results"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    analysis_run_id = Column(String, ForeignKey("analysis_runs.id"), nullable=False)
    changed_function = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    direct_impact = Column(JSON, nullable=False, default=list)
    transitive_impact = Column(JSON, nullable=False, default=list)
    impact_score = Column(Integer, nullable=False, default=0)
    impact_level = Column(String, nullable=False, default="LOW")
    explanation = Column(Text, nullable=False, default="")
    affected_components = Column(JSON, nullable=False, default=list)
    impact_paths = Column(JSON, nullable=False, default=list)
    nodes = Column(JSON, nullable=False, default=list)
    edges = Column(JSON, nullable=False, default=list)
    ml_risk = Column(Integer, nullable=False, default=0)
    ml_risk_level = Column(String, nullable=False, default="EXPERIMENTAL")
    llm_explanation = Column(JSON, nullable=False, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    analysis_run = relationship("AnalysisRun", back_populates="impact_results")
