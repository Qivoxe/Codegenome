from __future__ import annotations

import networkx as nx

from codegenome.models import EdgeType, GraphEdge, GraphNode


class GenomeGraph:
    def __init__(self) -> None:
        self.graph = nx.MultiDiGraph()

    def add_node(self, node: GraphNode) -> None:
        self.graph.add_node(
            node.id,
            type=node.type.value,
            name=node.name,
            qualified_name=node.qualified_name,
            file_path=node.file_path,
            lineno=node.lineno,
            end_lineno=node.end_lineno,
            metadata=node.metadata,
        )

    def add_edge(self, edge: GraphEdge) -> None:
        self.graph.add_edge(
            edge.source,
            edge.target,
            type=edge.type.value,
            metadata=edge.metadata,
        )

    def build(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> None:
        for node in nodes:
            self.add_node(node)
        for edge in edges:
            self.add_edge(edge)

    def successors_by_type(self, node_id: str, edge_type: EdgeType) -> list[str]:
        result: list[str] = []
        for _, target, data in self.graph.out_edges(node_id, data=True):
            if data.get("type") == edge_type.value:
                result.append(target)
        return result

    def predecessors_by_type(self, node_id: str, edge_type: EdgeType) -> list[str]:
        result: list[str] = []
        for source, _, data in self.graph.in_edges(node_id, data=True):
            if data.get("type") == edge_type.value:
                result.append(source)
        return result

    def get_callers(self, node_id: str) -> list[str]:
        return self.predecessors_by_type(node_id, EdgeType.CALLS)

    def get_callees(self, node_id: str) -> list[str]:
        return self.successors_by_type(node_id, EdgeType.CALLS)

    def get_downstream_dependencies(self, node_id: str) -> list[str]:
        visited: set[str] = set()
        result: list[str] = []
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for _, target, data in self.graph.out_edges(current, data=True):
                edge_type = data.get("type")
                if target not in visited and edge_type in {EdgeType.CALLS.value, EdgeType.DEPENDS_ON.value, EdgeType.IMPORTS.value}:
                    visited.add(target)
                    result.append(target)
                    queue.append(target)
        return result

    def get_upstream_dependencies(self, node_id: str) -> list[str]:
        visited: set[str] = set()
        result: list[str] = []
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            for source, _, data in self.graph.in_edges(current, data=True):
                edge_type = data.get("type")
                if source not in visited and edge_type in {EdgeType.CALLS.value, EdgeType.DEPENDS_ON.value, EdgeType.IMPORTS.value}:
                    visited.add(source)
                    result.append(source)
                    queue.append(source)
        return result

    def get_impact_paths(self, start: str, end: str) -> list[list[str]]:
        visited: set[str] = set()
        paths: list[list[str]] = []

        def dfs(current: str, path: list[str]) -> None:
            if current == end:
                paths.append(path.copy())
                return
            if current in visited:
                return
            visited.add(current)
            for _, target, data in self.graph.out_edges(current, data=True):
                edge_type = data.get("type")
                if edge_type in {EdgeType.CALLS.value, EdgeType.DEPENDS_ON.value}:
                    path.append(target)
                    dfs(target, path)
                    path.pop()
            visited.discard(current)

        dfs(start, [start])
        return paths

    def downstream_callers(self, node_id: str) -> list[str]:
        visited: set[str] = set()
        result: list[str] = []
        queue = [node_id]
        while queue:
            current = queue.pop(0)
            callers = self.predecessors_by_type(current, EdgeType.CALLS)
            for caller in callers:
                if caller not in visited:
                    visited.add(caller)
                    result.append(caller)
                    queue.append(caller)
        return result

    def node_count(self) -> int:
        return int(self.graph.number_of_nodes())

    def edge_count(self) -> int:
        return int(self.graph.number_of_edges())


__all__ = ["GenomeGraph"]
