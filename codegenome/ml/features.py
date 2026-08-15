from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from codegenome.git_engine import GitEngine


@dataclass
class FunctionFeatures:
    qualified_name: str
    file_path: str
    lineno: int
    dependency_count: int = 0
    downstream_count: int = 0
    call_depth: int = 0
    centrality: int = 0
    historical_changes: int = 0
    author_count: int = 0
    lines_changed: int = 0
    file_age_days: float = 0.0
    recent_change_frequency: float = 0.0
    files_affected: int = 0
    affected_components: int = 0


class FeatureExtractor:
    def __init__(self, repo_path: str) -> None:
        self.repo_path = repo_path
        self.git_engine = GitEngine(repo_path)

    def extract(self, function_qualified_name: str, graph: Any) -> FunctionFeatures:
        file_path, lineno = self._parse_qualified_name(function_qualified_name)
        commit_history = self._get_commit_history(file_path)
        first_commit = commit_history[-1] if commit_history else None
        file_age_days = self._compute_file_age_days(first_commit)
        recent_change_frequency = self._compute_recent_change_frequency(commit_history)

        historical_changes = len(commit_history)
        authors = {c.author for c in commit_history if c.author}
        author_count = len(authors)
        lines_changed = sum(self._count_changed_lines(c, file_path) for c in commit_history)

        callers = graph.get_callers(function_qualified_name)
        callees = graph.get_callees(function_qualified_name)
        centrality = len(callers) + len(callees)

        visited: set[str] = set()
        queue = list(callees)
        downstream_count = 0
        while queue:
            current = queue.pop(0)
            if current not in visited:
                visited.add(current)
                downstream_count += 1
                queue.extend(graph.get_callees(current))

        visited2: set[str] = set()
        queue2 = [function_qualified_name]
        max_depth = 0
        while queue2:
            current = queue2.pop(0)
            if current not in visited2:
                visited2.add(current)
                for callee in graph.get_callees(current):
                    max_depth = max(max_depth, 1)
                    queue2.append(callee)

        affected_components = len({name.split(".")[0] for name in visited})
        files_affected = len({self._qualified_to_file(n) for n in visited})

        return FunctionFeatures(
            qualified_name=function_qualified_name,
            file_path=file_path,
            lineno=lineno,
            dependency_count=len(callers) + len(callees),
            downstream_count=downstream_count,
            call_depth=max_depth,
            centrality=centrality,
            historical_changes=historical_changes,
            author_count=author_count,
            lines_changed=lines_changed,
            file_age_days=file_age_days,
            recent_change_frequency=recent_change_frequency,
            files_affected=files_affected,
            affected_components=affected_components,
        )

    def _parse_qualified_name(self, qualified_name: str) -> tuple[str, int]:
        parts = qualified_name.split(".")
        if len(parts) >= 2:
            module = ".".join(parts[:-1])
            return f"{module}.py", 1
        return "", 1

    def _qualified_to_file(self, qualified_name: str) -> str:
        parts = qualified_name.split(".")
        if len(parts) >= 2:
            module = ".".join(parts[:-1])
            return f"{module}.py"
        return qualified_name

    def _get_commit_history(self, file_path: str) -> list[Any]:
        commits = list(self.git_engine.repo.iter_commits("HEAD", paths=[file_path]))
        return commits

    def _compute_file_age_days(self, first_commit: Any) -> float:
        if not first_commit:
            return 0.0
        committed = first_commit.committed_datetime
        delta = datetime.now(committed.tzinfo) - committed
        return float(delta.total_seconds() / 86400.0)

    def _compute_recent_change_frequency(self, commits: list[Any]) -> float:
        if len(commits) < 2:
            return 0.0
        first = commits[-1].committed_datetime
        last = commits[0].committed_datetime
        delta = last - first
        if delta.total_seconds() <= 0:
            return 0.0
        return float(len(commits) / (delta.total_seconds() / 86400.0))

    def _count_changed_lines(self, commit: Any, file_path: str) -> int:
        try:
            stats = commit.stats.files.get(file_path, {})
            if hasattr(stats, "get"):
                return int(stats.get("insertions", 0)) + int(stats.get("deletions", 0))
            return 0
        except (AttributeError, KeyError):
            return 0


__all__ = ["FeatureExtractor", "FunctionFeatures"]
