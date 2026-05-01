"""Pydantic models and enums shared across the application."""

from enum import Enum

from pydantic import BaseModel, Field


class LLMProviderEnum(str, Enum):
    """Supported LLM provider backends."""
    local = "local"
    cloud = "cloud"


class CloudServiceEnum(str, Enum):
    """Cloud LLM services."""
    openai = "openai"
    gemini = "gemini"


class SearchModeEnum(str, Enum):
    """Code search strategies."""
    keyword = "keyword"
    semantic = "semantic"
    hybrid = "hybrid"


class TicketInput(BaseModel):
    """Input for generating a bug fix from a ticket description."""
    title: str = Field(..., min_length=1, examples=["Fix export button issue"])
    description: str = Field(
        ...,
        min_length=1,
        examples=["Export fails when user status is pending"],
    )
    file_hint: str | None = Field(
        default=None,
        description="Optional filename hint to narrow context search",
        examples=["user_service.py"],
    )


class FilePatch(BaseModel):
    """A single file's patch with original, fixed code, and unified diff."""
    file_path: str
    original_code: str
    fixed_code: str
    diff: str
    warning: str = ""


class PatchOutput(BaseModel):
    """Response containing generated patches and explanation."""
    ticket_title: str
    patches: list[FilePatch]
    explanation: str


class RefineInput(BaseModel):
    """Input for refining a previous fix with user feedback."""
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    feedback: str = Field(..., min_length=1, examples=["The fix should also dispatch fetchProducts in a useEffect"])
    file_hint: str | None = None
    previous_patches: list[FilePatch] = Field(..., description="Patches from the previous response")


class IndexRequest(BaseModel):
    """Request to index a repository directory."""
    repo_path: str = Field(..., min_length=1)


class ProviderRequest(BaseModel):
    """Request to change the LLM provider."""
    provider: LLMProviderEnum


class ModelRequest(BaseModel):
    """Request to change the LLM model name."""
    model: str = Field(..., min_length=1)


class ApiKeyRequest(BaseModel):
    """Request to set a cloud API key."""
    service: CloudServiceEnum
    api_key: str = Field(..., min_length=1)


class SearchModeRequest(BaseModel):
    """Request to change the code search strategy."""
    mode: SearchModeEnum


class MaxContextFilesRequest(BaseModel):
    """Request to change the max number of context files sent to the LLM."""
    max_files: int = Field(..., ge=1, le=20)
