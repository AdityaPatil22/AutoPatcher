from pathlib import Path

EXTENSION_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".jsx": "jsx", ".ts": "typescript",
    ".tsx": "tsx", ".java": "java", ".go": "go", ".rb": "ruby", ".rs": "rust",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".swift": "swift", ".kt": "kotlin", ".vue": "vue", ".svelte": "svelte",
}

SYSTEM_PROMPT = """\
You are a senior software engineer performing a code review and bug fix.
You will be given a bug report and one or more relevant source files.
The source files have line numbers in the format "N | code" for reference only.

Respond with valid JSON using this exact structure:
{
  "fixes": [
    {
      "filename": "<actual filename>",
      "changes": [
        {
          "original": "<exact lines from source that need to change>",
          "modified": "<corrected version of those lines>"
        }
      ]
    }
  ],
  "explanation": "<describe what the bug was and how your fix resolves it>"
}

Critical rules for "original":
- Copy the EXACT source code lines that need to change
- Do NOT include line numbers (no "1 |", "23 |", etc.)
- Include 1-2 surrounding context lines so the block is unique in the file
- Preserve the exact indentation (spaces/tabs) from the source

Critical rules for "modified":
- Write the corrected version of those same lines
- Keep the same indentation style as the original

Critical rules for "explanation":
- Describe the ACTUAL bug from the bug report and how your changes fix it
- Do NOT use a generic or placeholder explanation
- Keep it under 3 sentences

General rules:
- Only include files that actually need changes
- Keep each change small and focused\
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
