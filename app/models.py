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


class PatchOutput(BaseModel):
    ticket_title: str
    file_path: str
    original_code: str
    fixed_code: str
    diff: str
    explanation: str
