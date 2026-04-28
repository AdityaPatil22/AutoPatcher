from fastapi import APIRouter, HTTPException

from app.models import PatchOutput, TicketInput
from app.services.context import get_best_context
from app.services.llm import call_llm
from app.services.prompt import build_prompt
from app.utils.diff import generate_unified_diff

router = APIRouter(tags=["patch"])


@router.post("/generate-fix", response_model=PatchOutput)
def generate_fix(ticket: TicketInput):
    """
    Accept a bug ticket, find relevant code, ask the LLM for a fix,
    and return the patch as a unified diff.
    """
    context = get_best_context(ticket.description, ticket.file_hint)

    if not context["content"] or context["content"] == "No relevant code found.":
        raise HTTPException(
            status_code=404,
            detail="Could not find relevant source code for this bug description.",
        )

    messages = build_prompt(ticket.model_dump(), context)

    try:
        llm_result = call_llm(messages)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"LLM call failed: {e}",
        )

    fixed_code = llm_result.get("fixed_code", "")
    explanation = llm_result.get("explanation", "No explanation provided.")

    diff = generate_unified_diff(context["content"], fixed_code, context["filename"])

    return PatchOutput(
        ticket_title=ticket.title,
        file_path=context["filename"],
        original_code=context["content"],
        fixed_code=fixed_code,
        diff=diff,
        explanation=explanation,
    )
