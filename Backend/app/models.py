"""Pydantic models and enums shared across the application."""

from enum import Enum

from pydantic import BaseModel, Field, model_validator


class LLMProviderEnum(str, Enum):
    """Supported LLM provider backends."""
    gemini = "gemini"
    browser = "browser"



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
    """Request to index a repository via local path or GitHub URL."""
    repo_path: str | None = Field(default=None, min_length=1)
    github_url: str | None = Field(default=None, min_length=1, examples=["https://github.com/owner/repo"])

    @model_validator(mode="after")
    def at_least_one_source(self):
        if not self.repo_path and not self.github_url:
            raise ValueError("Provide either repo_path or github_url")
        return self


class ProviderRequest(BaseModel):
    """Request to change the LLM provider."""
    provider: LLMProviderEnum


class ModelRequest(BaseModel):
    """Request to change the LLM model name."""
    model: str = Field(..., min_length=1)


class MaxContextFilesRequest(BaseModel):
    """Request to change the max number of context files sent to the LLM."""
    max_files: int = Field(..., ge=1, le=20)


class PromptOutput(BaseModel):
    """Response from /generate-prompt containing the LLM prompt and a session ID for context reuse."""
    session_id: str
    prompt: str = Field(..., description="Flattened prompt string for Ollama /api/generate")
    messages: list[dict] = Field(..., description="Chat messages for Ollama /api/chat")
    model_hint: str = Field(default="llama3", description="Suggested model name")


class BuildPatchesRequest(BaseModel):
    """Submit raw LLM output to be parsed into patches using a stored prompt session."""
    session_id: str = Field(..., min_length=1)
    raw_response: str = Field(..., min_length=1)


class CreatePRRequest(BaseModel):
    """Request to create a GitHub Pull Request from generated patches."""
    ticket_title: str = Field(..., min_length=1)
    explanation: str = Field(default="")
    patches: list[FilePatch] = Field(..., min_items=1)
    base_branch: str | None = Field(default=None, description="Target branch (defaults to repo's default branch)")


class CreatePRResponse(BaseModel):
    """Response after successfully creating a Pull Request."""
    pr_number: int
    pr_url: str
    branch: str
