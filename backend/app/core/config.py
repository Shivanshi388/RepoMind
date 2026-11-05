import os
from pathlib import Path

# Read the local .env without requiring a dotenv package; process environment wins.
def _load_env_file():
    env_file=Path(__file__).resolve().parents[2]/".env"
    if not env_file.exists(): return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line=line.strip()
        if not line or line.startswith("#") or "=" not in line: continue
        key,value=line.split("=",1)
        os.environ.setdefault(key.strip(),value.strip().strip("\"'"))
_load_env_file()
class Settings:
    app_name=os.getenv("APP_NAME","RepoMind API")
    environment=os.getenv("ENVIRONMENT","development")
    cors_origins=os.getenv("CORS_ORIGINS","http://localhost:5173")
    github_token=os.getenv("GITHUB_TOKEN","")
    max_files=int(os.getenv("MAX_FILES","2000"))
    max_file_bytes=int(os.getenv("MAX_FILE_BYTES","512000"))
    max_total_bytes=int(os.getenv("MAX_TOTAL_BYTES","20971520"))
    max_repo_tree_entries=int(os.getenv("MAX_REPO_TREE_ENTRIES","100000"))
    ollama_url=os.getenv("OLLAMA_URL","http://127.0.0.1:11434").rstrip("/")
    ollama_chat_model=os.getenv("OLLAMA_CHAT_MODEL","qwen2.5-coder:3b")
    ollama_embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL","embeddinggemma")
    @property
    def ollama_enabled(self):
        from urllib.parse import urlparse
        parsed=urlparse(self.ollama_url)
        return parsed.scheme=="http" and parsed.hostname in {"localhost","127.0.0.1","::1"}
    @property
    def origins(self): return [x.strip() for x in self.cors_origins.split(",") if x.strip()]
settings=Settings()
