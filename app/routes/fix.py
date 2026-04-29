from fastapi import APIRouter, HTTPException

from app.models import FilePatch, PatchOutput, RefineInput, TicketInput
from app.services.context import get_top_contexts
from app.services.llm import call_llm
from app.services.prompt import build_prompt, build_refine_prompt
from app.utils.diff import generate_unified_diff
from app.utils.patch import apply_changes

router = APIRouter(tags=["patch"])


@router.post("/generate-fix", response_model=PatchOutput)
def generate_fix(ticket: TicketInput):
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

    explanation = llm_result.get("explanation", "No explanation provided.")
    patches = _build_patches(llm_result, contexts)

    return PatchOutput(
        ticket_title=ticket.title,
        patches=patches,
        explanation=explanation,
    )


@router.post("/refine-fix", response_model=PatchOutput)
def refine_fix(refine: RefineInput):
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
    patches = _build_patches(llm_result, contexts)

    return PatchOutput(
        ticket_title=refine.title,
        patches=patches,
        explanation=explanation,
    )


def _build_patches(llm_result: dict, contexts: list[dict]) -> list[FilePatch]:
    ctx_by_name = {ctx["filename"]: ctx for ctx in contexts}
    patches = []

    fixes = llm_result.get("fixes", [])
    for fix in fixes:
        fname = fix.get("filename", "")
        ctx = ctx_by_name.get(fname)
        if not ctx:
            continue

        changes = fix.get("changes", [])
        if changes:
            fixed_code = apply_changes(ctx["content"], changes)
            warning = ""
            if fixed_code == ctx["content"]:
                warning = (
                    "None of the search/replace blocks matched the source code. "
                    "The LLM may have copied the original lines incorrectly."
                )
        elif fix.get("fixed_code"):
            fixed_code = fix["fixed_code"]
            warning = _validate_full_file(ctx["content"], fixed_code)
        else:
            continue

        diff = generate_unified_diff(ctx["content"], fixed_code, fname)
        patches.append(FilePatch(
            file_path=fname,
            original_code=ctx["content"],
            fixed_code=fixed_code,
            diff=diff,
            warning=warning,
        ))

    if not patches and "fixed_code" in llm_result:
        ctx = contexts[0]
        fixed_code = llm_result["fixed_code"]
        warning = _validate_full_file(ctx["content"], fixed_code)
        diff = generate_unified_diff(ctx["content"], fixed_code, ctx["filename"])
        patches.append(FilePatch(
            file_path=ctx["filename"],
            original_code=ctx["content"],
            fixed_code=fixed_code,
            diff=diff,
            warning=warning,
        ))

    return patches


def _validate_full_file(original: str, fixed: str) -> str:
    orig_lines = original.count("\n") + 1
    fixed_lines = fixed.count("\n") + 1

    if orig_lines > 10 and fixed_lines / orig_lines < 0.3:
        return (
            f"Patch removes too much code ({orig_lines} -> {fixed_lines} lines). "
            "The LLM likely truncated the file instead of making a targeted fix."
        )

    if "..." in fixed and fixed.count("...") > fixed.count("\n") * 0.1:
        return (
            "Patch contains placeholder '...' instead of actual code. "
            "The LLM abbreviated the file instead of returning it in full."
        )

    return ""
