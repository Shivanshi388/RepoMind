# API

Base `/api/v1`; OpenAPI docs at `/docs`. Repository IDs are URL-encoded `owner/repository@commitSHA` values.

## Ingestion and exploration
- `POST /repositories/analyze` body `{ "url": "https://github.com/owner/repo" }`; returns job ID.
- `GET /repositories/jobs/{job_id}` returns stage/progress.
- `GET /repositories/{repo_id}` returns overview.
- `GET /repositories/{repo_id}/files` and `/files/content?path=...` return file metadata/source.
- `GET /repositories/{repo_id}/architecture`, `/insights`, `/search?q=...`. Search uses BM25 lexical ranking with symbol boosts.

## Phase 2
- `GET /repositories/{repo_id}/history`; up to 25 recent commit details.
- `GET /repositories/{repo_id}/risk`; time-split experiment when adequate data exists, otherwise heuristic.
- `GET /repositories/{repo_id}/impact?path=...`; reverse dependency closure and related tests.
- `GET /repositories/{repo_id}/similarity?path=...`; token Jaccard matches.
- `GET /repositories/{repo_id}/test-suggestions`; proposed checks, never executed.
- `POST /repositories/{repo_id}/compare` body `{ "base":"main", "head":"sha" }`.

## Phase 3
- `GET /repositories/{repo_id}/semantic-search?q=...`; BM25 plus optional local Ollama embedding rerank.
- `POST /repositories/{repo_id}/chat` body `{ "question":"..." }`; retrieved evidence and citations.
- `POST /repositories/{repo_id}/debug` body `{ "question":"..." }`; investigation hypotheses.
- `POST /repositories/{repo_id}/code-review` body `{ "path":"..." }` (optional path); static findings and optional local model review.
- `POST /repositories/{repo_id}/pull-request` body `{ "url":"https://github.com/owner/repo/pull/123" }`; public PR changed paths, impact and findings.
- `GET /health`.

Errors use FastAPI JSON detail responses. GitHub rate limits apply, especially to history inspection.
