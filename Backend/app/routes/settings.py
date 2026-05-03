"""Settings routes for configuring LLM provider and model."""

from fastapi import APIRouter, Depends

import app.config as config
from app.models import (
    MaxContextFilesRequest,
    ModelRequest,
    ProviderRequest,
)
from app.models_db import User
from app.routes.auth import get_current_user_optional

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings(user: User | None = Depends(get_current_user_optional)):
    """Return current settings including provider and model."""
    return {
        "provider": config.LLM_PROVIDER,
        "model": config.LLM_MODEL,
        "gemini_available": bool(config.GEMINI_API_KEY),
        "max_context_files": config.MAX_CONTEXT_FILES,
        "repo_path": user.repo_path if user else None,
    }


@router.put("/settings/provider")
def set_provider(req: ProviderRequest):
    """Update the LLM provider (local or gemini)."""
    config.LLM_PROVIDER = req.provider.value
    return {"provider": config.LLM_PROVIDER}


@router.put("/settings/model")
def set_model(req: ModelRequest):
    """Update the LLM model name."""
    config.LLM_MODEL = req.model
    return {"model": config.LLM_MODEL}


@router.put("/settings/max-context-files")
def set_max_context_files(req: MaxContextFilesRequest):
    """Update the maximum number of context files sent to the LLM."""
    config.MAX_CONTEXT_FILES = req.max_files
    return {"max_context_files": config.MAX_CONTEXT_FILES}
