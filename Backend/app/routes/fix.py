"""Routes for generating and refining bug-fix patches."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from app.models import PatchOutput, RefineInput, TicketInput
from app.models_db import User
from app.routes.auth import get_current_user
from app.services.context import get_top_contexts
from app.services.fix_builder import build_patches
from app.services.llm import call_llm
from app.services.prompt import build_prompt, build_refine_prompt

logger = logging.getLogger(__name__)

router = APIRouter(tags=["patch"])


@router.post("/generate-fix", response_model=PatchOutput)
def generate_fix(ticket: TicketInput, _user: User = Depends(get_current_user)):
    """Generate code patches for a bug described in the ticket."""
    contexts = get_top_contexts(ticket.description, ticket.file_hint)

    if not contexts:
        raise HTTPException(
            status_code=404,
            detail="Could not find relevant source code for this bug description.",
        )

    messages = build_prompt(ticket.model_dump(), contexts)

    try:
        llm_result = call_llm(messages)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    logger.info("LLM result keys: %s", list(llm_result.keys()))

    explanation = llm_result.get("explanation", "No explanation provided.")
    patches = build_patches(llm_result, contexts)

    return PatchOutput(
        ticket_title=ticket.title,
        patches=patches,
        explanation=explanation,
    )


@router.post("/refine-fix", response_model=PatchOutput)
def refine_fix(refine: RefineInput, _user: User = Depends(get_current_user)):
    """Refine a previous fix based on user feedback."""
    contexts = get_top_contexts(refine.description, refine.file_hint)

    if not contexts:
        raise HTTPException(
            status_code=404,
            detail="Could not find relevant source code for this bug description.",
        )

    previous_patches = [p.model_dump() for p in refine.previous_patches]

    messages = build_refine_prompt(
        ticket={"title": refine.title, "description": refine.description},
        contexts=contexts,
        previous_patches=previous_patches,
        feedback=refine.feedback,
    )

    try:
        llm_result = call_llm(messages)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    explanation = llm_result.get("explanation", "No explanation provided.")
    patches = build_patches(llm_result, contexts)

    return PatchOutput(
        ticket_title=refine.title,
        patches=patches,
        explanation=explanation,
    )
