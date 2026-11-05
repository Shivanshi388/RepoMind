# Architecture

React/Vite calls a FastAPI modular monolith. GitHub ingestion validates public URLs, reads metadata/tree and downloads a bounded archive. Static analysis filters source, extracts Python AST and Tree-sitter symbols/imports, and builds file relationships. No source is executed.

Phase 2 derives impact paths, token similarity and test suggestions. A history service fetches up to 25 commit details. The ML engine uses chronological snapshots and purges overlapping forward-label windows; it fits LogisticRegression only when the holdout is adequate, otherwise it reports a transparent heuristic.

Phase 3 retrieves BM25 chunks and citations. Optional Ollama calls are restricted to loopback: `/api/embed` reranks candidates and `/api/chat` generates from retrieved excerpts. Retrieval and deterministic checks remain available when Ollama is offline. PR endpoints use GitHub read-only APIs.

Jobs/results are process-local and cleared on backend restart. Multi-instance hosting needs durable storage, throttling, cleanup, authentication and concurrency controls. MongoDB Atlas is not connected yet.
