"""Settings routes for configuring LLM provider, model, and API keys."""

from fastapi import APIRouter

import app.config as config
from app.models import (
    ApiKeyRequest,
    CloudServiceEnum,
    MaxContextFilesRequest,
    ModelRequest,
    ProviderRequest,
)

router = APIRouter(tags=["settings"])


def _mask_key(key: str) -> str:
    """Return a masked version of an API key, showing only first and last 4 chars."""
    if not key or len(key) < 8:
        return ""
    return key[:4] + "..." + key[-4:]


@router.get("/settings")
def get_settings():
    """Return current settings including provider, model, and keys."""
    has_openai = bool(config.OPENAI_API_KEY)
    has_gemini = bool(config.GEMINI_API_KEY)

    if config.GEMINI_API_KEY:
        cloud_backend = "gemini"
    elif config.OPENAI_API_KEY:
        cloud_backend = "openai"
    else:
        cloud_backend = None

    return {
        "provider": config.LLM_PROVIDER,
        "model": config.LLM_MODEL,
        "cloud_backend": cloud_backend,
        "cloud_available": has_openai or has_gemini,
        "openai_key_set": has_openai,
        "gemini_key_set": has_gemini,
        "openai_key_hint": _mask_key(config.OPENAI_API_KEY),
        "gemini_key_hint": _mask_key(config.GEMINI_API_KEY),
        "max_context_files": config.MAX_CONTEXT_FILES,
        "repo_path": str(config.SAMPLE_REPO_PATH) if config.SAMPLE_REPO_PATH else None,
    }


@router.put("/settings/provider")
def set_provider(req: ProviderRequest):
    """Update the LLM provider (local or cloud)."""
    config.LLM_PROVIDER = req.provider.value
    return {"provider": config.LLM_PROVIDER}


@router.put("/settings/model")
def set_model(req: ModelRequest):
    """Update the LLM model name."""
    config.LLM_MODEL = req.model
    return {"model": config.LLM_MODEL}


@router.put("/settings/api-key")
def set_api_key(req: ApiKeyRequest):
    """Store an API key for the specified cloud service."""
    if req.service == CloudServiceEnum.openai:
        config.OPENAI_API_KEY = req.api_key
    else:
        config.GEMINI_API_KEY = req.api_key
    return {
        "service": req.service.value,
        "key_hint": _mask_key(req.api_key),
    }


@router.put("/settings/max-context-files")
def set_max_context_files(req: MaxContextFilesRequest):
    """Update the maximum number of context files sent to the LLM."""
    config.MAX_CONTEXT_FILES = req.max_files
    return {"max_context_files": config.MAX_CONTEXT_FILES}
