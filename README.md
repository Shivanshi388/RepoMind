# RepoMind — Codebase Intelligence

RepoMind analyzes public GitHub repositories and turns their structure, symbols, dependencies, and source into an explorable engineering archive. This project contains a runnable three-phase product foundation using React + Vite and FastAPI. Deterministic analysis works without an LLM, and submitted code is never executed.

## Implemented

- Public GitHub URL validation, metadata/tree ingestion, commit-pinned archive download.
- Background analysis jobs and same-process commit cache with progress.
- Repository overview, language distribution, file explorer, line-numbered source viewer, symbol list.
- Python AST parsing and Tree-sitter attempt for supported languages, with conservative fallback extraction.
- Relative-import dependency graph, lexical/symbol search, measured file insights, deterministic complexity estimates.
- Editorial ivory UI with horizontal repository tabs and responsive layouts.
- File, archive and repository limits; skips common generated/build/dependency/secret paths.
- **Phase 2:** recent commit churn, explainable history-based review ranking, time-ordered logistic-regression experiment when data allows, holdout metrics and churn baseline; impact paths; token similarity; test suggestions.
- **Phase 3:** BM25 retrieval with source ranges, optional local Ollama embedding reranking and RAG chat, debugging hypotheses, static code review, commit comparison and public PR diff analysis.

## Limits and interpretation

This is a portfolio foundation, not a production service. ML labels come from commit-message wording and can be wrong; scores are relative rankings, never calibrated bug probabilities. Training is skipped when history lacks enough examples. At most 25 recent commit details are inspected. Impact misses dynamic relationships; similarity uses token overlap; test ideas are suggestions and repository tests are never run. Pull request checks inspect added diff lines and are advisory.

AI and semantic reranking require a local Ollama server and models. Without Ollama, BM25 retrieval, citations, static findings, debugging evidence and PR analysis still work; generated explanations are reported unavailable rather than fabricated. Code is supplied as untrusted quoted context. No hosted or paid LLM is used. Ollama chat and embedding requests use its local API endpoints ([API schema](https://github.com/ollama/ollama/blob/main/docs/openapi.yaml)).

The graph displays a manageable node subset without zoom, pan or filters. The viewer uses lightweight token highlighting. Job/results cache is process-local and disappears at restart. MongoDB Atlas is documented but not wired in; authentication and multi-user quotas are absent.

## Project layout

`frontend/` contains the Vite app (`src/pages`, reusable `src/components`, `src/services`, `src/styles`). `backend/app/` contains versioned routes, GitHub/history/intelligence services, parsing, graph/analysis and ML engines. `backend/tests/` contains unit tests. `ml/` and `docs/` contain evaluation and operations notes.

## Requirements

- Python 3.11+
- Node.js 20+
- Internet access for GitHub API and package installation
- Optional public-only GitHub token to improve API rate limits

## Run in VS Code

Backend terminal:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8000
```

Frontend terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open the Vite URL, normally http://localhost:5173, and enter a public repository URL such as `https://github.com/pallets/flask`. API docs are available at http://localhost:8000/docs.

## Optional local AI

Install and start Ollama separately, then pull the configured models if you want generated answers and semantic reranking:

```powershell
ollama pull qwen2.5-coder:3b
ollama pull embeddinggemma
```

Defaults are in `backend/.env.example`; change model names to ones available locally. Hardware needs vary. RepoMind only connects to loopback Ollama URLs.

## Configuration and safeguards

`backend/.env.example` has API/CORS and configurable file/archive/tree limits. Copy it to `.env`; never commit secrets. `GITHUB_TOKEN` is optional and should not include private-repository access. Only `github.com/{owner}/{repo}` is accepted. Archive redirects are restricted to GitHub archive hosts. Repository code is never executed and dependencies are never installed.

Defaults: 2,000 eligible files, 500 KB/file, 20 MB archive/source cap, 100,000 tree entries. GitHub rate limits apply.

## Checks

`cd backend; python -m pytest` and `cd frontend; npm run build`. See `docs/` for architecture, API routes, data model, AI safety, deployment limits and ML evaluation.
