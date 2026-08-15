from __future__ import annotations

from collections import deque
from typing import Any

import networkx as nx

from codegenome.graph import GenomeGraph
from codegenome.models import EdgeType, GraphEdge, GraphNode, ImpactLevel, ImpactReport


class ImpactEngine:
    def __init__(
        self,
        graph: GenomeGraph,
        risk_predictor: Any | None = None,
        llm_explainer: Any | None = None,
        feature_extractor: Any | None = None,
    ) -> None:
        self.graph = graph
        self.risk_predictor = risk_predictor
        self.llm_explainer = llm_explainer
        self.feature_extractor = feature_extractor

    def compute_impact(self, function_qualified_name: str) -> ImpactReport:
        direct_callers = self.graph.get_callers(function_qualified_name)
        all_affected: set[str] = set()
        queue = deque(direct_callers)
        while queue:
            current = queue.popleft()
            if current not in all_affected:
                all_affected.add(current)
                queue.extend(self.graph.get_callers(current))

        transitive_callers = [name for name in all_affected if name not in direct_callers and name != function_qualified_name]
        direct_callers = [name for name in direct_callers if name != function_qualified_name]

        affected_modules = self._count_affected_modules(all_affected)
        max_depth = self._max_dependency_depth(function_qualified_name, all_affected)
        centrality = self._centrality_score(function_qualified_name)

        score = self._compute_score(
            direct_count=len(direct_callers),
            transitive_count=len(transitive_callers),
            affected_modules=affected_modules,
            max_depth=max_depth,
            centrality=centrality,
        )

        level = self._score_to_level(score)
        explanation = self._build_explanation(
            function_qualified_name,
            direct_callers,
            transitive_callers,
            affected_modules,
            max_depth,
            score,
            level,
        )

        impact_paths = self._compute_impact_paths(function_qualified_name, all_affected)

        nodes: list[GraphNode] = []
        edges: list[GraphEdge] = []
        seen_nodes: set[str] = set()

        all_involved = {function_qualified_name, *direct_callers, *transitive_callers}
        for node_id in all_involved:
            if node_id in self.graph.graph.nodes:
                seen_nodes.add(node_id)
                data = self.graph.graph.nodes[node_id]
                nodes.append(
                    GraphNode(
                        id=node_id,
                        type=data.get("type", ""),
                        name=data.get("name", node_id.split(".")[-1]),
                        qualified_name=data.get("qualified_name", node_id),
                        file_path=data.get("file_path", ""),
                        lineno=data.get("lineno", 0),
                    )
                )

        for src in seen_nodes:
            for _, tgt, data in self.graph.graph.out_edges(src, data=True):
                if tgt in seen_nodes and data.get("type") == EdgeType.CALLS.value:
                    edges.append(
                        GraphEdge(
                            source=src,
                            target=tgt,
                            type=EdgeType.CALLS,
                        )
                    )

        affected_components = sorted({node_id.split(".")[0] for node_id in all_affected})

        ml_risk = 0.0
        ml_risk_level = "EXPERIMENTAL"
        if self.risk_predictor and self.feature_extractor:
            try:
                features = self.feature_extractor.extract(function_qualified_name, self.graph)
                pred = self.risk_predictor.predict({
                    "dependency_count": float(features.dependency_count),
                    "downstream_count": float(features.downstream_count),
                    "call_depth": float(features.call_depth),
                    "centrality": float(features.centrality),
                    "historical_changes": float(features.historical_changes),
                    "author_count": float(features.author_count),
                    "lines_changed": float(features.lines_changed),
                    "file_age_days": features.file_age_days,
                    "recent_change_frequency": features.recent_change_frequency,
                    "files_affected": float(features.files_affected),
                    "affected_components": float(features.affected_components),
                })
                ml_risk = pred.get("risk", 0.0)
                ml_risk_level = pred.get("level", "EXPERIMENTAL")
            except (ValueError, KeyError, TypeError):
                pass

        llm_explanation: dict[str, Any] = {}
        if self.llm_explainer:
            try:
                llm_explanation = self.llm_explainer.explain(
                    ExplanationInput(
                        changed_function=function_qualified_name,
                        impact_score=score,
                        impact_level=level.value,
                        affected_components=affected_components,
                        impact_paths=impact_paths,
                        direct_impact=direct_callers,
                        transitive_impact=transitive_callers,
                        risk_factors={"ml_risk": ml_risk},
                    )
                ).model_dump()
            except (ValueError, KeyError, TypeError):
                pass

        return ImpactReport(
            changed_function=function_qualified_name,
            file_path=self.graph.graph.nodes[function_qualified_name].get("file_path", ""),
            direct_impact=direct_callers,
            transitive_impact=transitive_callers,
            impact_score=score,
            impact_level=level,
            explanation=explanation,
            affected_components=affected_components,
            impact_paths=impact_paths,
            nodes=nodes,
            edges=edges,
            ml_risk=ml_risk,
            ml_risk_level=ml_risk_level,
            llm_explanation=llm_explanation,
        )

    def _compute_score(
        self,
        direct_count: int,
        transitive_count: int,
        affected_modules: int,
        max_depth: int,
        centrality: int,
    ) -> int:
        score = 0
        if direct_count > 0:
            score += 25
        if transitive_count > 0:
            score += min(25, transitive_count * 5)
        if affected_modules > 1:
            score += min(20, affected_modules * 5)
        if max_depth >= 3:
            score += min(20, max_depth * 5)
        if centrality > 2:
            score += min(10, centrality * 2)
        return min(100, score)

    def _score_to_level(self, score: int) -> ImpactLevel:
        if score >= 76:
            return ImpactLevel.CRITICAL
        if score >= 51:
            return ImpactLevel.HIGH
        if score >= 26:
            return ImpactLevel.MEDIUM
        return ImpactLevel.LOW

    def _count_affected_modules(self, affected: set[str]) -> int:
        modules: set[str] = set()
        for node_id in affected:
            parts = node_id.split(".")
            if parts:
                modules.add(parts[0])
        return len(modules)

    def _max_dependency_depth(self, start: str, affected: set[str]) -> int:
        max_depth = 0
        for node_id in affected:
            try:
                path_length = nx.shortest_path_length(self.graph.graph, start, node_id)
                max_depth = max(max_depth, path_length)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass
        return max_depth

    def _centrality_score(self, node_id: str) -> int:
        return len(self.graph.get_callers(node_id)) + len(self.graph.get_callees(node_id))

    def _build_explanation(
        self,
        function_name: str,
        direct: list[str],
        transitive: list[str],
        affected_modules: int,
        max_depth: int,
        score: int,
        level: ImpactLevel,
    ) -> str:
        reasons: list[str] = []
        if direct:
            direct_names = ", ".join(f"`{n}`" for n in direct[:5])
            reasons.append(f"`{function_name}` has {len(direct)} direct caller(s): {direct_names}.")
        if transitive:
            trans_names = ", ".join(f"`{n}`" for n in transitive[:5])
            reasons.append(f"{len(transitive)} transitive caller(s) depend on this change: {trans_names}.")
        if affected_modules > 1:
            reasons.append(f"Impact spans {affected_modules} module(s), increasing blast radius.")
        if max_depth >= 3:
            reasons.append(f"Dependency chain depth is {max_depth}, meaning changes cascade deeply.")
        if level == ImpactLevel.CRITICAL:
            reasons.append("Critical impact: many components depend on this function.")
        elif level == ImpactLevel.HIGH:
            reasons.append("High impact: several components will be affected.")
        elif level == ImpactLevel.MEDIUM:
            reasons.append("Medium impact: some components may be affected.")
        else:
            reasons.append("Low impact: few or no components depend on this change.")
        return " ".join(reasons)

    def _compute_impact_paths(self, start: str, affected: set[str]) -> list[list[str]]:
        paths: list[list[str]] = []
        for end in affected:
            try:
                simple_paths = list(nx.all_simple_paths(self.graph.graph, start, end, cutoff=5))
                for p in simple_paths[:3]:
                    if len(p) > 1:
                        paths.append(p)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass
        return paths[:20]


from codegenome.llm import ExplanationInput

__all__ = ["ImpactEngine"]
