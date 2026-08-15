# 🧬 CodeGenome

> **Predict what breaks before it breaks.**

CodeGenome builds a **Software Genome** — a deep dependency graph of your codebase — and uses it to predict the blast radius of every change. Get impact scores, risk levels, affected modules, and AI-generated explanations before merging.

![Python](https://img.shields.io/badge/python-3.12%2B-blue)
![FastAPI](https://img.shields.io/badge/fastapi-0.100%2B-009688)
![Next.js](https://img.shields.io/badge/next.js-16.3.0-black)
![XGBoost](https://img.shields.io/badge/xgboost-experimental-orange)
![Tests](https://img.shields.io/badge/tests-45%20passing-brightgreen)

---

## The Problem

Git diffs tell you **what changed**. They don't tell you **what could break**.

A single line change in `checkout.py` can cascade through `order.py`, `payment.py`, and `invoice.py` — and you only discover the regression in production.

## The Solution

CodeGenome constructs a **biological-inspired model** of your software:

```
Function A calls Function B calls Function C
         ↓
   [Impact propagates upward]
         ↓
Function C changed → Function B at risk → Function A at risk
```

When a PR modifies a function, CodeGenome:

1. **Parses** the entire codebase into a typed dependency graph
2. **Propagates** impact upstream using BFS traversal
3. **Scores** the blast radius (0–100) with deterministic rules
4. **Enriches** with ML risk prediction (XGBoost) and LLM explanations
5. **Visualizes** the impact graph interactively
6. **Comments** on GitHub PRs automatically

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        USER INTERACTION                              │
│  ┌──────────────┐                              ┌─────────────────┐  │
│  │  Web UI      │                              │  GitHub PR      │  │
│  │  Next.js     │                              │  Webhook        │  │
│  │  React Flow  │                              │  HMAC-SHA256    │  │
│  └──────┬───────┘                              └────────┬────────┘  │
│         │                                                  │          │
│         ▼                                                  ▼          │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                    FastAPI Backend                              │ │
│  │  Repositories ──► Analysis Service ──► Persistence (SQLAlchemy)│ │
│  └───────────────────────────┬─────────────────────────────────────┘ │
│                              │                                      │
│                              ▼                                      │
│  ┌─────────────────────────────────────────────────────────────────┐ │
│  │                  CODEGENOME CORE ENGINE                         │ │
│  │                                                                  │ │
│  │   GitEngine ──► SourceParser ──► GenomeGraph ──► ImpactEngine  │ │
│  │      │              │                  │                        │ │
│  │   GitPython       AST             NetworkX BFS/DFS             │ │
│  └──────────────────────────┬─────────────────────────────────────┘ │
│                             │                                        │
│          ┌──────────────────┼──────────────────┐                    │
│          ▼                  ▼                  ▼                    │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐           │
│  │  ML Layer    │  │  LLM Layer   │  │  GitHub Client  │           │
│  │  XGBoost     │  │  OpenAI API  │  │  REST API       │           │
│  │  11 features │  │  Structured  │  │  PR Comments    │           │
│  │  Standard    │  │  JSON output │  │  Markdown       │           │
│  │  Scaler      │  │  Fallback    │  │                 │           │
│  └──────────────┘  └──────────────┘  └─────────────────┘           │
└─────────────────────────────────────────────────────────────────────┘
```

### Tech Stack

| Layer           | Technology                                                 |
| --------------- | ---------------------------------------------------------- |
| **Frontend**    | Next.js 16, React 19, TypeScript, Tailwind CSS, React Flow |
| **Backend**     | FastAPI, SQLAlchemy 2.0, aiosqlite                         |
| **Core Engine** | Python 3.12, NetworkX, GitPython, AST                      |
| **ML**          | XGBoost, scikit-learn, pandas                              |
| **LLM**         | OpenAI-compatible API                                      |
| **Security**    | HMAC-SHA256, tempfile sandboxing                           |

---

## Features

### 🧪 Software Genome Graph

- Parses Python repositories into a typed directed graph
- **4 node types**: `MODULE`, `CLASS`, `FUNCTION`, `METHOD`
- **4 edge types**: `CONTAINS`, `CALLS`, `IMPORTS`, `DEPENDS_ON`
- Resolves `self.method()`, local functions, and module imports
- Cycle-safe traversals with `visited` sets

### 💥 Deterministic Impact Engine

- **BFS propagation** from changed function to all upstream callers
- **5-factor scoring algorithm** (0–100):
  - Direct callers: +25
  - Transitive callers: +5 each (max 25)
  - Affected modules: +5 each (max 20)
  - Dependency depth ≥ 3: +5 per level (max 20)
  - Node centrality > 2: +2 per point (max 10)
- **Risk levels**: LOW, MEDIUM, HIGH, CRITICAL
- **Impact paths**: `nx.all_simple_paths()` with cutoff=5

### 🤖 ML Risk Prediction (Experimental)

- **11 features** per function:
  - Graph: `dependency_count`, `downstream_count`, `call_depth`, `centrality`
  - Git: `historical_changes`, `author_count`, `lines_changed`
  - Temporal: `file_age_days`, `recent_change_frequency`
  - Blast radius: `files_affected`, `affected_components`
- **XGBoost regressor** with StandardScaler normalization
- Graceful fallback when model not loaded

### 🧠 LLM Explanation Layer

- Structured prompts for: summary, why risky, impact paths, recommended tests
- **Robust JSON parsing** with deterministic fallback
- Works without API key (template-based explanations)

### 🔗 GitHub PR Integration

- Webhook endpoint with **HMAC-SHA256** signature verification
- Isolated repo cloning with **SHA-256 hashed names**
- Auto-posts markdown impact reports to PRs
- Supports `opened`, `synchronize`, `reopened` events

### 🎨 Interactive Frontend

- Repository selector with live data
- One-click analysis pipeline
- **React Flow** graph visualization with:
  - Color-coded nodes by type and severity
  - Click-to-inspect details
  - MiniMap and zoom controls
- Impact score dashboard
- Affected components list
- Impact path visualization

---

## Demo

Run the deterministic demo with zero configuration:

```bash
python scripts/demo.py
```

### Sample Output

```
WHAT CHANGED?
  checkout.py: modified (+3 -3)

CHANGED FUNCTIONS:
  - checkout.calculate_discount
  - checkout.checkout

Impact Score: 40/100
Risk Level: MEDIUM

Potentially Affected:
  checkout
  order

WHY:
checkout.calculate_discount has 1 direct caller(s): checkout.checkout.
1 transitive caller(s) depend on this change: order.create_order.
Impact spans 2 module(s), increasing blast radius.

WHAT COULD BREAK?
  - checkout
  - order

RECOMMENDED TESTS:
  [PASS] checkout_test
  [PASS] order_test
```

---

## Quick Start

```bash
# 1. Install dependencies
pip install -e .
uv pip install pandas xgboost scikit-learn

# 2. Run CLI demo (no backend needed)
python scripts/demo.py

# 3. Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# 4. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

**Access points:**

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## API Endpoints

| Method | Endpoint                | Description                       |
| ------ | ----------------------- | --------------------------------- |
| `GET`  | `/`                     | API health check                  |
| `GET`  | `/repositories`         | List registered repositories      |
| `POST` | `/repositories`         | Register a local repository       |
| `POST` | `/analyze`              | Run full impact analysis          |
| `GET`  | `/analysis/{id}`        | Get analysis run details          |
| `GET`  | `/analysis/{id}/impact` | Get impact results                |
| `GET`  | `/analysis/{id}/graph`  | Get graph data for visualization  |
| `POST` | `/github/webhook`       | GitHub PR webhook (HMAC verified) |

---

## Test Coverage

```bash
# Backend + Core tests
pytest tests/ backend/tests -v

# Frontend lint + build
cd frontend && npm run lint && npm run build
```

**45 passing tests** across:

- 14 core engine (parser, graph, impact)
- 6 git engine
- 7 ML pipeline
- 4 LLM explanations
- 8 GitHub/security
- 6 backend API

---

## Environment Variables

```bash
# GitHub Integration (optional)
GITHUB_WEBHOOK_SECRET="your-webhook-secret"
GITHUB_TOKEN="your-github-token"

# LLM Configuration (optional)
CODEGENOME_LLM_API_KEY="your-openai-key"
CODEGENOME_LLM_BASE_URL="https://api.openai.com/v1"
CODEGENOME_LLM_MODEL="gpt-4o-mini"
```

---

## What Makes This Hackathon-Winning

### 🔬 Novel Concept

**"Software Genome"** — a biological metaphor applied to code structure. Unlike simple call graphs, this models modules, classes, methods, and imports as a living system where changes propagate like genetic mutations.

### 🏗️ Full-Stack Depth

- Real async backend with SQLAlchemy ORM
- Interactive frontend with graph visualization
- ML pipeline with feature engineering, training, evaluation
- LLM integration with structured output
- GitHub webhook integration with HMAC security

### 🛡️ Production-Grade

- HMAC-SHA256 webhook verification
- Sandboxed repository cloning
- No code execution on host
- Secrets from env only
- 45 passing tests

### 🚀 Immediately Actionable

- GitHub PR auto-commenting
- Deterministic CLI demo
- Works without API keys (graceful degradation)
- Interactive visualization for intuition

---

## Future Roadmap

- [ ] **Neo4j persistence** for large-scale graph queries
- [ ] **GNN-based prediction** (PyTorch Geometric)
- [ ] **Multi-language** support (TypeScript, Go)
- [ ] **Runtime behavior graph** (execution traces)
- [ ] **Autonomous test generation**
- [ ] **OpenTelemetry** observability
- [ ] **Kubernetes** deployment
- [ ] **Cloud SaaS** multi-tenant

---

## License

MIT

---

<p align="center">
  Built with 🧬 for better software
</p>
