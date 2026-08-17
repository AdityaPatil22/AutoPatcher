"""GitHub OAuth authentication routes and session management."""

from urllib.parse import urlencode

import httpx
import jwt
import time
from fastapi import APIRouter, Cookie, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session

import app.config as config
from app.db import get_db
from app.models_db import User

router = APIRouter(tags=["auth"])

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
COOKIE_NAME = "autopatch_session"
JWT_ALGORITHM = "HS256"


def _callback_url() -> str:
    return f"{config.BACKEND_URL.rstrip('/')}/api/auth/callback"


@router.get("/auth/github")
def github_login():
    """Redirect the user to GitHub's OAuth authorization page."""
    params = urlencode({
        "client_id": config.GITHUB_CLIENT_ID,
        "redirect_uri": _callback_url(),
        "scope": "read:user user:email repo",
    })
    return RedirectResponse(url=f"{GITHUB_AUTHORIZE_URL}?{params}")


@router.get("/auth/callback")
def github_callback(
    code: str | None = Query(default=None),
    error: str | None = Query(default=None),
    error_description: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Handle the OAuth callback: exchange code, fetch profile, upsert user, set session cookie."""
    if error or not code:
        detail = error_description or error or "GitHub OAuth failed: no authorization code received."
        raise HTTPException(status_code=400, detail=detail)
    token_resp = httpx.post(
        GITHUB_TOKEN_URL,
        data={
            "client_id": config.GITHUB_CLIENT_ID,
            "client_secret": config.GITHUB_CLIENT_SECRET,
            "code": code,
        },
        headers={"Accept": "application/json"},
        timeout=15,
    )
    token_data = token_resp.json()
    access_token = token_data.get("access_token")
    if not access_token:
        raise HTTPException(status_code=400, detail="GitHub OAuth failed: no access token returned.")

    user_resp = httpx.get(
        GITHUB_USER_URL,
        headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        timeout=10,
    )
    if user_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="Failed to fetch GitHub user profile.")

    profile = user_resp.json()
    github_id = profile["id"]
    username = profile.get("login", "")
    email = profile.get("email")
    avatar_url = profile.get("avatar_url", "")
    granted_scopes = {s.strip() for s in user_resp.headers.get("X-OAuth-Scopes", "").split(",") if s.strip()}
    has_repo_scope = "repo" in granted_scopes

    user = db.query(User).filter(User.github_id == github_id).first()
    if user:
        user.username = username
        user.email = email
        user.avatar_url = avatar_url
        user.has_repo_scope = has_repo_scope
        user.set_access_token(access_token)
    else:
        user = User(
            github_id=github_id,
            username=username,
            email=email,
            avatar_url=avatar_url,
            has_repo_scope=has_repo_scope,
        )
        user.set_access_token(access_token)
        db.add(user)

    db.commit()
    db.refresh(user)

    session_token = jwt.encode(
        {"github_id": github_id, "username": username, "exp": time.time() + 60 * 60 * 24 * 7},
        config.JWT_SECRET,
        algorithm=JWT_ALGORITHM,
    )

    response = RedirectResponse(url=config.FRONTEND_URL, status_code=302)
    response.set_cookie(
        key=COOKIE_NAME,
        value=session_token,
        httponly=True,
        secure=not config.FRONTEND_URL.startswith("http://"),
        samesite="lax",
        max_age=60 * 60 * 24 * 7,
        path="/",
    )
    return response


def get_current_user(
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User:
    """FastAPI dependency: decode session cookie and return the authenticated User, or raise 401."""
    if not session:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(session, config.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid session")

    user = db.query(User).filter(User.github_id == payload["github_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user_optional(
    session: str | None = Cookie(default=None, alias=COOKIE_NAME),
    db: Session = Depends(get_db),
) -> User | None:
    """Like get_current_user but returns None instead of raising 401."""
    if not session:
        return None
    try:
        payload = jwt.decode(session, config.JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.InvalidTokenError:
        return None
    return db.query(User).filter(User.github_id == payload["github_id"]).first()


@router.get("/auth/me")
def get_me(user: User = Depends(get_current_user)):
    """Return the currently authenticated user's profile, including token scope status."""
    return {
        "github_id": user.github_id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "has_repo_scope": user.has_repo_scope,
    }


@router.post("/auth/logout")
def logout():
    """Clear the session cookie."""
    response = JSONResponse(content={"status": "ok"})
    response.delete_cookie(key=COOKIE_NAME, path="/")
    return response
