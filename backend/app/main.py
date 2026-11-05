from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.repositories import router
from app.api.routes.intelligence import router as intelligence_router
from app.core.config import settings
app=FastAPI(title=settings.app_name,version="1.0.0",description="Static analysis for public GitHub repositories. Submitted code is never executed.")
app.add_middleware(CORSMiddleware,allow_origins=settings.origins,allow_credentials=False,allow_methods=["GET","POST"],allow_headers=["Content-Type"])
app.include_router(intelligence_router,prefix="/api/v1")
app.include_router(router,prefix="/api/v1")
@app.get("/health")
def health():return {"status":"ok","service":"repomind-api"}
