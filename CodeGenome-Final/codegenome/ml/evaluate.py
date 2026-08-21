from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sklearn.metrics import (
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


@dataclass
class EvaluationResult:
    precision: float
    recall: float
    f1: float
    roc_auc: float | None = None
    confusion_matrix_data: dict[str, Any] | None = None
    feature_importances: dict[str, float] | None = None
    notes: str = ""


class ModelEvaluator:
    def __init__(self, threshold: float = 0.5) -> None:
        self.threshold = threshold

    def evaluate(self, actuals: list[float], predictions: list[float], feature_importances: dict[str, float] | None = None) -> EvaluationResult:
        y_true = [1 if a >= self.threshold else 0 for a in actuals]
        y_pred = [1 if p >= self.threshold else 0 for p in predictions]

        precision = precision_score(y_true, y_pred, zero_division=0)
        recall = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        cm = confusion_matrix(y_true, y_pred).tolist()
        labels = ["low", "high"] if len(cm) == 2 else ["class_0", "class_1"]
        cm_data = {
            "matrix": cm,
            "labels": labels,
        }

        try:
            roc_auc = roc_auc_score(y_true, predictions)
        except ValueError:
            roc_auc = None

        notes = "Experimental model trained on controlled fixture data. Results are illustrative."
        if len(set(y_true)) < 2:
            notes += " Only one class present in test set."

        return EvaluationResult(
            precision=precision,
            recall=recall,
            f1=f1,
            roc_auc=roc_auc,
            confusion_matrix_data=cm_data,
            feature_importances=feature_importances or {},
            notes=notes,
        )

    def to_dict(self, result: EvaluationResult) -> dict[str, Any]:
        return {
            "precision": result.precision,
            "recall": result.recall,
            "f1": result.f1,
            "roc_auc": result.roc_auc,
            "confusion_matrix": result.confusion_matrix_data,
            "feature_importances": result.feature_importances,
            "notes": result.notes,
        }


__all__ = ["EvaluationResult", "ModelEvaluator"]
