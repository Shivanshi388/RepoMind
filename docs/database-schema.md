# Data and persistence

MongoDB Atlas `repomind_db` remains the target database but is not wired up in this build. Jobs, analysis, history and embedding cache are process-local. They are lost at restart. Natural collections are repositories, analysis_jobs, files, symbols, dependencies and history metrics. Index repository + commit SHA, job ID and repository + path. Avoid one giant document and respect MongoDB's document-size limit.
