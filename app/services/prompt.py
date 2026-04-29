from pathlib import Path

EXTENSION_TO_LANGUAGE = {
    ".py": "python", ".js": "javascript", ".jsx": "jsx", ".ts": "typescript",
    ".tsx": "tsx", ".java": "java", ".go": "go", ".rb": "ruby", ".rs": "rust",
    ".c": "c", ".cpp": "cpp", ".h": "c", ".hpp": "cpp", ".cs": "csharp",
    ".swift": "swift", ".kt": "kotlin", ".vue": "vue", ".svelte": "svelte",
}

SYSTEM_PROMPT = """\
You are a senior software engineer performing a code review and bug fix.
You will be given a bug report and the relevant source code.

Your response MUST be valid JSON with exactly these keys:
- "fixed_code": the complete corrected source file (not a snippet, the full file)
- "explanation": a concise explanation of what was wrong and what you changed

Rules:
- Read the bug description carefully and make the FUNCTIONAL change needed to fix the described bug
- You MUST add, remove, or modify actual logic/code to fix the bug — not just formatting
- Do NOT change indentation, whitespace, spacing, or formatting of lines you are not fixing
- Preserve the original code style, indentation characters (tabs vs spaces), and indent width exactly
- Only change what is necessary to fix the described bug
- Do NOT add unrelated improvements or refactors
- Return the ENTIRE file content in "fixed_code", not just the changed lines
- Keep your explanation under 3 sentences\
"""


def build_prompt(ticket: dict, code_context: dict) -> list[dict]:
    filename = code_context["filename"]
    ext = Path(filename).suffix.lower()
    language = EXTENSION_TO_LANGUAGE.get(ext, "")

    user_content = f"""\
## Bug Report

**Title:** {ticket["title"]}
**Description:** {ticket["description"]}

## Source File: `{filename}`

```{language}
{code_context["content"]}
```

Fix the bug described above by making the necessary functional code changes.
Respond with JSON only. No markdown fences, no extra text.\
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
