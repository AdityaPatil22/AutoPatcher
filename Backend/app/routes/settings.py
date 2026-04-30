from enum import Enum

from fastapi import APIRouter
from pydantic import BaseModel, Field

import app.config as config

router = APIRouter(tags=["settings"])


class LLMProviderEnum(str, Enum):
    local = "local"
    cloud = "cloud"


class CloudServiceEnum(str, Enum):
    openai = "openai"
    gemini = "gemini"


class SearchModeEnum(str, Enum):
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"


class ProviderRequest(BaseModel):
    provider: LLMProviderEnum


class ModelRequest(BaseModel):
    model: str = Field(..., min_length=1)


class ApiKeyRequest(BaseModel):
    service: CloudServiceEnum
    api_key: str = Field(..., min_length=1)


class SearchModeRequest(BaseModel):
    mode: SearchModeEnum


class MaxContextFilesRequest(BaseModel):
    max_files: int = Field(..., ge=1, le=20)


def _mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return ""
    return key[:4] + "..." + key[-4:]


@router.get("/settings")
def get_settings():
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
        "search_mode": config.SEARCH_MODE,
        "max_context_files": config.MAX_CONTEXT_FILES,
        "repo_path": str(config.SAMPLE_REPO_PATH) if config.SAMPLE_REPO_PATH else None,
    }


@router.put("/settings/provider")
def set_provider(req: ProviderRequest):
    config.LLM_PROVIDER = req.provider.value
    return {"provider": config.LLM_PROVIDER}


@router.put("/settings/model")
def set_model(req: ModelRequest):
    config.LLM_MODEL = req.model
    return {"model": config.LLM_MODEL}


@router.put("/settings/api-key")
def set_api_key(req: ApiKeyRequest):
    if req.service == CloudServiceEnum.openai:
        config.OPENAI_API_KEY = req.api_key
    else:
        config.GEMINI_API_KEY = req.api_key
    return {
        "service": req.service.value,
        "key_hint": _mask_key(req.api_key),
    }


@router.put("/settings/search-mode")
def set_search_mode(req: SearchModeRequest):
    config.SEARCH_MODE = req.mode.value
    return {"search_mode": config.SEARCH_MODE}


@router.put("/settings/max-context-files")
def set_max_context_files(req: MaxContextFilesRequest):
    config.MAX_CONTEXT_FILES = req.max_files
    return {"max_context_files": config.MAX_CONTEXT_FILES}
