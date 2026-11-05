# Deployment

Follow the root README. Python dependencies include FastAPI, HTTPX, Tree-sitter Language Pack and scikit-learn. Optional AI requires Ollama on the backend host; remote Ollama URLs are intentionally rejected.

Free hosting may sleep and limits change. Set `VITE_API_URL`, exact CORS origins and do not commit secrets. In-memory jobs/results do not survive restarts or work across multiple backend instances. No paid service is required locally.
