"""Routes for generating and refining bug-fix patches."""

import logging
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.models import BuildPatchesRequest, PatchOutput, PromptOutput, RefineInput, TicketInput
from app.models_db import User
from app.routes.auth import get_current_user
from app.services.context import get_top_contexts
from app.services.fix_builder import build_patches
from app.services.llm import call_llm, _parse_response
from app.services.prompt import build_prompt, build_refine_prompt
import app.config as config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["patch"])

# ---------------------------------------------------------------------------
# In-memory prompt session cache for browser-local LLM flow
# ---------------------------------------------------------------------------
_prompt_sessions: dict[str, dict] = {}
_SESSION_TTL = 600  # 10 minutes


def _store_session(contexts: list[dict], ticket_title: str) -> str:
    """Store context for later patch building and return a session ID."""
    now = time.time()
    expired = [k for k, v in _prompt_sessions.items() if now - v["ts"] > _SESSION_TTL]
    for k in expired:
        del _prompt_sessions[k]

    sid = uuid.uuid4().hex
    _prompt_sessions[sid] = {"contexts": contexts, "ticket_title": ticket_title, "ts": now}
    return sid


def _get_session(session_id: str) -> dict:
    """Retrieve a stored session, raising 404 if expired or missing."""
    session = _prompt_sessions.pop(session_id, None)
    if not session or time.time() - session["ts"] > _SESSION_TTL:
        raise HTTPException(status_code=404, detail="Prompt session expired or not found. Please generate a new prompt.")
    return session


def _flatten_messages(messages: list[dict]) -> str:
    """Convert chat messages into a single prompt string for Ollama /api/generate."""
    parts = []
    for msg in messages:
        role = msg["role"].upper()
        parts.append(f"[{role}]\n{msg['content']}")
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# Standard flow (backend calls the LLM)
# ---------------------------------------------------------------------------

@router.post("/generate-fix", response_model=PatchOutput)
def generate_fix(ticket: TicketInput, _user: User = Depends(get_current_user)):
    """Generate code patches for a bug described in the ticket."""
    contexts = get_top_contexts(
        ticket.description, ticket.file_hint,
        user_id=_user.id, repo_path=_user.repo_path,
    )

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
    contexts = get_top_contexts(
        refine.description, refine.file_hint,
        user_id=_user.id, repo_path=_user.repo_path,
    )

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


# ---------------------------------------------------------------------------
# Browser-local LLM flow: backend prepares prompt, browser calls Ollama
# ---------------------------------------------------------------------------

@router.post("/generate-prompt", response_model=PromptOutput)
def generate_prompt(ticket: TicketInput, _user: User = Depends(get_current_user)):
    """Prepare the LLM prompt and context without calling the LLM.

    The frontend calls the user's local Ollama with the returned prompt,
    then submits the raw response to /build-patches.
    """
    contexts = get_top_contexts(
        ticket.description, ticket.file_hint,
        user_id=_user.id, repo_path=_user.repo_path,
    )

    if not contexts:
        raise HTTPException(
            status_code=404,
            detail="Could not find relevant source code for this bug description.",
        )

    messages = build_prompt(ticket.model_dump(), contexts)
    session_id = _store_session(contexts, ticket.title)
    model_hint = config.LLM_MODEL or "llama3"

    return PromptOutput(
        session_id=session_id,
        prompt=_flatten_messages(messages),
        messages=messages,
        model_hint=model_hint,
    )


@router.post("/refine-prompt", response_model=PromptOutput)
def refine_prompt(refine: RefineInput, _user: User = Depends(get_current_user)):
    """Prepare a refinement prompt without calling the LLM."""
    contexts = get_top_contexts(
        refine.description, refine.file_hint,
        user_id=_user.id, repo_path=_user.repo_path,
    )

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

    session_id = _store_session(contexts, refine.title)
    model_hint = config.LLM_MODEL or "llama3"

    return PromptOutput(
        session_id=session_id,
        prompt=_flatten_messages(messages),
        messages=messages,
        model_hint=model_hint,
    )


@router.post("/build-patches", response_model=PatchOutput)
def build_patches_from_raw(req: BuildPatchesRequest):
    """Parse raw LLM output (from the user's local Ollama) into structured patches."""
    session = _get_session(req.session_id)

    try:
        llm_result = _parse_response(req.raw_response)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Could not parse LLM response: {e}")

    logger.info("Browser-LLM result keys: %s", list(llm_result.keys()))

    explanation = llm_result.get("explanation", "No explanation provided.")
    patches = build_patches(llm_result, session["contexts"])

    return PatchOutput(
        ticket_title=session["ticket_title"],
        patches=patches,
        explanation=explanation,
    )
