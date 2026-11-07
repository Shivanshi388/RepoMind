from datetime import datetime, timezone

from authlib.integrations.starlette_client import OAuth
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from pymongo import MongoClient, DESCENDING
from pymongo.errors import PyMongoError

from app.core.config import settings
from app.services.analysis import get_repository

router = APIRouter(tags=["account"])
client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=7000)
db = client[settings.mongodb_database]
users = db["users"]
user_repositories = db["user_repositories"]

oauth = OAuth()
oauth.register(
    name="github",
    client_id=settings.github_client_id,
    client_secret=settings.github_client_secret,
    authorize_url="https://github.com/login/oauth/authorize",
    access_token_url="https://github.com/login/oauth/access_token",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "read:user user:email"},
)

class SaveRepository(BaseModel):
    repository_id: str = Field(min_length=3, max_length=300)

def require_user(request: Request):
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Please sign in first.")
    user = users.find_one({"_id": user_id}, {"_id": 0, "github_id": 0})
    if not user:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Your session expired. Please sign in again.")
    return user_id, user

@router.get("/github/login")
async def github_login(request: Request):
    callback = request.url_for("github_callback")
    return await oauth.github.authorize_redirect(request, callback)

@router.get("/github/callback", name="github_callback")
async def github_callback(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
        profile_response = await oauth.github.get("user", token=token)
        profile_response.raise_for_status()
        profile = profile_response.json()

        email = profile.get("email")
        if not email:
            email_response = await oauth.github.get("user/emails", token=token)
            if email_response.is_success:
                emails = email_response.json()
                email = next(
                    (item["email"] for item in emails if item.get("primary") and item.get("verified")),
                    None
                )

        github_id = str(profile["id"])
        now = datetime.now(timezone.utc)
        user = {
            "_id": github_id,
            "github_id": github_id,
            "username": profile.get("login", "github-user"),
            "name": profile.get("name") or profile.get("login", "GitHub user"),
            "email": email,
            "avatar_url": profile.get("avatar_url"),
            "profile_url": profile.get("html_url"),
            "updated_at": now,
            "last_login_at": now,
        }
        users.update_one(
            {"_id": github_id},
            {"$set": user, "$setOnInsert": {"created_at": now}},
            upsert=True,
        )
        request.session.clear()
        request.session["user_id"] = github_id
        return RedirectResponse(f"{settings.frontend_url}/?login=success", status_code=302)
    except Exception as exc:
        print(f"GitHub OAuth callback failed: {type(exc).__name__}: {exc}", flush=True)
        request.session.clear()
        return RedirectResponse(f"{settings.frontend_url}/?login=failed", status_code=302)

@router.get("/me")
def me(request: Request):
    _, user = require_user(request)
    return user

@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}

@router.get("/repositories")
def my_repositories(request: Request):
    user_id, _ = require_user(request)
    try:
        rows = list(
            user_repositories.find({"user_id": user_id}, {"_id": 0})
            .sort("saved_at", DESCENDING)
            .limit(100)
        )
        return {"repositories": rows}
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Could not load your saved repositories.") from exc

@router.post("/repositories")
def save_repository(body: SaveRepository, request: Request):
    user_id, _ = require_user(request)
    repo = get_repository(body.repository_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Analyze this repository before saving it.")
    now = datetime.now(timezone.utc)
    row = {
        "user_id": user_id,
        "repository_id": repo["id"],
        "full_name": repo.get("full_name"),
        "name": repo.get("name"),
        "owner": repo.get("owner"),
        "description": repo.get("description"),
        "html_url": repo.get("html_url"),
        "default_branch": repo.get("default_branch"),
        "commit_sha": repo.get("commit_sha"),
        "file_count": repo.get("file_count", 0),
        "analyzed_at": repo.get("analyzed_at"),
        "saved_at": now,
    }
    try:
        user_repositories.update_one(
            {"user_id": user_id, "repository_id": body.repository_id},
            {"$set": row},
            upsert=True,
        )
        return {"saved": True, "repository": {k: v for k, v in row.items() if k != "user_id"}}
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Could not save this repository to your dashboard.") from exc

