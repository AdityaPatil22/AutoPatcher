"""LLM integration layer: call providers, parse responses, and sanitize code output."""

import json
import re

import app.config as config


def _scrub_key(text: str) -> str:
    """Remove the Gemini API key from any string to prevent accidental leakage."""
    if config.GEMINI_API_KEY and config.GEMINI_API_KEY in text:
        text = text.replace(config.GEMINI_API_KEY, "[REDACTED]")
    return re.sub(r"AIza[0-9A-Za-z_-]{35}", "[REDACTED]", text)


def call_llm(messages: list[dict]) -> dict:
    """Call the configured LLM provider and return parsed JSON response."""
    try:
        raw = _call_gemini(messages)
    except Exception as exc:
        raise RuntimeError(_scrub_key(str(exc))) from None

    return _parse_response(raw)


def _call_gemini(messages: list[dict]) -> str:
    """Send messages to the Google Gemini API using the google-genai SDK with thinking and search."""
    from google import genai
    from google.genai import types

    client = genai.Client(api_key=config.GEMINI_API_KEY)
    model = config.LLM_MODEL or "gemini-2.5-flash"

    system_parts = []
    contents = []
    for msg in messages:
        if msg["role"] == "system":
            system_parts.append(msg["content"])
        else:
            role = "model" if msg["role"] == "assistant" else "user"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=msg["content"])],
                )
            )

    THINKING_MODELS = {"gemini-3-flash-preview", "gemini-2.5-pro-preview-05-06"}

    config_kwargs = {
        "system_instruction": "\n\n".join(system_parts) if system_parts else None,
        "temperature": 0.2,
        "tools": [types.Tool(google_search=types.GoogleSearch())],
    }
    if model in THINKING_MODELS:
        config_kwargs["thinking_config"] = types.ThinkingConfig(thinking_level="HIGH")

    generate_config = types.GenerateContentConfig(**config_kwargs)

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_config,
    )
    return response.text


def _sanitize_code(code) -> str:
    """Fix common LLM output issues in code strings."""
    if isinstance(code, list):
        code = "\n".join(str(item) for item in code)

    if not code or not isinstance(code, str):
        return code or ""

    real_newlines = code.count("\n")
    escaped_newlines = code.count("\\n")
    if escaped_newlines > real_newlines and escaped_newlines > 3:
        code = code.replace("\\n", "\n").replace("\\t", "\t")

    code = re.sub(r"^(jsx|tsx|javascript|typescript|python|go|java|ruby|rust|cpp?|csharp|swift|kotlin)\n",
                  "", code, count=1)

    if code.count('\\"') > 2 and code.count('"') < code.count('\\"'):
        code = code.replace('\\"', '"')

    # Strip line number prefixes the LLM may have copied from the prompt
    lines = code.split("\n")
    stripped = [re.sub(r"^\s*\d+\s*\|\s?", "", line) for line in lines]
    if stripped != lines:
        code = "\n".join(stripped)

    return code


def _sanitize_result(result: dict) -> dict:
    """Recursively sanitize all code strings in the parsed LLM result."""
    if "fixed_code" in result:
        result["fixed_code"] = _sanitize_code(result["fixed_code"])

    if "fixes" in result and isinstance(result["fixes"], list):
        for fix in result["fixes"]:
            if not isinstance(fix, dict):
                continue
            if "fixed_code" in fix:
                fix["fixed_code"] = _sanitize_code(fix["fixed_code"])
            for change in fix.get("changes", []):
                if isinstance(change, dict):
                    if "original" in change:
                        change["original"] = _sanitize_code(change["original"])
                    if "modified" in change:
                        change["modified"] = _sanitize_code(change["modified"])

    return result


def _parse_response(raw) -> dict:
    """Parse raw LLM text into a dict, handling JSON fences, partial extraction, and fallbacks."""
    if raw is None:
        raw = ""
    if isinstance(raw, list):
        raw = "\n".join(
            part.get("text", str(part)) if isinstance(part, dict) else str(part)
            for part in raw
        )
    if not isinstance(raw, str):
        raw = str(raw)

    cleaned = raw.strip()

    fence_match = re.search(r"```(?:json)?\s*\n?(.*?)```", cleaned, re.DOTALL)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    try:
        return _sanitize_result(json.loads(cleaned))
    except json.JSONDecodeError:
        pass

    brace_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if brace_match:
        try:
            return _sanitize_result(json.loads(brace_match.group()))
        except json.JSONDecodeError:
            pass

    for key in ("fixed_code", "explanation"):
        pattern = rf'"{key}"\s*:\s*"((?:[^"\\]|\\.)*)"'
        match = re.search(pattern, cleaned, re.DOTALL)
        if match:
            extracted = {key: match.group(1).encode().decode("unicode_escape")}
            for other_key in ("fixed_code", "explanation"):
                if other_key != key:
                    other = re.search(
                        rf'"{other_key}"\s*:\s*"((?:[^"\\]|\\.)*)"',
                        cleaned,
                        re.DOTALL,
                    )
                    if other:
                        extracted[other_key] = other.group(1).encode().decode("unicode_escape")
            if "fixed_code" in extracted:
                return _sanitize_result(extracted)

    return {
        "fixed_code": cleaned,
        "explanation": "Warning: could not parse LLM JSON response. Returning raw text.",
    }
