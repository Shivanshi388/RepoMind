from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from app.api.routes.repositories import router
from app.api.routes.intelligence import router as intelligence_router
from app.api.routes.auth import router as auth_router
from app.core.config import settings

if not settings.auth_secret_key:
    raise RuntimeError("AUTH_SECRET_KEY is missing from backend/.env")
if not settings.github_client_id or not settings.github_client_secret:
    raise RuntimeError("GITHUB_CLIENT_ID or GITHUB_CLIENT_SECRET is missing from backend/.env")
if not settings.mongodb_uri:
    raise RuntimeError("MONGODB_URI is missing from backend/.env")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Static analysis for public GitHub repositories. Submitted code is never executed."
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.auth_secret_key,
    session_cookie="repomind_session",
    max_age=1209600,
    same_site="lax",
    https_only=settings.environment != "development",
)
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(intelligence_router, prefix="/api/v1")
app.include_router(router, prefix="/api/v1")

@app.get("/health")
def health():
    return {"status": "ok", "service": "repomind-api"}
