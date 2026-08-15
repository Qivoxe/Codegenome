# ML Risk Prediction

## Purpose

The ML layer predicts the risk of a code change based on historical features extracted from Git history.

## Pipeline

### 1. Feature Extraction

`FeatureExtractor` computes 11 features for each function:

| Feature | Description |
|---------|-------------|
| `dependency_count` | Total callers + callees |
| `downstream_count` | Number of transitive callees |
| `call_depth` | Maximum call chain depth |
| `centrality` | Callers + callees |
| `historical_changes` | Number of commits touching the file |
| `author_count` | Unique authors who modified the file |
| `lines_changed` | Total lines changed across history |
| `file_age_days` | Age of the file in days |
| `recent_change_frequency` | Commits per day |
| `files_affected` | Number of files in downstream call graph |
| `affected_components` | Number of modules in downstream call graph |

### 2. Dataset Building

`DatasetBuilder` converts features into labeled training examples. Labels are generated using a deterministic heuristic that approximates real impact.

### 3. Model Training

`ModelTrainer` trains an XGBoost regressor:

- Algorithm: XGBRegressor
- Objective: reg:squarederror
- Max depth: 4
- Learning rate: 0.1
- Train/test split: 80/20
- Feature scaling: StandardScaler

### 4. Evaluation

`ModelEvaluator` computes:

- Precision
- Recall
- F1 Score
- ROC-AUC
- Confusion matrix

### 5. Prediction

`RiskPredictor` loads a trained model and returns:

- `risk`: Float between 0.0 and 1.0
- `level`: MINIMAL/LOW/MEDIUM/HIGH
- `features_used`: List of feature names

## Model Status

The model is **experimental**. It is trained on controlled fixture data from the sample repository. Do not treat ML risk as production-grade until trained on larger real-world history.

## Integration

The ML model is optional. The system works without it:

```python
engine = ImpactEngine(graph)  # deterministic only
engine = ImpactEngine(graph, risk_predictor=predictor)  # with ML
```

## Limitations

1. Small training dataset (fixture repository only)
2. Heuristic labels may not match real-world outcomes
3. No temporal validation (no train on past, test on future)
4. Features are file-level, not function-level for some historical metrics
