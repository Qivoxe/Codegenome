from __future__ import annotations

from pathlib import Path

import pytest

from codegenome.graph import GenomeGraph
from codegenome.impact import ImpactEngine
from codegenome.ml.dataset import DatasetBuilder
from codegenome.ml.evaluate import ModelEvaluator
from codegenome.ml.features import FeatureExtractor
from codegenome.ml.predict import RiskPredictor
from codegenome.ml.train import ModelTrainer
from codegenome.parser import SourceParser

REPO_ROOT = Path(__file__).resolve().parent.parent / "sample_repo"


def test_feature_extractor_extracts_features() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values())
        + list(parser.method_nodes.values()),
        parser.edges,
    )
    extractor = FeatureExtractor(str(REPO_ROOT))
    features = extractor.extract("checkout.calculate_discount", graph)
    assert features.qualified_name == "checkout.calculate_discount"
    assert features.dependency_count >= 1
    assert features.call_depth >= 0
    assert features.centrality >= 1
    assert features.file_age_days >= 0.0
    assert features.recent_change_frequency >= 0.0


def test_dataset_builder_generates_dataframe() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )
    builder = DatasetBuilder(str(REPO_ROOT))
    df = builder.build(graph, ["checkout.calculate_discount", "checkout.checkout"])
    assert len(df) == 2
    assert "dependency_count" in df.columns
    assert "downstream_count" in df.columns
    assert "label" in df.columns
    assert df["label"].min() >= 0.0
    assert df["label"].max() <= 1.0


def test_model_trainer_trains_xgboost() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )
    builder = DatasetBuilder(str(REPO_ROOT))
    all_functions = list(parser.functions.keys())
    df = builder.build(graph, all_functions)
    if len(df) < 2:
        pytest.skip("Not enough data to train")
    trainer = ModelTrainer()
    result = trainer.train(df)
    assert "predictions" in result
    assert "actuals" in result
    assert len(result["predictions"]) == len(result["actuals"])
    assert all(0.0 <= p <= 1.0 for p in result["predictions"])


def test_model_evaluator_computes_metrics() -> None:
    evaluator = ModelEvaluator()
    actuals = [0.1, 0.9, 0.8, 0.2, 0.95, 0.05]
    predictions = [0.15, 0.85, 0.75, 0.25, 0.90, 0.10]
    result = evaluator.evaluate(actuals, predictions)
    assert 0.0 <= result.precision <= 1.0
    assert 0.0 <= result.recall <= 1.0
    assert 0.0 <= result.f1 <= 1.0
    assert result.roc_auc is None or 0.0 <= result.roc_auc <= 1.0
    assert result.confusion_matrix_data is not None
    assert "matrix" in result.confusion_matrix_data


def test_risk_predictor_predicts() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )
    builder = DatasetBuilder(str(REPO_ROOT))
    all_functions = list(parser.functions.keys())
    df = builder.build(graph, all_functions)
    if len(df) < 2:
        pytest.skip("Not enough data to train")
    trainer = ModelTrainer()
    trainer.train(df)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        trainer.save(tmp.name)
        predictor = RiskPredictor()
        predictor.load(tmp.name)
        features = {
            "dependency_count": 2.0,
            "downstream_count": 3.0,
            "call_depth": 2.0,
            "centrality": 5.0,
            "historical_changes": 1.0,
            "author_count": 1.0,
            "lines_changed": 10.0,
            "file_age_days": 30.0,
            "recent_change_frequency": 0.1,
            "files_affected": 2.0,
            "affected_components": 2.0,
        }
        pred = predictor.predict(features)
        assert "risk" in pred
        assert "level" in pred
        assert 0.0 <= pred["risk"] <= 1.0


def test_impact_engine_without_ml() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )
    engine = ImpactEngine(graph)
    report = engine.compute_impact("checkout.calculate_discount")
    assert report.ml_risk == 0.0
    assert report.ml_risk_level == "EXPERIMENTAL"
    assert report.llm_explanation == {}


def test_dataset_builder_persistence() -> None:
    parser = SourceParser(REPO_ROOT)
    parser.parse_repo()
    graph = GenomeGraph()
    graph.build(
        list(parser.modules.values())
        + list(parser.function_nodes.values()),
        parser.edges,
    )
    builder = DatasetBuilder(str(REPO_ROOT))
    df = builder.build(graph, ["checkout.calculate_discount"])
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        builder.save(df, tmp.name)
        loaded = builder.load(tmp.name)
        assert len(loaded) == len(df)
        assert list(loaded.columns) == list(df.columns)