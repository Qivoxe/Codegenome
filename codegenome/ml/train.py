from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler


class ModelTrainer:
    def __init__(self, random_state: int = 42) -> None:
        self.random_state = random_state
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            max_depth=4,
            learning_rate=0.1,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            objective="reg:squarederror",
        )
        self.scaler = StandardScaler()

    def train(self, df: pd.DataFrame, target_column: str = "label") -> dict[str, Any]:
        feature_columns = [c for c in df.columns if c not in {"qualified_name", target_column}]
        x = df[feature_columns]
        y = df[target_column]

        x_train, x_test, y_train, y_test = train_test_split(x, y, test_size=0.2, random_state=self.random_state)

        x_train_scaled = self.scaler.fit_transform(x_train)
        x_test_scaled = self.scaler.transform(x_test)

        self.model.fit(x_train_scaled, y_train)
        preds = self.model.predict(x_test_scaled)

        return {
            "feature_columns": feature_columns,
            "train_size": len(x_train),
            "test_size": len(x_test),
            "predictions": preds.tolist(),
            "actuals": y_test.tolist(),
            "feature_importances": dict(zip(feature_columns, self.model.feature_importances_.tolist())),
        }

    def save(self, path: str) -> None:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.model.save_model(path)
        import joblib
        joblib.dump(self.scaler, f"{path}.scaler")

    def load(self, path: str) -> None:
        self.model.load_model(path)
        import joblib
        self.scaler = joblib.load(f"{path}.scaler")


__all__ = ["ModelTrainer"]
