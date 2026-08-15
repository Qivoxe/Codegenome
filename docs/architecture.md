# CodeGenome Architecture

## Overview

CodeGenome is a deterministic software intelligence platform that predicts the potential impact of code changes by constructing a Software Genome: a graph representing dependencies, function calls, data flow, control flow, APIs, and eventually runtime behavior.

## Problem

Git diff tells developers WHAT changed.
CodeGenome tells developers WHAT COULD BREAK because of that change.

## Solution

CodeGenome analyzes Python repositories by:

1. Parsing source files using Python AST
2. Extracting modules, classes, functions, methods, imports, and function calls
3. Building a call/dependency graph using NetworkX
4. Propagating impact through the graph when a function changes
5. Computing deterministic impact scores
6. Optionally applying ML risk prediction
7. Optionally generating LLM explanations

## High-Level Architecture

```
Git Repository
      ↓
Git Change Detection
      ↓
Python AST Parser
      ↓
Software Genome (Graph)
      ↓
Impact Propagation
      ↓
Impact Score (Deterministic)
      ↓
ML Risk Prediction (Optional)
      ↓
LLM Explanation (Optional)
      ↓
Impact Report
      ↓
PR Comment (Optional)
      ↓
Interactive Dashboard
```

## Components

### Core Engine (`codegenome/`)

- `parser.py` — AST-based source parser
- `graph.py` — NetworkX graph wrapper with upstream/downstream queries
- `impact.py` — Deterministic impact propagation engine
- `git_engine.py` — Git change detection
- `models.py` — Pydantic schemas
- `report.py` — Markdown report renderer

### ML Pipeline (`codegenome/ml/`)

- `features.py` — Historical feature extraction from Git history
- `dataset.py` — Dataset builder with heuristic labels
- `train.py` — XGBoost model trainer
- `evaluate.py` — Model evaluator with precision/recall/F1/ROC-AUC
- `predict.py` — Risk predictor

### LLM Layer (`codegenome/llm.py`)

- Optional structured explanation generator
- Graceful fallback when no API key is configured

### GitHub Integration (`codegenome/github.py`, `backend/app/routes/github.py`)

- Webhook signature verification
- PR comment posting
- Repository cloning via secure manager

### Backend (`backend/`)

- FastAPI service wrapping the core engine
- SQLAlchemy + aiosqlite persistence
- Service layer architecture
- REST API endpoints

### Frontend (`frontend/`)

- Next.js 16 + React 19 + TypeScript + Tailwind
- React Flow interactive graph visualization
- Dark engineering UI

## Data Flow

1. **Repository Ingestion**: Git repo is cloned or validated
2. **Git Analysis**: Changed files and functions are detected
3. **Source Parsing**: Python AST extracts structural information
4. **Graph Construction**: NetworkX builds the Software Genome
5. **Impact Propagation**: BFS/DFS traverses upstream callers
6. **Score Computation**: Deterministic heuristic computes 0-100 score
7. **ML Prediction**: XGBoost model predicts risk (experimental)
8. **Explanation**: LLM or template generates human-readable explanation
9. **Report Generation**: Structured output with nodes, edges, paths
10. **Dashboard Display**: React Flow renders interactive graph

## Security Model

- Repository paths are validated and sandboxed
- Webhook signatures are verified using HMAC-SHA256
- No repository code is executed on the host
- Secrets are loaded from environment variables only
- No secrets are logged

## Free-Tier Constraints

- SQLite for persistence (no PostgreSQL/Redis)
- Local XGBoost for ML (no cloud ML)
- Optional local LLM API (no mandatory cloud services)
- No Kubernetes, no Neo4j, no Celery
