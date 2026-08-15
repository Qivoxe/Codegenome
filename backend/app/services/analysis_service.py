from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.models import AnalysisRun, ChangedFunction, ImpactResult, Repository
from codegenome import GenomeGraph, GitEngine, ImpactEngine, SourceParser
from codegenome.github import GitHubClient, GitHubWebhookPayload
from codegenome.llm import LLMExplainer
from codegenome.ml.features import FeatureExtractor
from codegenome.ml.predict import RiskPredictor
from codegenome.pr_comment import format_pr_comment
from codegenome.security import SecureRepoManager


class AnalysisService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.ml_model_path = Path("models") / "xgboost_risk.json"
        self.risk_predictor = RiskPredictor()
        if self.ml_model_path.exists():
            self.risk_predictor.load(str(self.ml_model_path))
        self.llm_explainer = LLMExplainer()
        self.repo_manager = SecureRepoManager()

    async def run_analysis(self, repository_id: str) -> AnalysisRun:
        repo = await self.session.get(Repository, repository_id)
        if repo is None:
            raise ValueError("Repository not found")

        repo_path = self.repo_manager.validate_path(str(repo.path))
        return await self._analyze_path(repo_path, str(repo.id))

    async def run_analysis_for_pr(
        self,
        repo_name: str,
        owner: str,
        pr_number: int,
        head_sha: str,
        clone_url: str,
        webhook_payload: GitHubWebhookPayload,
    ) -> AnalysisRun:
        repo_id = f"{owner}/{repo_name}"
        repo_path = self.repo_manager.clone_repo(repo_id, clone_url, head_sha)
        try:
            analysis = await self._analyze_path(repo_path, repo_id)
            github_token = os.getenv("GITHUB_TOKEN", "")
            if github_token:
                client = GitHubClient(token=github_token)
                comment = self._build_pr_comment(analysis)
                client.post_pr_comment(owner, repo_name, pr_number, comment)
            return analysis
        finally:
            self.repo_manager.cleanup(repo_id)

    async def _analyze_path(self, repo_path: Path, repository_id: str) -> AnalysisRun:
        git_engine = GitEngine(str(repo_path))
        commits = list(git_engine.repo.iter_commits("HEAD"))
        if not commits:
            raise ValueError("No commits found in repository")

        latest_commit = commits[0]
        analysis = AnalysisRun(
            id=str(uuid.uuid4()),
            repository_id=repository_id,
            commit_hash=latest_commit.hexsha,
            commit_message=latest_commit.message.strip(),
        )
        self.session.add(analysis)
        await self.session.flush()

        parser = SourceParser(repo_path)
        parser.parse_repo()

        graph = GenomeGraph()
        graph.build(
            list(parser.modules.values())
            + list(parser.classes.values())
            + list(parser.function_nodes.values())
            + list(parser.method_nodes.values()),
            parser.edges,
        )

        feature_extractor = FeatureExtractor(str(repo_path))
        engine = ImpactEngine(
            graph,
            risk_predictor=self.risk_predictor,
            llm_explainer=self.llm_explainer,
            feature_extractor=feature_extractor,
        )
        changed_files = git_engine.get_changed_files(latest_commit.hexsha)

        for cf in changed_files:
            if not cf.file_path.endswith(".py"):
                continue
            changed_functions = git_engine.get_changed_functions(latest_commit.hexsha, cf.file_path)
            for cf_obj in changed_functions:
                changed_function = ChangedFunction(
                    id=str(uuid.uuid4()),
                    analysis_run_id=analysis.id,
                    qualified_name=cf_obj.qualified_name,
                    file_path=cf_obj.file_path,
                    lineno=cf_obj.lineno,
                    end_lineno=cf_obj.end_lineno,
                    change_type=cf_obj.change_type,
                )
                self.session.add(changed_function)

                report = engine.compute_impact(cf_obj.qualified_name)
                impact = ImpactResult(
                    id=str(uuid.uuid4()),
                    analysis_run_id=analysis.id,
                    changed_function=report.changed_function,
                    file_path=report.file_path,
                    direct_impact=report.direct_impact,
                    transitive_impact=report.transitive_impact,
                    impact_score=report.impact_score,
                    impact_level=report.impact_level.value,
                    explanation=report.explanation,
                    affected_components=report.affected_components,
                    impact_paths=report.impact_paths,
                    nodes=[n.model_dump() for n in report.nodes],
                    edges=[e.model_dump() for e in report.edges],
                    ml_risk=int(report.ml_risk * 100),
                    ml_risk_level=report.ml_risk_level,
                    llm_explanation=report.llm_explanation,
                )
                self.session.add(impact)

        await self.session.commit()
        await self.session.refresh(analysis)
        return analysis

    def _build_pr_comment(self, analysis: AnalysisRun) -> str:
        impacts = []
        for impact in analysis.impact_results:
            component_levels = {}
            for comp in impact.affected_components:
                component_levels[comp] = impact.impact_level
            for path in impact.impact_paths:
                for node in path:
                    comp = node.split(".")[0]
                    if comp not in component_levels:
                        component_levels[comp] = "LOW"
            impacts.append({
                "changed_function": impact.changed_function,
                "impact_score": impact.impact_score,
                "impact_level": impact.impact_level,
                "affected_components": impact.affected_components,
                "component_levels": component_levels,
                "explanation": impact.explanation,
                "impact_paths": impact.impact_paths,
                "recommended_tests": impact.llm_explanation.get("recommended_tests", [])
                if impact.llm_explanation
                else [],
            })

        if not impacts:
            return "🧬 **CODEGENOME IMPACT REPORT**\n\nNo Python changes detected."

        primary = impacts[0]
        return format_pr_comment(
            changed_function=primary["changed_function"],
            impact_score=primary["impact_score"],
            impact_level=primary["impact_level"],
            affected_components=primary["affected_components"],
            component_levels=primary["component_levels"],
            explanation=primary["explanation"],
            impact_paths=primary["impact_paths"],
            recommended_tests=primary["recommended_tests"],
        )

    async def get_analysis(self, analysis_id: str) -> AnalysisRun | None:
        return await self.session.get(AnalysisRun, analysis_id)

    async def get_impact_results(self, analysis_id: str) -> list[ImpactResult]:
        result = await self.session.execute(
            select(ImpactResult).where(ImpactResult.analysis_run_id == analysis_id)
        )
        return list(result.scalars().all())

    async def get_graph_data(self, analysis_id: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]] | None:
        result = await self.session.execute(
            select(ImpactResult).where(ImpactResult.analysis_run_id == analysis_id)
        )
        impacts = result.scalars().all()
        if not impacts:
            return None

        all_nodes: dict[str, Any] = {}
        all_edges: list[dict[str, Any]] = []

        for impact in impacts:
            nodes = impact.nodes
            if isinstance(nodes, list):
                for node in nodes:
                    all_nodes.setdefault(node["id"], node)
            edges = impact.edges
            if isinstance(edges, list):
                for edge in edges:
                    all_edges.extend([edge])

        return list(all_nodes.values()), all_edges
