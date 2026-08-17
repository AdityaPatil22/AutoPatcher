"""Settings routes for configuring LLM provider and model."""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import app.config as config
from app.db import get_db
from app.models import (
    MaxContextFilesRequest,
    ModelRequest,
    ProviderRequest,
)
from app.models_db import User
from app.routes.auth import get_current_user, get_current_user_optional
from app.routes.fix import LLM_DAILY_LIMIT

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings(user: User | None = Depends(get_current_user_optional)):
    """Return current settings including provider and model, per-user if logged in."""
    llm_remaining = LLM_DAILY_LIMIT
    if user:
        today = datetime.now(timezone.utc).date()
        used = user.llm_requests_today if user.llm_requests_date == today else 0
        llm_remaining = max(0, LLM_DAILY_LIMIT - used)

    return {
        "provider": (user.llm_provider if user and user.llm_provider else config.LLM_PROVIDER),
        "model": (user.llm_model if user and user.llm_model else config.LLM_MODEL),
        "api_key_set": bool(config.API_KEY),
        "max_context_files": (user.max_context_files if user and user.max_context_files else config.MAX_CONTEXT_FILES),
        "repo_path": user.repo_path if user else None,
        "ollama_url": "http://localhost:11434",
        "llm_requests_remaining": llm_remaining,
        "llm_daily_limit": LLM_DAILY_LIMIT,
        "backend_url": config.BACKEND_URL,
    }


@router.put("/settings/provider")
def set_provider(req: ProviderRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the LLM provider for the current user."""
    user.llm_provider = req.provider.value
    db.commit()
    return {"provider": user.llm_provider}


@router.put("/settings/model")
def set_model(req: ModelRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the LLM model name for the current user."""
    user.llm_model = req.model
    db.commit()
    return {"model": user.llm_model}


@router.put("/settings/max-context-files")
def set_max_context_files(req: MaxContextFilesRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Update the maximum number of context files sent to the LLM for the current user."""
    user.max_context_files = req.max_files
    db.commit()
    return {"max_context_files": user.max_context_files}
