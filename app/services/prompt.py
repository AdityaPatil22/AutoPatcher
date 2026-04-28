SYSTEM_PROMPT = """\
You are a senior software engineer performing a code review and bug fix.
You will be given a bug report and the relevant source code.

Your response MUST be valid JSON with exactly these keys:
- "fixed_code": the complete corrected source file (not a snippet, the full file)
- "explanation": a concise explanation of what was wrong and what you changed

Rules:
- Preserve the original code style and structure
- Only change what is necessary to fix the described bug
- Do NOT add unrelated improvements or refactors
- Return the ENTIRE file content in "fixed_code", not just the changed lines
- Keep your explanation under 3 sentences\
"""


def build_prompt(ticket: dict, code_context: dict) -> list[dict]:
    """Build the message list for the LLM chat completion."""
    user_content = f"""\
## Bug Report

**Title:** {ticket["title"]}
**Description:** {ticket["description"]}

## Source File: `{code_context["filename"]}`

```python
{code_context["content"]}
```

Respond with JSON only. No markdown fences, no extra text.\
"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_content},
    ]
