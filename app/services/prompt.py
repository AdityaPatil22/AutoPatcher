from pathlib import Path

EXTENSION_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".jsx": "jsx", ".ts": "typescript",
    ".tsx": "tsx", ".java": "java", ".go": "go", ".rb": "ruby", ".rs": "rust",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".swift": "swift", ".kt": "kotlin", ".vue": "vue", ".svelte": "svelte",
}

SYSTEM_PROMPT = """\
You are a senior software engineer performing a code review and bug fix.
You will be given a bug report and one or more relevant source files with line numbers.

Your response MUST be valid JSON with exactly these keys:
- "fixes": an array of objects, one per file that needs changes. Each object has:
  - "filename": the exact filename as provided
  - "changes": an array of modifications. Each modification has:
    - "original": the exact original lines from the source that need to change (copy them precisely, WITHOUT line numbers)
    - "modified": the replacement lines
- "explanation": a concise explanation of what was wrong and what you changed

Rules:
- In "original", copy the exact lines that need to change from the source code (do NOT include line numbers)
- In "modified", write the corrected version of those same lines
- Do NOT return the entire file — only the specific lines that need to change
- Keep each change small and focused: just the lines that fix the bug plus 1-2 surrounding lines for context
- Preserve indentation and code style exactly
- Only include files that actually need changes
- Keep your explanation under 3 sentences\
"""


def _lang_for_file(filename: str) -> str:
    ext = Path(filename).suffix.lower()
    return EXTENSION_TO_LANGUAGE.get(ext, "")


def _add_line_numbers(content: str) -> str:
    lines = content.split("\n")
    width = len(str(len(lines)))
    return "\n".join(f"{i + 1:>{width}} | {line}" for i, line in enumerate(lines))


def build_prompt(ticket: dict, contexts: list[dict]) -> list[dict]:
    files_section = ""
    for ctx in contexts:
        filename = ctx["filename"]
        language = _lang_for_file(filename)
        numbered = _add_line_numbers(ctx["content"])
        files_section += f"\n### `{filename}`\n\n```{language}\n{numbered}\n```\n"

    user_content = f"""\
## Bug Report

**Title:** {ticket["title"]}
**Description:** {ticket["description"]}

## Source Files
{files_section}
Fix the bug described above. Return ONLY the specific lines that need to change, not the entire file.
Line numbers are for reference only — do NOT include them in "original" or "modified".
Respond with JSON only. No markdown fences, no extra text.\
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]


def build_refine_prompt(
    ticket: dict,
    contexts: list[dict],
    previous_patches: list[dict],
    feedback: str,
) -> list[dict]:
    files_section = ""
    for ctx in contexts:
        filename = ctx["filename"]
        language = _lang_for_file(filename)
        numbered = _add_line_numbers(ctx["content"])
        files_section += f"\n### `{filename}`\n\n```{language}\n{numbered}\n```\n"

    original_user = f"""\
## Bug Report

**Title:** {ticket["title"]}
**Description:** {ticket["description"]}

## Source Files
{files_section}
Fix the bug described above. Return ONLY the specific lines that need to change, not the entire file.
Line numbers are for reference only — do NOT include them in "original" or "modified".
Respond with JSON only. No markdown fences, no extra text.\
"""

    import json
    previous_response = json.dumps({
        "fixes": [
            {
                "filename": p["file_path"],
                "changes": [{"original": "(previous attempt)", "modified": p.get("fixed_code", "")[:500]}],
            }
            for p in previous_patches
        ],
        "explanation": "Previous attempt.",
    })

    feedback_message = f"""\
Your previous fix was not correct. Here is the feedback:

{feedback}

Please revise your fix based on this feedback. Look at the ORIGINAL source files shown earlier and provide the corrected search/replace changes.
Respond with the same JSON format. No markdown fences, no extra text.\
"""

    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": original_user},
        {"role": "assistant", "content": previous_response},
        {"role": "user", "content": feedback_message},
    ]
