# Phase 2 ML

Runtime model training and evaluation are implemented in `backend/app/engines/ml/risk.py`. The endpoint fits per-repository LogisticRegression only when time-ordered snapshots have adequate labels; otherwise it returns an explainable heuristic. Bug-fix labels are commit-message proxies, not confirmed defects. No dataset or model artifact is stored.
