<div align="center">

# 🧬 CodeGenome

### Know what your code change could break — *before* production does.

`Git diff` tells you **what changed**. CodeGenome tells you **what that change touches**.

![status](https://img.shields.io/badge/status-hackathon%20MVP-orange)
![python](https://img.shields.io/badge/backend-Python%20%2F%20FastAPI-3776AB)
![frontend](https://img.shields.io/badge/frontend-Next.js%20%2F%20React%20Flow-black)
![license](https://img.shields.io/badge/license-add--your--license-lightgrey)

[Quick Start](#-quick-start-2-terminals) · [How It Works](#-how-it-works) · [60-Second Demo](#-60-second-judge-demo) · [Roadmap](#-roadmap)

</div>

---

## ⚡ The Pitch

A developer changes **one line**:

```diff
- amount = order.total
+ amount = order.total * 1.18
```

Git reports: `1 file changed, 1 line changed`.

What actually happens downstream:

```
order.total → payment amount → charge_card() → payment provider
order.total → invoice generation → tax calculation
```

**Change size ≠ change impact.** CodeGenome parses your repo into a dependency graph (a "Software Genome"), traces that graph from any changed function, and shows you — with evidence, not vibes — everything downstream that could break.

Built for large legacy codebases, monorepos, microservices, and payment/financial systems: places where no single engineer holds the whole call graph in their head.

---

## 🎬 60-Second Judge Demo

1. Paste a public GitHub URL (e.g. `github.com/tiangolo/fastapi`) → **Analyze Repository**
2. Watch it clone → parse → build the Software Genome live
3. Open **Software Genome** → search a real function in that repo
4. Hit **Analyze Impact** → show the Impact Score + affected components
5. Click into an **Impact Path** → show *why* (the actual call chain, not a black box)
6. Line to close with: *"Git told us what changed. CodeGenome tells us what that change touches — and why."*

---

## 🧠 How It Works

```
GitHub URL → Clone → Parse (Python AST) → Software Genome (NetworkX graph)
    → Impact Propagation → Risk Features → [optional ML] → [optional LLM explanation]
    → Developer Dashboard
```

**Design principle:** deterministic graph analysis is the source of truth. AI is an *explainer*, never the evidence.

```
Bad:   Code → LLM → "Looks risky"
Ours:  Code → Static Analysis → Graph → Evidence → Risk Score → LLM explains the evidence
```

If no LLM key is configured, the deterministic engine still works end-to-end — nothing about correctness depends on AI being switched on.

### The Software Genome

Four relationship types are enough to model real impact:

| Relationship | Meaning |
|---|---|
| `CONTAINS` | Module → Class → Function/Method |
| `CALLS` | Function → Function |
| `IMPORTS` | Module → Module |
| `DEPENDS_ON` | Module → Module |

Example trace for a single changed function:

```
calculate_discount()
        ↓
    checkout() ──┬── invoice() ──── refund()
                 ↓         ↓            ↓
             payment()  tax_engine() refund_calc()
                 ↓
          payment_provider
```

One "1 line changed" commit → **5 downstream components**, all surfaced automatically, with the call chain shown as evidence for each.

### Output: score + reasons, not just a label

CodeGenome never just says `HIGH RISK`. It shows the path:

> `checkout()` depends on `calculate_discount()`, and `payment()` is downstream of `checkout()` → **Impact Score: 78/100 · HIGH**

From that graph it can also derive a **targeted test plan** instead of "re-run everything":

```
REQUIRED   ✓ checkout_discount_test  ✓ payment_total_test  ✓ invoice_total_test
OPTIONAL   ○ analytics_discount_test
```

---

## 🏗️ Architecture

```
Browser → Next.js (:3000) → HTTP → FastAPI (:8000)
                                       ├── Git Analyzer
                                       ├── Source Parser (Python AST)
                                       ├── Software Genome (NetworkX)
                                       └── Impact Engine → [Risk/ML] → [LLM explain]
```

## 🛠️ Tech Stack

| Layer | Tech |
|---|---|
| Backend | Python, FastAPI, Uvicorn |
| Static Analysis | Python `ast` |
| Git Analysis | GitPython |
| Graph | NetworkX |
| Database | SQLite |
| Frontend | Next.js, React, TypeScript, Tailwind, React Flow |
| ML (optional) | scikit-learn, XGBoost |
| LLM (optional) | Provider-agnostic abstraction |
| Env / Tooling | `uv`, `npm` |

MVP is **local-first** — no paid cloud infra required to run or demo it.

---

## 🚀 Quick Start (2 terminals)

**Prereqs:** Python 3.12+, Node 20+, Git, `uv`, `npm`

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd codegenome
```

**Terminal 1 — Backend**
```bash
uv sync
uv run uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```
→ API: `http://localhost:8000` · Docs: `http://localhost:8000/docs`

**Terminal 2 — Frontend**
```bash
cd frontend
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL=http://localhost:8000
npm run dev
```
→ App: `http://localhost:3000`

Then paste a public GitHub repo URL into the UI and hit **Analyze Repository**. Results are generated from *that* repo — never a hardcoded demo.

<details>
<summary><strong>Troubleshooting</strong></summary>

- `uvicorn is not recognized` → always run through `uv run uvicorn ...`, not bare `uvicorn`
- `ModuleNotFoundError: No module named 'backend'` → you must run from the project root (`codegenome/`), not `codegenome/backend/`
- `--port $PORT` fails locally on Windows → `$PORT` is a hosting-platform env var; use `--port 8000` explicitly for local dev
- `uv sync` reports a locked/broken `.venv` → kill running python/uvicorn processes, delete `.venv`, re-run `uv sync`
- Frontend can't reach backend → confirm `http://localhost:8000/docs` loads, check `NEXT_PUBLIC_API_URL` in `.env.local`, check the Network tab

</details>

<details>
<summary><strong>Tests</strong></summary>

```bash
uv run pytest              # backend
uv run ruff check .        # lint, if configured
cd frontend && npm test    # frontend
npm run build               # production build check before committing
```

</details>

---

## 🔌 API Overview

```
GET  /health
POST /repositories/github
POST /repositories/{id}/analyze
GET  /analysis/{id}          GET /analysis/{id}/graph
GET  /analysis/{id}/functions
POST /analysis/{id}/impact   GET /analysis/{id}/impact
```
Live OpenAPI spec at `/docs` is the source of truth for the running version — endpoints above may evolve.

## 🔒 Security Posture

Repository source code is treated as **untrusted input**.

| Allowed | Never |
|---|---|
| Read source files, parse AST, read git metadata, build graphs | Auto-execute repo Python, npm scripts, shell scripts, Makefiles, setup scripts, tests |

Also: GitHub URL validation, safe temp dirs, path-traversal prevention, no `shell=True` on untrusted input, webhook signature verification, temp-repo cleanup.

## ⚠️ Known Limitations

- Static analysis can't perfectly resolve dynamic/reflective calls
- Python is the current primary analysis target (unsupported languages are reported honestly, not silently skipped)
- Impact scores need validation against real historical outcomes
- ML quality is bounded by available historical data — no fabricated accuracy numbers, ever
- LLM explanations are only as good as the graph evidence feeding them

## 🧭 Roadmap

| Phase | Focus |
|---|---|
| 1 — Core Intelligence *(current)* | Python parsing, git detection, genome graph, deterministic impact |
| 2 — Developer Platform | FastAPI + SQLite API, interactive React Flow dashboard |
| 3 — AI Intelligence | XGBoost risk model, evidence-grounded LLM explanations, test recommendation |
| 4 — Engineering Integration | GitHub PR bot, automated impact reports, multi-language (Tree-sitter) support |
| Future | OpenTelemetry runtime graphs, Graph Neural Networks, autonomous test selection |

## 🤝 Contributing

Focused PRs with tests + docs, no secrets, no arbitrary execution of repository code. Good first areas: Python parser edge cases, Tree-sitter language support, graph algorithms, impact scoring, visualization.

## 📜 License

_Add your actual license here — don't claim one the repo doesn't have._

---

<div align="center">

**CodeGenome** — understand the impact before production does.

</div>
