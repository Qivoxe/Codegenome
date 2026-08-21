from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from codegenome.graph import GenomeGraph
from codegenome.ml.features import FeatureExtractor


@dataclass
class TrainingExample:
    qualified_name: str
    features: dict[str, float]
    label: float


class DatasetBuilder:
    def __init__(self, repo_path: str) -> None:
        self.repo_path = repo_path
        self.extractor = FeatureExtractor(repo_path)

    def build(self, graph: GenomeGraph, changed_functions: list[str]) -> pd.DataFrame:
        examples: list[TrainingExample] = []
        for func in changed_functions:
            features = self.extractor.extract(func, graph)
            score = self._heuristic_label(features)
            examples.append(
                TrainingExample(
                    qualified_name=func,
                    features=self._to_dict(features),
                    label=score,
                )
            )
        return pd.DataFrame([{"qualified_name": e.qualified_name, **e.features, "label": e.label} for e in examples])

    def _heuristic_label(self, features: Any) -> float:
        score = 0.0
        score += min(25.0, features.dependency_count * 5)
        score += min(25.0, features.downstream_count * 5)
        score += min(20.0, features.call_depth * 5)
        score += min(15.0, features.centrality * 2)
        score += min(15.0, features.historical_changes * 2)
        if features.author_count > 1:
            score += 5.0
        score += min(10.0, features.lines_changed / 10.0)
        if features.file_age_days < 7:
            score += 5.0
        if features.recent_change_frequency > 1.0:
            score += 5.0
        score += min(10.0, features.files_affected * 2)
        score += min(10.0, features.affected_components * 2)
        return float(min(1.0, score / 100.0))

    def _to_dict(self, features: Any) -> dict[str, float]:
        return {
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
        }

    def save(self, df: pd.DataFrame, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=False)

    def load(self, path: str) -> pd.DataFrame:
        return pd.read_csv(path)


__all__ = ["DatasetBuilder", "TrainingExample"]
