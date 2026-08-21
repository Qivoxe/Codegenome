from __future__ import annotations

from typing import Any

import pandas as pd

from codegenome.ml.train import ModelTrainer


class RiskPredictor:
    def __init__(self, model_path: str | None = None) -> None:
        self.trainer = ModelTrainer()
        self._feature_names: list[str] = []
        self._loaded = False
        if model_path:
            self.load(model_path)

    def load(self, model_path: str) -> None:
        self.trainer.load(model_path)
        booster = self.trainer.model.get_booster()
        names = booster.feature_names if hasattr(booster, "feature_names") else None
        if names:
            self._feature_names = list(names)
        else:
            self._feature_names = [
                "dependency_count",
                "downstream_count",
                "call_depth",
                "centrality",
                "historical_changes",
                "author_count",
                "lines_changed",
                "file_age_days",
                "recent_change_frequency",
                "files_affected",
                "affected_components",
            ]
        self._loaded = True

    def predict(self, features: dict[str, float]) -> dict[str, Any]:
        if not self._loaded:
            return {"risk": 0.0, "level": "EXPERIMENTAL", "note": "Model not loaded. Using deterministic score only."}
        row = {k: features.get(k, 0.0) for k in self._feature_names}
        df = pd.DataFrame([row])
        x = df[self._feature_names]
        x_scaled = self.trainer.scaler.transform(x)
        risk = float(self.trainer.model.predict(x_scaled)[0])
        risk = max(0.0, min(1.0, risk))
        level = self._risk_to_level(risk)
        return {
            "risk": round(risk, 4),
            "level": level,
            "features_used": list(features.keys()),
        }

    def _risk_to_level(self, risk: float) -> str:
        if risk >= 0.75:
            return "HIGH"
        if risk >= 0.5:
            return "MEDIUM"
        if risk >= 0.25:
            return "LOW"
        return "MINIMAL"


__all__ = ["RiskPredictor"]
