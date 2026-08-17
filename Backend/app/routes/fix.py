"""Routes for generating and refining bug-fix patches."""

import logging
import time
import uuid
from datetime import date, timezone, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import BuildPatchesRequest, PatchOutput, PromptOutput, RefineInput, TicketInput
from app.models_db import User
from app.routes.auth import get_current_user
from app.services.context import get_top_contexts
from app.services.fix_builder import build_patches
from app.services.indexer import is_index_stale
from app.services.llm import call_llm, _parse_response
from app.services.prompt import build_prompt, build_refine_prompt
import app.config as config

LLM_DAILY_LIMIT = config.LLM_DAILY_LIMIT

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
# Per-user daily LLM usage limiting
# ---------------------------------------------------------------------------

def _check_llm_limit(user: User, db: Session) -> None:
    today = datetime.now(timezone.utc).date()
    if user.llm_requests_date != today:
        user.llm_requests_today = 0
        user.llm_requests_date = today
        db.commit()
    if user.llm_requests_today >= LLM_DAILY_LIMIT:
        raise HTTPException(
            status_code=429,
            detail=f"Daily LLM request limit reached ({LLM_DAILY_LIMIT}/day). Try again tomorrow or use Local (Ollama).",
        )


def _increment_llm_usage(user: User, db: Session) -> None:
    user.llm_requests_today += 1
    db.commit()


def _raise_if_no_contexts(contexts: list, user_id: int) -> None:
    if contexts:
        return
    if is_index_stale(user_id):
        raise HTTPException(
            status_code=410,
            detail="Index stale — indexed files are no longer on disk. Please re-index your repository.",
        )
    raise HTTPException(
        status_code=404,
        detail="Could not find relevant source code for this bug description.",
    )


# ---------------------------------------------------------------------------
# Standard flow (backend calls the LLM)
# ---------------------------------------------------------------------------

@router.post("/generate-fix", response_model=PatchOutput)
def generate_fix(ticket: TicketInput, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Generate code patches for a bug described in the ticket."""
    _check_llm_limit(_user, db)

    contexts = get_top_contexts(
        ticket.description, ticket.file_hint,
        max_files=_user.max_context_files,
        user_id=_user.id, repo_path=_user.repo_path,
    )

    _raise_if_no_contexts(contexts, _user.id)

    messages = build_prompt(ticket.model_dump(), contexts)

    try:
        llm_result = call_llm(messages, provider=_user.llm_provider, model=_user.llm_model)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    _increment_llm_usage(_user, db)
    logger.info("LLM result keys: %s", list(llm_result.keys()))

    explanation = llm_result.get("explanation", "No explanation provided.")
    patches = build_patches(llm_result, contexts)

    return PatchOutput(
        ticket_title=ticket.title,
        patches=patches,
        explanation=explanation,
    )


@router.post("/refine-fix", response_model=PatchOutput)
def refine_fix(refine: RefineInput, _user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Refine a previous fix based on user feedback."""
    _check_llm_limit(_user, db)

    contexts = get_top_contexts(
        refine.description, refine.file_hint,
        max_files=_user.max_context_files,
        user_id=_user.id, repo_path=_user.repo_path,
    )

    _raise_if_no_contexts(contexts, _user.id)

    previous_patches = [p.model_dump() for p in refine.previous_patches]

    messages = build_refine_prompt(
        ticket={"title": refine.title, "description": refine.description},
        contexts=contexts,
        previous_patches=previous_patches,
        feedback=refine.feedback,
    )

    try:
        llm_result = call_llm(messages, provider=_user.llm_provider, model=_user.llm_model)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM call failed: {e}")

    _increment_llm_usage(_user, db)
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
        max_files=_user.max_context_files,
        user_id=_user.id, repo_path=_user.repo_path,
    )

    _raise_if_no_contexts(contexts, _user.id)

    messages = build_prompt(ticket.model_dump(), contexts)
    session_id = _store_session(contexts, ticket.title)
    model_hint = _user.llm_model or config.LLM_MODEL or "gemini-2.5-flash"

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
        max_files=_user.max_context_files,
        user_id=_user.id, repo_path=_user.repo_path,
    )

    _raise_if_no_contexts(contexts, _user.id)

    previous_patches = [p.model_dump() for p in refine.previous_patches]

    messages = build_refine_prompt(
        ticket={"title": refine.title, "description": refine.description},
        contexts=contexts,
        previous_patches=previous_patches,
        feedback=refine.feedback,
    )

    session_id = _store_session(contexts, refine.title)
    model_hint = _user.llm_model or config.LLM_MODEL or "gemini-2.5-flash"

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
