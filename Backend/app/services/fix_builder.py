"""Build file patches from LLM results by matching, normalizing, and applying changes."""

import logging
from pathlib import Path

from app.models import FilePatch
from app.utils.diff import generate_unified_diff
from app.utils.patch import apply_changes

logger = logging.getLogger(__name__)


def match_context(filename: str, contexts: list[dict]) -> dict | None:
    """Find the best matching context entry for a filename returned by the LLM."""
    fname_lower = filename.lower()
    fname_base = Path(filename).name.lower()

    for ctx in contexts:
        ctx_name = ctx["filename"].lower()
        if ctx_name == fname_lower or ctx_name == fname_base:
            return ctx

    for ctx in contexts:
        if Path(ctx["filename"]).name.lower() == fname_base:
            return ctx

    for ctx in contexts:
        if fname_base in ctx["filename"].lower() or ctx["filename"].lower() in fname_lower:
            return ctx

    return None


def normalize_fixes(llm_result: dict) -> list[dict]:
    """Extract and normalize fixes from the LLM result, handling common structural variations."""
    fixes = llm_result.get("fixes", [])

    if isinstance(fixes, dict):
        fixes = [fixes]

    if not fixes:
        if "filename" in llm_result or "file" in llm_result:
            fixes = [llm_result]
        elif "changes" in llm_result and isinstance(llm_result["changes"], list):
            fixes = [llm_result]

    normalized = []
    for fix in fixes:
        if not isinstance(fix, dict):
            continue

        fname = fix.get("filename") or fix.get("file") or fix.get("file_path", "")
        changes = fix.get("changes", [])

        if isinstance(changes, dict):
            changes = [changes]

        if not changes and "original" in fix and "modified" in fix:
            changes = [{"original": fix["original"], "modified": fix["modified"]}]

        normalized.append({"filename": fname, "changes": changes, **fix})

    return normalized


def validate_full_file(original: str, fixed: str) -> str:
    """Check if a full-file replacement looks valid, returning a warning message if not."""
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


def build_patches(llm_result: dict, contexts: list[dict]) -> list[FilePatch]:
    """Convert LLM fix results into FilePatch objects with diffs and warnings."""
    patches = []

    fixes = normalize_fixes(llm_result)
    logger.info("Normalized %d fixes from LLM result", len(fixes))

    for fix in fixes:
        fname = fix.get("filename", "")
        ctx = match_context(fname, contexts)
        if not ctx:
            if len(contexts) == 1:
                logger.info("Single context fallback for unmatched filename: %s", fname)
                ctx = contexts[0]
            else:
                logger.warning("No context match for LLM filename: %s", fname)
                continue

        changes = fix.get("changes", [])

        if changes:
            logger.info(
                "Applying %d changes to %s", len(changes), ctx["filename"]
            )
            for i, c in enumerate(changes):
                orig_preview = str(c.get("original", ""))[:80]
                logger.info("  Change %d original: %s", i, repr(orig_preview))

            fixed_code = apply_changes(ctx["content"], changes)
            warning = ""
            if fixed_code == ctx["content"]:
                warning = (
                    "None of the search/replace blocks matched the source code. "
                    "The LLM may have copied the original lines incorrectly."
                )
        elif fix.get("fixed_code"):
            fixed_code = fix["fixed_code"]
            warning = validate_full_file(ctx["content"], fixed_code)
        else:
            continue

        diff = generate_unified_diff(ctx["content"], fixed_code, ctx["filename"])
        patches.append(FilePatch(
            file_path=ctx["filename"],
            original_code=ctx["content"],
            fixed_code=fixed_code,
            diff=diff,
            warning=warning,
        ))

    if not patches and "fixed_code" in llm_result:
        ctx = contexts[0]
        fixed_code = llm_result["fixed_code"]
        warning = validate_full_file(ctx["content"], fixed_code)
        diff = generate_unified_diff(ctx["content"], fixed_code, ctx["filename"])
        patches.append(FilePatch(
            file_path=ctx["filename"],
            original_code=ctx["content"],
            fixed_code=fixed_code,
            diff=diff,
            warning=warning,
        ))

    return patches
