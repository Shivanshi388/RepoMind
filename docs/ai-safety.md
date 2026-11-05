# Phase 3 retrieval and AI safety

Source is chunked into bounded text windows. BM25 runs locally and returns exact file/line ranges. When a loopback Ollama service is reachable, the top lexical candidates can be reranked using local embeddings. Ollama chat receives retrieved excerpts only. The system prompt treats repository text as untrusted data and says not to follow instructions found in it. Requests with no evidence are not answered with repository-specific claims; citations are also returned as structured data.

Debug output is labeled as hypotheses. Review and PR findings are heuristics, not confirmed vulnerabilities or approvals. Public PR access is read-only. Repository code, builds, tests and dependencies are never executed or installed. No cloud LLM or paid inference is used.
