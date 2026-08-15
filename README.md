# CodeGenome - Phase 4

## What was built

Phase 4 adds GitHub PR integration, security hardening, final documentation, and a deterministic demo on top of the existing CodeGenome Phase 1+2+3 platform.

### GitHub PR Integration
- **Webhook endpoint** (`POST /github/webhook`) with HMAC-SHA256 signature verification
- **GitHub REST API client** for posting PR comments
- **Secure repository manager** that clones PR branches into isolated temp directories
- **PR comment formatter** that generates markdown impact reports
- Supports `pull_request.opened`, `pull_request.synchronize`, `pull_request.reopened`

### Security
- Repository path validation and sandboxing
- Webhook signature verification
- No repository code execution on host
- Secrets loaded from environment variables only
- No secrets in logs

### Demo
- **Deterministic e-commerce repository** (`demo_repo/`) with realistic Git history
- **`python scripts/demo.py`** runs real analysis and prints:
  - What changed
  - Changed functions
  - Impact score and risk level
  - Affected components
  - Why the change is risky
  - Recommended tests
  - ASCII dashboard visualization

### Documentation
- `docs/architecture.md` — System architecture and data flow
- `docs/software-genome.md` — Graph structure and queries
- `docs/impact-engine.md` — Impact propagation algorithm
- `docs/ml.md` — ML pipeline and model status
- `docs/demo.md` — Demo instructions and GitHub webhook setup

## Repository structure

```
codegenome/
  pyproject.toml
  README.md

  codegenome/
    __init__.py
    models.py
    parser.py
    graph.py
    impact.py
    git_engine.py
    report.py
    llm.py
    security.py
    github.py
    pr_comment.py

    ml/
      features.py
      dataset.py
      train.py
      evaluate.py
      predict.py

  backend/
    app/
      main.py
      database.py
      models.py
      schemas.py
      routes/
        health.py
        repositories.py
        analysis.py
        github.py
      services/
        repository_service.py
        analysis_service.py
    tests/
      conftest.py
      test_api.py

  frontend/
    app/
      layout.tsx
      page.tsx
      globals.css
    components/
      GenomeGraph.tsx
      ImpactCard.tsx
    lib/
      api.ts

  tests/
    test_codegenome.py
    test_git_engine.py
    test_github.py
    test_ml.py
    test_llm.py

  demo_repo/
    checkout.py
    payment.py
    order.py
    invoice.py
    refund.py
    analytics.py
    notification.py

  sample_repo/
    checkout.py
    payment.py
    order.py
    invoice.py
    refund.py
    analytics.py
    notification.py

  scripts/
    demo.py
    demo_analysis.py

  docs/
    architecture.md
    software-genome.md
    impact-engine.md
    ml.md
    demo.md
```

## Running tests

```bash
# All tests (Phase 1 + Phase 2 + Phase 3 + Phase 4)
pytest tests/ backend/tests -v

# Frontend lint
cd frontend && npm run lint

# Frontend build
cd frontend && npm run build
```

## Test coverage

- **45 total tests passed**
  - 14 Phase 1 core tests (parser, graph, impact)
  - 6 Git engine tests
  - 7 ML pipeline tests (features, dataset, training, evaluation, prediction, persistence)
  - 4 LLM explanation tests (fallback, empty inputs, API key handling)
  - 8 GitHub/security tests (webhook signature, secure repo manager, PR comment formatting)
  - 3 FastAPI backend tests (health, create repo, list repos)
  - 3 GitHub webhook API tests

## Quick start

```bash
# Install dependencies
pip install -e .

# Run demo
python scripts/demo.py

# Start backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload

# Start frontend
cd frontend && npm run dev
```

## Environment variables

```bash
# GitHub webhook secret (required for webhook endpoint)
GITHUB_WEBHOOK_SECRET="your-webhook-secret"

# GitHub token for PR comments (optional)
GITHUB_TOKEN="your-github-token"

# LLM configuration (optional)
CODEGENOME_LLM_API_KEY="your-openai-key"
CODEGENOME_LLM_BASE_URL="https://api.openai.com/v1"
CODEGENOME_LLM_MODEL="gpt-4o-mini"
```

## GitHub webhook setup

1. Create a GitHub App or use a personal access token
2. Set `GITHUB_WEBHOOK_SECRET` and `GITHUB_TOKEN` environment variables
3. Configure webhook URL: `https://your-host/github/webhook`
4. Select events: `Pull requests`
5. When a PR is opened/synchronized/reopened, CodeGenome will:
   - Verify the webhook signature
   - Clone the PR branch
   - Run full analysis
   - Post a comment with the impact report

## Demo output

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
`checkout.calculate_discount` has 1 direct caller(s): `checkout.checkout`.
1 transitive caller(s) depend on this change: `order.create_order`.
Impact spans 2 module(s), increasing blast radius.

WHAT COULD BREAK?
  - checkout
  - order

RECOMMENDED TESTS:
  [PASS] checkout_test
  [PASS] order_test
```

## Known limitations

1. **ML model**: experimental, trained on small fixture data
2. **LLM**: no streaming, no retry logic, single-shot request
3. **Graph layout**: deterministic hash-based positioning
4. **Backend concurrency**: synchronous analysis only
5. **GitHub**: requires manual webhook configuration; no built-in GitHub App installation flow

## Future roadmap

- Neo4j persistence for large-scale graphs
- OpenTelemetry observability
- GNN-based impact prediction (PyTorch Geometric)
- Multi-language analysis (JavaScript/TypeScript, Go)
- Runtime behavior graph
- Autonomous test generation
- Kubernetes deployment
- Cloud deployment
