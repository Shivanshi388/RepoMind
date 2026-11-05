# Phase 2 risk model

The endpoint inspects up to 25 recent commits and changed-file statistics. A commit-message regex provides noisy bug-fix proxy labels. Historical snapshots use only earlier commit counts, line churn and recency; the target is whether a file appears in a bug-fix-labelled commit in the next four commits. A four-commit purge separates training from the time-ordered holdout.

When both partitions have enough examples and classes, scikit-learn LogisticRegression is fitted on standardized features. The endpoint reports holdout precision, recall, F1 and average precision, plus a top-k churn-only baseline. Model output ranks current files; scores are not calibrated probabilities. Sparse or one-class data receives an explainable heuristic instead.

The proxy labels can be wrong, evaluation is repository-specific, and deleted files are not modeled. Broader multi-repository validation and label review are required before making stronger claims.
