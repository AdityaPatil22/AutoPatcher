from pydantic import BaseModel, Field


class TicketInput(BaseModel):
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
    file_path: str
    original_code: str
    fixed_code: str
    diff: str
    warning: str = ""


class PatchOutput(BaseModel):
    ticket_title: str
    patches: list[FilePatch]
    explanation: str


class RefineInput(BaseModel):
    title: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    feedback: str = Field(..., min_length=1, examples=["The fix should also dispatch fetchProducts in a useEffect"])
    file_hint: str | None = None
    previous_patches: list[FilePatch] = Field(..., description="Patches from the previous response")
